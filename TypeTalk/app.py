import json
import re
import os
import threading
import time
import requests
from db import BotDB
from edit_data import *
from send_data import *
from utils import *
from config import create_redis_client
from commands import *
from calback_actions import *
from matching_system import matching_system

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
    
# Can be 'age_collect', 'age_interval', 'region_collect'
def state_handler(update, state):
    chat_id = update['message']['from']['id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    condition = f'chat_id = {chat_id}'
    if state == 'age_collect':
        if "message" not in update or "text" not in update["message"]:
            system_send_message(chat_id, texts["exceptions"]["invalid_data"][lang], None, "age set error")
            return
        text = update['message']['text']
        pattern = r"^(\d+)$"
        match = re.match(pattern, text)
        if match and int(text) < 100:
            if int(text) < 12:
                system_send_message(chat_id, texts["exceptions"]["not_enough_age"][lang], None, 'error setage message')
            else:
                cache.srem("age_collect", chat_id)
                db.upsert_user_data({'age' : text}, condition)
                system_delete_message(chat_id, update['message']['message_id'])
                system_delete_message(chat_id, cache.hget("waiting_message", chat_id).decode())
                cache.hdel("waiting_message", chat_id)
                system_send_message(chat_id, texts["success"]["age_set"][lang], None, 'setage')
        else:
            system_send_message(chat_id, texts["exceptions"]["invalid_data"][lang], None, 'error setage message')
            return
    elif state == 'age_interval':
        if "message" not in update or "text" not in update["message"]:
            system_send_message(chat_id, texts["exceptions"]["invalid_data"][lang], None, "age set error")
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
                system_send_message(chat_id, texts["exceptions"]["low_age_alert"][lang], None, "Pedophil error")
                return
            db.upsert_user_data({'preferred_ages' : text}, condition)
            cache.srem("age_interval", chat_id)
            system_delete_message(chat_id, update['message']['message_id'])
            system_delete_message(chat_id, cache.hget("waiting_message", chat_id).decode())
            cache.hdel("waiting_message", chat_id)
            system_send_message(chat_id, texts["success"]["age_set"][lang], None, 'setage interval')
        else:
            system_send_message(chat_id, texts["exceptions"]["invalid_data"][lang], None, "age set error")
            return
    elif state == 'region_collect':
        if "message" not in update or "location" not in update["message"]:
            system_send_message(chat_id, texts["exceptions"]["invalid_data"][lang], None, "location data error")
            return
        latitude = update['message']['location']['latitude']
        longitude = update['message']['location']['longitude']
        db.upsert_user_data({'region_lat' : latitude}, condition)
        db.upsert_user_data({'region_lon' : longitude}, condition)
        system_delete_message(chat_id, update['message']['message_id'])
        system_delete_message(chat_id, cache.hget("waiting_message", chat_id).decode())
        cache.hdel("waiting_message", chat_id)
        system_send_message(chat_id, texts["success"]["location_set"][lang], None, 'coords')

    cache.hdel('state', chat_id)
    settings(chat_id)

callback_actions = {
    "language": lang_setting,
    "TYPE": TYPE_setting,
    "TYPES": TYPES_setting,
    "region": handle_region,
    "my_age": handle_my_age,
    "prefered_ages": handle_preferred_ages,
    "sex" : handle_my_sex,
    "sexes" : handle_preferred_sexes,
    "clall": handle_clall,
    "cancel_state" : handle_cancel_state,
    "cancel_waiting" : handle_cancel_waiting,
    "idkhow" : idkhow,
    "iknow" : iknow,
    "resloc" : reset_location
    }

action_patterns = {
    '_m': change_type,
    '_p': change_p_types,
    '_mysex': change_sex,
    '_preferredsex': change_p_sex,
    "en": handle_language,
    "fr": handle_language,
    "ru": handle_language,
    "es": handle_language,
}

def callback_handler(update):
    callback_data = update['callback_query']['data']
    chat_id = update['callback_query']['from']['id']
    message_id = update['callback_query']['message']['message_id']
    lang = db.select_parameter("language", f"chat_id = {chat_id}")["language"]
    if callback_data in callback_actions:
        callback_actions[callback_data](chat_id, message_id, lang)
        return
    for pattern, action in action_patterns.items():
        if callback_data.endswith(pattern):
            action(chat_id, message_id, lang, callback_data)
            return
    if re.match(r'like_(\d+)', callback_data):
        like(chat_id, message_id, lang, callback_data)
    elif re.match(r'dislike_(\d+)', callback_data):
        dislike(chat_id, message_id, lang, callback_data)
    else:
        handle_unsupported_callback(update)

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

COMMANDS = {
    '👋 Start The Conversation' : join,
    '👋 Commencer la conversation' : join,
    '👋 Начать разговор' : join,
    '👋 Comenzar la conversación' : join,
    '🛠️ Manage Settings' : settings,
    '🛠️ Gérer les Paramètres' : settings,
    '🛠️ Управление настройками' : settings,
    '🛠️ Administrar la Configuración' : settings,
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
        if cache.sismember("waiting_pool", chat_id):
            return
        if cache.hexists('state', chat_id):
                state_handler(update, cache.hget('state', chat_id).decode())
                return
        if 'text' in update['message']:
            text = update['message']['text']
            if text == '/shareprofile':
                username = update['message']['from']['username'] if 'username' in update['message']['from'] else None
                shareprofile(chat_id, username)
                return
            if text in COMMANDS:
                COMMANDS[text](chat_id)
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
    # matching_thread = threading.Thread(target=matching_system)
    # matching_thread.start()
    main()
    # matching_thread.join()
    db.close()