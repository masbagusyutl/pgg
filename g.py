import requests
from requests_oauthlib import OAuth1
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

# File yang berisi daftar accountId dan info autentikasi Twitter
AUTH_FILE = 'x.txt'  # File berisi autentikasi Twitter
ACCOUNTS_FILE = 'data.txt'  # File berisi daftar accountId

def get_twitter_auth(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
        consumer_key = lines[0].strip().split(':')[1]
        consumer_secret = lines[1].strip().split(':')[1]
        access_token = lines[2].strip().split(':')[1]
        access_token_secret = lines[3].strip().split(':')[1]
    return OAuth1(consumer_key, client_secret=consumer_secret,
                  resource_owner_key=access_token, resource_owner_secret=access_token_secret)

def get_latest_tweet(url, auth):
    try:
        response = requests.get(url, auth=auth)
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
    return current_utc_time.weekday() < 5 and start_hour <= current_utc_time.hour < end_hour

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
    auth = get_twitter_auth(AUTH_FILE)
    while True:
        if is_within_time_range(MONITOR_START_HOUR, MONITOR_END_HOUR):
            latest_tweet = get_latest_tweet(TWITTER_URL, auth)
            if latest_tweet:
                print(f"Latest tweet: {latest_tweet}")
                code = extract_code(latest_tweet)
                if code:
                    print(f"Extracted code: {code}")
                    account_ids = get_account_ids(ACCOUNTS_FILE)  # Menggunakan data.txt untuk account IDs
                    for account_id in account_ids:
                        status_code, response = perform_task(account_id, code)
                        print(f"Performed task for account {account_id}: Status Code {status_code}, Response {response}")
                else:
                    print("No code found in the latest tweet.")
            else:
                print("Failed to retrieve the latest tweet.")
        else:
            countdown = time_until_start(MONITOR_START_HOUR)
            print("Outside monitoring time range.")
            while countdown.total_seconds() > 0:
                hours, remainder = divmod(countdown.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                print(f"\rCountdown to monitoring start: {hours:02d}:{minutes:02d}:{seconds:02d}", end="")
                time.sleep(1)
                countdown -= timedelta(seconds=1)
            print("\nStarting monitoring period...")

        # Tunggu selama beberapa detik sebelum memeriksa kembali
        time.sleep(60)
