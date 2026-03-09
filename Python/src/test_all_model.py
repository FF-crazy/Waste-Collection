import csv
import time
from pathlib import Path

import httpx

BASEURL: str = ""  # 结尾一定不要有 /
API_KEY: str = ""
MAX_RETRIES: int = 3

INTERFACES: dict[str, dict] = {
    "OpenAI": {
        "models": "/v1/models",
        "chat": "/v1/chat/completions",
        "build_body": lambda model: {
            "model": model,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
        },
    },
    "Gemini": {
        "models": "/v1/models",
        "chat": "/v1/chat/completions",
        "build_body": lambda model: {
            "model": model,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
        },
    },
    "Claude": {
        "models": "/v1/models",
        "chat": "/v1/messages",
        "build_body": lambda model: {
            "model": model,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
        },
    },
}

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "x-api-key": API_KEY,  # Claude 格式
    "anthropic-version": "2023-06-01",
}


def fetch_models(client: httpx.Client, endpoint: str) -> list[str]:
    """获取全部可用模型列表"""
    url = BASEURL + endpoint
    try:
        resp = client.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            print(f"  [!] 获取模型列表失败: HTTP {resp.status_code}")
            return []
        data = resp.json()
        # OpenAI 格式: {"data": [{"id": "model-name"}, ...]}
        if "data" in data:
            return [m["id"] for m in data["data"]]
        # 兜底：直接返回空
        print(f"  [!] 无法解析模型列表响应: {list(data.keys())}")
        return []
    except Exception as e:
        print(f"  [!] 获取模型列表异常: {e}")
        return []


def test_model(
    client: httpx.Client, model: str, chat_endpoint: str, body: dict
) -> str:
    """测试单个模型，返回 '可用' / '不可用' / '429重试耗尽'"""
    url = BASEURL + chat_endpoint
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.post(url, headers=HEADERS, json=body, timeout=30)
            if resp.status_code == 200:
                return "可用"
            if resp.status_code == 429:
                print(f"    [429] 并发限制，等待 10s 后重试 ({attempt}/{MAX_RETRIES})")
                time.sleep(10)
                continue
            return f"不可用 (HTTP {resp.status_code})"
        except httpx.TimeoutException:
            return "不可用 (超时)"
        except Exception as e:
            return f"不可用 ({e})"
    return "不可用 (429重试耗尽)"


def run() -> None:
    if not BASEURL or not API_KEY:
        print("请先设置 BASEURL 和 API_KEY")
        return

    # 按模型名聚合结果: {model: {OpenAI: status, Gemini: status, Claude: status}}
    model_results: dict[str, dict[str, str]] = {}
    fmt_names = list(INTERFACES.keys())

    with httpx.Client() as client:
        # 先获取全部模型列表（去重）
        all_models: list[str] = []
        seen: set[str] = set()
        for cfg in INTERFACES.values():
            for m in fetch_models(client, cfg["models"]):
                if m not in seen:
                    seen.add(m)
                    all_models.append(m)

        if not all_models:
            print("  未获取到任何模型")
            return
        print(f"\n  共发现 {len(all_models)} 个模型\n")

        # 逐个模型测试，可用即跳过剩余接口
        for i, model in enumerate(all_models, 1):
            print(f"  [{i}/{len(all_models)}] {model}")
            model_results[model] = {}
            found_available = False

            for fmt_name, cfg in INTERFACES.items():
                if found_available:
                    model_results[model][fmt_name] = "跳过"
                    print(f"    {fmt_name}: 跳过")
                    continue

                body = cfg["build_body"](model)
                print(f"    {fmt_name} ...", end=" ", flush=True)
                status = test_model(client, model, cfg["chat"], body)
                print(status)
                model_results[model][fmt_name] = status

                if status == "可用":
                    found_available = True

    # 保存 CSV
    # 从 BASEURL 提取域名作为文件名
    from urllib.parse import urlparse
    hostname = urlparse(BASEURL).hostname or "unknown"
    output_path = Path(__file__).parent.parent / f"{hostname}.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["模型名"] + [f"{name}接口可用性" for name in fmt_names])
        for model in sorted(model_results):
            row = [model] + [model_results[model].get(name, "未测试") for name in fmt_names]
            writer.writerow(row)

    print(f"\n{'='*60}")
    print(f"  结果已保存至: {output_path}")
    print(f"{'='*60}")

    # 汇总报告
    total = len(model_results)
    for fmt_name in fmt_names:
        available = sum(
            1 for r in model_results.values() if r.get(fmt_name) == "可用"
        )
        print(f"  [{fmt_name}] 可用 {available}/{total}")


if __name__ == "__main__":
    run()
