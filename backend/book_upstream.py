"""HTTP client and HTML parser for Z-Library ebooks."""

import hashlib
import os
import re
import sys
import time
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from curl_cffi import requests

BASE_URL = "https://zh.z-library.sk"


def get_system_proxy():
    """自动检测系统代理配置（Windows 注册表或系统环境变量）。"""
    if sys.platform == "win32":
        try:
            import winreg

            reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(reg, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
            enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
            if enabled:
                server, _ = winreg.QueryValueEx(key, "ProxyServer")
                if server:
                    if not server.startswith("http://") and not server.startswith("https://"):
                        server = "http://" + server
                    return {"http": server, "https": server}
        except Exception:
            pass

    env_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")
    if env_proxy:
        return {"http": env_proxy, "https": env_proxy}
    return None


def solve_pow(html_text):
    """自动解析并突破 Z-Library 站点的 503 WAF 算力(PoW)挑战。"""
    m = re.search(r"a0_0x2a54=\['(.*?)'\];", html_text)
    if not m:
        return None, None
    raw_arr = [x.strip("'") for x in m.group(1).split("','")]

    rot_m = re.search(r"a0_0x2a54,(0x[0-9a-fA-F]+|\d+)\)\);", html_text)
    if not rot_m:
        return None, None
    rot_count = int(rot_m.group(1), 16) if rot_m.group(1).startswith("0x") else int(rot_m.group(1))
    for _ in range(rot_count):
        raw_arr.append(raw_arr.pop(0))

    token_hash = raw_arr[2]
    n1 = int(token_hash[0], 16)

    cond_m = re.search(r"s\[n1\]===(0x[0-9a-fA-F]+|\d+)\)&&\(s\[n1\+0x1\]===(0x[0-9a-fA-F]+|\d+)\)", html_text)
    if not cond_m:
        return None, None
    b1 = int(cond_m.group(1), 16) if cond_m.group(1).startswith("0x") else int(cond_m.group(1))
    b2 = int(cond_m.group(2), 16) if cond_m.group(2).startswith("0x") else int(cond_m.group(2))

    start = time.time()
    i = 0
    while True:
        digest = hashlib.sha1((token_hash + str(i)).encode("utf-8")).digest()
        if digest[n1] == b1 and digest[n1 + 1] == b2:
            elapsed = time.time() - start
            return f"{token_hash}{i}", str(round(elapsed, 3))
        i += 1


def build_search_url(keyword: str) -> str:
    """根据输入的关键词构造 Z-Library 搜索网址。"""
    encoded_keyword = quote(keyword.strip())
    return f"{BASE_URL}/s/{encoded_keyword}?"


def parse_zlib_html(html_content):
    """解析 Z-Library 搜索结果页面 HTML。"""
    soup = BeautifulSoup(html_content, "lxml")
    book_cards = soup.find_all("z-bookcard")
    results = []

    for idx, card in enumerate(book_cards, start=1):
        # 1. 书名
        title_tag = card.find("div", attrs={"slot": "title"})
        if not title_tag:
            title_tag = card.find(class_="title")
        title = title_tag.get_text(strip=True) if title_tag else "未知书名"

        # 2. 封面图片
        img_tag = card.find("img", class_="image")
        if not img_tag:
            img_tag = card.find("img")
        cover_url = ""
        if img_tag:
            cover_url = img_tag.get("src") or img_tag.get("data-src") or ""
            if cover_url and cover_url.startswith("/"):
                cover_url = urljoin(BASE_URL, cover_url)

        # 3. 作者名字
        author_tag = card.find("div", attrs={"slot": "author"})
        if not author_tag:
            author_tag = card.find("div", class_="author")
        author = author_tag.get_text(strip=True) if author_tag else "未知作者"

        # 4. 电子书格式与大小
        extension = card.get("extension", "").upper()
        filesize = card.get("filesize", "")

        # 5. 语言
        language = card.get("language", "")

        # 6. 下载地址
        download_path = card.get("download", "")
        download_url = urljoin(BASE_URL, download_path) if download_path else ""

        # 详情链接
        detail_path = card.get("href", "")
        detail_url = urljoin(BASE_URL, detail_path) if detail_path else ""

        results.append({
            "title": title,
            "coverUrl": cover_url,
            "author": author,
            "format": extension,
            "filesize": filesize,
            "language": language,
            "downloadUrl": download_url,
            "detailUrl": detail_url,
        })

    return results


class BookUpstreamClient:
    def __init__(self, proxies=None, timeout=25):
        self.proxies = proxies if proxies is not None else get_system_proxy()
        self.timeout = timeout

    def search(self, keyword: str):
        search_url = build_search_url(keyword)
        session = requests.Session(proxies=self.proxies, impersonate="chrome120")
        try:
            response = session.get(search_url, timeout=self.timeout)
            if response.status_code == 503 and "c_token=" in response.text:
                token_val, time_val = solve_pow(response.text)
                if token_val:
                    session.cookies.set("c_token", token_val, domain=".z-library.sk")
                    session.cookies.set("c_time", time_val, domain=".z-library.sk")
                    response = session.get(search_url, timeout=self.timeout)

            if response.status_code == 200:
                return parse_zlib_html(response.text)
            return []
        finally:
            session.close()