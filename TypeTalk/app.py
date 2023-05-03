import json
import time
import requests
from functools import lru_cache
import math
import redis

from send_data import *
from edit_data import *
from db import BotDB
db = BotDB("Telebots/TypeTalk/userdata.db")
cache = redis.Redis(host='localhost', port=6379, db=0)

# Set up API endpoint and bot token
API_LINK = "https://api.telegram.org/bot6114753472:AAFBAES3t622glVzoe5-4BpKF0hjbBeX6_c"
GET_UPDATES_URL = f"{API_LINK}/getUpdates"
SEND_MESSAGE_URL = f"{API_LINK}/sendMessage"
DELETE_MESSAGE_URL = f"{API_LINK}/deleteMessage"
INLINE_KEYBOARD = f"{API_LINK}/InlineKeyboardMarkup"

# Define constants for string literals for localisation 
START_MESSAGE = "👋 Start The Conversation"
SETTINGS_MESSAGE = "🛠️ Manage your Settings"
ABOUT_MESSAGE = "📖About the bot"

with open('Telebots/TypeTalk/typetalk_texts.json', 'r', encoding="UTF-8") as f:
    texts = json.load(f)

PROCCESSED_OFFSET = 0
mbti_types = {
    0: "INTJ", 1: "INFJ", 2: "ISTJ", 3: "ISTP",
    4: "INTP", 5: "INFP", 6: "ISFJ", 7: "ISFP",
    8: "ENTJ", 9: "ENFJ", 10: "ESTJ", 11: "ESTP",
    12: "ENTP", 13: "ENFP", 14: "ESFJ", 15: "ESFP"
    }
mbti_indexes = {
    "INTJ": 0, "INFJ": 1, "ISTJ": 2, "ISTP": 3,
    "INTP": 4, "INFP": 5, "ISFJ": 6, "ISFP": 7,
    "ENTJ": 8, "ENFJ": 9, "ESTJ": 10, "ESTP": 11,
    "ENTP": 12, "ENFP": 13, "ESFJ": 14, "ESFP": 15
    }

def haversine_distance(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude coordinates from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])

    d_lat = lat2 - lat1
    d_lon = lon2 - lon1

    # Calculate the Haversine formula
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = 6371 * c # Radius of the Earth in kilometers

    return distance

@lru_cache(maxsize=None)
def get_mbti_types_keyboard(x):
    num_bits = 16
    # Create a list of the MBTI types, with checkmark emojis for the selected types
    mbti_types_list = [f"✅ {mbti_types[bit]}" if (x >> bit) & 1 else f" {mbti_types[bit]}" for bit in range(num_bits)]

    # Divide the MBTI types into rows of 4, and create the keyboard
    keyboard = {
    "inline_keyboard": [
        [{"text": mbti_types_list[bit], "callback_data": mbti_types[bit] + "_p"} for bit in range(row * 4, (row + 1) * 4) if bit < num_bits] for row in range((num_bits - 1) // 4 + 1)
    ]}
    keyboard["inline_keyboard"].append([{"text" : "clear all", "callback_data" : "clall"}])
    return keyboard

def main_keyboard(chat_id):
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    keyboard = {
        "keyboard": 
            [[{"text": texts["main keyboard"]["joining"][lang]},
            {"text": texts["main keyboard"]["settings"][lang]}],
            [{"text": texts["main keyboard"]["about page"][lang]}]],

        "resize_keyboard": True,
        "one_time_keyboard" : True
    }
    return keyboard

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
        
    return response.content

def system_edit_types_message(receiver, message_id, res = None):
    if res is None:
        res = db.select_parameter("TYPES", f"chat_id = {receiver}")['TYPES']
    keyboard = get_mbti_types_keyboard(res)
    
    data = {
        "chat_id" : receiver,
        "message_id" : message_id,
        "text" : "Choose your preffered MBTI types",
        "reply_markup" : json.dumps(keyboard)
    }
    response = requests.post(EDIT_MESSAGE_URL, json=data)
    if response.ok:
            print(f"types choosing menu for {receiver} updated successfully")
    else:
            print(f"failed to update types choosing menu for {receiver}")

def system_delete_message(receiver, message_id):
    data = {
        "chat_id" : receiver,
        "message_id" : message_id
    }
    response = requests.post(DELETE_MESSAGE_URL, json=data)
    if response.ok:
            print(f"{receiver} message deleted successfully")
    else:
            print(f"failed to delete message for {receiver}")

def make_pair(chat_id1, chat_id2):
    cache.hset('pairs', chat_id1, chat_id2)
    cache.hset('pairs', chat_id2, chat_id1)

def del_pair(chat_id1):
    chat_id2 = cache.hget('pairs', chat_id1).decode()
    cache.delete(str(chat_id1))
    cache.delete(str(chat_id2))
    cache.hdel('pairs', chat_id1)
    cache.hdel('pairs', chat_id2)

def shareprofile(update):
    chat_id = update['message']['from']['id']
    username = update['message']['from']['username']
    receiver = cache.hget('pairs', chat_id).decode()
    text = "Here is the @" + username + '.'
    system_send_message(receiver, text, None,'Shareprofile message')

def matching(chat_id1, chat_id2):
    start = time.time()
    params1 = db.select_parameter("*", f"chat_id = {chat_id1}")
    params2 = db.select_parameter("*", f"chat_id = {chat_id2}")
    first_type = int(params1["TYPE"])
    first_types = int(params1["TYPES"])
    second_type = int(params2["TYPE"])
    second_types = int(params2["TYPES"])
    is_type1 = second_types & (1 << first_type)
    is_type1 = is_type1 >> first_type

    is_type2 = first_types & (1 << second_type)
    is_type2 = is_type2 >> second_type

    if bool(is_type1) is not True or bool(is_type2) is not True:
        return False
    first_age = int(params1["age"])
    first_ages = params1["age_interval"]
    second_age = int(params2["age"])
    second_ages = params2["age_interval"]
    first_ages = first_ages.split('-')
    second_ages = second_ages.split('-')

    if not(int(second_ages[0]) < first_age < int(second_ages[1]) and int(first_ages[0]) < second_age < int(first_ages[1])):
        return False
    
    first_lat = params1["region_lat"]
    first_lon = params1["region_lon"]
    second_lat = params2["region_lat"]
    second_lon = params2["region_lon"]

    dist = haversine_distance(first_lat, first_lon, second_lat, second_lon)

    if dist > 17.4:
        return False
    
    #checking gender
    # ...
    
    cache.srem("waiting_pool", chat_id1)
    cache.srem("waiting_pool", chat_id2)

    system_send_message(chat_id1, "your partner has been found", None, "partner message")
    system_send_message(chat_id2, "your partner has been found", None, "partner message")

    make_pair(chat_id1, chat_id2)

    end = time.time()
    print(end - start)
    return True

def join(update):
    chat_id = update['message']['from']['id']

    content = system_send_message(chat_id, "waiting..").decode()
    #print(content)

    if not cache.sismember("waiting_pool", chat_id):
        cache.sadd("waiting_pool", chat_id)
        
    waiting_users = cache.smembers("waiting_pool")

    for user in waiting_users:
        chat_id2 = int(user)
        if chat_id2 is not chat_id:
            print(chat_id)
            print(chat_id2)
            if matching(chat_id, chat_id2):
                pass
    
# Define a function to handle the /start command
def start(update):
    chat_id = update['message']['from']['id']
    name = update['message']['from']['first_name']
    print(db.is_chat_id_exists(chat_id))
    if db.is_chat_id_exists(chat_id) is False:
        db.insert_user(chat_id)
        text = "Hey there, " + name + "! Welcome to TypeTalk, the anonymous chatbot based on MBTI personality types." \
            "To get started, we recommend setting your search parameters in /settings.For more infromation type /about"
        system_send_message(chat_id, text, main_keyboard(), "Start menu")
    else:
        join(update)

# Define a function to handle the /about command
def about(update):
    chat_id = update['message']['from']['id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    data = {
        "chat_id" : chat_id,
        "photo" : "https://i.pinimg.com/474x/a1/2b/8e/a12b8ebbfa769903ac48ba27c6519e9d.jpg",
        "caption" : texts["about page"][lang],
        "reply_markup" : json.dumps(main_keyboard(chat_id))
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
        lang1 = db.select_parameter("language", f"chat_id = {chat_id1}")["language"]
        lang2 = db.select_parameter("language", f"chat_id = {chat_id2}")["language"]
        system_send_message(chat_id1, texts["ended conversation"][lang1])
        system_send_message(chat_id2, texts["ended conversation"][lang2])
        del_pair(chat_id1)

def lang_setting(update):
    chat_id = update['callback_query']['from']['id']
    keyboard = {
    "inline_keyboard": [
        [{"text": "🇺🇸 English", "callback_data": "en"},
        {"text": "🇷🇺 Русский", "callback_data": "ru"}],
        [{"text": "🇫🇷 français", "callback_data": "fr"},
        {"text": "🇪🇸 Español", "callback_data": "es"}]
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
    x = db.select_parameter("TYPES", f"chat_id = {chat_id}")['TYPES']
    keyboard = get_mbti_types_keyboard(x)
    
    system_send_message(chat_id, "Choose your preffered MBTI types", keyboard, 'MBTI preffered types selection menu')

def change_type(update):
    try:
        chat_id = update['callback_query']['from']['id']
        mbti_type = update['callback_query']['data'][:-2]
    except KeyError:
        print("Error: Invalid update format")
        return
    try:
        index = mbti_indexes[mbti_type]
        condition = f'chat_id = {chat_id}'
        db.upsert_user_data({'TYPE': index}, condition)
        system_delete_message(chat_id, update['callback_query']['message']['message_id'])
        system_send_message(chat_id, "Your MBTI type set successfully")
    except ValueError:
        print("Error: Invalid MBTI type")
        return

def change_p_types(update):
    chat_id = update['callback_query']['from']['id']
    mbti_type = update['callback_query']['data'][:-2]
    condition = f'chat_id = {chat_id}'
    mask = 1 << mbti_indexes[mbti_type]
    current_types = db.select_parameter('TYPES', condition)['TYPES']
    new_types = (current_types & ~mask) | (mask & ~current_types)
    db.upsert_user_data({'TYPES': new_types}, condition)
    system_edit_types_message(chat_id, update['callback_query']['message']['message_id'], new_types)
    
def settings(update):
    chat_id = update['message']['from']['id']
    keyboard = {
    "inline_keyboard": [
        [{"text": "Language", "callback_data": "language"},],
        [{"text": "Your MBTI Type", "callback_data": "TYPE"},
        {"text": "Prefered MBTI Types", "callback_data": "TYPES"},],
        [{"text": "Your Age", "callback_data": "my_age"},
        {"text": "Prefered Age Interval", "callback_data": "prefered_ages"},],
        [{"text": "Gender", "callback_data": "genders"},
        {"text": "Region", "callback_data": "region"}]
        ]}
    
    system_send_message(chat_id, "Which one you would prefer to change?", keyboard, "Settings")
    
# Can be 'age_collect', 'age_interval', 'region_collect'
def state_handler(update, state):
    chat_id = update['message']['from']['id']
    condition = f'chat_id = {chat_id}'
    if state == 'age_collect':
        if "message" not in update or "text" not in update["message"]:
            system_send_message(chat_id, "invalid data", None, "age set error")
            return
        text = update['message']['text']
        if text.isdigit() and int(text) < 100:
            if int(text) < 12:
                system_send_message(chat_id, 'your age is not enough(', None, 'error setage message')
            else:
                db.upsert_user_data({'age' : text}, condition)
                system_send_message(chat_id, 'age set succesfully', None, 'setage')
        else:
            system_send_message(chat_id, 'this isn\'t look like age', None, 'error setage message')
    elif state == 'age_interval':
        if "message" not in update or "text" not in update["message"]:
            system_send_message(chat_id, "invalid data", None, "age set error")
            return
        text = update['message']['text']
        ages = text.split("-")
        
        if int(ages[0]) > int(ages[1]) or len(ages) > 2:
            system_send_message(chat_id, "invalid interval", None, "interval comp error")
            return
        if ages[0].isdigit() and ages[1].isdigit().isdigit():
            system_send_message(chat_id, "enter with numbers", None, "interval comp error")
            return

        if int(ages[0]) < 13:
            system_send_message(chat_id, "Do I need to call the POLICE??!?!?!??!", None, "Pedophil error")
            return
        db.upsert_user_data({'age_interval' : text}, condition)
        system_send_message(chat_id, 'age set succesfully', None, 'setage interval')
    elif state == 'region_collect':
        print(update)
        if "message" not in update or "location" not in update["message"]:
            system_send_message(chat_id, "something gone wrong, try again!", None, "location data error")
            return
        latitude = update['message']['location']['latitude']
        longitude = update['message']['location']['longitude']
        db.upsert_user_data({'region_lat' : latitude}, condition)
        db.upsert_user_data({'region_lon' : longitude}, condition)
        system_send_message(chat_id, 'location set succesfully', None, 'coords')

        
    cache.hdel('state', chat_id)

def callback_handler(update):
    callback_data = update['callback_query']['data']
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
    if callback_data == "en" or callback_data == "fr" or callback_data == "ru" or callback_data == "es":
        chat_id = update['callback_query']['from']['id']
        db.upsert_user_data({"language" : callback_data}, f"chat_id = {chat_id}")
        system_send_message(chat_id, texts["set language"][callback_data], None, "language parameter")
    if callback_data.endswith('_m'):
        change_type(update)
        return
    if callback_data.endswith('_p'):
        change_p_types(update)
        return
    if callback_data == "clall":
        chat_id = update["callback_query"]["from"]["id"]
        db.upsert_user_data({"TYPES" : 0}, f"chat_id = {chat_id}")
        system_edit_types_message(chat_id, update['callback_query']['message']['message_id'], 0)
        return

COMMANDS = {
    '👋 Start The Conversation' : join,
    '👋 Commencer la conversation' : join,
    '👋 Начать разговор' : join,
    '👋 Comenzar la conversación' : join,
    '🛠️ Manage your Settings' : settings,
    '🛠️ Gérer vos paramètres' : settings,
    '🛠️ Управление настройками' : settings,
    '🛠️ Administrar tus ajustes' : settings,
    '📖 About the bot' : about,
    '📖 À propos du bot' : about,
    '📖 О боте' : about,
    '📖 Sobre el bot' : about,
    '/start': start,
    '/join': join,
    '/stop': stop,
    '/settings': settings,
    '/shareprofile': shareprofile,
    '/about': about
}

def update_handler(update):
    if 'message' in update:
        chat_id = update['message']['from']['id']
        if cache.hexists('state', chat_id):
                state_handler(update, cache.hget('state', chat_id).decode())
        if 'text' in update['message']:
            text = update['message']['text']
            if text in COMMANDS:
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
    elif 'edited_message' in update:
        if 'text' in update['edited_message']:
            edit_message(update)
        else:
            edit_media(update)
            
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