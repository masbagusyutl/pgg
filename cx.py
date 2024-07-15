import requests
from requests_oauthlib import OAuth1
import json

# URL akun Twitter yang ingin dipantau
TWITTER_URL = 'https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=GetGames_TG&count=1'

# File yang berisi info autentikasi Twitter
TWITTER_AUTH_FILE = 'x.txt'

def get_twitter_auth(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
        consumer_key = lines[0].strip().split(':')[1]
        consumer_secret = lines[1].strip().split(':')[1]
        access_token = lines[2].strip().split(':')[1]
        access_token_secret = lines[3].strip().split(':')[1]
    return OAuth1(consumer_key, client_secret=consumer_secret,
                  resource_owner_key=access_token, resource_owner_secret=access_token_secret)

def get_latest_tweet(auth):
    try:
        response = requests.get(TWITTER_URL, auth=auth)
        if response.status_code == 200:
            tweets = response.json()
            if tweets:
                latest_tweet = tweets[0]['text']
                return latest_tweet
            else:
                print("No tweets found.")
        else:
            print(f"Failed to retrieve tweets: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    return None

if __name__ == "__main__":
    twitter_auth = get_twitter_auth(TWITTER_AUTH_FILE)
    latest_tweet = get_latest_tweet(twitter_auth)
    if latest_tweet:
        print(f"Latest tweet: {latest_tweet}")
    else:
        print("Failed to retrieve the latest tweet.")
