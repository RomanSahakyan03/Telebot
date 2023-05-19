import json
import re
import threading
import time
import redis
import requests
from db import BotDB
from edit_data import *
from send_data import *
from utils import *

db = BotDB("TypeTalk/userdata.db")
cache = redis.Redis(host='localhost', port=6379, db=0)


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

def shareprofile(update):
    chat_id = update['message']['from']['id']
    username = update['message']['from']['username']
    receiver = cache.hget('pairs', chat_id).decode()
    text = "Here is the @" + username + '.'
    system_send_message(receiver, text, None,'Shareprofile message')

def matching():
    while True:
        while cache.scard("waiting_pool") < 2:
            print("waiting..")
            time.sleep(2)
        print("the elems are more than two")
        chat_id1, chat_id2 = cache.srandmember("waiting_pool", 2)
        chat_id1 = int(chat_id1)
        chat_id2 = int(chat_id2)
        params1 = db.select_parameter("*", f"chat_id = {chat_id1}")
        params2 = db.select_parameter("*", f"chat_id = {chat_id2}")

        first_type = params1["TYPE"]
        first_types = params1["TYPES"]
        second_type = params2["TYPE"]
        second_types = params2["TYPES"]

        is_type1 = bool(int(second_types) & (1 << int(first_type)))
        is_type2 = bool(int(first_types) & (1 << int(second_type)))

        if not is_type1 or not is_type2:
            continue
        print("types matching passed")

        first_age = params1["age"]
        first_ages = params1["age_interval"]
        second_age = params2["age"]
        second_ages = params2["age_interval"]
        second_ages = second_ages.split('-')

        if not (int(second_ages[0]) < int(first_age) < int(second_ages[1])):
            continue

        first_ages = first_ages.split('-')

        if not (int(first_ages[0]) < int(second_age) < int(first_ages[1])):
            continue

        print("age matching passed")
        first_lat = params1["region_lat"]
        first_lon = params1["region_lon"]
        second_lat = params2["region_lat"]
        second_lon = params2["region_lon"]

        if haversine_distance(first_lat, first_lon, second_lat, second_lon) > 67.4:
            continue

        print("region matching passed")

        #checking gender
        # ...

        cache.srem("waiting_pool", chat_id1)
        cache.srem("waiting_pool", chat_id2)

        system_send_message(chat_id1, "your partner has been found", None, "partner message")
        system_send_message(chat_id2, "your partner has been found", None, "partner message")
        make_pair(chat_id1, chat_id2)


        print("end matching ")

def join(update):
    chat_id = update['message']['from']['id']

    keyboard = {
        "keyboard":
        {"text": "Cancel"},
        "resize_keyboard": True,
        "one_time_keyboard" : True
    }
    system_send_message(chat_id, "waiting..", keyboard)

    if not cache.sismember("waiting_pool", chat_id):
        cache.sadd("waiting_pool", chat_id)
    
# Define a function to handle the /start command
def start(update):
    chat_id = update['message']['from']['id']
    name = update['message']['from']['first_name']
    print(db.is_chat_id_exists(chat_id))
    if db.is_chat_id_exists(chat_id) is False:
        db.insert_user(chat_id)
        text = "Hey there, " + name + "! Welcome to TypeTalk, the anonymous chatbot based on MBTI personality types." \
            "To get started, we recommend setting your search parameters in /settings.For more infromation type /about"
        system_send_message(chat_id, text, main_keyboard(chat_id), "Start menu")
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
        system_send_message(chat_id1, texts["ended conversation"][lang1], main_keyboard(chat_id1))
        system_send_message(chat_id2, texts["ended conversation"][lang2], main_keyboard(chat_id2))
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

def handle_region(update):
    chat_id = update['callback_query']['from']['id']
    system_send_message(chat_id, "Send your location with Telegram:", None, "set location")
    cache.hset('state', chat_id, 'region_collect')

def handle_my_age(update):
    chat_id = update['callback_query']['from']['id']
    system_send_message(chat_id, "Input your age:", None, "set age menu")
    cache.hset('state', chat_id, 'age_collect')

def handle_preferred_ages(update):
    chat_id = update['callback_query']['from']['id']
    system_send_message(chat_id, "Please enter your preferred age range in the following format: 12-21", None, "set age interval menu")
    cache.hset('state', chat_id, 'age_interval')

def handle_unsupported_callback(update):
    # Handle unsupported callback_data values
    print(f"Unsupported callback_data: {update['callback_query']['data']}")

def change_p_types(update):
    chat_id = update['callback_query']['from']['id']
    mbti_type = update['callback_query']['data'][:-2]
    condition = f'chat_id = {chat_id}'
    mask = 1 << mbti_indexes[mbti_type]
    current_types = db.select_parameter('TYPES', condition)['TYPES']
    new_types = (current_types & ~mask) | (mask & ~current_types)
    db.upsert_user_data({'TYPES': new_types}, condition)
    system_edit_types_message(chat_id, update['callback_query']['message']['message_id'], new_types)

def handle_language(update):
    chat_id = update['callback_query']['from']['id']
    callback_data = update['callback_query']['data']
    db.upsert_user_data({"language": callback_data}, f"chat_id = {chat_id}")
    system_send_message(chat_id, texts["set language"][callback_data], None, "language parameter")

def handle_clall(update):
    chat_id = update["callback_query"]["from"]["id"]
    db.upsert_user_data({"TYPES": 0}, f"chat_id = {chat_id}")
    system_edit_types_message(chat_id, update['callback_query']['message']['message_id'], 0)

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
        pattern = r"^\d+-\d+$"
        match = re.match(pattern, text)
        if match:
            age1 = int(match.group(1))
            age2 = int(match.group(2))
            if age1 > age2:
                age1, age2 = age2, age1
            if age1 <= 13:
                system_send_message(chat_id, "Do I need to call the POLICE??!?!?!??!", None, "Pedophil error")
                return
            db.upsert_user_data({'age_interval' : text}, condition)
            system_send_message(chat_id, 'age set succesfully', None, 'setage interval')
        else:
            system_send_message(chat_id, "invalid data", None, "age set error")
            return
    elif state == 'region_collect':
        if "message" not in update or "location" not in update["message"]:
            system_send_message(chat_id, "something gone wrong, try again!", None, "location data error")
            return
        latitude = update['message']['location']['latitude']
        longitude = update['message']['location']['longitude']
        db.upsert_user_data({'region_lat' : latitude}, condition)
        db.upsert_user_data({'region_lon' : longitude}, condition)
        system_send_message(chat_id, 'location set succesfully', None, 'coords')


    cache.hdel('state', chat_id)

message_handlers = {
    'photo': send_photo,
    'voice': send_audio,
    'video': send_video,
    'video_note': send_video_note,
    'animation': send_animation,
    'document': send_document,
    'location': send_location,
    'sticker': send_sticker,
    'poll': send_poll
}

callback_actions = {
    "language": lang_setting,
    "TYPE": TYPE_setting,
    "TYPES": TYPES_setting,
    "region": handle_region,
    "my_age": handle_my_age,
    "prefered_ages": handle_preferred_ages,
    "en": handle_language,
    "fr": handle_language,
    "ru": handle_language,
    "es": handle_language,
    "clall": handle_clall
    }

def callback_handler(update):
    callback_data = update['callback_query']['data']
    if callback_data in callback_actions:
        callback_actions[callback_data](update)
    elif callback_data.endswith('_m'):
        change_type(update)
    elif callback_data.endswith('_p'):
        change_p_types(update)
    else:
        # Handle unsupported callback_data values
        handle_unsupported_callback(update)

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
            elif cache.hexists('pairs', chat_id):
                pair = cache.hget('pairs', chat_id).decode()
                send_message(pair, update)
        for keyword, handler in message_handlers.items():
            if keyword in update['message']:
                print(f"sending {keyword}")
                handler(pair, update)     
    elif 'edited_message' in update:
        if 'text' in update['edited_message']:
            edit_message(update)
        else:
            edit_media(update)
    elif 'callback_query' in update and 'data' in update['callback_query']:
        callback_handler(update)

def main():
    proccessed_offset = 0
    while True:
        try:
            response = requests.get(GET_UPDATES_URL, params={'offset': proccessed_offset})
            if response.ok:
                updates = response.json()['result']
                for update in updates:
                    print(update)
                    update_handler(update)
                    proccessed_offset = max(proccessed_offset, update['update_id'] + 1)
            time.sleep(0.75)
        except Exception as e:
            print(f'Error occurred: {e}')
            time.sleep(5)

if __name__ ==  "__main__":
    #matching_thread = threading.Thread(target=matching)
    # matching_thread.start()
    main()
    #matching_thread.join()