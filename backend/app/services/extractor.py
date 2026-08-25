import re
from urllib.parse import urljoin

import trafilatura
from bs4 import BeautifulSoup
from markdownify import markdownify
from readability import Document

MIN_CONTENT_LEN = 40


def _md_to_text(md: str) -> str:
    """粗略地把 Markdown 转成纯文本，供全文检索使用。"""
    if not md:
        return ""
    text = re.sub(r"```.*?```", " ", md, flags=re.S)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[#>*_~\-|]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_content(html: str, url: str) -> tuple[str, str]:
    """提取正文，返回 (markdown, 纯文本)。"""
    # 1) trafilatura 直接输出 Markdown
    try:
        md = trafilatura.extract(
            html,
            url=url,
            output_format="markdown",
            include_comments=False,
            include_tables=True,
        )
    except Exception:
        md = None
    if md and len(md.strip()) >= MIN_CONTENT_LEN:
        return md.strip(), _md_to_text(md)

    # 2) readability 取主内容 HTML -> markdownify
    try:
        content_html = Document(html).summary()
        md = markdownify(content_html, heading_style="ATX")
        if md and len(md.strip()) >= MIN_CONTENT_LEN:
            return md.strip(), _md_to_text(md)
    except Exception:
        pass

    # 3) 兜底：整页纯文本
    try:
        text = trafilatura.extract(html, url=url, output_format="text")
    except Exception:
        text = None
    if not text:
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    text = (text or "").strip()
    return text, text


def extract_metadata(html: str, url: str) -> tuple[str, str, str]:
    """提取标题、描述、favicon，返回 (title, description, favicon_url)。"""
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            title = h1.get_text(strip=True)
    title = title[:512]

    description = ""
    og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
    if og_desc and og_desc.get("content"):
        description = og_desc["content"].strip()[:1000]

    favicon = ""
    icon_link = soup.find("link", rel=lambda r: r and "icon" in r)
    if icon_link and icon_link.get("href"):
        favicon = urljoin(url, icon_link["href"])
    else:
        favicon = urljoin(url, "/favicon.ico")

    return title, description, favicon
