# 傻福学校平台，不用https，RSA也不用，还硬编码AES密钥，Base64编码两次觉得自己很聪明是吧

import asyncio
import base64
from dataclasses import dataclass
from pathlib import Path
import logging
import csv

import httpx
from Crypto.Cipher import AES


USER_ID: str = "YOUR_CLASS_ID_HERE"
PASSWORD: str = "YOUR_PASSWORD_HERE"
# 为空默认查所有, 格式类似为 "2025-2026-1", "2024-2025-3"
SEMESTER: str = ""

"""
Do not modify code after this line, unless you know what you are doing.
"""
AES_KEY: str = "qzkj1kjghd=876&*"
BLOCK_SIZE: int = 16
URL: str = "http://newjwh5.cau.edu.cn"
FILE: Path = Path("./grade.csv")

class Inquiry:
    def __init__(self) -> None:
        self.http_client = httpx.AsyncClient()
        self.aes_pwd: str = self._process_password()
        self.token: str = ""

    async def login(self) -> None:
        try:
            response: httpx.Response = await self.http_client.post(
                url=f"{URL}/bzb_njwhd/login",
                params={"userNo": USER_ID, "pwd": self.aes_pwd},
            )
            resp: dict = response.json()
            match resp["code"]:
                case "0":
                    logging.error("该帐号不存在或密码错误")
                    raise ValueError("该帐号不存在或密码错误")
                case "1":
                    self.token = resp["data"]["token"]
                    logging.info("get token successfully")
                case _:
                    raise RuntimeError("脚本已过期，请联系作者修改（或者你自己看看怎么办）")
        except httpx.HTTPStatusError as e:
            logging.error(e)
            raise e

    async def query(self) -> list[dict[str, str]]:
        try:
            response: httpx.Response = await self.http_client.post(
                url=f"{URL}/bzb_njwhd/student/termGPA",
                params={"semester": SEMESTER},
                headers={"token": self.token},
            )
            resp = response.json()
            # print(resp)
            match resp["code"]:
                case "401":
                    # 我自己也不明白为什么要写一句这个，理论上程序不可能运行到这里
                    logging.error("未授权访问")
                    raise RuntimeError()
                case "1":
                    return resp["data"][0]["achievement"]
                case _:
                    return []

        except httpx.HTTPStatusError as e:
            logging.error(e)
            raise e

    def _process_password(self) -> str:
        plaintext: str = f'"{PASSWORD}"'

        def pkcs7_pad(data: bytes) -> bytes:
            """PKCS7 填充到 BLOCK_SIZE 的整数倍"""
            pad_len = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
            return data + bytes([pad_len] * pad_len)

        padded = pkcs7_pad(plaintext.encode("utf-8"))
        cipher = AES.new(AES_KEY.encode("utf-8"), AES.MODE_ECB)
        ciphertext = cipher.encrypt(padded)
        b64_first = base64.b64encode(ciphertext).decode("ascii")
        b64_second = base64.b64encode(b64_first.encode("utf-8")).decode("ascii")
        return b64_second

class Processor:
    def __init__(self, grade_list: list[dict[str, str]]) -> None:
        self.grade_list: list[dict[str, str]] = grade_list
        FILE.touch()
    
    def output(self) -> None:
        with open(FILE, mode='w',) as f:
            data: list[list[str | int]] = [
                [
                    item["courseNature"],
                    item["kkxq"],
                    item["courseName"],
                    int(item["credit"]),
                    item["fraction"],
                ]
                for item in self.grade_list
            ]
            writer = csv.writer(f)
            writer.writerow(["课程类别", "学期", "课程名", "学分", "成绩"])
            writer.writerows(data)

async def main() -> None:
    inquiry = Inquiry()
    await inquiry.login()
    processor = Processor(await inquiry.query())
    processor.output()



if __name__ == "__main__":
    asyncio.run(main())
