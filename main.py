import os
import sys
import concurrent.futures
import time
import threading
import requests
from requests.exceptions import RequestException, SSLError, ReadTimeout
from pystyle import Write, System, Colors, Colorate
from colorama import Fore, Style, init
from datetime import datetime as dt
import ctypes
import json
import signal
import psutil
import socket
import socks
import msvcrt
import random
import string
import shutil

# Initialize colorama
init()

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
http_links = config.get("http_links", [])
socks5_links = config.get("socks5_links", [])

# Create and manage random folder
def generate_random_folder_name(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def remove_old_folders(base_folder="."):
    for folder_name in os.listdir(base_folder):
        folder_path = os.path.join(base_folder, folder_name)
        if os.path.isdir(folder_path) and len(folder_name) == 32:
            try:
                shutil.rmtree(folder_path)
            except OSError as e:
                print(f"Error: {folder_path} : {e.strerror}")

new_folder_name = generate_random_folder_name()
new_folder_path = os.path.join(".", new_folder_name)

remove_old_folders()

os.makedirs(new_folder_path)
if os.name == 'nt':
    ctypes.windll.kernel32.SetFileAttributesW(new_folder_path, 2)

results_folder = "results"
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

# Map usage levels to thread counts and RAM limits
thread_levels = {
    1: (500, 1024),   # Low system usage allowance: 500 threads, 1GB RAM
    2: (1000, 1536),  # Mid system usage allowance: 1000 threads, 1.5GB RAM
    3: (1500, 2048)   # High system usage allowance: 1500 threads, 2GB RAM
}
allowed_threads, ram_limit = thread_levels.get(usage_level, (1000, 1536))

https_scraped = 0
socks5_scraped = 0
http_checked = 0
socks5_checked = 0
exit_message_printed = False
exit_message_lock = threading.Lock()
validation_complete = False

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

# Limit validation
validate_limit = 0
loading = True
log_enabled = True

def get_time_rn():
    date = dt.now()
    return date.strftime("%H:%M:%S")

def get_usage_level_str(level):
    return {1: 'Low', 2: 'Mid', 3: 'High'}.get(level, 'Mid')

def update_title(http_selected, socks5_selected, usage_level):
    process = psutil.Process(os.getpid())
    cpu_usage = psutil.cpu_percent()
    ram_usage = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    title = f'[ Scraper ]'
    if http_selected:
        title += f' ~ HTTP/s valid: {http_checked}'
    if socks5_selected:
        title += f' ~ SOCKS5 valid: {socks5_checked}'
    title += f' ~ CPU {cpu_usage}% ~ RAM {ram_usage:.2f}MB ~ Level: {get_usage_level_str(usage_level)}'
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

def check_proxy_link(link):
    try:
        response = requests.get(link, timeout=10)
        if response.status_code == 200:
            return True
    except RequestException:
        pass
    return False

def clean_proxy_links():
    global http_links, socks5_links
    http_links = [link for link in http_links if check_proxy_link(link)]
    socks5_links = [link for link in socks5_links if check_proxy_link(link)]

def scrape_proxies(proxy_list, proxy_type, file_name):
    proxies = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=allowed_threads) as executor:
        results = executor.map(lambda link: scrape_proxy_links(link, proxy_type), proxy_list)
        for result in results:
            proxies.extend(result)

    with open(os.path.join(new_folder_path, file_name), "w") as file:
        for proxy in proxies:
            if ":" in proxy and not any(c.isalpha() for c in proxy):
                file.write(proxy + '\n')
    return proxies

def check_proxy_http(proxy):
    global http_checked, exit_message_printed, validation_complete
    if validation_complete:
        return
    proxy_dict = {
        "http": "http://" + proxy,
        "https": "https://" + proxy
    }
    try:
        if psutil.virtual_memory().available < ram_limit * 1024 * 1024:
            return
        url = 'http://httpbin.org/get'
        r = requests.get(url, proxies=proxy_dict, timeout=10)
        if r.status_code == 200:
            with output_lock:
                time_rn = get_time_rn()
                print(f"[ {pink}{time_rn}{reset} ] | ( {green}VALID{reset} ) {pretty}HTTP/S --> ", end='')
                sys.stdout.flush()
                Write.Print(proxy + "\n", Colors.cyan_to_blue, interval=0.000)
                http_checked += 1
                if http_checked >= validate_limit:
                    validation_complete = True
                    with exit_message_lock:
                        if not exit_message_printed:
                            print(f"{Fore.GREEN}Desired number of validated proxies reached. Exiting...{reset}")
                            exit_message_printed = True
                            time.sleep(1)  # Short delay to ensure the message appears below the last proxy validation
                            os._exit(0)
                update_title(http_selected, socks5_selected, usage_level)
            with open(os.path.join(results_folder, "http.txt"), "a+") as f:
                f.write(proxy + "\n")
    except requests.exceptions.RequestException:
        pass

def check_proxy_socks5(proxy):
    global socks5_checked, exit_message_printed, validation_complete
    if validation_complete:
        return
    try:
        if psutil.virtual_memory().available < ram_limit * 1024 * 1024:
            return
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy.split(':')[0], int(proxy.split(':')[1]))
        socket.socket = socks.socksocket
        s = socket.socket()
        s.connect(("www.google.com", 80))
        s.sendall(b"GET / HTTP/1.1\r\nHost: www.google.com\r\n\r\n")
        response = s.recv(4096)
        if b"200 OK" in response:
            with output_lock:
                time_rn = get_time_rn()
                print(f"[ {pink}{time_rn}{reset} ] | ( {green}VALID{reset} ) {pretty}SOCKS5 --> ", end='')
                sys.stdout.flush()
                Write.Print(proxy + "\n", Colors.cyan_to_blue, interval=0.000)
                socks5_checked += 1
                if socks5_checked >= validate_limit:
                    validation_complete = True
                    with exit_message_lock:
                        if not exit_message_printed:
                            print(f"{Fore.GREEN}Desired number of validated proxies reached. Exiting...{reset}")
                            exit_message_printed = True
                            time.sleep(1)  # Short delay to ensure the message appears below the last proxy validation
                            os._exit(0)
                update_title(http_selected, socks5_selected, usage_level)
            with open(os.path.join(results_folder, "socks5.txt"), "a+") as f:
                f.write(proxy + "\n")
    except (socks.ProxyConnectionError, socket.timeout, OSError):
        pass

def check_http_proxies(proxies):
    with concurrent.futures.ThreadPoolExecutor(max_workers=allowed_threads) as executor:
        for _ in executor.map(check_proxy_http, proxies):
            if validation_complete:
                break
            time.sleep(1 / 3)  # Limit to 3 validations per second

def check_socks5_proxies(proxies):
    with concurrent.futures.ThreadPoolExecutor(max_workers=allowed_threads) as executor:
        for _ in executor.map(check_proxy_socks5, proxies):
            if validation_complete:
                break
            time.sleep(1 / 3)  # Limit to 3 validations per second

def signal_handler(sig, frame):
    print("\nProcess interrupted by user.")
    remove_old_folders()  # Remove old folders on exit
    sys.exit(0)

def set_process_priority():
    p = psutil.Process(os.getpid())
    try:
        p.nice(psutil.HIGH_PRIORITY_CLASS)
    except AttributeError:
        p.nice(-20)

def loading_animation():
    width = os.get_terminal_size().columns
    while loading:
        for char in '|/-\\':
            sys.stdout.write('\r' + ' ' * width + '\r')  # Clear line
            sys.stdout.write(f'\r{Colorate.Horizontal(Colors.yellow_to_red, center_text(f"Verifying proxy links... {char}", width))}')
            sys.stdout.flush()
            time.sleep(0.1)

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
    ui()  # Redraw the UI

def continuously_update_title():
    while True:
        update_title(http_selected, socks5_selected, usage_level)
        time.sleep(1)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    set_process_priority()
    ui()

    # Initial title update
    http_selected = False
    socks5_selected = False
    update_title(http_selected, socks5_selected, usage_level)

    # Ask user what they want to scrape and validate
    width = os.get_terminal_size().columns
    Write.Print("What do you want to scrape and validate?\n", Colors.green_to_blue, interval=0.000)
    print(f"{Fore.WHITE}Press {Fore.GREEN}1{Fore.WHITE} for {Fore.MAGENTA}HTTP/s{Fore.RESET}")
    print(f"{Fore.WHITE}Press {Fore.GREEN}2{Fore.WHITE} for {Fore.MAGENTA}SOCKS5{Fore.RESET}")
    
    choice = msvcrt.getch()

    if choice in [b'1', b'2']:
        clear_console()  # Clear the console after successful input

    if choice == b'1':
        http_selected = True
        socks5_selected = False
    elif choice == b'2':
        http_selected = False
        socks5_selected = True
    else:
        print(f"{red}Invalid choice!{reset}")
        sys.exit(1)
    
    Write.Print("Enter the number of proxies to validate:\n", Colors.green_to_blue, interval=0.000)
    validate_limit = int(input())

    clear_console()  # Clear the console after successful input

    # Start continuously updating the console title
    title_thread = threading.Thread(target=continuously_update_title)
    title_thread.daemon = True
    title_thread.start()

    # Start loading animation
    loading_thread = threading.Thread(target=loading_animation)
    loading_thread.start()

    # Clean proxy links on startup
    clean_proxy_links()

    # Stop loading animation
    loading = False
    loading_thread.join()
    sys.stdout.write('\r' + ' ' * 60 + '\r')
    sys.stdout.flush()

    # Delete old files on startup
    if os.path.exists(os.path.join(new_folder_path, "http_proxies.txt")):
        os.remove(os.path.join(new_folder_path, "http_proxies.txt"))
    if os.path.exists(os.path.join(new_folder_path, "socks5_proxies.txt")):
        os.remove(os.path.join(new_folder_path, "socks5_proxies.txt"))
    
    open(os.path.join(results_folder, "http.txt"), "w").close()
    open(os.path.join(results_folder, "socks5.txt"), "w").close()

    valid_http = []
    valid_socks5 = []

    if http_selected:
        proxies_http = scrape_proxies(http_links, "https", "http_proxies.txt")
        check_http_proxies(proxies_http)
    if socks5_selected:
        proxies_socks5 = scrape_proxies(socks5_links, "socks5", "socks5_proxies.txt")
        check_socks5_proxies(proxies_socks5)

    while (http_selected and http_checked < validate_limit) or (socks5_selected and socks5_checked < validate_limit):
        time.sleep(1)

    with exit_message_lock:
        if not exit_message_printed:
            print(f"{Fore.GREEN}Desired number of validated proxies reached. Exiting...{reset}")
            exit_message_printed = True
    remove_old_folders()  # Remove old folders on exit
    sys.exit(0)
