import os
import concurrent.futures
import sys
import time
import threading
import requests
from requests.exceptions import RequestException, SSLError, ReadTimeout
from pystyle import Write, System, Colors, Colorate, Anime
from colorama import Fore, Style
from datetime import datetime as dt
import ctypes
from proxy_links import http_links, socks5_links
import json
import signal
import psutil

try:
    import requests, colorama, pystyle, datetime, aiosocks, asyncio, aiohttp_socks, socks, socket, tls_client
except ModuleNotFoundError:
    os.system("pip install requests")
    os.system("pip install colorama")
    os.system("pip install pystyle")
    os.system("pip install datetime")
    os.system("pip install aiosocks")
    os.system("pip install asyncio")
    os.system("pip install aiohttp-socks")
    os.system("pip install socks")
    os.system("pip install tls_client")

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
        icon_index = 0x0000002
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('myappid')
        ctypes.windll.user32.LoadIconW(0, ctypes.windll.kernel32.MAKEINTRESOURCEW(icon_path, icon_index))
        ctypes.windll.kernel32.SetConsoleIcon(ctypes.windll.user32.LoadImageW(0, icon_path, 1, 0, 0, icon_index))

def get_time_rn():
    date = dt.now()
    hour = date.hour
    minute = date.minute
    second = date.second
    timee = "{:02d}:{:02d}:{:02d}".format(hour, minute, second)
    return timee

def update_title(title):
    if os.name == 'nt':
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    else:
        print(f'\33]0;{title}\a', end='', flush=True)

def update_title_scraped():
    global https_scraped, socks5_scraped
    process = psutil.Process(os.getpid())
    cpu_usage = psutil.cpu_percent()
    ram_usage = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    title = f'[ Scraper ] HTTP/s Scraped : {https_scraped} ~ Socks5 Scraped : {socks5_scraped} ~ CPU {cpu_usage}% ~ RAM {ram_usage:.2f}MB'
    update_title(title)

def update_title_checked():
    global http_checked, socks5_checked
    process = psutil.Process(os.getpid())
    cpu_usage = psutil.cpu_percent()
    ram_usage = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    title = f'[ Scraper ] HTTP/s valid : {http_checked} ~ Socks5 valid : {socks5_checked} ~ CPU {cpu_usage}% ~ RAM {ram_usage:.2f}MB'
    update_title(title)

def center_text(text, width):
    lines = text.split('\n')
    centered_lines = [line.center(width) for line in lines]
    return '\n'.join(centered_lines)

def ui():
    update_title("[ Scraper ]")
    System.Clear()
    width = os.get_terminal_size().columns
    ascii_art = """
  ____                        ____                                 
 |  _ \ _ __ _____  ___   _  / ___|  ___ _ __ __ _ _ __   ___ _ __ 
 | |_) | '__/ _ \ \/ / | | | \___ \ / __| '__/ _` | '_ \ / _ \ '__|
 |  __/| | | (_) >  <| |_| |  ___) | (__| | | (_| | |_) |  __/ |   
 |_|   |_|  \___/_/\_\\__, | |____/ \___|_|  \__,_| .__/ \___|_|   
                      |___/                       |_|              
"""
    Write.Print(center_text(ascii_art, width), Colors.red_to_blue, interval=0.000)
    time.sleep(3)

ui()

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
                update_title_scraped()
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

scrape_proxies(http_links, "https", "http_proxies.txt")
scrape_proxies(socks5_links, "socks5", "socks5_proxies.txt")

time.sleep(1)
if not os.path.exists("results"):
    os.makedirs("results")

a = open("results/http.txt", "w")
b = open("results/socks5.txt", "w")

a.write("")
b.write("")

a.close()
b.close()

valid_http = []
valid_socks5 = []

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
                print(f"[ {pink}{time_rn}{reset} ] | ( {green}valid{reset} ) {pretty}HTTP/S --> ", end='')
                sys.stdout.flush()
                Write.Print(proxy + "\n", Colors.cyan_to_blue, interval=0.000)
            valid_http.append(proxy)
            http_checked += 1
            update_title_checked()
            with open(f"results/http.txt", "a+") as f:
                f.write(proxy + "\n")
    except requests.exceptions.RequestException as e:
        pass

def checker_proxy_socks5(proxy):
    global socks5_checked
    try:
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy.split(':')[0], int(proxy.split(':')[1]))
        socket.socket = socks.socksocket
        socket.create_connection(("www.google.com", 443), timeout=5)
        socks5_checked += 1
        update_title_checked()
        with output_lock:
            time_rn = get_time_rn()
            print(f"[ {pink}{time_rn}{reset} ] | ( {green}valid{reset} ) {pretty}SOCKS5 --> ", end='')
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

def LetsCheckIt(proxy_types):
    threadsCrack = []
    for proxy_type in proxy_types:
        if os.path.exists(f"scraped/{proxy_type}_proxies.txt"):
            t = threading.Thread(target=check_all, args=(proxy_type, f"scraped/{proxy_type}_proxies.txt"))
            t.start()
            threadsCrack.append(t)
    for t in threadsCrack:
        t.join()

proxy_types = ["http", "socks5"]
LetsCheckIt(proxy_types)

# Check if the file exists before attempting to remove it
if os.path.exists("scraped/http_proxies.txt"):
    os.remove("scraped/http_proxies.txt")
if os.path.exists("scraped/socks5_proxies.txt"):
    os.remove("scraped/socks5_proxies.txt")

def signal_handler(sig, frame):
    print("\nProcess interrupted by user.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    set_console_icon()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
