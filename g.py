import requests
from requests_oauthlib import OAuth1
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime, timedelta

# URL akun Twitter yang ingin dipantau
TWITTER_URL = 'https://twitter.com/GetGames_TG'
TELEGRAM_URL = 'https://t.me/GetGames_TG'
POST_URL = 'https://dolphin-app-2-qkmuv.ondigitalocean.app/api/tasks/chest/open'

# Waktu pemantauan dalam UTC
MONITOR_START_HOUR = 13
MONITOR_END_HOUR = 20

# File yang berisi daftar accountId dan info autentikasi Twitter
TWITTER_AUTH_FILE = 'x.txt'  # File berisi autentikasi Twitter
TELEGRAM_AUTH_FILE = 'tg.txt'  # File berisi token bot Telegram
ACCOUNTS_FILE = 'data.txt'  # File berisi daftar accountId

# Pola regex untuk mengekstrak kode unik
CODE_PATTERN = r'\b[a-zA-Z0-9]{10}\b'  # Sesuaikan pola ini dengan format kode unik yang Anda cari

def get_twitter_auth(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
        consumer_key = lines[0].strip().split(':')[1]
        consumer_secret = lines[1].strip().split(':')[1]
        access_token = lines[2].strip().split(':')[1]
        access_token_secret = lines[3].strip().split(':')[1]
    return OAuth1(consumer_key, client_secret=consumer_secret,
                  resource_owner_key=access_token, resource_owner_secret=access_token_secret)

def get_telegram_auth(filename):
    with open(filename, 'r') as file:
        return file.readline().strip()

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

def get_latest_telegram_post(bot_token, channel_username):
    try:
        url = f'https://api.telegram.org/bot{bot_token}/getChatHistory'
        response = requests.get(url, params={'chat_id': channel_username})
        if response.status_code == 200:
            data = response.json()
            messages = data.get('result', [])
            if messages:
                latest_message = messages[0].get('text', '')
                return latest_message
            else:
                print("No messages found in chat history.")
        else:
            print(f"Failed to retrieve chat history: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    return None

def extract_code(text):
    match = re.search(CODE_PATTERN, text)
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

def perform_task(account_id, tdcode, xcode):
    payload = {
        "chestId": 1,
        "accountId": account_id,
        "tdCode": tdcode,
        "xCode": xcode
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(POST_URL, json=payload, headers=headers)
    return response.status_code, response.json()

if __name__ == "__main__":
    twitter_auth = get_twitter_auth(TWITTER_AUTH_FILE)
    telegram_auth = get_telegram_auth(TELEGRAM_AUTH_FILE)

    while True:
        if is_within_time_range(MONITOR_START_HOUR, MONITOR_END_HOUR):
            # Memantau Twitter
            latest_tweet = get_latest_tweet(TWITTER_URL, twitter_auth)
            if latest_tweet:
                print(f"Latest tweet: {latest_tweet}")
                twitter_code = extract_code(latest_tweet)
                if twitter_code:
                    print(f"Extracted Twitter code: {twitter_code}")
                    account_ids = get_account_ids(ACCOUNTS_FILE)
                    for account_id in account_ids:
                        status_code, response = perform_task(account_id, "", twitter_code)
                        print(f"Performed Twitter task for account {account_id}: Status Code {status_code}, Response {response}")
                else:
                    print("No Twitter code found in the latest tweet.")
            else:
                print("Failed to retrieve the latest tweet.")

            # Memantau Telegram
            latest_telegram_post = get_latest_telegram_post(telegram_auth, TELEGRAM_CHANNEL_USERNAME)
            if latest_telegram_post:
                print(f"Latest Telegram post: {latest_telegram_post}")
                telegram_code = extract_code(latest_telegram_post)
                if telegram_code:
                    print(f"Extracted Telegram code: {telegram_code}")
                    account_ids = get_account_ids(ACCOUNTS_FILE)
                    for account_id in account_ids:
                        status_code, response = perform_task(account_id, telegram_code, "")
                        print(f"Performed Telegram task for account {account_id}: Status Code {status_code}, Response {response}")
                else:
                    print("No Telegram code found in the latest post.")
            else:
                print("Failed to retrieve the latest Telegram post.")
        
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
