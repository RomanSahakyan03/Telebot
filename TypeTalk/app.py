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
import os
import copy

# Get the absolute path of the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute texts path
db_path = os.path.join(current_dir, 'userdata.db')

db = BotDB(db_path)
cache = create_redis_client()

# Construct the absolute texts path
texts_path = os.path.join(current_dir, 'typetalk_texts.json')

with open(texts_path, 'r', encoding="UTF-8") as f:
    texts = json.load(f)

def system_send_message(receiver, text,reply_markup = None, handler = None):
    data = {
            "chat_id": receiver,
            "text": text
        }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)

    if handler is None:
        handler = f"{receiver} message sent"

    content = send_request(data, SEND_MESSAGE, handler)

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
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    if cache.hexists('pairs', chat_id):
        if 'username' in update['message']['from']:
            username = update['message']['from']['username']
            receiver = cache.hget('pairs', chat_id).decode()
            text = "Here is the @" + username + '.'
            system_send_message(receiver, text, None,'Shareprofile message')
        else:
            system_send_message(chat_id, texts["no username"][lang], None, "NoShareprofile message")

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
        first_ages = params1["prefarred_ages"]
        second_age = params2["age"]
        second_ages = params2["prefarred_ages"]
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

        sex1 = params1["sex"]
        sex2 = params1["sex"]
        sexes1 = params1["sexes"]
        sexes2 = params1["sexes"]

        if sexes1 != 2 and ((sex1 ^ 1) != sexes2):
            continue

        if sexes2 != 2 and ((sex2 ^ 1) != sexes1):
            continue

        lang1 = params1["language"]
        lang2 = params2["language"]

        text1 = f"{texts['matching']['partner found'][lang1]}\n"
        text1 += f"{texts['matching']['age'][lang1]}{second_age}\n"
        text1 += f"{texts['matching']['region'][lang1]}{from_coords_to_name(second_lat, second_lon, lang1)}\n"
        text1 += f"{texts['matching']['type'][lang1]}{mbti_types[second_type]}\n"
        text1 += f"{texts['matching']['sex'][lang1]}{texts[sexes[sex2]][lang1]}"

        text2 = f"{texts['matching']['partner found'][lang2]}\n"
        text2 += f"{texts['matching']['age'][lang2]}{first_age}\n"
        text2 += f"{texts['matching']['region'][lang2]}{from_coords_to_name(first_lat, first_lon, lang2)}\n"
        text2 += f"{texts['matching']['type'][lang2]}{mbti_types[first_type]}\n"
        text2 += f"{texts['matching']['sex'][lang2]}{texts[sexes[sex1]][lang2]}"

        system_delete_message(chat_id1, int(cache.hget("waiting_message", chat_id1)))
        system_delete_message(chat_id2, int(cache.hget("waiting_message", chat_id2)))
        cache.srem("waiting_pool", chat_id1, chat_id2)
        cache.hdel("waiting_message", chat_id1, chat_id2)
        system_send_message(chat_id1, text1, {"remove_keyboard" : True}, "partner message")
        system_send_message(chat_id2, text2, {"remove_keyboard" : True}, "partner message")

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
        name = from_coords_to_name(lat, lon, lang)
        preferred_ages = params["prefarred_ages"]
        types = params["TYPES"]
        sex_index = params["sexes"]

        # if no one selected <=> all types available
        if types == 0:
            types = 65535 

        num_bits = 16
        types_list = [f"{mbti_types[bit]}" for bit in range(num_bits) if (types >> bit) & 1]


        text = f"{texts['join'][lang]}\n"
        text += f"{texts['prefarred_ages'][lang]}{preferred_ages}\n"
        text += f"{texts['region'][lang]}{name}\n"
        text += f"{texts['TYPES'][lang]}{', '.join(types_list)}\n"
        text += f"{texts['sexes'][lang]}{texts[sexes[sex_index]][lang]}"
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
        text = f"Hey there, {name}! Welcome to TypeTalk, the anonymous chatbot based on MBTI personality types. " \
       "To get started, please choose your preferred language by selecting one of the options below:"
        data = {
            "chat_id" : chat_id,
            "photo" : "AgACAgIAAxkBAAIMG2R669446fymMURznmwSEwwLxzBIAAKWzDEb9zTZS1nd7Nbv63VJAQADAgADeAADLwQ",
            "caption" : text,
            "reply_markup" : lang_keyboard_with_settings
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
        "reply_markup" : main_keyboard(lang)
    }

    send_request(data, "sendPhoto", f"About menu opened for {chat_id}")

def stop(update):
    chat_id1 = update['message']['from']['id']
    if cache.hexists('pairs', chat_id1):
        chat_id2 = cache.hget('pairs', chat_id1).decode()
        lang1 = db.select_parameter("language", f"chat_id = {chat_id1}")["language"]
        lang2 = db.select_parameter("language", f"chat_id = {chat_id2}")["language"]
        
        system_send_message(chat_id1, texts["ended conversation"][lang1], main_keyboard(lang1))
        system_send_message(chat_id2, texts["ended conversation"][lang2], main_keyboard(lang2))

        rate_keyboard_copy = copy.deepcopy(rate_keyboard)

        rate_keyboard_copy["inline_keyboard"][0][0]["callback_data"] = f"like_{chat_id2}"
        rate_keyboard_copy["inline_keyboard"][0][1]["callback_data"] = f"dislike_{chat_id2}"
        system_send_message(chat_id1, texts["rate_op"][lang1], rate_keyboard_copy)

        rate_keyboard_copy["inline_keyboard"][0][0]["callback_data"] = f"like_{chat_id1}"
        rate_keyboard_copy["inline_keyboard"][0][1]["callback_data"] = f"dislike_{chat_id1}"
        system_send_message(chat_id2, texts["rate_op"][lang2], rate_keyboard_copy)

        del_pair(chat_id1)

def next(update):
    stop(update)
    join(update)

def settings(update):
    
    chat_id = update['message']['from']['id'] if 'message' in update else update['callback_query']['from']['id']
    params = db.select_parameter("*", f"chat_id = {chat_id}")
    lang = params["language"]
    keyboard = {
    "inline_keyboard": [
        [{"text": texts["settings"]["menu_lang"][lang], "callback_data": "language"},
         {"text": texts["settings"]["menu_region"][lang], "callback_data": "region"}],
        [{"text": texts["settings"]["menu_type"][lang], "callback_data": "TYPE"},
        {"text": texts["settings"]["menu_types"][lang], "callback_data": "TYPES"},],
        [{"text": texts["settings"]["menu_age"][lang], "callback_data": "my_age"},
        {"text": texts["settings"]["menu_ages"][lang], "callback_data": "prefered_ages"},],
        [{"text": texts["settings"]["menu_sex"][lang], "callback_data": "sex"},
        {"text": texts["settings"]["menu_sexes"][lang], "callback_data": "sexes"}]
        ]}
    
    text = f"{texts['settings']['header'][lang]}\n"
    for key, value in params.items():
        if key not in ["id", "chat_id"]:
            if value != None or key in ["region_lat", "region_lon"] :
                if key == "region_lat":
                    lat = value
                elif key == "region_lon":
                    region = from_coords_to_name(lat, value, lang)
                    if region:
                        text += f"{texts['region'][lang]}{region}\n"
                    else:
                        text += f"{texts['region'][lang]}{texts['empty'][lang]}\n"
                elif key == "TYPE":
                    text += f"{texts[key][lang]}{mbti_types[value]}\n"
                elif key == "TYPES":
                    if value == 0:
                        value = 65535 
                    num_bits = 16
                    types_list = [f"{mbti_types[bit]}" for bit in range(num_bits) if (value >> bit) & 1]
                    text += f"{texts[key][lang]}{', '.join(types_list)}\n"
                elif key == "sex" or key == "sexes":
                    text += f"{texts[key][lang]}{texts[sexes[value]][lang]}\n"
                else:
                    if key == "rate" and value == round(value):
                        value = round(value) 

                    text += f"{texts[key][lang]}{value}\n"
            else:
                text += f"{texts[key][lang]}{texts['empty'][lang]}\n"
                

    system_send_message(chat_id, text, keyboard, "Settings")

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
                system_delete_message(chat_id, int(cache.hget("waiting_message", chat_id)))
                cache.hdel("waiting_message", chat_id)
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
            db.upsert_user_data({'prefarred_ages' : text}, condition)
            cache.srem("age_interval", chat_id)
            system_delete_message(chat_id, int(cache.hget("waiting_message", chat_id)))
            cache.hdel("waiting_message", chat_id)
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
        system_delete_message(chat_id, int(cache.hget("waiting_message", chat_id)))
        cache.hdel("waiting_message", chat_id)
        system_send_message(chat_id, texts["location set"][lang], None, 'coords')


    cache.hdel('state', chat_id)

message_handlers = {
    'text' : send_message,
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
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    content = system_send_message(chat_id, texts["location handle"][lang], cancel_keyboard(chat_id, "state"), "set location")
    cache.hset("waiting_message", chat_id, content["message_id"])
    cache.sadd("region_collect", chat_id)
    cache.hset('state', chat_id, 'region_collect')

def handle_my_age(update):
    chat_id = update['callback_query']['from']['id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    content = system_send_message(chat_id, texts["age handle"][lang], cancel_keyboard(chat_id, "state"), "set age menu")
    cache.hset("waiting_message", chat_id, content["message_id"])
    cache.hset('state', chat_id, 'age_collect')

def handle_preferred_ages(update):
    chat_id = update['callback_query']['from']['id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    content = system_send_message(chat_id, texts["ages handle"][lang], cancel_keyboard(chat_id, "state"), "set age interval menu")
    cache.hset("waiting_message", chat_id, content["message_id"])
    cache.hset('state', chat_id, 'age_interval')

# ----------------------------  

def handle_unsupported_callback(update):
    # Handle unsupported callback_data values
    print(f"Unsupported callback_data: {update['callback_query']['data']}")

# ------- handling settings -------  

def change_type(update):
    chat_id = update['callback_query']['from']['id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    mbti_type = update['callback_query']['data'][:-2]
    index = mbti_indexes[mbti_type]
    condition = f'chat_id = {chat_id}'

    db.upsert_user_data({'TYPE': index}, condition)
    system_delete_message(chat_id, update['callback_query']['message']['message_id'])
    system_send_message(chat_id, texts["type set"][lang])

def change_p_types(update):
    chat_id = update['callback_query']['from']['id']
    mbti_type = update['callback_query']['data'][:-2]
    condition = f'chat_id = {chat_id}'
    mask = 1 << mbti_indexes[mbti_type]
    current_types = db.select_parameter('TYPES', condition)['TYPES']
    new_types = (current_types & ~mask) | (mask & ~current_types)
    db.upsert_user_data({'TYPES': new_types}, condition)
    system_edit_types_message(chat_id, update['callback_query']['message']['message_id'], new_types)

def change_sex(update):
    chat_id = update['callback_query']['from']['id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    sex = update['callback_query']['data'][:-6]
    condition = f'chat_id = {chat_id}'
    sex_num = sexes.index(sex)
    
    db.upsert_user_data({'sex': sex_num}, condition)
    system_delete_message(chat_id, update['callback_query']['message']['message_id'])
    system_send_message(chat_id, texts["sex set"][lang])

def change_p_sex(update):
    chat_id = update['callback_query']['from']['id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    psex = update['callback_query']['data'][:-13]
    condition = f'chat_id = {chat_id}'
    sexes_num = sexes.index(psex)

    db.upsert_user_data({'sexes': sexes_num}, condition)
    system_delete_message(chat_id, update['callback_query']['message']['message_id'])
    system_send_message(chat_id, texts["sexes set"][lang])

def handle_language(update):
    chat_id = update['callback_query']['from']['id']
    callback_data = update['callback_query']['data']
    system_delete_message(chat_id, update['callback_query']['message']['message_id'])
    db.upsert_user_data({"language": callback_data}, f"chat_id = {chat_id}")

def handle_language_with_settings(update):
    chat_id = update['callback_query']['from']['id']
    callback_data = update['callback_query']['data'][:2]
    print(callback_data)
    system_delete_message(chat_id, update['callback_query']['message']['message_id'])
    db.upsert_user_data({"language": callback_data}, f"chat_id = {chat_id}")
    system_send_message(chat_id, texts["set language"][callback_data], main_keyboard(callback_data), "language parameter _with_settings")
    settings(update)

def handle_clall(update):
    chat_id = update["callback_query"]["from"]["id"]
    db.upsert_user_data({"TYPES": 0}, f"chat_id = {chat_id}")
    system_edit_types_message(chat_id, update['callback_query']['message']['message_id'], 0)

def lang_setting(update):
    chat_id = update['callback_query']['from']['id']
    # system_delete_message(chat_id, update['callback_query']['message']['message_id'])
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


def handle_my_sex(update):
    chat_id = update['callback_query']['from']['id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]

    system_send_message(chat_id, texts["sex settings"][lang], sex_keyboard(lang), "set sex") 

def handle_preferred_sexes(update):
    chat_id = update['callback_query']['from']['id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    system_send_message(chat_id, texts["sexes settings"][lang], preferred_sexes_keyboard(lang), "set preferred sexes")


def handle_cancel_state(update):
    chat_id = update['callback_query']['from']['id']
    message_id = update['callback_query']['message']['message_id']
    system_delete_message(chat_id, message_id)
    if cache.hexists('state', chat_id):
        lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
        cache.hdel('state', chat_id)
        system_send_message(chat_id, texts["cancel_state"][lang], main_keyboard(lang), "state cancled message")

def handle_cancel_waiting(update):
    chat_id = update['callback_query']['from']['id']
    message_id = update['callback_query']['message']['message_id']
    system_delete_message(chat_id, message_id)
    if cache.sismember('waiting_pool', chat_id):
        lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
        cache.srem('waiting_pool', chat_id)
        cache.hdel("waiting_message", chat_id)
        system_send_message(chat_id, texts["cancel_waiting"][lang], main_keyboard(lang), "waiting cancled message")
    

# ---------------------------- 

def like(update):
    callback_data = update['callback_query']['data']
    match = re.match(r'like_(\d+)', callback_data)
    print(match)
    chat_id1 = update['callback_query']['from']['id']
    chat_id2 = match.group(1)
    rating = db.select_parameter("rate", f"chat_id = {chat_id2}")["rate"]
    lang = db.select_parameter("language", f"chat_id = {chat_id2}")["language"]
    new_rating = min(rating + 1, 50)
    db.upsert_user_data({"rate" : new_rating}, f"chat_id = {chat_id2}")
    system_edit_message(chat_id1, update['callback_query']['message']['message_id'], texts["tanks_rating"][lang], None, "rating")

def dislike(update):
    callback_data = update['callback_query']['data']
    match = re.match(r'dislike_(\d+)', callback_data)
    print(match) 
    chat_id1 = update['callback_query']['from']['id']
    chat_id2 = match.group(1)
    rating = db.select_parameter("rate", f"chat_id = {chat_id2}")["rate"]
    lang = db.select_parameter("language", f"chat_id = {chat_id2}")["language"]
    new_rating = max(rating - 1, 0)
    db.upsert_user_data({"rate" : new_rating}, f"chat_id = {chat_id2}")
    system_edit_message(chat_id1, update['callback_query']['message']['message_id'], texts["tanks_rating"][lang], None, "rating")

callback_actions = {
    "language": lang_setting,
    "TYPE": TYPE_setting,
    "TYPES": TYPES_setting,
    "region": handle_region,
    "my_age": handle_my_age,
    "prefered_ages": handle_preferred_ages,
    "sex" : handle_my_sex,
    "sexes" : handle_preferred_sexes,
    "en": handle_language,
    "fr": handle_language,
    "ru": handle_language,
    "es": handle_language,
    "en_with_settings": handle_language_with_settings,
    "fr_with_settings": handle_language_with_settings,
    "ru_with_settings": handle_language_with_settings,
    "es_with_settings": handle_language_with_settings,
    "clall": handle_clall,
    "cancel_state" : handle_cancel_state,
    "cancel_waiting" : handle_cancel_waiting,
    }

def callback_handler(update):
    callback_data = update['callback_query']['data']
    if callback_data in callback_actions:
        callback_actions[callback_data](update)
    elif callback_data.endswith('_m'):
        change_type(update)
    elif callback_data.endswith('_p'):
        change_p_types(update)
    elif callback_data.endswith('_mysex'):
        change_sex(update)
    elif callback_data.endswith('_preferredsex'):
        change_p_sex(update)
    elif re.match(r'like_(\d+)', callback_data):
        like(update)
    elif re.match(r'dislike_(\d+)', callback_data):
        dislike(update)
    else:
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
                return
        for keyword, handler in message_handlers.items():
            if keyword in update['message'] and cache.hexists('pairs', chat_id):
                pair = cache.hget('pairs', chat_id).decode()
                print(f"sending {keyword} from {chat_id} to {pair}.")
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