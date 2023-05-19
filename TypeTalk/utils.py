import math
import json
import redis
cache = redis.Redis(host='localhost', port=6379, db=0) 
# Set up API endpoint and bot token


API_LINK = "https://api.telegram.org/bot6114753472:AAFBAES3t622glVzoe5-4BpKF0hjbBeX6_c"
GET_UPDATES_URL = f"{API_LINK}/getUpdates"
SEND_MESSAGE_URL = f"{API_LINK}/sendMessage"
DELETE_MESSAGE_URL = f"{API_LINK}/deleteMessage"
INLINE_KEYBOARD = f"{API_LINK}/InlineKeyboardMarkup"
EDIT_MESSAGE_URL = f"{API_LINK}/editMessageText"

with open('TypeTalk/typetalk_texts.json', 'r', encoding="UTF-8") as f:
    texts = json.load(f)

mbti_types = [
    "INTJ", "INFJ", "ISTJ", "ISTP",
    "INTP", "INFP", "ISFJ", "ISFP",
    "ENTJ", "ENFJ",  "ESTJ",  "ESTP",
    "ENTP",  "ENFP",  "ESFJ",  "ESFP"
]
mbti_indexes = {type : i for i, type in enumerate(mbti_types)}

def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])

    d_lat = lat2 - lat1
    d_lon = lon2 - lon1

    a = math.pow(math.sin(d_lat / 2), 2) + math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(d_lon / 2), 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = 6371 * c # Radius of the Earth in kilometers

    return distance

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

def make_pair(chat_id1, chat_id2):
    cache.hset('pairs', chat_id1, chat_id2)
    cache.hset('pairs', chat_id2, chat_id1)

def del_pair(chat_id1):
    chat_id2 = cache.hget('pairs', chat_id1).decode()
    cache.delete(str(chat_id1))
    cache.delete(str(chat_id2))
    cache.hdel('pairs', chat_id1)
    cache.hdel('pairs', chat_id2)

if __name__ ==  "__main__":
    pass