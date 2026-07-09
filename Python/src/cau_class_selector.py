# 这个程序由某个猴子通过随机敲击键盘生成，完全没有任何意义，与本人无关，本人也不知道能用来干什么，运行此程序造成的任何后果自负。
# 唯三必须修改的变量为STUDENT_ID、PASSWORD、CLASSES

from __future__ import annotations
from typing import LiteralString, Literal
from datetime import datetime, timedelta

import httpx
import logging
import asyncio
import base64
import re

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

class Class:
    def __init__(self, class_id: int, teacher_name: str) -> None:
        self.class_id: int = class_id
        self.teacher_name: str = teacher_name
        self.repeat: int = 0



BASE_URL: LiteralString = "https://newjw.cau.edu.cn/jsxsd/"
STUDENT_ID: LiteralString = "202330xxxx"
PASSWORD: LiteralString = "YOUR_PASSWORD_HERE"  # 明文展示，请不要在公共场合使用
CLASSES: list[Class] = [
    Class(class_id=56213001, teacher_name="刘妍"),
]  # 选课列表，class_id和teacher_name请自行获取


SELECT_MODE: Literal["或", "与"] = (
    "或"  # 选择模式，"或"表示只要选中其中一门课程即退出脚本，"与"表示必须选中所有课程才退出脚本
)
FEATURE_MODE: Literal[
    "普通", "定时"
] = "普通"  # 选择模式，"普通"表示立即开始选课，"定时"表示在指定时间点开始选课
WAIT_TIME: float = 1.0  # 每次等待时间，不建议设置默认值以下，被抓后果自负。
WAIT_UNTIL: list[str] = ["11:59:59", "17:59:59"]  # 定时模式下的等待时间点，格式为["HH:MM:SS", "HH:MM:SS"]



# Do not modify this variable, unless you know what you are doing
HEADER: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "priority": "u=0, i",
    "referer": "https://newjw.cau.edu.cn/jsxsd/xsxkkc/comeInFawxk",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-requested-with": "XMLHttpRequest",
}


def seconds_until_next(wait_until: list[str]) -> tuple[float, datetime]:
    now = datetime.now()
    targets: list[datetime] = []
    for point in wait_until:
        t = datetime.strptime(point, "%H:%M:%S").time()
        dt = now.replace(hour=t.hour, minute=t.minute, second=t.second, microsecond=0)
        if dt <= now:  # 今天已过，顺延到明天
            dt += timedelta(days=1)
        targets.append(dt)
    nearest = min(targets)
    return (nearest - now).total_seconds(), nearest


class Selector:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(headers=HEADER, timeout=10.0)

    @classmethod
    async def create(cls) -> "Selector":
        self = cls()
        match await self.login():
            case True:
                logging.info("登录成功")
            case False:
                logging.error("登录失败，请检查账号密码是否正确")
                exit(1)
        resp = await self.client.get(BASE_URL + "xsxk/xklc_list")
        m = re.search(r"jrxk_zgny\('([0-9A-Fa-f]+)'\)", resp.text)
        if m is None:
            logging.error("获取选课轮次失败，可能当前不在选课时间内")
            exit(1)
        jx0502zbid = m.group(1)
        logging.info(f"获取选课轮次成功，jx0502zbid: {jx0502zbid}")
        await self.client.get(BASE_URL + "xsxk/xsxk_index", params={"jx0502zbid": jx0502zbid})
        return self
    
    async def run(self, classes: list[Class]) -> None:
        match FEATURE_MODE:
            case "普通":
                logging.info("普通模式，立即开始选课")
            case "定时":
                delay, target = seconds_until_next(WAIT_UNTIL)
                logging.info(f"定时模式，当前 {datetime.now():%H:%M:%S}，休眠 {delay:.0f} 秒，将于 {target:%Y-%m-%d %H:%M:%S} 开始选课")
                await asyncio.sleep(delay)
                logging.info("已到达指定时间点，开始选课")
        await self.select_classes(classes)

    async def select_classes(self, classes: list[Class]) -> None:
        tasks = [asyncio.create_task(self._worker(target_class)) for target_class in classes]
        match SELECT_MODE:
            case "或":
                pending = set(tasks)
                selected = False
                while pending:
                    done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                    if any(task.result() for task in done):
                        selected = True
                        break
                for task in pending:
                    task.cancel()
                if pending:
                    await asyncio.gather(*pending, return_exceptions=True)
                if not selected:
                    logging.error("所有课程均未选中")
            case "与":
                await asyncio.gather(*tasks)

    async def _worker(self, target_class: Class) -> bool:
        while True:
            match await self.select(target_class):
                case "selected":
                    return True
                case "not_found":
                    return False
                case "retry":
                    await asyncio.sleep(WAIT_TIME)

    async def select(self, target_class: Class) -> Literal["selected", "not_found", "retry"]:
        target_class.repeat += 1
        logging.info(f"少女折寿中，第 {target_class.repeat} 次尝试选课，课程ID: {target_class.class_id}, 教师姓名: {target_class.teacher_name}")
        try:
            resp = await self.client.post(
                BASE_URL + "xsxkkc/xsxkFawxk",
                params={"kcxx": target_class.class_id, "skls": target_class.teacher_name},
                data={
                    "sEcho": 1,
                    "iColumns": 12,
                    "iDisplayStart": 0,
                    "iDisplayLength": 30,
                    "iSortingCols": 0,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if not data["aaData"]:
                logging.error(f"选课失败，课程ID: {target_class.class_id}, 教师姓名: {target_class.teacher_name}，错误信息: \"未找到该课程，请检查课程ID和教师姓名是否正确\"")
                return "not_found"
            row = data["aaData"][0]
            if int(row["syrs"]) <= 0:
                return "retry"
            result = await self.client.post(BASE_URL + "xsxkkc/fawxkOper", params={"kcid": target_class.class_id, "jx0404id": row["jx0404id"]})
            result.raise_for_status()
            result = result.json()
            if result["success"]:
                logging.info(f"选课成功，总尝试次数: {target_class.repeat}, 课程ID: {target_class.class_id}, 教师姓名: {target_class.teacher_name}")
                return "selected"
            logging.error(f"选课失败，课程ID: {target_class.class_id}, 教师姓名: {target_class.teacher_name}，错误信息: \"{result['message']}\"")
            return "retry"
        except (httpx.HTTPError, ValueError, KeyError) as e:
            logging.warning(f"网络异常，稍后重试，课程ID: {target_class.class_id}, 教师姓名: {target_class.teacher_name}，异常: {e!r}")
            return "retry"


    async def login(self) -> bool:
        await self.client.get(BASE_URL)
        account_b64 = base64.b64encode(STUDENT_ID.encode()).decode()
        password_b64 = base64.b64encode(PASSWORD.encode()).decode()
        encoded = f"{account_b64}%%%{password_b64}"
        response = await self.client.post(
            BASE_URL + "xk/LoginToXk",
            data={
                "userAccount": STUDENT_ID,
                "userPassword": PASSWORD,
                "encoded": encoded,
            },
        )
        return response.status_code == 302


async def main() -> None:
    selector = await Selector.create()
    await selector.run(CLASSES)


if __name__ == "__main__":
    asyncio.run(main())
