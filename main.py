import os
import sys
import concurrent.futures
import time
import threading
import requests
from requests.exceptions import RequestException, SSLError, ReadTimeout
from pystyle import Write, System, Colors
from colorama import Fore, Style
from datetime import datetime as dt
import ctypes
from proxy_links import http_links, socks5_links
import json
import signal
import psutil

# Ensure required modules are installed
required_modules = [
    'requests', 'colorama', 'pystyle', 'datetime', 'aiosocks', 
    'asyncio', 'aiohttp-socks', 'socks', 'tls_client', 'psutil', 'pywin32'
]
for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        os.system(f"pip install {module}")

# Run pywin32_postinstall to complete the installation
try:
    import pywin32_postinstall
    pywin32_postinstall.main()
except Exception as e:
    print(f"Error running pywin32_postinstall: {e}")

# Retry importing win32api, win32con, win32gui after ensuring installation
try:
    import win32api
    import win32con
    import win32gui
except ImportError:
    print("Failed to import win32 modules. Ensure pywin32 is properly installed.")
    sys.exit(1)

from aiohttp_socks import ProxyConnector, ProxyType

# Load configuration
with open("config.json", "r") as config_file:
    config = json.load(config_file)
usage_level = config.get("usage_level", 3)

# Map usage levels to thread counts
usage_to_threads = {i: 100 + 50 * (i - 1) for i in range(1, 11)}
allowed_threads = usage_to_threads.get(usage_level, 200)

https_scraped = 0
socks5_scraped = 0
http_checked = 0
socks5_checked = 0

red = Fore.RED
yellow = Fore.YELLOW
green = Fore.GREEN
blue = Fore.BLUE
orange = Fore.RED + Fore.YELLOW
pretty = Fore.LIGHTMAGENTA_EX + Fore.LIGHTCYAN_EX
magenta = Fore.MAGENTA
lightblue = Fore.LIGHTBLUE_EX
cyan = Fore.CYAN
gray = Fore.LIGHTBLACK_EX + Fore.WHITE
reset = Fore.RESET
pink = Fore.LIGHTGREEN_EX + Fore.LIGHTMAGENTA_EX
dark_green = Fore.GREEN + Style.BRIGHT
output_lock = threading.Lock()

def set_console_icon():
    if os.name == 'nt':
        icon_path = os.path.join(os.getenv('systemroot'), 'system32', 'pifmgr.dll')
        icon_index = 2  # The index for the MSDOS icon in pifmgr.dll
        hicon = win32gui.ExtractIcon(win32api.GetModuleHandle(None), icon_path, icon_index)
        ctypes.windll.kernel32.SetConsoleIcon(hicon)

def get_time_rn():
    date = dt.now()
    return date.strftime("%H:%M:%S")

def update_title():
    process = psutil.Process(os.getpid())
    cpu_usage = psutil.cpu_percent()
    ram_usage = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    title = f'[ Scraper ] HTTP/s valid : {http_checked} ~ Socks5 valid : {socks5_checked} ~ CPU {cpu_usage}% ~ RAM {ram_usage:.2f}MB'
    if os.name == 'nt':
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    else:
        print(f'\33]0;{title}\a', end='', flush=True)

def center_text(text, width):
    lines = text.split('\n')
    return '\n'.join([line.center(width) for line in lines])

def ui():
    update_title()
    System.Clear()
    width = os.get_terminal_size().columns
    ascii_art = """
  ____                        ____                                 
 |  _ \\ _ __ _____  ___   _  / ___|  ___ _ __ __ _ _ __   ___ _ __ 
 | |_) | '__/ _ \\ \\/ / | | | \\___ \\ / __| '__/ _` | '_ \\ / _ \\ '__|
 |  __/| | | (_) >  <| |_| |  ___) | (__| | | (_| | |_) |  __/ |   
 |_|   |_|  \\___/_/\\_\\\\__, | |____/ \\___|_|  \\__,_| .__/ \\___|_|   
                      |___/                       |_|              
"""
    Write.Print(center_text(ascii_art, width), Colors.red_to_blue, interval=0.000)
    print("\n[ This tool is a scraper & checker for HTTP/s and SOCKS5 proxies. ]\n")
    time.sleep(3)

def scrape_proxy_links(link, proxy_type):
    global https_scraped, socks5_scraped
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.get(link, timeout=10)
            if response.status_code == 200:
                with output_lock:
                    time_rn = get_time_rn()
                    print(f"[ {pink}{time_rn}{reset} ] | ( {green}SUCCESS{reset} ) {pretty}Scraped --> ", end='')
                    sys.stdout.flush()
                    Write.Print(link[:60] + "*******\n", Colors.purple_to_red, interval=0.000)
                proxies = response.text.splitlines()
                if proxy_type == "https":
                    https_scraped += len(proxies)
                elif proxy_type == "socks5":
                    socks5_scraped += len(proxies)
                update_title()
                return proxies
        except (SSLError, ReadTimeout) as ssl_err:
            with output_lock:
                time_rn = get_time_rn()
                print(f"[ {pink}{time_rn}{reset} ] | ( {red}ERROR{reset} ) Failed to scrape {link}: {ssl_err}")
            break  # Skip retries for SSL and timeout errors
        except RequestException as e:
            with output_lock:
                time_rn = get_time_rn()
                print(f"[ {pink}{time_rn}{reset} ] | ( {red}ERROR{reset} ) Failed to scrape {link}: {e}")
            time.sleep(2)  # Wait before retrying
    return []

def scrape_proxies(proxy_list, proxy_type, file_name):
    proxies = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=allowed_threads) as executor:
        results = executor.map(lambda link: scrape_proxy_links(link, proxy_type), proxy_list)
        for result in results:
            proxies.extend(result)

    if not os.path.exists("scraped"):
        os.makedirs("scraped")

    with open(f"scraped/{file_name}", "w") as file:
        for proxy in proxies:
            if ":" in proxy and not any(c.isalpha() for c in proxy):
                file.write(proxy + '\n')

def check_proxy_http(proxy):
    global http_checked
    proxy_dict = {
        "http": "http://" + proxy,
        "https": "https://" + proxy
    }
    try:
        url = 'http://httpbin.org/get'
        r = requests.get(url, proxies=proxy_dict, timeout=30)
        if r.status_code == 200:
            with output_lock:
                time_rn = get_time_rn()
                print(f"[ {pink}{time_rn}{reset} ] | ( {green}VALID{reset} ) {pretty}HTTP/S --> ", end='')
                sys.stdout.flush()
                Write.Print(proxy + "\n", Colors.cyan_to_blue, interval=0.000)
            with output_lock:
                valid_http.append(proxy)
                http_checked += 1
                update_title()
            with open(f"results/http.txt", "a+") as f:
                f.write(proxy + "\n")
    except requests.exceptions.RequestException:
        pass

def checker_proxy_socks5(proxy):
    global socks5_checked
    try:
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy.split(':')[0], int(proxy.split(':')[1]))
        socket.socket = socks.socksocket
        socket.create_connection(("www.google.com", 443), timeout=5)
        with output_lock:
            socks5_checked += 1
            update_title()
            time_rn = get_time_rn()
            print(f"[ {pink}{time_rn}{reset} ] | ( {green}VALID{reset} ) {pretty}SOCKS5 --> ", end='')
            sys.stdout.flush()
            Write.Print(proxy + "\n", Colors.cyan_to_blue, interval=0.000)
        with open("results/socks5.txt", "a+") as f:
            f.write(proxy + "\n")
    except (socks.ProxyConnectionError, socket.timeout, OSError):
        pass

def check_all(proxy_type, pathTXT):
    with open(pathTXT, "r") as f:
        proxies = f.read().splitlines()

    with concurrent.futures.ThreadPoolExecutor(max_workers=allowed_threads) as executor:
        if proxy_type.startswith("http") or proxy_type.startswith("https"):
            executor.map(check_proxy_http, proxies)
        if proxy_type.startswith("socks5"):
            executor.map(checker_proxy_socks5, proxies)

def lets_check_it(proxy_types):
    threadsCrack = []
    for proxy_type in proxy_types:
        if os.path.exists(f"scraped/{proxy_type}_proxies.txt"):
            t = threading.Thread(target=check_all, args=(proxy_type, f"scraped/{proxy_type}_proxies.txt"))
            t.start()
            threadsCrack.append(t)
    for t in threadsCrack:
        t.join()

def signal_handler(sig, frame):
    print("\nProcess interrupted by user.")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    set_console_icon()
    ui()

    scrape_proxies(http_links, "https", "http_proxies.txt")
    scrape_proxies(socks5_links, "socks5", "socks5_proxies.txt")

    time.sleep(1)
    if not os.path.exists("results"):
        os.makedirs("results")

    open("results/http.txt", "w").close()
    open("results/socks5.txt", "w").close()

    valid_http = []
    valid_socks5 = []

    proxy_types = ["http", "socks5"]
    lets_check_it(proxy_types)

    # Check if the file exists before attempting to remove it
    if os.path.exists("scraped/http_proxies.txt"):
        os.remove("scraped/http_proxies.txt")
    if os.path.exists("scraped/socks5_proxies.txt"):
        os.remove("scraped/socks5_proxies.txt")

    while True:
        time.sleep(1)
