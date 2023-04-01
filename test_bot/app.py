import json
import time
import requests

# Set up API endpoint and bot token
API_LINK = "https://api.telegram.org/bot6114753472:AAFBAES3t622glVzoe5-4BpKF0hjbBeX6_c"
GET_UPDATES_URL = f"{API_LINK}/getUpdates"
SEND_MESSAGE_URL = f"{API_LINK}/sendMessage"
INLINE_KEYBOARD = f"{API_LINK}/InlineKeyboardMarkup"
SEND_PHOTO_URL = f"{API_LINK}/sendPhoto"
PROCCESSED_OFFSET = 0


# Define constants for string literals
START_MESSAGE = "👋 Start The Conversation"
SETTINGS_MESSAGE = "🛠️ Manage your Settings"
ABOUT_MESSAGE = "📖About the bot"
PAYMENT_MESSGAE = "💵Payment"
ABOUT_TEXT =  "Welcome to TypeTalk! We're an anonymous chat bot that connects you with like-minded people based on your MBTI personality type. " \
              "To start a new chat, type /join. Use /settings to customize your search parameters. \n\n" \
              "During a conversation, you can use the /stop command to end the chat at any time. " \
              "If you want to chat with a new person, use the /next command to be matched with a new partner based on your search preferences. \n\n" \
              "You can adjust your search parameters anytime by using /settings. For more information about TypeTalk, type /about. \n\n" \
              "We prioritize your privacy and ensure that all chats are anonymous and kept confidential!! "


def join(update):
    pass

# Define a function to handle the /start command
def start(update):
    if(None):
        start(update)
    else:    
        join(update)

# Define a function to handle the /about command
def about(update):
    chat_id = update['message']['chat']['id']
    keyboard = {
        "keyboard": 
            [[{"text": START_MESSAGE},
             {"text": SETTINGS_MESSAGE}],
            [{"text": ABOUT_MESSAGE},
             {"text": PAYMENT_MESSGAE}]],

        "resize_keyboard": True
    }
# MARIA's chat id 842079224

    data = {
        "chat_id": chat_id,
        "photo" : "https://64.media.tumblr.com/16f5503bc2c6017c4738dc434b037500/tumblr_ol8v1amxc91ugs09ro1_1280.jpg",
        "caption": ABOUT_TEXT,
        "reply_markup": json.dumps(keyboard)
    }
    start_response = requests.post(SEND_PHOTO_URL, json=data, timeout=1.5)
    if start_response.ok:
        print('Start Text Message Sent Successfully.')
    else:
        print('Failed to Send Start Text Message.')


def stop(update):
    chat_id = update['message']['chat']['id']
    data = {
        "chat_id": chat_id,
        "text": "Conversation ended. Type /join to begin a new conversation."
    }
    response = requests.post(SEND_MESSAGE_URL, json=data, timeout=1.5)
    if response.ok:
        print('Conversation Stoped Successfully.')
    else:
        print('Failed to Stop Conversation.')

def settings(update):
    chat_id = update['message']['chat']['id']
    # Create the keyboard
    keyboard = {
    "inline_keyboard": [
        [{"text": "Your MBTI Type", "callback_data": "my_type"},
        {"text": "Prefered MBTI Types", "callback_data": "prefered_types"},],
        [{"text": "Your Age", "callback_data": "my_age"},
        {"text": "Prefered Age Interval", "callback_data": "prefered_ages"},],
        [{"text": "💸Gender", "callback_data": "genders"},
        {"text": "Region", "callback_data": "region"}]
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


def callback_handler(call_back_data):
    print(call_back_data)
    if call_back_data == "my_type":
        pass
    if call_back_data == "prefered_types":
        pass
    if call_back_data == "genders":
        pass
    if call_back_data == "region":
        pass


COMMANDS = {
    '/start': None,
    '👋 Start The Conversation' : None,
    '/join': None,
    '/stop': stop,
    '/settings': settings,
    '🛠️ Manage your Settings' : settings,
    '/shareprofile': None,
    '/about': about,
    '📖About the bot' : about
}


while True:
    try:
        response = requests.get(GET_UPDATES_URL, params={'offset': PROCCESSED_OFFSET})
        if response.ok:
            updates = response.json()['result']
            for update in updates:
                if 'message' in update and 'text' in update['message']:
                    text = update['message']['text']
                    if text in COMMANDS:
                        handler = COMMANDS[text]
                        if handler:
                            handler(update)
                if 'callback_query' in update and 'data' in update['callback_query']:
                    callback_data = update['callback_query']['data']
                    if 'data' in update['callback_query']:
                        callback_handler(callback_data)
            PROCCESSED_OFFSET = max(PROCCESSED_OFFSET, update['update_id'] + 1)
        time.sleep(0.75)
    except Exception as e:
        print(f'Error occurred: {e}')
        time.sleep(5)