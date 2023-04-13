import json
import time
import requests
import redis

from send_data import *
from db import BotDB
db = BotDB("./TypeTalk/userdata.db")
cache = redis.Redis(host='localhost', port=6379, db=0)

# Set up API endpoint and bot token
API_LINK = "https://api.telegram.org/bot6114753472:AAFBAES3t622glVzoe5-4BpKF0hjbBeX6_c"
GET_UPDATES_URL = f"{API_LINK}/getUpdates"
SEND_MESSAGE_URL = f"{API_LINK}/sendMessage"
INLINE_KEYBOARD = f"{API_LINK}/InlineKeyboardMarkup"

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

def system_send_message(receiver, text,reply_markup = None, handler = None):
    data = {
            "chat_id": receiver,
            "text": text
        }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    if handler:
        handler_success = f"{handler} opened Successfully."
        handler_fail = f"Failed to open {handler}."
    else:
        handler_success = "Message sent successfully."
        handler_fail = "Failed to send message."

    response = requests.post(SEND_MESSAGE_URL, json=data)
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

def shareprofile(update):
    chat_id = update['message']['from']['id']
    username = update['message']['from']['username']
    receiver = cache.hget('pairs', chat_id)
    text = "Here is the @" + username + '.'
    system_send_message(receiver, text, None,'Shareprofile message')

def join(update):
    chat_id = update['message']['from']['id']
    print(db.select_parameter("*", f"chat_id = {chat_id}"))
    
# Define a function to handle the /start command
def start(update):
    chat_id = update['message']['from']['id']
    name = update['message']['from']['first_name']
    print(db.is_chat_id_exists(chat_id))
    if db.is_chat_id_exists(chat_id) is False:
        db.insert_user(chat_id)
        keyboard = {
            "keyboard": 
                [[{"text": START_MESSAGE},
                {"text": SETTINGS_MESSAGE}],
                [{"text": ABOUT_MESSAGE}]],

            "resize_keyboard": True
        }
        text = "Hey there, " + name + "! Welcome to TypeTalk, the anonymous chatbot based on MBTI personality types." \
            "To get started, we recommend setting your search parameters in /settings.For more infromation type /about"
        system_send_message(chat_id, text, keyboard, "Start menu")
    else:
        join(update)

# Define a function to handle the /about command
def about(update):
    chat_id = update['message']['from']['id']
    keyboard = {
        "keyboard": 
            [[{"text": START_MESSAGE},
             {"text": SETTINGS_MESSAGE}],
            [{"text": ABOUT_MESSAGE}]],

        "resize_keyboard": True
    }
    data = {
        "chat_id" : chat_id,
        "photo" : "https://i.pinimg.com/474x/a1/2b/8e/a12b8ebbfa769903ac48ba27c6519e9d.jpg",
        "caption" : ABOUT_TEXT,
        "reply_markup" : json.dumps(keyboard)
    }
    response = requests.post(SEND_PHOTO_URL, json=data)
    if response.ok:
        print(f"About menu opened for {chat_id} successfully.")
    else:
        print(f"Failed to open About menu for {chat_id}.")
    
def stop(update):
    chat_id1 = update['message']['from']['id']
    if cache.hexists('pairs', chat_id1): 
        chat_id2 = cache.hget('pairs', chat_id1).decode()
        system_send_message(chat_id1, '👋 Conversation ended. Type /join to begin a new conversation.')
        system_send_message(chat_id2, '👋 Conversation ended. Type /join to begin a new conversation.')

        del_pair(chat_id1)

def lang_setting(update):
    chat_id = update['callback_query']['from']['id']
    keyboard = {
    "inline_keyboard": [
        [{"text": "🇺🇸 English", "callback_data": "English"},
        {"text": "🇷🇺 Russian", "callback_data": "Russian"}]
        ]}
    system_send_message(chat_id, "Preferred language?", keyboard, 'Language selection menu')

def TYPE_setting(update):
    chat_id = update['callback_query']['from']['id']
    # Create the keyboard
    keyboard = {
    "inline_keyboard": [
        [{"text": mbti_types[bit], "callback_data": mbti_types[bit] + "_m"} for bit in range(row * 4, (row + 1) * 4) if bit < 16] for row in range((16 - 1) // 4 + 1)
    ]}

    system_send_message(chat_id, 'Choose your MBTI type', keyboard, 'MBTI type selection menu')

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
    
    system_send_message(chat_id, "Choose your preffered MBTI types", keyboard, 'MBTI preffered types selection menu')

def settings(update):
    chat_id = update['message']['from']['id']
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
    
    system_send_message(chat_id, "Which one you would prefer to change?", keyboard, "Settings")
    
# Can be 'age_collect', 'age_interval', 'region_collect'
def state_handler(update, state):
    chat_id = update['message']['from']['id']
    text = update['message']['text']
    condition = 'chat_id = ' + str(chat_id)
    if state == 'age_collect':
        if text.isdigit() and int(text) < 100:
            if int(text) < 12:
                system_send_message(chat_id, 'your age is not enough(', None, 'error setage message', None)
            else:
                db.upsert_user_data({'age' : text}, condition)
                system_send_message(chat_id, 'age set succesfully', None, 'setage', None)
        else:
            system_send_message(chat_id, 'this isn\'t look like age', None, 'error setage message')
    elif state == 'age_interval':
        db.upsert_user_data({'age_interval' : text}, condition)
        system_send_message(chat_id, 'age set succesfully', None, 'setage interval', None)
    elif state == 'region_collect':
        latitude = update['message']['location']['latitude']
        longitude = update['message']['location']['longitude']
        db.upsert_user_data({'region_lat' : latitude}, condition)
        db.upsert_user_data({'region_lon' : longitude}, condition)
        system_send_message(chat_id, 'location set succesfully', None, 'coords')

        
    cache.hdel('state', chat_id)

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
        chat_id = update['callback_query']['from']['id']
        system_send_message(chat_id, "send your location with telegram:", None, "set location")
        cache.hset('state', chat_id, 'region_collect')
        return
    if callback_data == "my_age":
        chat_id = update['callback_query']['from']['id']
        system_send_message(chat_id, "input your age:", None, "set age menu")
        cache.hset('state', chat_id, 'age_collect')
        return
    if callback_data == "prefered_ages":
        chat_id = update['callback_query']['from']['id']
        system_send_message(chat_id, "Please enter your preferred age range in the following format: 12-21  ", None, "set age interval menu")
        cache.hset('state', chat_id, 'age_interval')
        return

COMMANDS = {
    '/start': start,
    '👋 Start The Conversation' : join,
    '/join': join,
    '/stop': stop,
    '/settings': settings,
    '🛠️ Manage your Settings' : settings,
    '/shareprofile': shareprofile,
    '/about': about,
    '📖About the bot' : about
}

def update_handler(update):
    if 'message' in update:
        chat_id = update['message']['from']['id']
        if 'text' in update['message']:
            text = update['message']['text']
            if cache.hexists('state', chat_id):
                state_handler(update, cache.hget('state', chat_id).decode())
            elif text in COMMANDS:
                COMMANDS[text](update)
            elif(cache.hexists('pairs', chat_id)):
                send_message(cache.hget('pairs', chat_id).decode(), update)
        elif 'photo' in update['message'] and cache.hexists('pairs', chat_id):
            print("sending photo")
            send_photo(cache.hget('pairs', chat_id).decode(), update)
        elif 'voice' in update['message'] and cache.hexists('pairs', chat_id):
            print("sending voice")
            send_audio(cache.hget('pairs', chat_id).decode(), update)
        elif 'video' in update['message'] and cache.hexists('pairs', chat_id):
            print("sending video")
            send_video(cache.hget('pairs', chat_id).decode(), update)
        elif 'video_note' in update['message'] and cache.hexists('pairs', chat_id):
            print("sending video_note")
            send_video_note(cache.hget('pairs', chat_id).decode(), update)
        elif 'animation' in update['message'] and cache.hexists('pairs', chat_id):
            print("sending animation")
            send_animation(cache.hget('pairs', chat_id).decode(), update)
        elif 'document' in update['message'] and cache.hexists('pairs', chat_id):
            print("sending document")
            send_document(cache.hget('pairs', chat_id).decode(), update)
        elif 'location' in update['message'] and cache.hexists('pairs', chat_id):
            print("sending location")
            send_location(cache.hget('pairs', chat_id).decode(), update)
        elif 'sticker' in update['message'] and cache.hexists('pairs', chat_id):
            print("sending sticker")
            send_sticker(cache.hget('pairs', chat_id).decode(), update)
        elif 'poll' in update['message'] and cache.hexists('pairs', chat_id):
            print("sending poll")
            send_poll(cache.hget('pairs', chat_id).decode(), update)
        
            
    elif 'callback_query' in update and 'data' in update['callback_query']:
        callback_handler(update)              

while True:
    try:
        response = requests.get(GET_UPDATES_URL, params={'offset': PROCCESSED_OFFSET})
        if response.ok:
            updates = response.json()['result']
            for update in updates:
                update_handler(update)
                PROCCESSED_OFFSET = max(PROCCESSED_OFFSET, update['update_id'] + 1)
        time.sleep(0.75)
    except Exception as e:
        print(f'Error occurred: {e}')
        time.sleep(5)