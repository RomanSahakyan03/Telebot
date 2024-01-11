from utils import send_request, cache
from load_json import texts

SEND_MESSAGE = "sendMessage"
SEND_PHOTO = "sendPhoto"
SEND_AUDIO = "sendAudio"
SEND_DOCUMENT = "sendDocument"
SEND_VIDEO = "sendVideo"
SEND_ANIMATION = "sendAnimation"
SEND_LOCATION = "sendLocation"
SEND_VIDEONOTE = "sendVideoNote"
SEND_STICKER = "sendSticker"
SEND_POLL = "sendPoll"

def cache_message_ids(receiver, update, response_data):
    chat_id = update['message']['from']['id']
    message_id1 = update['message']['message_id']
    message_id2 = response_data['result']['message_id']
    cache.hset(receiver, message_id1, message_id2)
    cache.hset(chat_id, message_id2, message_id1)


async def send_message(session, receiver, update, db):
    chat_id = update['message']['from']['id']
    text = update['message']['text']
    data = {
            "chat_id": receiver,
            "text": text,
        }
    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(receiver, message_id):
            data["reply_to_message_id"] = cache.hget(receiver, message_id).decode()
        
    message = await send_request(session, data, SEND_MESSAGE, f"message sent from {chat_id} to {receiver}")
    cache_message_ids(receiver, update, message)

async def send_photo(session, receiver, update, db): 
    chat_id = update['message']['from']['id']
    info = await db.select_parameter("rate, language", f"chat_id = {chat_id}")
    sender_rating = info["rate"]
    lang = info["language"]
    if sender_rating > 20:
        photo = update["message"]["photo"][-1]["file_id"]
        data = {
            "chat_id" : receiver,
            "photo" : photo,
        }
        if "caption" in update["message"]:
            data["caption"] = update["message"]["caption"]
        if "reply_to_message" in update["message"]:
            message_id = update["message"]["reply_to_message"]["message_id"]
            if cache.hexists(receiver, message_id):
                data["reply_to_message_id"] = cache.hget(receiver, message_id).decode()
        
        message = await send_request(session, data, SEND_PHOTO, f"Photo sent from {chat_id} to {receiver}")
        cache_message_ids(receiver, update, message)
    else:
        data = {
            "chat_id": chat_id,
            "text": texts["exceptions"]["not_kenough_rating"][lang]
        }
        await send_request(session, data, "sendMessage")

async def send_audio(session, receiver, update, db):
    chat_id = update['message']['from']['id']
    data = {
        "chat_id" : receiver,
        "audio" : update["message"]["voice"]["file_id"]
    }

    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(receiver, message_id):
            data["reply_to_message_id"] = cache.hget(receiver, message_id).decode()
    
    message = await send_request(session, data, SEND_AUDIO, f"Audio sent from {chat_id} to {receiver}")
    cache_message_ids(receiver, update, message)

async def send_document(session, receiver, update, db):
    chat_id = update['message']['from']['id']
    data = {
        "chat_id" : receiver,
        "document" : update["message"]["document"]["file_id"],
    }
    if "caption" in update["message"]:
        data["caption"] = update["message"]["caption"]
    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(receiver, message_id):
            data["reply_to_message_id"] = cache.hget(receiver, message_id).decode()
    message = await send_request(session, data, SEND_DOCUMENT, f"Document sent from {chat_id} to {receiver}")
    cache_message_ids(receiver, update, message)

async def send_video(session, receiver, update, db):
    chat_id = update['message']['from']['id']
    info = await db.select_parameter("rate, language", f"chat_id = {chat_id}")
    sender_rating = info["rate"]
    lang = info["language"]
    if sender_rating > 20:
        video = update["message"]["video"]["file_id"]
        data = {
            "chat_id" : receiver,
            "video" : video,
        }
        if "caption" in update["message"]:
            data["caption"] = update["message"]["caption"]
        if "reply_to_message" in update["message"]:
            message_id = update["message"]["reply_to_message"]["message_id"]
            if cache.hexists(receiver, message_id):
                data["reply_to_message_id"] = cache.hget(receiver, message_id).decode()

        message = await send_request(session, data, SEND_VIDEO, f"Video sent from {chat_id} to {receiver}")
        cache_message_ids(receiver, update, message)
    else:
        data = {
            "chat_id": chat_id,
            "text" : texts["exceptions"]["not_kenough_rating"][lang]
        }
        await send_request(session, data, "sendMessage")

async def send_animation(session, receiver, update, db):
    chat_id = update['message']['from']['id']
    animation = update["message"]["animation"]["file_id"]
    data = {
        "chat_id" : receiver,
        "animation" : animation
    }
    if "caption" in update["message"]:
        data["caption"] = update["message"]["caption"]
    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(receiver, message_id):
            data["reply_to_message_id"] = cache.hget(receiver, message_id).decode()

    message = await send_request(session, data, SEND_ANIMATION, f"Animation sent from {chat_id} to {receiver}")
    cache_message_ids(receiver, update, message)

async def send_location(session, receiver, update, db):
    chat_id = update['message']['from']['id']
    latitude = update['message']['location']['latitude']
    longitude = update['message']['location']['longitude']
    data = {
        "chat_id" : receiver,
        'latitude' : latitude,
        'longitude' : longitude,        
    }
    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(receiver, message_id):
            data["reply_to_message_id"] = cache.hget(receiver, message_id).decode()

    message = await send_request(session, data, SEND_LOCATION, f"Location sent from {chat_id} to {receiver}")
    cache_message_ids(receiver, update, message)
    
async def send_video_note(session, receiver, update, db):
    chat_id = update['message']['from']['id']
    info = await db.select_parameter("rate, language", f"chat_id = {chat_id}")
    sender_rating = info["rate"]
    lang = info["language"]
    if sender_rating > 20:
        video_note = update["message"]["video_note"]["file_id"]
        data = {
            "chat_id" : receiver,
            "video_note" : video_note,
        }
        if "reply_to_message" in update["message"]:
            message_id = update["message"]["reply_to_message"]["message_id"]
            if cache.hexists(receiver, message_id):
                data["reply_to_message_id"] = cache.hget(receiver, message_id).decode()

        message = await send_request(session, data, SEND_VIDEONOTE, f"Video Note sent from {chat_id} to {receiver}")
        cache_message_ids(receiver, update, message)
    else:
        data = {
            "chat_id": chat_id,
            "text": texts["exceptions"]["not_kenough_rating"][lang]
        }
        await send_request(session, data, "sendMessage")

async def send_sticker(session, receiver, update, db):
    chat_id = update['message']['from']['id']
    data = {
        "chat_id" : receiver,
        "sticker" : update["message"]["sticker"]["file_id"]
    }
    if "reply_to_message" in update["message"]:
        message_id = update["message"]["reply_to_message"]["message_id"]
        if cache.hexists(receiver, message_id):
            data["reply_to_message_id"] = cache.hget(receiver, message_id).decode()
            
    message = await send_request(session, data, SEND_STICKER, f"Sticker sent from {chat_id} to {receiver}")
    cache_message_ids(receiver, update, message)

async def send_poll(session, receiver, update, db):
    chat_id = update['message']['from']['id']
    data = {
        "chat_id" : receiver,
        "question" : update["message"]["poll"]["question"],
        "options" : update["message"]["poll"]["options"],
        "is_anonymous" : True,
        "allows_multiple_answers" : update["message"]["poll"]["allows_multiple_answers"],
    }

    message = await send_request(session, data, SEND_POLL, f"Poll sent from {chat_id} to {receiver}")
    cache_message_ids(receiver, update, message)
