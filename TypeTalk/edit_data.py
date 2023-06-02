import requests
import redis
import os
cache = redis.Redis(host='localhost', port=6379, db=0)
telegram_token = os.environ.get('TELEGRAM_API_TOKEN')
API_LINK = f"https://api.telegram.org/bot{telegram_token}"
EDIT_MESSAGE_URL = f"{API_LINK}/editMessageText"
EDIT_CAPTION_URL = f"{API_LINK}/editMessageCaption"
EDIT_MEDIA_URL = f"{API_LINK}/editMessageMedia"


def edit_message(update):
    message_id = update["edited_message"]["message_id"]
    receiver = cache.hget('pairs', update["edited_message"]["from"]["id"]).decode()
    data = {
        'chat_id' : receiver,
        'message_id' : cache.hget(str(receiver), message_id).decode(),
        'text' : update['edited_message']['text']
    }
    response = requests.post(EDIT_MESSAGE_URL, json=data)
    if response.ok:
        print(f"edited message in {receiver} successfully")
    else:
        print(f"failed to edited message for {receiver}")

def edit_media(update):
    message_id = update["edited_message"]["message_id"]
    receiver = cache.hget('pairs', update["edited_message"]["from"]["id"]).decode()
    data = {
        'chat_id' : receiver,
        'message_id' : cache.hget(str(receiver), message_id).decode(),
        'media' : {}
    }
    if 'photo' in update['edited_message']:
        print('in photo')
        data['media']['type'] = 'photo'
        data['media']['media'] = update['edited_message']['photo'][-1]['file_id']
    elif 'video' in update['edited_message']:
        data['media']['type'] = 'video'
        data['media']['media'] = update['edited_message']['video']['file_id']
    elif 'animation' in update['edited_message']:
        data['media']['type'] = 'animation'
        data['media']['media'] = update['edited_message']['animation']['file_id']
    elif 'document' in update['edited_message']:
        data['media']['type'] = 'document'
        data['media']['media'] = update['edited_message']['document']['file_id']
    elif 'audio' in update['edited_message']:
        data['media']['type'] = 'audio'
        data['media']['media'] = update['edited_message']['voice']['file_id']

    if 'caption' in update['edited_message']:
        print('in caption')
        data['media']['caption'] = update['edited_message']['caption']
    print(data['media'])
    print(data['message_id'])
    response = requests.post(EDIT_MEDIA_URL, json=data)
    if response.ok:
            print(f"edited media in {receiver} successfully")
    else:
            print(f"failed to edited media for {receiver}")