import requests
import json
import time as tm
import random
import urllib.parse
from setproctitle import setproctitle
from cv import get
from colorama import Fore, Style, init
from datetime import datetime as dt, timedelta
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from banner import *
from fake_useragent import UserAgent
from selenium import webdriver

green = Fore.LIGHTGREEN_EX
black = Fore.LIGHTBLACK_EX
red = Fore.LIGHTRED_EX
yellow = Fore.LIGHTYELLOW_EX
white = Fore.LIGHTWHITE_EX
magenta = Fore.LIGHTMAGENTA_EX

init(autoreset=True)

def headers():
    headers = {
        "authority": "notpx.app",
        "method": "GET/POST",
        "path": "/api/v1/mining/status",
        "scheme": "https",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "initData",
        "origin": "https://app.notpx.app",
        "referer": "https://app.notpx.app",
        "user-agent": UserAgent(os="android").random
    }

    return headers

url = "https://notpx.app/api/v1/users/me"
newurl = "https://notpx.app/api/v2/"
minurl = "https://notpx.app/api/v1/"
rpnurl = "https://notpx.app/api/v2/"

WAIT = 180 * 3
DELAY = 2

WIDTH = 1000
HEIGHT = 1000
MAX_HEIGHT = 50

setproctitle("NotPixel")
image = get("")

colour = {
    '#': "#000000",
    '.': "#3690EA",
    '*': "#ffffff"
}

def log_message(message, color=Style.RESET_ALL):
    current_time = dt.now().strftime("[%H:%M:%S]")
    print(f"{black}{current_time}{Style.RESET_ALL}{color}{message}{Style.RESET_ALL}")

def get_sessions_retries(retries=3, backoff_factor=0.5, status_forcelist=(500, 502, 504)):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,

    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

session = get_sessions_retries()

def get_color(pixel, header):
    try:
        response = session.get(f"{newurl}/image/get/{str(pixel)}", headers=header, timeout=10)
        if response.status_code == 403:
            return -1
        
        ##content_type = response.headers.get('Content-Type')
        ##if 'application/json' not in content_type:
        ##   log_message(f"{yellow}Unexpected content type for pixel {pixel}: {content_type}. Response: {response.text}")
        ##   return "#000000"
        
        ##try:
            ##json_data = response.json()
            ##return json_data.get('pixel', {}).get('color', "#000000")
        ##except ValueError:
            ##log_message(f"{yellow}Invalid JSON for pixel {pixel}. Response: {response.text}")
            ##return "#000000"
        
        response.raise_for_status()
        return response.json().get('pixel', {}).get('color', "#000000")
    
    except KeyError:
        log_message(f"{yellow}KeyError: 'color' not found for {pixel}")
        return "#000000"
    except requests.exceptions.Timeout:
        log_message(f"{yellow}Request timed out for pixel {pixel}")
        return "#000000"
    except requests.exceptions.ConnectionError as e:
        log_message(f"{yellow}Connection error {pixel}: {e}")
        return "#000000"
    except requests.exceptions.RequestException as e:
        log_message(f"{yellow}Request failed {pixel}: {e}")
        return "#000000"
    
##driver = webdriver.Chrome()
##driver.get(f"{newurl}/image/get/{str(205473)}")
##page_source = driver.page_source
##print(page_source)

##driver.quit()
    
def claim(header):
    log_message(f"{blue}Claim Resources")
    try:
        session.get(f"{url}/mining/claim", headers=header, timeout=10)
    except requests.exceptions.RequestException as e:
        log_message(f"{red}Failed to claim: {e}")

def get_pixel(x, y):
    return y * 1000 + x + 1

def get_pos(pixel, size_x):
    return pixel % size_x, pixel // size_x

def get_canvas_pos(x, y):
    return get_pixel(start_x + x - 1, start_y + y - 1)

start_x = 472 #920
start_y = 205 #386

def paint(canvas_pos, color, header):
    data = {
        "pixelId": canvas_pos,
        "newColor": color
    }

    try:
        response = session.post(f"{rpnurl}/repaint/start", data=json.dumps(data), headers=header, timeout=10)
        x, y = get_pos(canvas_pos, 1000)

        if response.status_code == 400:
            log_message(f"{red}Out of energy")
            return False
        if response.status_code == 401:
            return -1

        log_message(f"{green}Paint: {x},{y}")
        return True
    except requests.exceptions.RequestException as e:
        log_message(f"{red}Failed to paint: {e}")
        return False

def extract_username_from_initdata(init_data):
    
    decoded_data = urllib.parse.unquote(init_data)
    
    username_start = decoded_data.find('"username":"') + len('"username":"')
    username_end = decoded_data.find('"', username_start)
    
    if username_start != -1 and username_end != -1:
        return decoded_data[username_start:username_end]
    
    return "Unknown"

def multi_login(login_url, accounts):
    session = session()
    for account in accounts:
        response = username(session, login_url, account)
        init_data = response.data
        username = extract_username_from_initdata(init_data)
        
        print(f"Extracted Username: {username}")

def load_accounts_from_file(filename):
    with open(filename, 'r') as file:
        accounts = [f"initData {line.strip()}" for line in file if line.strip()]
    return accounts

def fetch_mining_data(header):
    try:
        response = session.get(f"https://notpx.app/api/v1/mining/status", headers=header, timeout=10)
        if response.status_code == 200:
            data = response.json()
            user_balance = data.get('userBalance', 'Unknown')
            log_message(f"{yellow}Balance: {user_balance}")
        else:
            log_message(f"{red}Failed to fetch mining data: {response.status_code}")
    except requests.exceptions.RequestException as e:
        log_message(f"{red}Error fetching mining data: {e}")


def main(auth, account):
    headers = {'authorization': auth}

    try:
        fetch_mining_data(headers)
        
        claim(headers)

        size = len(image) * len(image[0])
        order = [i for i in range(size)]
        random.shuffle(order)

        for pos_image in order:
            x, y = get_pos(pos_image, len(image[0]))
            tm.sleep(0.05 + random.uniform(0.01, 0.1))
            try:
                color = get_color(get_canvas_pos(x, y), headers)
                if color == -1:
                    log_message(f"{red}NOT FOUND or DIE, TRY WITH GET NEW QUERY_ID")
                    print(headers["authorization"])
                    break

                if image[y][x] == ' ' or color == colour[image[y][x]]:
                    log_message(f"{white}Skip: {start_x + x - 1},{start_y + y - 1}")
                    continue

                result = paint(get_canvas_pos(x, y), colour[image[y][x]], headers)
                if result == -1:
                    log_message(f"{red}DIES")
                    print(headers["authorization"])
                    break
                elif result:
                    continue
                else:
                    break

            except IndexError:
                log_message(f"{red}IndexError at pos_image: {pos_image}, y: {y}, x: {x}")

    except requests.exceptions.RequestException as e:
        log_message(f"{red}Network error in account {account}: {e}")

def process_accounts(accounts):
    first_account_start_time = dt.now()

    for account in accounts:
        username = extract_username_from_initdata(account)
        log_message(f"{green}ACCOUNT: {username}")
        main(account, account)

    time_elapsed = dt.now() - first_account_start_time
    time_to_wait = timedelta(hours=1) - time_elapsed

    if time_to_wait.total_seconds() > 0:
        log_message(f"{yellow}SLEEPING FOR {int(time_to_wait.total_seconds() // 60)} MINUTES")
        tm.sleep(time_to_wait.total_seconds())
    else:
        log_message(f"{green}NO NEED RETRIES, PROCCESSING ABOUT 1H")

if __name__ == "__main__":
    accounts = load_accounts_from_file('data.txt')
    print(banner)

    while True:
        process_accounts(accounts)