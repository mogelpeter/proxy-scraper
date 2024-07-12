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
import socket
import socks

# Ensure required modules are installed
required_modules = [
    'requests', 'colorama', 'pystyle', 'datetime', 'socks', 'psutil'
]
for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        os.system(f"pip install {module}")

# Load configuration
with open("config.json", "r") as config_file:
    config = json.load(config_file)
usage_level = config.get("usage_level", 2)  # Default to 2 (mid system usage allowance)

# Map usage levels to thread counts
thread_levels = {
    1: 500,   # Low system usage allowance
    2: 1000,  # Mid system usage allowance
    3: 1500   # High system usage allowance
}
allowed_threads = thread_levels.get(usage_level, 1000)

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

def get_time_rn():
    date = dt.now()
    return date.strftime("%H:%M:%S")

def get_usage_level_str(level):
    return {1: 'Low', 2: 'Mid', 3: 'High'}.get(level, 'Mid')

def update_title(http_selected, socks5_selected, usage_level):
    process = psutil.Process(os.getpid())
    cpu_usage = psutil.cpu_percent()
    ram_usage = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    title = f'[ Scraper - Level: {get_usage_level_str(usage_level)} ]'
    if http_selected:
        title += f' HTTP/s valid : {http_checked}'
    if socks5_selected:
        title += f' ~ Socks5 valid : {socks5_checked}'
    title += f' ~ CPU {cpu_usage}% ~ RAM {ram_usage:.2f}MB'
    if os.name == 'nt':
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    else:
        print(f'\33]0;{title}\a', end='', flush=True)

def center_text(text, width):
    lines = text.split('\n')
    return '\n'.join([line.center(width) for line in lines])

def ui():
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
    centered_message = center_text("[ This tool is a scraper & checker for HTTP/s and SOCKS5 proxies. ]", width)
    print(f"\n{centered_message}\n")
    time.sleep(1)

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
                update_title(http_selected, socks5_selected, usage_level)
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
    return proxies

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
                http_checked += 1
                update_title(http_selected, socks5_selected, usage_level)
            with open(f"results/http.txt", "a+") as f:
                f.write(proxy + "\n")
    except requests.exceptions.RequestException:
        pass

def check_proxy_socks5(proxy):
    global socks5_checked
    try:
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy.split(':')[0], int(proxy.split(':')[1]))
        socket.socket = socks.socksocket
        s = socket.socket()
        s.connect(("www.google.com", 80))
        s.sendall(b"GET / HTTP/1.1\r\nHost: www.google.com\r\n\r\n")
        response = s.recv(4096)
        if b"200 OK" in response:
            with output_lock:
                socks5_checked += 1
                update_title(http_selected, socks5_selected, usage_level)
                time_rn = get_time_rn()
                print(f"[ {pink}{time_rn}{reset} ] | ( {green}VALID{reset} ) {pretty}SOCKS5 --> ", end='')
                sys.stdout.flush()
                Write.Print(proxy + "\n", Colors.cyan_to_blue, interval=0.000)
            with open("results/socks5.txt", "a+") as f:
                f.write(proxy + "\n")
    except (socks.ProxyConnectionError, socket.timeout, OSError):
        pass

def check_http_proxies(proxies):
    with concurrent.futures.ThreadPoolExecutor(max_workers=allowed_threads) as executor:
        executor.map(check_proxy_http, proxies)

def check_socks5_proxies(proxies):
    with concurrent.futures.ThreadPoolExecutor(max_workers=allowed_threads) as executor:
        executor.map(check_proxy_socks5, proxies)

def signal_handler(sig, frame):
    print("\nProcess interrupted by user.")
    sys.exit(0)

def set_process_priority():
    p = psutil.Process(os.getpid())
    try:
        p.nice(psutil.HIGH_PRIORITY_CLASS)
    except AttributeError:
        p.nice(-20)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    set_process_priority()
    ui()

    # Delete old files on startup
    if os.path.exists("scraped/http_proxies.txt"):
        os.remove("scraped/http_proxies.txt")
    if os.path.exists("scraped/socks5_proxies.txt"):
        os.remove("scraped/socks5_proxies.txt")
    
    if not os.path.exists("results"):
        os.makedirs("results")
    
    open("results/http.txt", "w").close()
    open("results/socks5.txt", "w").close()

    valid_http = []
    valid_socks5 = []

    # Ask user what they want to scrape and validate
    print(f"{Fore.GREEN}What do you want to scrape and validate?{Fore.RESET}")
    print(f"{Fore.WHITE}Press {Fore.GREEN}1{Fore.WHITE} for {Fore.MAGENTA}HTTP/s{Fore.RESET}")
    print(f"{Fore.WHITE}Press {Fore.GREEN}2{Fore.WHITE} for {Fore.MAGENTA}SOCKS5{Fore.RESET}")
    print(f"{Fore.WHITE}Press {Fore.GREEN}3{Fore.WHITE} for both {Fore.MAGENTA}HTTP/s{Fore.WHITE} and {Fore.MAGENTA}SOCKS5{Fore.RESET}")
    
    choice = input(f"{Fore.CYAN}Enter your choice (1, 2 or 3): {Fore.RESET}")
    
    http_selected = choice == '1' or choice == '3'
    socks5_selected = choice == '2' or choice == '3'
    
    if http_selected:
        proxies_http = scrape_proxies(http_links, "https", "http_proxies.txt")
        check_http_proxies(proxies_http)
    if socks5_selected:
        proxies_socks5 = scrape_proxies(socks5_links, "socks5", "socks5_proxies.txt")
        check_socks5_proxies(proxies_socks5)

    while True:
        time.sleep(1)
