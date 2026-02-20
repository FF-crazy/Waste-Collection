# 这个程序由某个猴子通过随机敲击键盘生成，完全没有任何意义，与本人无关，本人也不知道能用来干什么，运行此程序造成的任何后果自负。

from typing import LiteralString, Literal

import requests
import time

BASE_URL: LiteralString = "https://newjw.cau.edu.cn/jsxsd/xsxkkc/fawxkOper?"
JSESSIONID: LiteralString = "E8D6041DB0CB5E9B40D27C3C3B5B33D2"
SERVERID: LiteralString = "124"

# Do not modify this variable, unless you know what you are doing
COOKIE: LiteralString = f"SERVERID={SERVERID}; JSESSIONID={JSESSIONID}"

CLASS_ID: list[int] = [26308006]
INFORM_ID: list[int] = [202420253000553]
CLASS_MAP: dict[int, str] = {202420253000553: "史银雪"}

# Do not modify this variable, unless you know what you are doing
HEADERS: dict[str, str] = {
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
    "Cookie": COOKIE,
}


def post_request(class_id, inform_id) -> str:
    url = BASE_URL + f"kcid={class_id}&cfbs=null&jx0404id={inform_id}&xkzy&trjf"
    response = requests.get(url, headers=HEADERS)
    return response.text


def decode_response(response) -> Literal[-1, 0, 1, 2, 3]:
    if "选课成功" in response:
        return 0
    elif "请先登录系统" in response:
        return -1
    elif "当前教学班已选择！" in response:
        return 2
    elif "null" in response:
        return 3
    else:
        return 1


def IsValid() -> bool:
    return len(CLASS_ID) > 0 and len(INFORM_ID) > 0 and len(CLASS_ID) == len(INFORM_ID)


def main() -> None:
    if not IsValid():
        print("请先配置课程信息")
        return
    while True:
        for class_id, inform_id in zip(CLASS_ID, INFORM_ID):
            response = post_request(class_id, inform_id)
            result = decode_response(response)
            if result == 0:
                print(
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    f"选课成功: {CLASS_MAP[inform_id]}",
                )
                return
            elif result == -1:
                print(time.strftime("%Y-%m-%d %H:%M:%S"), "COOKIE失效，请重新获取")
                return
            elif result == 2:
                print(
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    f"课程已选: {CLASS_MAP[inform_id]}",
                )
                return
            elif result == 3:
                print(time.strftime("%Y-%m-%d %H:%M:%S"), f"非法课程: {inform_id}")
            else:
                print(
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    f"选课失败: {CLASS_MAP[inform_id]}",
                )
        time.sleep(1)


if __name__ == "__main__":
    main()
