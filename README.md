
# Proxy Scraper and Checker

![Stable](https://img.shields.io/badge/status-stable-brightgreen) 

![Discord](https://dcbadge.limes.pink/api/shield/741265873779818566?compact=true)

## Features

- **Configurable Threading**: Adjust the number of threads based on your system's capability using a `usage_level` setting from 1 to 3.
- **Scraping Proxies**: Scrape HTTP/s and SOCKS5 proxies from various sources.
- **Checking Proxies**: Validate the scraped proxies to ensure they are working.
- **System Monitoring**: Display CPU and RAM usage of the script in the console title.

## Installation

1. Clone the repository or download the .zip file.
2. Navigate to the project directory.

## Running the Script

Run the script using:

```bash
start.bat
```
or

```bash
python main.py
```

## Requirements

- Python 3.8+
- Required packages will be automatically installed on start.

## Important Information!

For educational & research purposes only!

## Detailed Documentation

### Configuration

The configuration file `config.json` contains settings for the script:

- `usage_level`: An integer from 1 to 3 representing system usage allowance.
- `http_links`: A list of URLs to scrape HTTP proxies from.
- `socks5_links`: A list of URLs to scrape SOCKS5 proxies from.

### Functions

#### `generate_random_folder_name(length=32)`

Generates a random folder name with the specified length.

#### `remove_old_folders(base_folder=".")`

Removes old folders with 32 character names in the base folder.

#### `get_time_rn()`

Returns the current time formatted as HH:MM:SS.

#### `get_usage_level_str(level)`

Converts the usage level integer to a string representation.

#### `update_title(http_selected, socks5_selected, usage_level)`

Updates the console title with current CPU, RAM usage, and validation counts.

#### `center_text(text, width)`

Centers the text within the given width.

#### `ui()`

Clears the console and displays the main UI with ASCII art.

#### `scrape_proxy_links(link, proxy_type)`

Scrapes proxies from the given link, retries up to 3 times in case of failure.

#### `check_proxy_link(link)`

Checks if a proxy link is accessible.

#### `clean_proxy_links()`

Cleans the proxy links by removing non-accessible ones.

#### `scrape_proxies(proxy_list, proxy_type, file_name)`

Scrapes proxies from the provided list of links and saves them to a file.

#### `check_proxy_http(proxy)`

Checks the validity of an HTTP/s proxy by making a request to httpbin.org.

#### `check_proxy_socks5(proxy)`

Checks the validity of a SOCKS5 proxy by connecting to google.com.

#### `check_http_proxies(proxies)`

Checks a list of HTTP/s proxies for validity.

#### `check_socks5_proxies(proxies)`

Checks a list of SOCKS5 proxies for validity.

#### `signal_handler(sig, frame)`

Handles SIGINT signal (Ctrl+C) to exit gracefully.

#### `set_process_priority()`

Sets the process priority to high for better performance.

#### `loading_animation()`

Displays a loading animation while verifying proxy links.

#### `clear_console()`

Clears the console screen.

#### `continuously_update_title()`

Continuously updates the console title with current status.

### Example `config.json`

```json
{
    "usage_level": 2,
    "http_links": [
        "https://api.proxyscrape.com/?request=getproxies&proxytype=https&timeout=10000&country=all&ssl=all&anonymity=all",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
    ],
    "socks5_links": [
        "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS5.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt"
    ]
}
```

By following this documentation, you should be able to set up, run, and understand the Proxy Scraper and Checker script with ease.

## Script Description

This script is designed to download and verify HTTP/s and SOCKS5 proxies from public databases and files. It offers the following key features:

- **Configurable Threading**: Adjust the number of threads based on your system's capability using a `usage_level` setting from 1 to 3.
- **Scraping Proxies**: Automatically scrape HTTP/s and SOCKS5 proxies from various online sources.
- **Checking Proxies**: Validate the functionality of the scraped proxies to ensure they are operational.
- **System Monitoring**: Display the script's CPU and RAM usage in the console title for real-time performance monitoring.

### Usage

1. **Installation**:
   - Clone the repository or download the .zip file.
   - Navigate to the project directory.

2. **Running the Script**:
   - Execute the script using:
     ```bash
     start.bat
     ```
     or
     ```bash
     python main.py
     ```

3. **Configuration**:
   - The script uses a `config.json` file to manage settings.
   - Adjust the `usage_level`, and specify the list of URLs for HTTP/s and SOCKS5 proxies.

4. **Educational & Research Purposes Only**:
   - This script is intended for educational and research purposes only. Use it responsibly and in accordance with applicable laws.

### Requirements

- Python 3.8+
- All necessary packages are automatically installed when the script is run.

### Example `config.json`

```json
{
    "usage_level": 2,
    "http_links": [
        "https://api.proxyscrape.com/?request=getproxies&proxytype=https&timeout=10000&country=all&ssl=all&anonymity=all",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
    ],
    "socks5_links": [
        "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS5.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt"
    ]
}
```

By following this documentation, you should be able to set up, run, and understand the Proxy Scraper and Checker script with ease.
