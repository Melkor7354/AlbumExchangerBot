import requests
import time

# Replace 'YOUR_BOT_URL_HERE' with the actual URL of your bot
BOT_URL = 'https://albumexchangerbot.onrender.com'


def keep_alive():
    while True:
        try:
            response = requests.get(BOT_URL)
            if response.status_code == 200:
                print("Ping sent successfully!")
            else:
                print(f"Failed to ping! Status code: {response.status_code}")
        except Exception as e:
            print(f"Error while pinging the bot: {e}")
        time.sleep(300)  # Ping every 5 minutes