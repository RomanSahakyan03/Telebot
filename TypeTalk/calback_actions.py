import os
import json
import re
from db import BotDB
from config import create_redis_client
from utils import system_delete_message, sexes, system_edit_message, system_send_message, system_edit_types_message, main_keyboard,lang_keyboard, mbti_indexes, mbti_types, get_mbti_types_keyboard, cancel_keyboard, sex_keyboard, preferred_sexes_keyboard
from commands import settings

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


def lang_setting(chat_id, message_id, lang):
    system_delete_message(chat_id, message_id)
    system_send_message(chat_id, texts["configuration_menus"]["lang_settings"][lang], lang_keyboard, 'Language selection menu')


def TYPE_setting(chat_id, message_id, lang):
    system_delete_message(chat_id, message_id)
    keyboard = {
    "inline_keyboard": [
        [{"text": mbti_types[bit], "callback_data": mbti_types[bit] + "_m"} for bit in range(row * 4, (row + 1) * 4) if bit < 16] for row in range((16 - 1) // 4 + 1)
    ]}

    system_send_message(chat_id, texts["configuration_menus"]["type_settings"][lang], keyboard, 'MBTI type selection menu')


def TYPES_setting(chat_id, message_id, lang):
    x = db.select_parameter("TYPES", f"chat_id = {chat_id}")['TYPES']
    keyboard = get_mbti_types_keyboard(x)
    system_send_message(chat_id, texts["configuration_menus"]["types_settings"][lang], keyboard, 'MBTI preffered types selection menu')


def handle_region(chat_id, message_id, lang):
    system_delete_message(chat_id, message_id)
    how_to = {"text": texts["location"]["idkhow_button"][lang], "callback_data": "idkhow"}
    reset_b = {"text": texts["location"]["reset_button"][lang], "callback_data": "resloc"}
    keyboard = cancel_keyboard(lang, "state")
    keyboard["inline_keyboard"][0].append(how_to)
    keyboard["inline_keyboard"][0].append(reset_b)
    content = system_send_message(chat_id, texts["configuration_menus"]["location_handle"][lang], keyboard, "set location")
    cache.hset("waiting_message", chat_id, content["message_id"])
    cache.hset('state', chat_id, 'region_collect')

def handle_my_age(chat_id, message_id, lang):
    system_delete_message(chat_id, message_id)
    content = system_send_message(chat_id, texts["configuration_menus"]["age_handle"][lang], cancel_keyboard(lang, "state"), "set age menu")
    cache.hset("waiting_message", chat_id, content["message_id"])
    cache.hset('state', chat_id, 'age_collect')

def handle_preferred_ages(chat_id, message_id, lang):
    system_delete_message(chat_id, message_id)
    content = system_send_message(chat_id, texts["configuration_menus"]["ages_handle"][lang], cancel_keyboard(lang, "state"), "set age interval menu")
    cache.hset("waiting_message", chat_id, content["message_id"])
    cache.hset('state', chat_id, 'age_interval')

def handle_my_sex(chat_id, message_id, lang):
    system_delete_message(chat_id, message_id)
    system_send_message(chat_id, texts["configuration_menus"]["sex_settings"][lang], sex_keyboard(lang), "set sex")

def handle_preferred_sexes(chat_id, message_id, lang):
    system_delete_message(chat_id, message_id)
    system_send_message(chat_id, texts["configuration_menus"]["sexes_settings"][lang], preferred_sexes_keyboard(lang), "set preferred sexes")

def handle_clall(chat_id, message_id, lang):
    db.upsert_user_data({"TYPES": 0}, f"chat_id = {chat_id}")
    system_edit_types_message(chat_id, message_id, 0, lang)

def handle_cancel_waiting(chat_id, message_id, lang):
    system_delete_message(chat_id, message_id)
    if cache.sismember('waiting_pool', chat_id):
        cache.srem('waiting_pool', chat_id)
        system_send_message(chat_id, texts["cancel_waiting"][lang], main_keyboard(lang), "waiting cancled message")

def idkhow(chat_id, message_id, lang):
    i_know = {"text": texts["location"]["close"][lang], "callback_data": "iknow"}
    keyboard = cancel_keyboard(lang, "state")
    keyboard["inline_keyboard"][0].append(i_know)
    system_edit_message(chat_id, message_id, texts["location"]["idkhow"][lang], keyboard)

def iknow(chat_id, message_id, lang):
    idkhow = {"text": texts["location"]["idkhow_button"][lang], "callback_data": "idkhow"}
    keyboard = cancel_keyboard(lang, "state")
    keyboard["inline_keyboard"][0].append(idkhow)
    system_edit_message(chat_id, message_id, texts["location"]["location_handle"][lang], keyboard)

def handle_cancel_state(chat_id, message_id, lang):
    system_delete_message(chat_id, message_id)
    if cache.hexists('state', chat_id):
        cache.hdel('state', chat_id)
        system_send_message(chat_id, texts["cancel_state"][lang], main_keyboard(lang), "state cancled message")
    settings(chat_id)

def reset_location(chat_id, message_id, lang):
    system_delete_message(chat_id, message_id)
    condition = f'chat_id = {chat_id}'
    db.upsert_user_data({'region_lat' : None}, condition)
    db.upsert_user_data({'region_lon' : None}, condition)
    content = system_send_message(chat_id, texts["location"]["location_reset"][lang])
    cache.hdel('state', chat_id, 'region_collect')
    settings(chat_id)

# Handle unsupported callback_data values
def handle_unsupported_callback(update):
    print(f"Unsupported callback_data: {update['callback_query']['data']}")


# ------- handling settings -------  

def change_type(chat_id, message_id, lang, mbti_type):
    mbti_type = mbti_type[:-2]
    index = mbti_indexes[mbti_type]
    condition = f'chat_id = {chat_id}'

    db.upsert_user_data({'TYPE': index}, condition)
    system_delete_message(chat_id, message_id)
    system_send_message(chat_id, texts["success"]["type_set"][lang])
    settings(chat_id)

def change_p_types(chat_id, message_id, lang, mbti_type):
    mbti_type = mbti_type[:-2]
    condition = f'chat_id = {chat_id}'
    mask = 1 << mbti_indexes[mbti_type]
    current_types = db.select_parameter('TYPES', condition)['TYPES']
    new_types = (current_types & ~mask) | (mask & ~current_types)
    db.upsert_user_data({'TYPES': new_types}, condition)
    system_edit_types_message(chat_id, message_id, new_types, lang)

def change_sex(chat_id, message_id, lang, sex):
    sex = sex[:-6]
    condition = f'chat_id = {chat_id}'
    sex_num = sexes.index(sex)
    
    db.upsert_user_data({'sex': sex_num}, condition)
    system_delete_message(chat_id, message_id)
    system_send_message(chat_id, texts["success"]["sex_set"][lang])
    settings(chat_id)

def change_p_sex(chat_id, message_id, lang, psex):
    psex = psex[:-13]
    condition = f'chat_id = {chat_id}'
    sexes_num = sexes.index(psex)

    db.upsert_user_data({'sexes': sexes_num}, condition)
    system_delete_message(chat_id, message_id)
    system_send_message(chat_id, texts["success"]["sexes_set"][lang])
    settings(chat_id)

def handle_language(chat_id, message_id, lang, callback_data):
    system_delete_message(chat_id, message_id)
    db.upsert_user_data({"language": callback_data}, f"chat_id = {chat_id}")
    system_send_message(chat_id, texts["success"]["language_set"][callback_data])
    settings(chat_id)

def like(chat_id1, message_id, lang, callback_data):
    match = re.match(r'like_(\d+)', callback_data)
    chat_id2 = match.group(1)
    rating = db.select_parameter("rate", f"chat_id = {chat_id2}")["rate"]
    new_rating = min(rating + 1, 50)
    db.upsert_user_data({"rate" : new_rating}, f"chat_id = {chat_id2}")
    system_edit_message(chat_id1, message_id, texts["rating"]["tanks_rating"][lang], None, "rating")

def dislike(chat_id1, message_id, lang, callback_data):
    match = re.match(r'dislike_(\d+)', callback_data)
    chat_id2 = match.group(1)
    rating = db.select_parameter("rate", f"chat_id = {chat_id2}")["rate"]
    lang = db.select_parameter("language", f"chat_id = {chat_id2}")["language"]
    new_rating = max(rating - 1, 0)
    db.upsert_user_data({"rate" : new_rating}, f"chat_id = {chat_id2}")
    system_edit_message(chat_id1, message_id, texts["rating"]["tanks_rating"][lang], None, "rating")