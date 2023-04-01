import json
#import time
import requests
import os

# Set up API endpoint and bot token
API_LINK = "https://api.telegram.org/bot6230593358:AAFqvivxeQtuW2q2zQLQsJNWC5_xuvqEsHA"


logo = {
    "chat_id"
}



description = {
    "name": "Anonymous Chatbot with MBTI Test",
    "description": "👋 Welcome to our anonymous chatbot with MBTI test! \n\n🧐 Take the MBTI test to discover your personality type and connect with others who have similar traits in our anonymous chat. 🕵️‍♀️ \n\n🤫 Chat anonymously without revealing any personal information and feel free to express yourself without judgment. \n\n👥 /join our anonymous chat community today and start exploring your personality!"
}

response = requests.post(API_LINK + "/setMyDescription", data=description, timeout=1.5)
if response.ok:
    print('Set Bot description Succesfully.')
else:
    print('Failed to Set Bot description.')

shortdescription = {
    "name": "Anonymous Chatbot with MBTI Test",
    "short_description": "👥 Discover your personality type and connect with others anonymously in our chatbot! 🕵️‍♀️"
}

response = requests.post(API_LINK + "/setMyDescription", data=description, timeout=1.5)
if response.ok:
    print('Set Bot short description Succesfully.')
else:
    print('Failed to Set Bot short description.')


commands = {"commands" : [
                    {"command" : "/join" , "description" : "🤝: Join the conversation"},
                    {"command" : "/stop" , "description" : "🚫: Stop the conversation"},
                    {"command" : "/settings" , "description" : "⚙️: Access your account settings"},
                    {"command" : "/about" , "description" : "ℹ️: Learn more about the bot or channel"},
                    {"command" : "/shareprofile" , "description" : "📤: Share your profile link"},
                      ]}

response = requests.post(API_LINK + "/setMyCommands", json=commands, timeout=1.5)
if response.ok:
    print('Commands Menu set succesfully.')
else:
    print('Failed to set Commands Menu.')

# Upload the photo to Telegram servers
url = f"{API_LINK}/sendPhoto"
photo_path = os.path.join(os.getcwd(), "pics", "logo.jpg")
files = {"photo": open(photo_path, "rb")}
response = requests.post(url, files=files)

if response.status_code != 200:
    print(f"Error uploading photo: {response.text}")
    exit()

photo_id = response.json().get("result", {}).get("photo", [])[-1].get("file_id")
if not photo_id:
    print("No photo_id found in response")
    exit()

# Set the photo as the bot profile photo
url = f"{API_LINK}/setMyBotPicture"
data = {"photo": json.dumps({"id": photo_id})}
response = requests.post(url, data=data)

if response.status_code != 200:
    print(f"Error setting bot profile photo: {response.text}")
    exit()

print("Bot profile photo set successfully")