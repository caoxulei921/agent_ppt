#!/usr/bin/env python3
"""
build-bundled.py — 把 app/core/index.html 与同目录下的 PNG/JPG/WebP/GIF
全部内联为 data: URI，生成一个双击即可在浏览器打开的单文件 PPT。

用法：
    python3 app/core/build-bundled.py

输出：
    app/core/index.bundled.html
"""
import base64
import mimetypes
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "index.html"
DST = HERE / "index.bundled.html"

# 匹配 <img ... src="path" ...>；path 以 png/jpg/jpeg/webp/gif 结尾
IMG_RE = re.compile(
    r'(<img\b[^>]*?\bsrc=["\'])'                    # 1: "<img ... src=\""
    r'([^"\']+\.(?:png|jpe?g|webp|gif))'            # 2: 相对路径
    r'(["\'][^>]*>)',                                # 3: "\"" 之后到 ">\" 收尾
    re.IGNORECASE,
)


def main() -> int:
    if not SRC.exists():
        print(f"[err] 源文件不存在: {SRC}", file=sys.stderr)
        return 1

    html = SRC.read_text(encoding="utf-8")
    missing: list[str] = []
    inlined = 0

    def replace(m: re.Match) -> str:
        nonlocal inlined
        before_src, rel, after_src = m.group(1), m.group(2), m.group(3)
        path = (HERE / rel).resolve()
        if not path.exists():
            missing.append(rel)
            return m.group(0)
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        inlined += 1
        return f"{before_src}data:{mime};base64,{b64}{after_src}"

    out = IMG_RE.sub(replace, html)
    DST.write_text(out, encoding="utf-8")

    size_kb = DST.stat().st_size / 1024
    print(f"[ok] {DST.name}  {size_kb:.1f} KB  ({inlined} images inlined)")
    if missing:
        print(f"[warn] 缺失图片，未内联: {missing}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())