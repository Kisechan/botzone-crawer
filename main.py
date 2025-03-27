import requests
from bs4 import BeautifulSoup
import time
import os
from urllib.parse import urljoin
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# 禁用 SSL 报错

BASE_URL = 'https://extra.botzone.org.cn/matchpacks/'
DOWNLOAD_DIR = 'downloaded_files'
GAME = 'Tetris2'
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}
DOWNLOAD_INTERVAL = 5   # 下载间隔（秒）
MAX_RETRIES = 0         # 最大重试次数

def create_download_dir():
    # 创建下载目录
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_file_links():
    # 获取所有符合条件的文件链接
    try:
        print(f"正在爬取索引页：{BASE_URL}")
        response = requests.get(BASE_URL, headers=REQUEST_HEADERS, timeout=30, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"无法获取索引页: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    links = []

    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith(GAME) and href.endswith('.zip'):
            full_url = urljoin(BASE_URL, href)
            links.append(full_url)

    return links

def download_file(url, retry_count=0):
    # 下载文件
    filename = os.path.basename(url)
    save_path = os.path.join(DOWNLOAD_DIR, filename)

    try:
        print(f"开始下载 [{filename}]")
        response = requests.get(url, headers=REQUEST_HEADERS, stream=True, timeout=30, verify=False)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"下载完成 [{filename}]")
        return True

    except Exception as e:
        if retry_count < MAX_RETRIES:
            print(f"下载失败 [{filename}]，正在重试 ({retry_count+1}/{MAX_RETRIES})")
            return download_file(url, retry_count+1)
        print(f"最终下载失败 [{filename}]，错误: {str(e)}")
        return False

def main():
    create_download_dir()

    print("正在扫描索引页")
    file_links = get_file_links()

    if not file_links:
        print("没有找到符合条件的文件")
        return

    print(f"找到 {len(file_links)} 个待下载文件")

    success_count = 0
    failed_urls = []

    for idx, url in enumerate(file_links, 1):
        print(f"\n正在处理文件 ({idx}/{len(file_links)})")

        if not download_file(url):
            failed_urls.append(url)
        else:
            success_count += 1

        if idx < len(file_links):
            print(f"等待 {DOWNLOAD_INTERVAL} 秒")
            time.sleep(DOWNLOAD_INTERVAL)

    print("\n下载结果汇总：")
    print(f"成功下载: {success_count} 个")
    print(f"失败下载: {len(failed_urls)} 个")

    if failed_urls:
        print("\n失败的下载链接：")
        for url in failed_urls:
            print(f"• {url}")

if __name__ == "__main__":
    main()