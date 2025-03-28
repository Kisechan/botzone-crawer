import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import urllib3
import threading
from queue import Queue
from datetime import datetime

# 禁用 SSL 报错
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = 'https://extra.botzone.org.cn/matchpacks/'
DOWNLOAD_DIR = 'downloaded_files'
GAME = 'Tetris2'
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

MAX_RETRIES = 0         # 最大重试次数
THREAD_NUM = 3          # 线程数量
DOWNLOAD_TIMEOUT = 30   # 下载超时时间(秒)

# 创建队列和锁
download_queue = Queue()
print_lock = threading.Lock()
stats_lock = threading.Lock()
progress_lock = threading.Lock()

# 统计变量和进度跟踪
success_count = 0
failed_urls = []
skipped_count = 0
progress_info = {}

def create_download_dir():
    # 创建下载目录
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_file_links():
    # 获取所有符合条件的文件链接
    try:
        with print_lock:
            print(f"正在爬取索引页：{BASE_URL}")
        response = requests.get(BASE_URL, headers=REQUEST_HEADERS, timeout=30, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        with print_lock:
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

def update_progress(thread_name, filename, percent):
    with progress_lock:
        progress_info[thread_name] = (filename, percent)

        if os.name == 'nt':
            # Windows
            os.system('cls')
        else:
            # Linux/Mac
            os.system('clear')

        print("当前下载进度：")
        for name, (file, pct) in progress_info.items():
            print(f"{name}: {file} - {pct:.1f}%")
        print("\n")

def download_worker():
    thread_name = threading.current_thread().name
    while True:
        url = download_queue.get()
        if url is None:
            break

        filename = os.path.basename(url)
        save_path = os.path.join(DOWNLOAD_DIR, filename)
        start_time = datetime.now()

        # 检查文件是否已存在
        if os.path.exists(save_path):
            with stats_lock:
                global skipped_count
                skipped_count += 1
            with print_lock:
                print(f"[{thread_name}] 文件已存在，跳过 [{filename}]")
            download_queue.task_done()
            continue

        try:
            with print_lock:
                print(f"[{thread_name}] 开始下载 [{filename}]")

            response = requests.get(url, headers=REQUEST_HEADERS, stream=True,
                                    timeout=DOWNLOAD_TIMEOUT, verify=False)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            percent = downloaded_size / total_size * 100
                            # update_progress(thread_name, filename, percent)

            elapsed = (datetime.now() - start_time).total_seconds()
            with print_lock:
                print(f"[{thread_name}] 下载完成 [{filename}], 耗时: {elapsed:.2f}秒")

            with stats_lock:
                global success_count
                success_count += 1

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            with print_lock:
                print(f"[{thread_name}] 下载失败 [{filename}], 耗时: {elapsed:.2f}秒, 错误: {str(e)}")

            try:
                if os.path.exists(save_path):
                    os.remove(save_path)
                    with print_lock:
                        print(f"[{thread_name}] 已清理未完成文件 [{filename}]")
            except Exception as cleanup_error:
                with print_lock:
                    print(f"[{thread_name}] 清理文件失败 [{filename}], 错误: {str(cleanup_error)}")

            with stats_lock:
                failed_urls.append(url)

        with progress_lock:
            if thread_name in progress_info:
                del progress_info[thread_name]
            # update_progress(thread_name, "", 0)  # 更新显示

        download_queue.task_done()

def main():
    create_download_dir()

    print("正在扫描索引页")
    file_links = get_file_links()

    if not file_links:
        print("没有找到符合条件的文件")
        return

    print(f"找到 {len(file_links)} 个待下载文件")
    print(f"启动 {THREAD_NUM} 个下载线程...\n")

    # 启动工作线程
    threads = []
    for i in range(THREAD_NUM):
        t = threading.Thread(target=download_worker, name=f"Worker-{i+1}")
        t.start()
        threads.append(t)

    # 将下载任务加入队列
    for url in file_links:
        download_queue.put(url)

    # 等待所有任务完成
    download_queue.join()

    # 停止工作线程
    for _ in range(THREAD_NUM):
        download_queue.put(None)
    for t in threads:
        t.join()

    # 清屏
    # if os.name == 'nt':
    #     os.system('cls')
    # else:
    #     os.system('clear')

    print("\n下载结果汇总：")
    print(f"成功下载: {success_count} 个")
    print(f"跳过下载: {skipped_count} 个")
    print(f"失败下载: {len(failed_urls)} 个")

    if failed_urls:
        print("\n失败的下载链接：")
        for url in failed_urls:
            print(f"• {url}")

if __name__ == "__main__":
    start_time = datetime.now()
    main()
    total_time = (datetime.now() - start_time).total_seconds()
    print(f"\n总耗时: {total_time:.2f}秒")