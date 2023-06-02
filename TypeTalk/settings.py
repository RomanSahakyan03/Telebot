import requests
from db import BotDB
from utils import send_request
import os
db = BotDB("./TypeTalk/userdata.db")

db.create_table('users', [
    'id INTEGER PRIMARY KEY AUTOINCREMENT', 
    'chat_id INTEGER', 
    'language TEXT',
    'TYPE INTEGER(1)', 
    'TYPES INTEGER(2) DEFAULT 0', 
    'region_lat REAL',
    'region_lon REAL',
    'age INTEGER(1)', 
    'age_interval TEXT',
    'rate INTEGER(1) DEFAULT 5',
    'gender TEXT',
    'preferred_genders TEXT'
])

telegram_token = os.environ.get('TELEGRAM_API_TOKEN')
API_LINK = f"https://api.telegram.org/bot{telegram_token}"

description = {
    "name": "Anonymous Chatbot with MBTI Test",
    "description": "👋 Welcome to our anonymous chatbot with MBTI test! \n\n🧐 Take the MBTI test to discover your personality type and connect with others who have similar traits in our anonymous chat. 🕵️‍♀️ \n\n🤫 Chat anonymously without revealing any personal information and feel free to express yourself without judgment. \n\n👥 /join our anonymous chat community today and start exploring your personality!"
}
send_request(description, "setMyDescription", "bot description")

# response = requests.post(API_LINK + "/setMyDescription", data=description, timeout=1.5)
# if response.ok:
#     print('Set Bot description Succesfully.')
# else:
#     print('Failed to Set Bot description.')

shortdescription = {
    "name": "Anonymous Chatbot with MBTI Test",
    "short_description": "👥 Discover your personality type and connect with others anonymously in our chatbot! 🕵️‍♀️"
}

response = requests.post(API_LINK + "/setMyShortDescription", data=description, timeout=1.5)
if response.ok:
    print('Set Bot short description Succesfully.')
else:
    print('Failed to Set Bot short description.')

commands = {
    "commands" : [
{"command" : "/join" , "description" : "🤝: Join the conversation"},
{"command" : "/stop" , "description" : "🚫: Stop the conversation"},
{"command" : "/settings" , "description" : "⚙️: Access your account settings"},
{"command" : "/about" , "description" : "ℹ️: Learn more about the bot or channel"},
{"command" : "/shareprofile" , "description" : "📤: Share your profile link"},
    ]}
    
send_request(commands, "setMyCommands", "Commands Menu")