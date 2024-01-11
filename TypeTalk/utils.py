import math
import json
import os
from config import create_redis_client
from geopy import Nominatim
from load_json import texts
import asyncio

telegram_token = os.environ.get('TELEGRAM_API_TOKEN')
API_LINK = f"https://api.telegram.org/bot{telegram_token}"
GET_UPDATES_URL = f"{API_LINK}/getUpdates"
EDIT_MESSAGE_URL = f"{API_LINK}/editMessageText"
EDIT_CAPTION_URL = f"{API_LINK}/editMessageCaption"
EDIT_MEDIA_URL = f"{API_LINK}/editMessageMedia"
SEND_MESSAGE = "sendMessage"
cache = create_redis_client()

# Get the absolute path of the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute file path
file_path = os.path.join(current_dir, 'typetalk_texts.json')

# cancel only "state" or "waiting"
def cancel_keyboard(lang, option):
    cancel = "cancel_" + option
    keyboard = {
    "inline_keyboard": [
        [{"text": texts["keyboards"]["cancel_keyboard"][lang], "callback_data": cancel}]
    ]}
    return keyboard

async def system_send_message(session, receiver, text, reply_markup=None, handler=None):
    data = {
        "chat_id": receiver,
        "text": text
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)

    if handler is None:
        handler = f"{receiver} message sent"

    content = await send_request(session, data, SEND_MESSAGE, handler)

    return content

async def system_edit_message(session, receiver, message_id, text=None, reply_markup=None, handler=None):
    data = {
        "chat_id": receiver,
        "message_id": message_id,
    }
    if text:
        data["text"] = text

    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)

    if handler is None:
        handler = f"{receiver} message edited"

    content = await send_request(session, data, "editMessageText", handler)

    return content

async def system_edit_types_message(session, receiver, message_id, res, lang):
    keyboard = get_mbti_types_keyboard(res)
    data = {
        "chat_id": receiver,
        "message_id": message_id,
        "text": texts["configuration_menus"]["types_settings"][lang],
        "reply_markup": json.dumps(keyboard)
    }

    content = await send_request(session, data, "editMessageText")

    return content

async def system_delete_message(session, receiver, message_id):
    data = {
        "chat_id": receiver,
        "message_id": message_id
    }

    try:
        content = await send_request(session, data, "deleteMessage", f"Deleted message {message_id} from {receiver}")
    except Exception as e:
        print(f"Error deleting message: {e}")
        content = None

    return content

# Create an instance of the geocoder
geolocator = Nominatim(user_agent="TypeTalk")


def from_coords_to_name(latitude, longitude, lang):
    if not(latitude or longitude):
        return texts['location']['anywhere'][lang]
    # Reverse geocode the coordinates to get the location information
    location = geolocator.reverse((latitude, longitude), exactly_one=True)
    address = location.raw['address']

    places = ["village", "town", "city"]
    for place in places:
        if name := address.get(place, ''):
            return name
    return texts["no_geo"][lang]

# Set up API endpoint and bot token
telegram_token = os.environ.get('TELEGRAM_API_TOKEN')
API_LINK = f"https://api.telegram.org/bot{telegram_token}"

mbti_types = [
    "INTJ", "INFJ", "ISTJ", "ISTP",
    "INTP", "INFP", "ISFJ", "ISFP",
    "ENTJ", "ENFJ",  "ESTJ",  "ESTP",
    "ENTP",  "ENFP",  "ESFJ",  "ESFP"
]
mbti_indexes = {type : i for i, type in enumerate(mbti_types)}

sexes = ["male", "female", "both"]

mbti_type_emoji = {
    "INTJ": "🧠",  # The Architect
    "INTP": "🔍",  # The Logician
    "ENTJ": "📈",  # The Commander
    "ENTP": "🗣️",  # The Debater
    "INFJ": "🎭",  # The Advocate
    "INFP": "🌱",  # The Mediator
    "ENFJ": "🌟",  # The Protagonist
    "ENFP": "😄",  # The Campaigner
    "ISTJ": "📊",  # The Logistician
    "ISFJ": "🧡",  # The Defender
    "ESTJ": "💼",  # The Executive
    "ESFJ": "🤗",  # The Consul
    "ISTP": "🛠️",  # The Virtuoso
    "ISFP": "🎨",  # The Adventurer
    "ESTP": "🚀",  # The Entrepreneur
    "ESFP": "🎉",  # The Entertainer
}

def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])

    d_lat = lat2 - lat1
    d_lon = lon2 - lon1

    a = math.pow(math.sin(d_lat / 2), 2) + math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(d_lon / 2), 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = 6371 * c # Radius of the Earth in kilometers

    return distance

def settings_status_bar(params : dict):
    lang = params["language"]
    text = f"{texts['settings']['header'][lang]}\n"
    for key, value in params.items():
        if key not in ["id", "chat_id", "adcount"]:
            if value != None or key in ["region_lat", "region_lon"] :
                if key == "language":
                    text += f"{texts['settings'][key][lang]}{texts[lang]}\n"
                elif key == "region_lat":
                    lat = value
                elif key == "region_lon":
                    region = from_coords_to_name(lat, value, lang)
                    text += f"{texts['settings']['region'][lang]}{region}\n"
                elif key == "TYPE":
                    text += f"{texts['settings'][key][lang]}{mbti_types[value]} {mbti_type_emoji[mbti_types[value]]}\n\n"
                elif key == "TYPES":
                    if value == 0:
                        value = 65535 
                    num_bits = 16
                    types_list = [f"{mbti_types[bit]}" for bit in range(num_bits) if (value >> bit) & 1]
                    text += f"{texts['settings'][key][lang]}"

                    text += ", ".join(types_list[:8]) + (",\n" if len(types_list) > 8 else "\n") + ", ".join(types_list[8:])
                    text += "\n" if len(types_list) > 8 else ""
                    text += "\n"
                elif key == "sex" or key == "sexes":
                    text += f"{texts['settings'][key][lang]}{texts['keyboards']['sex_keyboard'][sexes[value]][lang]}\n"
                    if key == "sexes":
                        text += "\n"
                elif key == "age" and value:
                    text += f"{texts['settings'][key][lang]}{value} 🎂\n"
                elif key == "preferred_ages" and value:
                    text += f"{texts['settings'][key][lang]}{value} 👫\n\n"
                else:
                    if key == "rate":
                        value = '.'.join(str(value)) 

                    text += f"{texts['settings'][key][lang]}{value}\n"
            else:
                text += f"{texts['settings'][key][lang]}{texts['settings']['empty'][lang]}\n"
    return text

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

def main_keyboard(lang):
    keyboard = {
        "keyboard":
            [[{"text": texts["keyboards"]["main_keyboard"]["joining"][lang]},
            {"text": texts["keyboards"]["main_keyboard"]["settings"][lang]}],
            [{"text": texts["keyboards"]["main_keyboard"]["about_page"][lang]}]],

        "resize_keyboard": True,
        "one_time_keyboard" : True
    }
    return keyboard

def sex_keyboard(lang):
    keyboard = {
        "inline_keyboard":
            [
                [{"text": texts["keyboards"]["sex_keyboard"]["male"][lang], "callback_data": "male_mysex"},
                {"text": texts["keyboards"]["sex_keyboard"]["female"][lang], "callback_data": "female_mysex"}]
            ],
    }
    return keyboard

def preferred_sexes_keyboard(lang):
    keyboard = {
        "inline_keyboard":
            [
                [{"text": texts["keyboards"]["sex_keyboard"]["male"][lang], "callback_data": "male_preferredsex"},
                {"text": texts["keyboards"]["sex_keyboard"]["female"][lang], "callback_data": "female_preferredsex"}],
                [{"text": texts["keyboards"]["sex_keyboard"]["both"][lang], "callback_data": "both_preferredsex"}]
            ],

    }
    
    return keyboard

rate_keyboard = {
        "inline_keyboard":
            [
                [{"text": "👍", "callback_data": "like"},
                {"text": "👎", "callback_data": "dislike"}],
            ]
    }

def make_pair(chat_id1, chat_id2):
    cache.hset('pairs', chat_id1, chat_id2)
    cache.hset('pairs', chat_id2, chat_id1)

def del_pair(chat_id1):
    chat_id2 = cache.hget('pairs', chat_id1).decode()
    cache.delete(chat_id1)
    cache.delete(chat_id2)
    cache.hdel('pairs', chat_id1)
    cache.hdel('pairs', chat_id2)

async def send_request(session, data: dict, method: str, handler=None):
    if handler:
        handler_success = f"Successfully: {handler}."
        handler_fail = f"Failed: {handler}."
    else:
        handler_success = f"{method.capitalize()} request successful."
        handler_fail = f"{method.capitalize()} request failed."

    async with session.post(f"{API_LINK}/{method}", json=data) as response:
        if response.status == 200:
            print(handler_success)
            return await response.json()
        else:
            print(handler_fail)
            print(await response.text())
    
if __name__ ==  "__main__":
    pass