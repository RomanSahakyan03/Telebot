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
def start(user_id):
    data = {
        "chat_id": user_id,
        "photo" : "https://64.media.tumblr.com/16f5503bc2c6017c4738dc434b037500/tumblr_ol8v1amxc91ugs09ro1_1280.jpg",
        "caption": "👋 Welcome to our MBTI-based chat bot! \n\n" \
              "We're here to help you connect with like-minded individuals based on your unique personality type. \n\n" \
              "Simply select your MBTI type and we'll match you with someone who shares your values and interests. \n\n" \
              "Whether you're seeking new friends, meaningful conversations, or just a bit of fun, " \
              "our chat bot has got you covered. \n\n" \
              "Start exploring your personality and connecting with others today! 🤗",
    }
    start_response = requests.post(SEND_PHOTO_URL, json=data, timeout=1.5)
    if start_response.ok:
        print('Start Text Message sent successfully.')
    else:
        print('Failed to send Start Text message.')


while True:
    response = requests.get(GET_UPDATES_URL, params={'offset': processed_offset, 'timeout': 30})
    if response.ok:
        updates = json.loads(response.content)['result']
        if updates:
            for update in updates:
                chat_id = update['message']['chat']['id']
                if 'text' in update['message']:
                    if update['message']['text'] == '/start':
                        start(chat_id)
                    if update['message']['text'] == '/join':
                        pass
                    if update['message']['text'] == '/settings':
                        pass
                    if update['message']['text'] == '/shareprofile':
                        pass
                    if update['message']['text'] == '/about':
                        start(chat_id)
                        
                processed_offset = max(processed_offset, update['update_id'] + 1)
        time.sleep(2)
    else:
        print('Failed to get updates.')
        time.sleep(5)
