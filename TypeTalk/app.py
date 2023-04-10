import json
import time
import requests
import redis

from db import BotDB
db = BotDB("./TypeTalk/userdata.db")
cache = redis.Redis(host='localhost', port=6379, db=0) 
# Can be 'age_collect', 'age_interval', 'region_collect'

# Set up API endpoint and bot token
API_LINK = "https://api.telegram.org/bot6114753472:AAFBAES3t622glVzoe5-4BpKF0hjbBeX6_c"
GET_UPDATES_URL = f"{API_LINK}/getUpdates"
SEND_MESSAGE_URL = f"{API_LINK}/sendMessage"
INLINE_KEYBOARD = f"{API_LINK}/InlineKeyboardMarkup"
SEND_PHOTO_URL = f"{API_LINK}/sendPhoto"

# Define constants for string literals for localisation 
START_MESSAGE = "👋 Start The Conversation"
SETTINGS_MESSAGE = "🛠️ Manage your Settings"
ABOUT_MESSAGE = "📖About the bot"
ABOUT_TEXT =  "Welcome to TypeTalk! \n" \
              "We're an anonymous chat bot that connects you with like-minded people based on your MBTI personality type.\n\n" \
              "Instructions: \n" \
              "Type /join to start a new chat\n" \
              "Use /settings to customize your search parameters. \n" \
              "Use /stop to end a chat anytime. \n" \
              "Use /next to switch chat partners during a conversation. \n\n" \
              "We prioritize your privacy and ensure that all chats are anonymous and kept confidential!! "

PROCCESSED_OFFSET = 0
mbti_types = {
    0: "INTJ", 1: "INFJ", 2: "ISTJ", 3: "ISTP",
    4: "INTP", 5: "INFP", 6: "ISFJ", 7: "ISFP",
    8: "ENTJ", 9: "ENFJ", 10: "ESTJ", 11: "ESTP",
    12: "ENTP", 13: "ENFP", 14: "ESFJ", 15: "ESFP"
    }

def send_message(text, to, reply_markup = None, handler = None):
    data = {
        "chat_id": to,
        "text": text
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    response = requests.post(SEND_MESSAGE_URL, json=data)
    handler_success = ' opened Successfully.'
    handler_fail = 'Failed to open '
    if handler:
        handler_success = handler + handler_success
        handler_fail = handler_fail + handler + '.'
    else:
        handler_success = 'Message sent' + handler_success
        handler_fail = handler_fail + 'sent message' + '.'

    if response.ok:
        print(handler_success)
    else:
        print(handler_fail)

def make_pair(chat_id1, chat_id2):
    cache.hset('pairs', chat_id1, chat_id2)
    cache.hset('pairs', chat_id2, chat_id1)

def del_pair(chat_id1):
    chat_id2 = cache.hget('pairs', chat_id1)
    cache.hdel('pairs', chat_id1)
    cache.hdel('pairs', chat_id2)

def join(update):
    pass

# Define a function to handle the /start command
def start(update):
    chat_id = update['message']['chat']['id']
    if db.check_exist(chat_id):
        join(update)
    else:
        print("not")

# Define a function to handle the /about command
def about(update):
    chat_id = update['message']['chat']['id']
    keyboard = {
        "keyboard": 
            [[{"text": START_MESSAGE},
             {"text": SETTINGS_MESSAGE}],
            [{"text": ABOUT_MESSAGE}]],

        "resize_keyboard": True
    }

    data = {
        "chat_id": chat_id,
        "photo" : "https://i.pinimg.com/474x/a1/2b/8e/a12b8ebbfa769903ac48ba27c6519e9d.jpg",
        "caption": ABOUT_TEXT,
        "reply_markup": json.dumps(keyboard)
    }
    start_response = requests.post(SEND_PHOTO_URL, json=data, timeout=1.5)
    if start_response.ok:
        print('Start Text Message Sent Successfully.')
    else:
        print('Failed to Send Start Text Message.')

def stop(update):
    chat_id1 = update['message']['chat']['id']
    if cache.hexists('pairs', chat_id1): 
        chat_id2 = cache.hget('pairs', chat_id)
        send_message('👋 Conversation ended. Type /join to begin a new conversation.', chat_id1)
        send_message('👋 Conversation ended. Type /join to begin a new conversation.', chat_id2)

        del_pair(chat_id1)

def lang_setting(update):
    chat_id = update['callback_query']['from']['id']
    keyboard = {
    "inline_keyboard": [
        [{"text": "🇺🇸 English", "callback_data": "English"},
        {"text": "🇷🇺 Russian", "callback_data": "Russian"}]
        ]}
    send_message("Preferred language?", chat_id, keyboard, 'Language selection menu')

def TYPE_setting(update):
    chat_id = update['callback_query']['from']['id']
    # Create the keyboard
    keyboard = {
    "inline_keyboard": [
        [{"text": mbti_types[bit], "callback_data": mbti_types[bit] + "_m"} for bit in range(row * 4, (row + 1) * 4) if bit < 16] for row in range((16 - 1) // 4 + 1)
    ]}

    send_message('Choose your MBTI type', chat_id, keyboard, 'MBTI type selection menu')

def TYPES_setting(update):
    chat_id = update['callback_query']['from']['id']
    #x = db.select_parameter("users", "TYPES", f"chat_id = {chat_id}")
    x = 1415
    print(x)
    num_bits = 16
    # Create a list of the MBTI types, with checkmark emojis for the selected types
    mbti_types_list = [f"✅ {mbti_types[bit]}" if (x >> bit) & 1 else f"  {mbti_types[bit]}" for bit in range(num_bits)]

    # Divide the MBTI types into rows of 4, and create the keyboard
    keyboard = {
    "inline_keyboard": [
        [{"text": mbti_types_list[bit], "callback_data": mbti_types[bit] + "_p"} for bit in range(row * 4, (row + 1) * 4) if bit < num_bits] for row in range((num_bits - 1) // 4 + 1)
    ]}
    
    send_message("Choose your preffered MBTI types", chat_id, keyboard, 'MBTI preffered types selection menu')

def settings(update):
    chat_id = update['message']['chat']['id']
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
    
    send_message("Which one you would prefer to change?", chat_id, keyboard, "Settings")

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
    '/start': start,
    '👋 Start The Conversation' : join,
    '/join': join,
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
                    chat_id = update['message']['chat']['id']
                    if text in COMMANDS:
                        handler = COMMANDS[text]
                        if handler:
                            handler(update)
                    if(cache.hexists('pairs', chat_id)):
                        send_message(text, cache.hget('pairs', chat_id))
                if 'callback_query' in update and 'data' in update['callback_query']:
                    callback_handler(update)              
                PROCCESSED_OFFSET = max(PROCCESSED_OFFSET, update['update_id'] + 1)
        time.sleep(0.75)
    except Exception as e:
        print(f'Error occurred: {e}')
        time.sleep(5)