#!/usr/bin/env python3
"""Delete `impl Solution { ... }` block from a Rust source file.

Usage:
    python remove_impl_solution.py
    python remove_impl_solution.py /path/to/main.rs
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


IMPL_PATTERN = re.compile(r"\bimpl\s+Solution\s*\{", re.MULTILINE)


def find_matching_brace(text: str, open_brace_index: int) -> int:
    """Return the index of the matching closing brace for text[open_brace_index]."""
    depth = 0
    i = open_brace_index

    in_line_comment = False
    in_block_comment = 0
    in_double_quote = False
    in_char = False
    escape = False

    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment > 0:
            if ch == "/" and nxt == "*":
                in_block_comment += 1
                i += 2
                continue
            if ch == "*" and nxt == "/":
                in_block_comment -= 1
                i += 2
                continue
            i += 1
            continue

        if in_double_quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_double_quote = False
            i += 1
            continue

        if in_char:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == "'":
                in_char = False
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue

        if ch == "/" and nxt == "*":
            in_block_comment += 1
            i += 2
            continue

        if ch == '"':
            in_double_quote = True
            i += 1
            continue

        if ch == "'":
            in_char = True
            i += 1
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i

        i += 1

    return -1


def remove_impl_solution_block(text: str) -> tuple[str, bool]:
    match = IMPL_PATTERN.search(text)
    if not match:
        return text, False

    line_start = text.rfind("\n", 0, match.start()) + 1
    open_brace_index = text.find("{", match.start(), match.end() + 1)
    if open_brace_index == -1:
        return text, False

    close_brace_index = find_matching_brace(text, open_brace_index)
    if close_brace_index == -1:
        raise ValueError("找到了 `impl Solution {`，但没有匹配到结束的 `}`。")

    line_end = text.find("\n", close_brace_index)
    remove_end = len(text) if line_end == -1 else line_end + 1

    new_text = text[:line_start] + text[remove_end:]
    return new_text, True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="删除 Rust 文件中的 `impl Solution { ... }` 代码块（包含 impl 这一行）"
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="~/proj/Waste-Collection/Rust/src/main.rs",
        help="目标 Rust 文件路径，默认是 ~/proj/Waste-Collection/Rust/src/main.rs",
    )
    args = parser.parse_args()

    path = Path(args.file).expanduser()
    if not path.exists():
        print(f"文件不存在: {path}", file=sys.stderr)
        return 1

    original = path.read_text(encoding="utf-8")
    updated, changed = remove_impl_solution_block(original)

    if not changed:
        print("未找到 `impl Solution { ... }`，未做修改。")
        return 0

    path.write_text(updated, encoding="utf-8")
    print(f"已删除 `impl Solution {{ ... }}` 代码块: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
