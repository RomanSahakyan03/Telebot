import requests
import redis
import os


cache = redis.Redis(host='localhost', port=6379, db=0)
telegram_token = os.environ.get('TELEGRAM_API_TOKEN')
API_LINK = f"https://api.telegram.org/bot{telegram_token}"
SEND_MESSAGE_URL = f"{API_LINK}/sendMessage"
SEND_PHOTO_URL = f"{API_LINK}/sendPhoto"
SEND_AUDIO_URL = f"{API_LINK}/sendAudio"
SEND_DOCUMENT_URL = f"{API_LINK}/sendDocument"
SEND_VIDEO_URL = f"{API_LINK}/sendVideo"
SEND_ANIMATION_URL = f"{API_LINK}/sendAnimation"
SEND_LOCATION_URL = f"{API_LINK}/sendLocation"
SEND_VIDEONOTE_URL = f"{API_LINK}/sendVideoNote"
SEND_STICKER_URL = f"{API_LINK}/sendSticker"
SEND_POLL_URL = f"{API_LINK}/sendPoll"

def cache_message_ids(receiver, update, response_data):
    chat_id = update['message']['from']['id']
    message_id1 = update['message']['message_id']
    message_id2 = response_data['result']['message_id']
    cache.hset(str(receiver), message_id1, message_id2)
    cache.hset(str(chat_id), message_id2, message_id1)


def send_message(receiver, update):
    text = update['message']['text']
    data = {
            "chat_id": receiver,
            "text": text,
        }
    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(str(receiver), message_id):
            data["reply_to_message_id"] = cache.hget(str(receiver), message_id).decode()
        
    response = requests.post(SEND_MESSAGE_URL, json=data)
    chat_id = update['message']['from']['id']
    if response.ok:
        print(f"message sent successfully from {chat_id} to {receiver}")
        response_data = response.json()
        cache_message_ids(receiver, update, response_data)
    else:
        print(f"failed to send message from {chat_id} to {receiver}")

def send_photo(receiver, update): 
    photo = update["message"]["photo"][-1]["file_id"]
    data = {
        "chat_id" : receiver,
        "photo" : photo,
    }
    if "caption" in update["message"]:
        data["caption"] = update["message"]["caption"]
    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(str(receiver), message_id):
            data["reply_to_message_id"] = cache.hget(str(receiver), message_id).decode()
    
    response = requests.post(SEND_PHOTO_URL, json=data)
    if response.ok:
        print(f"Photo sent to {receiver} successfully.")
        response_data = response.json()
        cache_message_ids(receiver, update, response_data)
    else:
        print(f"Failed to send {receiver} Photo message.")

def send_audio(receiver, update):
    data = {
        "chat_id" : receiver,
        "audio" : update["message"]["voice"]["file_id"]
    }

    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(str(receiver), message_id):
            data["reply_to_message_id"] = cache.hget(str(receiver), message_id).decode()
    
    response = requests.post(SEND_AUDIO_URL, json=data)
    if response.ok:
        print(f"Audio sent to {receiver} successfully.")
        response_data = response.json()
        cache_message_ids(receiver, update, response_data)
    else:
        print(f"Failed to send {receiver} Audio message.")

def send_document(receiver, update):
    data = {
        "chat_id" : receiver,
        "document" : update["message"]["document"]["file_id"],
    }
    if "caption" in update["message"]:
        data["caption"] = update["message"]["caption"]
    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(str(receiver), message_id):
            data["reply_to_message_id"] = cache.hget(str(receiver), message_id).decode()
    
    response = requests.post(SEND_DOCUMENT_URL, json=data)
    if response.ok:
        print(f"Document sent to {receiver} successfully.")
        response_data = response.json()
        cache_message_ids(receiver, update, response_data)
    else:
        print(f"Failed to send {receiver} Document message.")

def send_video(receiver, update):
    video = update["message"]["video"]["file_id"]
    data = {
        "chat_id" : receiver,
        "video" : video,
    }
    if "caption" in update["message"]:
        data["caption"] = update["message"]["caption"]
    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(str(receiver), message_id):
            data["reply_to_message_id"] = cache.hget(str(receiver), message_id).decode()

    response = requests.post(SEND_VIDEO_URL, json=data)
    if response.ok:
        print(f"Video sent to {receiver} successfully.")
        response_data = response.json()
        cache_message_ids(receiver, update, response_data)
    else:
        print(f"Failed to send {receiver} Video message.")   

def send_animation(receiver, update):
    animation = update["message"]["animation"]["file_id"]
    data = {
        "chat_id" : receiver,
        "animation" : animation
    }
    if "caption" in update["message"]:
        data["caption"] = update["message"]["caption"]
    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(str(receiver), message_id):
            data["reply_to_message_id"] = cache.hget(str(receiver), message_id).decode()

    response = requests.post(SEND_ANIMATION_URL, json=data)
    if response.ok:
        print(f"Animation sent to {receiver} successfully.")
        response_data = response.json()
        cache_message_ids(receiver, update, response_data)
    else:
        print(f"Failed to send {receiver} Animation message.")

def send_location(receiver, update):
    latitude = update['message']['location']['latitude']
    longitude = update['message']['location']['longitude']
    data = {
        "chat_id" : receiver,
        'latitude' : latitude,
        'longitude' : longitude,        
    }
    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(str(receiver), message_id):
            data["reply_to_message_id"] = cache.hget(str(receiver), message_id).decode()

    response = requests.post(SEND_LOCATION_URL, json=data)
    if response.ok:
        print(f"Location sent to {receiver} successfully.")
        response_data = response.json()
        cache_message_ids(receiver, update, response_data)
    else:
        print(f"Failed to send {receiver} Location message.")
    
def send_video_note(receiver, update):
    video_note = update["message"]["video_note"]["file_id"]
    data = {
        "chat_id" : receiver,
        "video_note" : video_note,
    }
    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(str(receiver), message_id):
            data["reply_to_message_id"] = cache.hget(str(receiver), message_id).decode()

    response = requests.post(SEND_VIDEONOTE_URL, json=data)
    if response.ok:
        print(f"VideoNote sent to {receiver} successfully.")
        response_data = response.json()
        cache_message_ids(receiver, update, response_data)
    else:
        print(f"Failed to send {receiver} VideoNote message.")

def send_sticker(receiver, update):
    data = {
        "chat_id" : receiver,
        "sticker" : update["message"]["sticker"]["file_id"]
    }
    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(str(receiver), message_id):
            data["reply_to_message_id"] = cache.hget(str(receiver), message_id).decode()
            
    response = requests.post(SEND_STICKER_URL, json=data)
    if response.ok:
        print(f"Stiker sent from to {receiver} successfully.")
        response_data = response.json()
        cache_message_ids(receiver, update, response_data)
    else:
        print(f"Failed to send {receiver} Sticker message.")

def send_poll(receiver, update):
    data = {
        "chat_id" : receiver,
        "question" : update["message"]["poll"]["question"],
        "options" : update["message"]["poll"]["options"],
        "is_anonymous" : True,
        "allows_multiple_answers" : update["message"]["poll"]["allows_multiple_answers"],
    }
    response = requests.post(SEND_POLL_URL, json=data)
    if response.ok:
        print(f"Poll sent from to {receiver} successfully.")
    else:
        print(f"Failed to send {receiver} Poll message.")
