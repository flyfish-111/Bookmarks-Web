import asyncio
from urllib.parse import urljoin

import httpx

from ..config import settings
from .ssrf import validate_url

REDIRECT_CODES = {301, 302, 303, 307, 308}


class FetchError(Exception):
    """抓取失败（SSRF 校验失败、HTTP 错误、体积超限、重定向异常等）。"""


async def fetch_html(url: str) -> tuple[str, str]:
    """抓取网页，逐跳跟随重定向（每一跳都做 SSRF 校验）。返回 (最终地址, HTML)。"""
    current = url
    headers = {
        "User-Agent": settings.user_agent,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    async with httpx.AsyncClient(
        timeout=settings.fetch_timeout,
        follow_redirects=False,
        headers=headers,
    ) as client:
        for _ in range(settings.max_redirects + 1):
            try:
                await asyncio.to_thread(validate_url, current)
            except ValueError as e:
                raise FetchError(str(e))

            resp = await client.get(current)

            if resp.status_code in REDIRECT_CODES:
                location = resp.headers.get("location")
                if not location:
                    raise FetchError("重定向缺少目标地址")
                current = urljoin(current, location)
                continue

            if resp.status_code >= 400:
                raise FetchError(f"抓取失败：HTTP {resp.status_code}")

            ctype = resp.headers.get("content-type", "").lower()
            if ctype and not any(t in ctype for t in ("text/html", "text/plain", "application/xhtml")):
                raise FetchError(f"该网址不是网页内容（{ctype or '未知类型'}）")

            if len(resp.content) > settings.max_fetch_bytes:
                raise FetchError("网页体积过大，已超过抓取上限")

            return current, resp.text

    raise FetchError("重定向次数过多")
