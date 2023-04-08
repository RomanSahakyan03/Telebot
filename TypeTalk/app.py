import json
import time
import requests

from bot import BotDB
db = BotDB("/userdata.db")

# Set up API endpoint and bot token
API_LINK = "https://api.telegram.org/bot6114753472:AAFBAES3t622glVzoe5-4BpKF0hjbBeX6_c"
GET_UPDATES_URL = f"{API_LINK}/getUpdates"
SEND_MESSAGE_URL = f"{API_LINK}/sendMessage"
INLINE_KEYBOARD = f"{API_LINK}/InlineKeyboardMarkup"
SEND_PHOTO_URL = f"{API_LINK}/sendPhoto"
PROCCESSED_OFFSET = 0
USER_STATE = {} # Can be 'age_collect', 'age_interval', 'region_collect'

# Define constants for string literals for localisation 
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
    chat_id = update['message']['chat']['id']
    if db.check_exist(chat_id):
        join(update)
    settings_queue = ['language', 'TYPE', 'TYPES', 'region', 'age', 'min_prefered_age', 'max_prefered_age']
    dict = {}
    
    #if 'language' not in dict:
    #    callback_handler('language')
    #    dict.update({'language' : })
    #    start(update, dict)

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

def lang_setting(update):
    chat_id = update['callback_query']['from']['id']
    keyboard = {
    "inline_keyboard": [
        [{"text": "🇺🇸 English", "callback_data": "English"},
        {"text": "🇷🇺 Russian", "callback_data": "Russian"}]
        ]}
    data = {
        "chat_id" : chat_id,
        "text" : "Preferred language?",
        "reply_markup" : json.dumps(keyboard)
    }
    response = requests.post(SEND_MESSAGE_URL, json=data, timeout=1.5)
    if response.ok:
        print('Language selection menu opened successfully.')
    else:
        print('Failed to open language selection menu.')

def TYPE_setting(update):
    chat_id = update['callback_query']['from']['id']
    mbti_types = {
    0: "INTJ", 1: "INFJ", 2: "ISTJ", 3: "ISTP",
    4: "INTP", 5: "INFP", 6: "ISFJ", 7: "ISFP",
    8: "ENTJ", 9: "ENFJ", 10: "ESTJ", 11: "ESTP",
    12: "ENTP", 13: "ENFP", 14: "ESFJ", 15: "ESFP"
    }
    # Create the keyboard
    keyboard = {
    "inline_keyboard": [
        [{"text": mbti_types[bit], "callback_data": mbti_types[bit] + "_m"} for bit in range(row * 4, (row + 1) * 4) if bit < 16] for row in range((16 - 1) // 4 + 1)
    ]
    }
    # Convert the keyboard to JSON format
    keyboard_json = json.dumps(keyboard)
    data = {
        "chat_id" : chat_id,
        "text" : "Choose your MBTI type",
        "reply_markup" : json.dumps(keyboard)
    }

    response = requests.post(SEND_MESSAGE_URL, json=data, timeout=1.5)
    if response.ok:
        print('MBTI type selection menu opened successfully.')
    else:
        print('Failed to open MBTI type selection menu.')


def TYPES_setting(update):
    chat_id = update['callback_query']['from']['id']
    mbti_types = {
    0: "INTJ", 1: "INFJ", 2: "ISTJ", 3: "ISTP",
    4: "INTP", 5: "INFP", 6: "ISFJ", 7: "ISFP",
    8: "ENTJ", 9: "ENFJ", 10: "ESTJ", 11: "ESTP",
    12: "ENTP", 13: "ENFP", 14: "ESFJ", 15: "ESFP"
    }
    #x = db.select_parameter("users", "TYPES", f"chat_id = {chat_id}")
    x = 1315
    print(x)
    num_bits = 16
    # Create a list of the MBTI types, with checkmark emojis for the selected types
    mbti_types_list = [f"✅ {mbti_types[bit]}" if (x >> bit) & 1 else f"  {mbti_types[bit]}" for bit in range(num_bits)]

    # Divide the MBTI types into rows of 4, and create the keyboard
    keyboard = {
    "inline_keyboard": [
        [{"text": mbti_types_list[bit], "callback_data": mbti_types[bit] + "_p"} for bit in range(row * 4, (row + 1) * 4) if bit < num_bits] for row in range((num_bits - 1) // 4 + 1)
    ]
}
    # Convert the keyboard to JSON format
    keyboard_json = json.dumps(keyboard)
    data = {
        "chat_id" : chat_id,
        "text" : "Choose your preffered MBTI types",
        "reply_markup" : json.dumps(keyboard)
    }

    response = requests.post(SEND_MESSAGE_URL, json=data, timeout=1.5)
    if response.ok:
        print('MBTI preffered types selection menu opened successfully.')
    else:
        print('Failed to open MBTI preffered types selection menu.')


def settings(update):
    chat_id = update['message']['chat']['id']
    # Create the keyboard
    keyboard = {
    "inline_keyboard": [
        [{"text": "Language", "callback_data": "language"},],
        [{"text": "Your MBTI Type", "callback_data": "TYPE"},
        {"text": "Prefered MBTI Types", "callback_data": "TYPES"},],
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


def callback_handler(update):
    callback_data = update['callback_query']['data']
    print(callback_data)
    if callback_data == "language":
        lang_setting(update)
        return
    if callback_data == "TYPE":
        TYPE_setting(update)
        return
    if callback_data == "TYPES":
        TYPES_setting(update)
        return
    if callback_data == "region":
        pass
    if callback_data == "age":
        pass
    if callback_data == "min_prefered_age":
        pass
    if callback_data == "max_prefered_age":
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
                    callback_handler(update)              
                PROCCESSED_OFFSET = max(PROCCESSED_OFFSET, update['update_id'] + 1)
        time.sleep(0.75)
    except Exception as e:
        print(f'Error occurred: {e}')
        time.sleep(5)