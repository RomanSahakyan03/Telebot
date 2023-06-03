import math
import json
import requests
import os
from config import create_redis_client
from geopy import Nominatim

cache = create_redis_client() 

# Create an instance of the geocoder
geolocator = Nominatim(user_agent="TypeTalk")


def from_coords_to_name(latitude, longitude):
    # Reverse geocode the coordinates to get the location information
    location = geolocator.reverse((latitude, longitude), exactly_one=True)
    address = location.raw['address']

    places = ["village", "town", "city"]
    for place in places:
        if name := address.get(place, ''):
            return name
    return "somewhere lol"

# Set up API endpoint and bot token
telegram_token = os.environ.get('TELEGRAM_API_TOKEN')
API_LINK = f"https://api.telegram.org/bot{telegram_token}"

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

lang_keyboard = {
    "inline_keyboard": [
        [{"text": "🇺🇸 English", "callback_data": "en"},
        {"text": "🇷🇺 Русский", "callback_data": "ru"}],
        [{"text": "🇫🇷 français", "callback_data": "fr"},
        {"text": "🇪🇸 Español", "callback_data": "es"}]
        ]}

def make_pair(chat_id1, chat_id2):
    cache.hset('pairs', chat_id1, chat_id2)
    cache.hset('pairs', chat_id2, chat_id1)

def del_pair(chat_id1):
    chat_id2 = cache.hget('pairs', chat_id1).decode()
    cache.delete(str(chat_id1))
    cache.delete(str(chat_id2))
    cache.hdel('pairs', chat_id1)
    cache.hdel('pairs', chat_id2)

def send_request(data: dict, method: str, handler = None):
    if handler:
        handler_success = f"{handler} opened Successfully."
        handler_fail = f"Failed to open {handler}."
    else:
        handler_success = f"{method.capitalize()} request successful."
        handler_fail = f"{method.capitalize()} request failed."

    response = requests.post(f"{API_LINK}/{method}", json=data)
    if response.status_code == 200:
        print(handler_success)
    else:
        print(handler_fail)
    return response.json()['result']

if __name__ ==  "__main__":
    pass