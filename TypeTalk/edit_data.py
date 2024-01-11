from utils import EDIT_MESSAGE_URL, EDIT_MEDIA_URL, cache

async def edit_message(session, update):
    message_id = update["edited_message"]["message_id"]
    receiver = cache.hget('pairs', update["edited_message"]["from"]["id"]).decode()
    message_key = cache.hget(str(receiver), message_id).decode()
    
    data = {
        'chat_id' : receiver,
        'message_id' : message_key,
        'text' : update['edited_message']['text']
    }
    
    async with session.post(EDIT_MESSAGE_URL, json=data) as response:
        if response.status == 200:
            print(f"Edited message in {receiver} successfully")
        else:
            print(f"Failed to edit message for {receiver}")

async def edit_media(session, update):
    message_id = update["edited_message"]["message_id"]
    receiver = cache.hget('pairs', update["edited_message"]["from"]["id"]).decode()
    message_key = cache.hget(str(receiver), message_id).decode()
    
    data = {
        'chat_id': receiver,
        'message_id': message_key,
        'media': {}
    }
    
    if 'photo' in update['edited_message']:
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
        data['media']['caption'] = update['edited_message']['caption']
    
    async with session.post(EDIT_MEDIA_URL, json=data) as response:
        if response.status == 200:
            print(f"Edited media in {receiver} successfully")
        else:
            print(f"Failed to edit media for {receiver}")