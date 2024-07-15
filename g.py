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
DATA_FILE = 'x.txt'

def get_twitter_auth(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
        consumer_key = lines[0].strip()
        consumer_secret = lines[1].strip()
        access_token = lines[2].strip()
        access_token_secret = lines[3].strip()
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

# Fungsi lain tetap sama seperti sebelumnya...

if __name__ == "__main__":
    auth = get_twitter_auth(DATA_FILE)
    while True:
        if is_within_time_range(MONITOR_START_HOUR, MONITOR_END_HOUR):
            latest_tweet = get_latest_tweet(TWITTER_URL, auth)
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
