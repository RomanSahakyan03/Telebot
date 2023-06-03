import json
import re
import threading
import time
import requests
from db import BotDB
from edit_data import *
from send_data import *
from utils import *
from config import create_redis_client

db = BotDB("TypeTalk/userdata.db")
cache = create_redis_client()

def system_send_message(receiver, text,reply_markup = None, handler = None):
    data = {
            "chat_id": receiver,
            "text": text
        }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)

    if handler is None:
        handler = f"{receiver} message sent"

    content = send_request(data, "sendMessage", handler)

    return content

def system_edit_message(receiver, message_id, text = None,reply_markup = None, handler = None):
    data = {
        "chat_id": receiver,
        "message_id" : message_id,
    }
    if text:
        data["text"] = text
        
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)

    if handler is None:
        handler = f"{receiver} message edited"

    content = send_request(data, "editMessageText", handler)

    return content

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

    content = send_request(data, "editMessageText")

    return content

def system_delete_message(receiver, message_id):
    data = {
        "chat_id" : receiver,
        "message_id" : message_id
    }

    handler = f"{receiver} message deleted"
    content = send_request(data, "deleteMessage", handler)

    return content

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

# cancel only "state" or "waiting"
def cancel_keyboard(chat_id, option):
    cancel = "cancel_" + option
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    keyboard = {
    "inline_keyboard": [
        [{"text": texts["cancel_keyboard"][lang], "callback_data": cancel}]
    ]}
    return keyboard

def shareprofile(update):
    chat_id = update['message']['from']['id']
    if cache.hexists('pairs', chat_id):
        if 'username' in update['message']['from']:
            username = update['message']['from']['username']
            receiver = cache.hget('pairs', chat_id).decode()
            text = "Here is the @" + username + '.'
            system_send_message(receiver, text, None,'Shareprofile message')
        else:
            system_send_message(chat_id, "You have no username to share....", None, "NoShareprofile message")

def matching_system():
    while True:
        while cache.scard("waiting_pool") < 2:
            time.sleep(2) # adjustable
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


        # if no one selected <=> all types available
        if int(first_types) == 0:
            first_types = 65535 
        if int(second_types) == 0:
            second_types = 65535


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

        if not (int(second_ages[0]) <= int(first_age) <= int(second_ages[1])):
            continue

        first_ages = first_ages.split('-')

        if not (int(first_ages[0]) <= int(second_age) <= int(first_ages[1])):
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


        lang1 = params1["language"]
        lang2 = params2["language"]

        text1 = f"{texts['matching']['partner found'][lang1]}\n"
        text1 += f"{texts['matching']['age'][lang1]}{second_age}\n"
        text1 += f"{texts['matching']['region'][lang1]}{from_coords_to_name(second_lat, second_lon)}\n"
        text1 += f"{texts['matching']['type'][lang1]}{second_type}"
        text1 = f"{texts['matching']['partner found'][lang1]}\n"

        text2 = f"{texts['matching']['partner found'][lang2]}\n"
        text2 += f"{texts['matching']['age'][lang2]}{first_age}\n"
        text2 += f"{texts['matching']['region'][lang2]}{from_coords_to_name(first_lat, first_lon)}\n"
        text2 += f"{texts['matching']['type'][lang2]}{first_type}"

        system_delete_message(chat_id1, int(cache.hget("waiting_message", chat_id1)))
        system_delete_message(chat_id2, int(cache.hget("waiting_message", chat_id2)))
        cache.srem("waiting_pool", chat_id1)
        cache.srem("waiting_pool", chat_id2)
        cache.hdel("waiting_message", chat_id1)
        cache.hdel("waiting_message", chat_id2)
        system_send_message(chat_id1, text1, {"reply_markup" : {"remove_keyboard" : True}}, "partner message")
        system_send_message(chat_id2, text2, {"reply_markup" : {"remove_keyboard" : True}}, "partner message")

        make_pair(chat_id1, chat_id2)


        print("end matching ")

def join(update):
    start = time.time()
    chat_id = update['message']['from']['id']
    if cache.sismember("waiting_pool", chat_id):
        return
    params = db.select_parameter("*", f"chat_id = {chat_id}")
    lang = params["language"]
    if db.check_all_columns_filled(chat_id):
        lat, lon = params["region_lat"], params["region_lon"]
        name = from_coords_to_name(lat, lon)
        age = params["age"]
        preferred_ages = params["age_interval"]
        type = params["TYPE"]
        types = int(params["TYPES"])

        # if no one selected <=> all types available
        if int(types) == 0:
            types = 65535 

        num_bits = 16
        types_list = [f"{mbti_types[bit]}" for bit in range(num_bits) if (types >> bit) & 1]

        print(types_list)
        text = f"{texts['join']['first_part'][lang]}\n"
        text += f"{texts['join']['age'][lang]}{age}\n"
        text += f"{texts['join']['prefarred_ages'][lang]}{preferred_ages}\n"
        text += f"{texts['join']['region'][lang]}{name}\n"
        text += f"{texts['join']['type'][lang]}{mbti_types[type]}\n"
        text += f"{texts['join']['types'][lang]}{', '.join(types_list)}"
        keyboard = cancel_keyboard(chat_id, "waiting")

        # Send the message
        content = system_send_message(chat_id, text, keyboard, "waiting message")
        cache.sadd("waiting_pool", chat_id)
        cache.hset("waiting_message", chat_id, content["message_id"])
    else:
        print(chat_id)
        system_send_message(chat_id, texts["do_not_join"][lang], None, "not joining error message")
    print(time.time() - start)
    
# Define a function to handle the /start command
def start(update):
    chat_id = update['message']['from']['id']
    print(chat_id)
    if db.is_chat_id_exists(chat_id) is False:
        name = update['message']['from']['first_name']
        db.insert_user(chat_id)
        text = "Hey there, " + name + "! Welcome to TypeTalk, the anonymous chatbot based on MBTI personality types. " \
       "To get started, please choose your preferred language by selecting one of the options below:"
        data = {
            "chat_id" : chat_id,
            "photo" : "AgACAgIAAxkBAAIMG2R669446fymMURznmwSEwwLxzBIAAKWzDEb9zTZS1nd7Nbv63VJAQADAgADeAADLwQ",
            "caption" : text
        }
        send_request(data, "sendPhoto", f"Start menu opened for {chat_id}")
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

    send_request(data, "sendPhoto", f"About menu opened for {chat_id}")

def stop(update):
    chat_id1 = update['message']['from']['id']
    if cache.hexists('pairs', chat_id1):
        chat_id2 = cache.hget('pairs', chat_id1).decode()
        lang1 = db.select_parameter("language", f"chat_id = {chat_id1}")["language"]
        lang2 = db.select_parameter("language", f"chat_id = {chat_id2}")["language"]
        system_send_message(chat_id1, texts["ended conversation"][lang1], main_keyboard(chat_id1))
        system_send_message(chat_id2, texts["ended conversation"][lang2], main_keyboard(chat_id2))
        del_pair(chat_id1)

def next(update):
    stop(update)
    join(update)

def settings(update):
    chat_id = update['message']['from']['id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    keyboard = {
    "inline_keyboard": [
        [{"text": texts["settings"]["lang"][lang], "callback_data": "language"},
         {"text": texts["settings"]["region"][lang], "callback_data": "region"}],
        [{"text": texts["settings"]["type"][lang], "callback_data": "TYPE"},
        {"text": texts["settings"]["types"][lang], "callback_data": "TYPES"},],
        [{"text": texts["settings"]["age"][lang], "callback_data": "my_age"},
        {"text": texts["settings"]["ages"][lang], "callback_data": "prefered_ages"},],
        [{"text": texts["settings"]["sex"][lang], "callback_data": "sex"},
        {"text": texts["settings"]["sexes"][lang], "callback_data": "sexes"}]
        ]}
    system_send_message(chat_id, texts["settings"]["header"][lang], keyboard, "Settings")

# Can be 'age_collect', 'age_interval', 'region_collect'
def state_handler(update, state):
    chat_id = update['message']['from']['id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    condition = f'chat_id = {chat_id}'
    if state == 'age_collect':
        if "message" not in update or "text" not in update["message"]:
            system_send_message(chat_id, texts["invalid data"][lang], None, "age set error")
            return
        text = update['message']['text']
        pattern = r"^(\d+)$"
        match = re.match(pattern, text)
        if match and int(text) < 100:
            if int(text) < 12:
                system_send_message(chat_id, texts["not enough age"][lang], None, 'error setage message')
            else:
                cache.srem("age_collect", chat_id)
                db.upsert_user_data({'age' : text}, condition)
                system_send_message(chat_id, texts["age set"][lang], None, 'setage')
        else:
            system_send_message(chat_id, texts["invalid data"][lang], None, 'error setage message')
    elif state == 'age_interval':
        if "message" not in update or "text" not in update["message"]:
            system_send_message(chat_id, texts["invalid data"][lang], None, "age set error")
            return
        text = update['message']['text']
        pattern = r"^(\d+)-(\d+)$"
        match = re.match(pattern, text)
        if match:
            age1 = int(match.group(1))
            age2 = int(match.group(2))
            if age1 > age2:
                age1, age2 = age2, age1
            if age1 <= 13:
                system_send_message(chat_id, texts["low age alert"][lang], None, "Pedophil error")
                return
            db.upsert_user_data({'age_interval' : text}, condition)
            cache.srem("age_interval", chat_id)
            system_send_message(chat_id, texts["age set"][lang], None, 'setage interval')
        else:
            system_send_message(chat_id, texts["invalid data"][lang], None, "age set error")
            return
    elif state == 'region_collect':
        if "message" not in update or "location" not in update["message"]:
            system_send_message(chat_id, texts["invalid data"][lang], None, "location data error")
            return
        latitude = update['message']['location']['latitude']
        longitude = update['message']['location']['longitude']
        db.upsert_user_data({'region_lat' : latitude}, condition)
        db.upsert_user_data({'region_lon' : longitude}, condition)
        cache.srem("region_collect", chat_id)
        system_send_message(chat_id, texts["location set"][lang], None, 'coords')


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

# ------- handling states -------

def handle_region(update):
    chat_id = update['callback_query']['from']['id']
    system_send_message(chat_id, "Send your location with Telegram:", cancel_keyboard(chat_id, "state"), "set location")
    cache.sadd("region_collect", )
    cache.hset('state', chat_id, 'region_collect')

def handle_my_age(update):
    chat_id = update['callback_query']['from']['id']
    system_send_message(chat_id, "Input your age:", cancel_keyboard(chat_id, "state"), "set age menu")
    cache.hset('state', chat_id, 'age_collect')

def handle_preferred_ages(update):
    chat_id = update['callback_query']['from']['id']
    system_send_message(chat_id, "Please enter your preferred age range in the following format: 12-21", cancel_keyboard(chat_id, "state"), "set age interval menu")
    cache.hset('state', chat_id, 'age_interval')

# ----------------------------  

def handle_unsupported_callback(update):
    # Handle unsupported callback_data values
    print(f"Unsupported callback_data: {update['callback_query']['data']}")

# ------- handling settings -------  

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

def handle_language(update):
    chat_id = update['callback_query']['from']['id']
    callback_data = update['callback_query']['data']
    system_delete_message(chat_id, update['callback_query']['message']['message_id'])
    db.upsert_user_data({"language": callback_data}, f"chat_id = {chat_id}")
    system_send_message(chat_id, texts["set language"][callback_data], None, "language parameter")

def handle_clall(update):
    chat_id = update["callback_query"]["from"]["id"]
    db.upsert_user_data({"TYPES": 0}, f"chat_id = {chat_id}")
    system_edit_types_message(chat_id, update['callback_query']['message']['message_id'], 0)

def lang_setting(update):
    chat_id = update['callback_query']['from']['id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    system_send_message(chat_id, texts["lang settings"][lang], lang_keyboard, 'Language selection menu')

def TYPE_setting(update):
    chat_id = update['callback_query']['from']['id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    # Create the keyboard
    keyboard = {
    "inline_keyboard": [
        [{"text": mbti_types[bit], "callback_data": mbti_types[bit] + "_m"} for bit in range(row * 4, (row + 1) * 4) if bit < 16] for row in range((16 - 1) // 4 + 1)
    ]}

    system_send_message(chat_id, texts["type settings"][lang], keyboard, 'MBTI type selection menu')

def TYPES_setting(update):
    chat_id = update['callback_query']['from']['id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    x = db.select_parameter("TYPES", f"chat_id = {chat_id}")['TYPES']
    keyboard = get_mbti_types_keyboard(x)

    system_send_message(chat_id, texts["types settings"][lang], keyboard, 'MBTI preffered types selection menu')

def handle_cancel_state(update):
    chat_id = update['callback_query']['from']['id']
    message_id = update['callback_query']['message']['message_id']
    system_delete_message(chat_id, message_id)
    if cache.hexists('state', chat_id):
        lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
        cache.hdel('state', chat_id)
        system_send_message(chat_id, texts["cancel_state"][lang], main_keyboard(chat_id), "state cancled message")

def handle_cancel_waiting(update):
    chat_id = update['callback_query']['from']['id']
    message_id = update['callback_query']['message']['message_id']
    system_delete_message(chat_id, message_id)
    if cache.sismember('waiting_pool', chat_id):
        lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
        cache.srem('waiting_pool', chat_id)
        system_send_message(chat_id, texts["cancel_waiting"][lang], main_keyboard(chat_id), "waiting cancled message")
    

# ---------------------------- 

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
    "clall": handle_clall,
    "cancel_state" : handle_cancel_state,
    "cancel_waiting" : handle_cancel_waiting
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
    '/next' : next,
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
            if keyword in update['message'] and cache.hexists('pairs', chat_id):
                print(f"sending {keyword}")
                pair = cache.hget('pairs', chat_id).decode()
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
    get_updates_url = f"{API_LINK}/getUpdates"
    while True:
        try:
            response = requests.get(get_updates_url, params={'offset': proccessed_offset})
            if response.ok:
                updates = response.json()['result']
                for update in updates:
                    update_handler(update)
                    proccessed_offset = max(proccessed_offset, update['update_id'] + 1)
            time.sleep(0.75)
        except Exception as e:
            print(f'Error occurred: {e}')
            time.sleep(5)

if __name__ ==  "__main__":
    matching_thread = threading.Thread(target=matching_system)
    matching_thread.start()
    main()
    matching_thread.join()
    db.close()