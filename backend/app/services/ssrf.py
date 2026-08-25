import ipaddress
import socket
from urllib.parse import urlparse


def validate_url(url: str) -> str:
    """校验 URL 是否安全（仅 http/https 且不指向内网/保留地址）。

    不安全时抛出 ValueError，否则原样返回 url。
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("仅支持 http/https 协议")
    host = parsed.hostname
    if not host:
        raise ValueError("无效的网址")

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise ValueError("域名无法解析")

    for info in infos:
        ip = info[4][0].split("%")[0]
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            raise ValueError("无效的 IP 地址")
        if not addr.is_global:
            raise ValueError("不允许访问内网或保留地址")

    return url
