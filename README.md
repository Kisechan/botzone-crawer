# botzone-crawer
用来多线程下载 Botzone 上面的对局数据集。

网站的 SSL 证书已过期，默认忽略证书验证。

## 依赖

```bash
pip install requests beautifulsoup4 urllib3
```

## 配置

在代码开头修改配置项：

```python
BASE_URL = 'https://extra.botzone.org.cn/matchpacks/'
# 数据集索引页

DOWNLOAD_DIR = 'downloaded_files'
# 文件存放路径

GAME = 'Tetris2'
# 游戏名称，程序会检索所有以这个名称开头、.zip结尾的文件

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

MAX_RETRIES = 0         # 最大重试次数
THREAD_NUM = 3          # 线程数量
DOWNLOAD_TIMEOUT = 30   # 下载超时时间(秒)
```

## 运行

```bash
python main.py
```

## 免责声明

- 本程序仅用于技术学习交流
- 使用前请确保遵守目标网站的服务条款
- 不得用于任何非法目的
- 因滥用本程序导致的任何后果由使用者自行承担

## 协议

[MIT](./LICENSE)
