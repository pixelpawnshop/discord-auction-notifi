import discord
import asyncio
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import requests
import network

# Discord bot token and channel ID
TOKEN = network.TOKEN
CHANNEL_ID = network.CHANNEL_ID  # Replace with your actual channel ID

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Ensure GUI is off
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Set path to chromedriver as per your configuration
webdriver_service = Service("C:/webdriver/chromedriver.exe")  # Change this to your path

def wei_to_eth(wei):
    return wei / 10**18

def getTime():
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    
    # Open the website
    driver.get("https://nouns.wtf/")
    # Wait for the page to load
    time.sleep(1)

    # Locate the elements using XPath and extract the text, removing the last character
    hour_text = driver.find_element(By.XPATH, '//*[@id="root"]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div[2]/div/div[2]/h2/div[1]').text[:-1]
    minute_text = driver.find_element(By.XPATH, '//*[@id="root"]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div[2]/div/div[2]/h2/div[2]').text[:-1]
    second_text = driver.find_element(By.XPATH, '//*[@id="root"]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div[2]/div/div[2]/h2/div[3]').text[:-1]

    # Convert the text values to integers
    hour = int(hour_text)
    minute = int(minute_text)
    second = int(second_text)
    
    current_bid = driver.find_element(By.XPATH, '//*[@id="root"]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div[1]/div/div[2]').text
    list_bid = current_bid.split(" ")
    current_bid = float(list_bid[1])
    print(f"checking the current bid: {current_bid}")    
    
    # Make API call to check the current top bid on OpenSea
    url = "https://api.opensea.io/api/v2/offers/collection/nouns"
    headers = {"accept": "application/json", "x-api-key": network.OPENSEA_API_KEY}
    response = requests.get(url, headers=headers)
    print(response)
    data = response.json()
    top_bid = int(data["offers"][0]["price"]["value"])
    eth = wei_to_eth(top_bid)
    
    if current_bid < eth * 0.9:
        print(f"current bid nouns ({current_bid}) < opensea top bid x 0.9 ({eth})")
        print("Init bid....")
        driver.quit()
        return True, current_bid, eth, hour, minute, second

    # Close the browser
    driver.quit()
    return False, None, None, hour, minute, second

# Discord bot client
class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        intents = kwargs.pop('intents', discord.Intents.default())
        super().__init__(*args, intents=intents, **kwargs)

    async def setup_hook(self):
        self.bg_task = self.loop.create_task(self.my_background_task())

    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def my_background_task(self):
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)
        while not self.is_closed():
            try:
                check, current_bid, eth, hour, minute, second = getTime()
                if check and channel:
                    # Constructing a mention string for the user
                    await channel.send(f"Current bid ({current_bid}) is less than 90% of the top bid on OpenSea ({eth}). Time left: {hour}:{minute}:{second}")
            except Exception as e:
                print(f"An error occurred: {e}")
            await asyncio.sleep(300)  # wait for 5 minutes

# Create the intents object
intents = discord.Intents.default()

client = MyClient(intents=intents)

# Run the Discord bot
client.run(TOKEN)
