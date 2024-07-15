import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime, timedelta

# URL akun Twitter yang ingin dipantau
TWITTER_URL = 'https://twitter.com/GetGames_TG'
POST_URL = 'https://dolphin-app-2-qkmuv.ondigitalocean.app/api/tasks/chest/open'

# Waktu pemantauan dalam UTC
MONITOR_START_HOUR = 13
MONITOR_END_HOUR = 20

# File yang berisi daftar accountId
DATA_FILE = 'data.txt'

def get_latest_tweet(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            tweet_divs = soup.find_all('div', {'data-testid': 'tweet'})
            if tweet_divs:
                latest_tweet = tweet_divs[0].get_text()
                return latest_tweet
        else:
            print(f"Failed to retrieve page: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    return None

def extract_code(text):
    # Asumsikan kode memiliki pola tertentu
    patterns = [
        r'\b[a-zA-Z0-9]{10}\b',  # 10 karakter alfanumerik
        r'\b[a-zA-Z0-9]{8}\b',   # 8 karakter alfanumerik
        r'\b[a-zA-Z0-9]{12}\b',  # 12 karakter alfanumerik
        r'\b[a-zA-Z0-9]{6,12}\b' # 6 hingga 12 karakter alfanumerik
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None

def is_within_time_range(start_hour, end_hour):
    current_utc_time = datetime.utcnow()
    start_time = current_utc_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end_time = current_utc_time.replace(hour=end_hour, minute=0, second=0, microsecond=0)
    return start_time <= current_utc_time <= end_time

def time_until_start(start_hour):
    current_utc_time = datetime.utcnow()
    start_time = current_utc_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    if current_utc_time > start_time:
        start_time += timedelta(days=1)
    return start_time - current_utc_time

def get_account_ids(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file.readlines()]

def perform_task(account_id, xcode):
    payload = {
        "chestId": 1,
        "accountId": account_id,
        "tdCode": "",
        "xCode": xcode
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(POST_URL, json=payload, headers=headers)
    return response.status_code, response.json()

if __name__ == "__main__":
    while True:
        if is_within_time_range(MONITOR_START_HOUR, MONITOR_END_HOUR):
            latest_tweet = get_latest_tweet(TWITTER_URL)
            if latest_tweet:
                print(f"Latest tweet: {latest_tweet}")
                code = extract_code(latest_tweet)
                if code:
                    print(f"Extracted code: {code}")
                    account_ids = get_account_ids(DATA_FILE)
                    for account_id in account_ids:
                        status_code, response = perform_task(account_id, code)
                        print(f"Performed task for account {account_id}: Status Code {status_code}, Response {response}")
                else:
                    print("No code found in the latest tweet.")
            else:
                print("Failed to retrieve the latest tweet.")
        else:
            countdown = time_until_start(MONITOR_START_HOUR)
            while countdown.total_seconds() > 0:
                hours, remainder = divmod(countdown.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                print(f"Outside monitoring time range. Countdown to monitoring start: {hours} hours, {minutes} minutes, {seconds} seconds.", end="\r")
                time.sleep(1)
                countdown -= timedelta(seconds=1)
            print("\nStarting monitoring period...")

        # Tunggu selama beberapa detik sebelum memeriksa kembali
        time.sleep(60)
