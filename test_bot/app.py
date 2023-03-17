import json
import time
import requests

# Set up API endpoint and bot token
API_LINK = "https://api.telegram.org/bot6230593358:AAFqvivxeQtuW2q2zQLQsJNWC5_xuvqEsHA"
GET_UPDATES_URL = API_LINK + "/getUpdates"
SEND_MESSAGE_URL = API_LINK + "/sendMessage"
INLINE_KEYBOARD = API_LINK + "/InlineKeyboardMarkup"
SEND_PHOTO_URL = API_LINK + "/sendPhoto"
PROCESSED_UPDATES = None
processed_offset = 0

# Define a function to handle the /start command
def start(chat_id):
    keyboard = {
        "keyboard": 
            [[{"text": "👋 Start The Conversation"},
             {"text": "🛠️ Manage your Settings"}],
            [{"text": "📖About the bot"},
             {"text": "💵Payment"}]],

        "resize_keyboard": True
    }



    data = {
        "chat_id": chat_id,
        "photo" : "https://64.media.tumblr.com/16f5503bc2c6017c4738dc434b037500/tumblr_ol8v1amxc91ugs09ro1_1280.jpg",
        "caption": "👋 Welcome to our MBTI-based chat bot! \n\n" \
              "We're here to help you connect with like-minded individuals based on your unique personality type. \n\n" \
              "Simply select your MBTI type and we'll match you with someone who shares your values and interests. \n\n" \
              "Whether you're seeking new friends, meaningful conversations, or just a bit of fun, " \
              "our chat bot has got you covered. \n\n" \
              "Start exploring your personality and connecting with others today! 🤗",
        "reply_markup": json.dumps(keyboard)
    }
    start_response = requests.post(SEND_PHOTO_URL, json=data, timeout=1.5)
    if start_response.ok:
        print('Start Text Message Sent Successfully.')
    else:
        print('Failed to Send Start Text Message.')


def stop(chat_id):
    data = {
        "chat_id": chat_id,
        "text": "Conversation ended. Type /join to begin a new conversation."
    }
    response = requests.post(SEND_MESSAGE_URL, json=data, timeout=1.5)
    if response.ok:
        print('Conversation Stoped Successfully.')
    else:
        print('Failed to Stop Conversation.')

def settings(chat_id):
    # Create the keyboard
    keyboard = {
    "inline_keyboard": [
        [{"text": "Your MBTI Type", "callback_data": "1"}],
        [{"text": "Prefered MBTI Types", "callback_data": "5"},],
        [{"text": "Gender", "callback_data": "9"}]
        ]}
    data = {
        "chat_id" : chat_id,
        "text" : "Which one you would prefer to change?",
        "reply_markup" : json.dumps(keyboard)
    }
    response = requests.post(SEND_MESSAGE_URL, json=data, timeout=1.5)
    if response.ok:
        print('Settings opened Successfully.')
    else:
        print('Failed to open Settings.')



while True:
    response = requests.get(GET_UPDATES_URL, params={'offset': processed_offset, 'timeout': 15}, timeout=15)
    if response.ok:
        updates = response.json()['result']
        if updates:
            for update in updates:
                if 'message' in update:
                    chat_id = update['message']['chat']['id']
                    if 'text' in update['message']:
                        if update['message']['text'] == '/start':
                            start(chat_id)
                        if update['message']['text'] == '/join' or update['message']['text'] == "👋 Start The Conversation":
                            pass
                        if update['message']['text'] == '/stop':
                            stop(chat_id)
                        if update['message']['text'] == '/settings' or update['message']['text'] == "🛠️ Manage your Settings":
                            settings(chat_id)
                        if update['message']['text'] == '/shareprofile':
                            pass
                        if update['message']['text'] == '/about' or update['message']['text'] == "📖About the bot":
                            start(chat_id)
                    processed_offset = max(processed_offset, update['update_id'] + 1)
        time.sleep(0.75)
    else:
        print('Failed to get updates.')
        time.sleep(5)
