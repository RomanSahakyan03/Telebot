import re
import os
from db import BotDB
from edit_data import *
from send_data import *
from utils import *
from commands import *
from calback_actions import *
from matching_system import matching_system
import asyncio
import aiohttp
from load_json import texts
   
processed_offset = 0
# Can be 'age_collect', 'age_interval', 'region_collect'
async def state_handler(session, update, db, state):
    chat_id = update['message']['from']['id']
    lang = (await db.select_parameter("language", f"chat_id = {chat_id}"))["language"]
    condition = f'chat_id = {chat_id}'
    if state == 'age_collect':
        if "message" not in update or "text" not in update["message"]:
            await system_send_message(session, chat_id, texts["exceptions"]["invalid_data"][lang], None, "age set error")
            return
        text = update['message']['text']
        pattern = r"^(\d+)$"
        match = re.match(pattern, text)
        if match and int(text) < 100:
            if int(text) < 12:
                await system_send_message(session, chat_id, texts["exceptions"]["not_enough_age"][lang], None, 'error setage message')
            else:
                cache.srem("age_collect", chat_id)
                await db.upsert_user_data({'age' : text}, condition)
                await system_delete_message(session, chat_id, update['message']['message_id'])
                await system_delete_message(session, chat_id, cache.hget("waiting_message", chat_id).decode())
                cache.hdel("waiting_message", chat_id)
                await system_send_message(session, chat_id, texts["success"]["age_set"][lang], None, 'setage')
        else:
            await system_send_message(session, chat_id, texts["exceptions"]["invalid_data"][lang], None, 'error setage message')
            return
    elif state == 'age_interval':
        if "message" not in update or "text" not in update["message"]:
            await system_send_message(session, chat_id, texts["exceptions"]["invalid_data"][lang], None, "age set error")
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
                await system_send_message(session, chat_id, texts["exceptions"]["low_age_alert"][lang], None, "Pedophil error")
                return
            await db.upsert_user_data({'preferred_ages' : text}, condition)
            cache.srem("age_interval", chat_id)
            await system_delete_message(session, chat_id, update['message']['message_id'])
            await system_delete_message(session, chat_id, cache.hget("waiting_message", chat_id).decode())
            cache.hdel("waiting_message", chat_id)
            await system_send_message(session, chat_id, texts["success"]["age_set"][lang], None, 'setage interval')
        else:
            await system_send_message(session, chat_id, texts["exceptions"]["invalid_data"][lang], None, "age set error")
            return
    elif state == 'region_collect':
        if "message" not in update or "location" not in update["message"]:
            await system_send_message(session, chat_id, texts["exceptions"]["invalid_data"][lang], None, "location data error")
            return
        latitude = update['message']['location']['latitude']
        longitude = update['message']['location']['longitude']
        await db.upsert_user_data({'region_lat' : latitude}, condition)
        await db.upsert_user_data({'region_lon' : longitude}, condition)
        await system_delete_message(session, chat_id, update['message']['message_id'])
        await system_delete_message(session, chat_id, cache.hget("waiting_message", chat_id).decode())
        cache.hdel("waiting_message", chat_id)
        await system_send_message(session, chat_id, texts["success"]["location_set"][lang], None, 'coords')

    cache.hdel('state', chat_id)
    await settings(session, chat_id, db)

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

async def callback_handler(session, update, db):
    callback_data = update['callback_query']['data']
    chat_id = update['callback_query']['from']['id']
    message_id = update['callback_query']['message']['message_id']
    lang = (await db.select_parameter("language", f"chat_id = {chat_id}"))["language"]
    if callback_data in callback_actions:
        await callback_actions[callback_data](session, chat_id, message_id, lang, db)
        return
    for pattern, action in action_patterns.items():
        if callback_data.endswith(pattern):
            await action(session, chat_id, message_id, lang, callback_data, db)
            return
    if re.match(r'like_(\d+)', callback_data):
        await like(session, chat_id, message_id, lang, callback_data, db)
    elif re.match(r'dislike_(\d+)', callback_data):
        await dislike(session, chat_id, message_id, lang, callback_data, db)
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

async def update_handler(session, update, db):
    if 'message' in update:
        chat_id = update['message']['from']['id']
        if cache.sismember("waiting_pool", chat_id):
            return
        if cache.hexists('state', chat_id):
                await state_handler(session, update, db, cache.hget('state', chat_id).decode())
                return
        if 'text' in update['message']:
            text = update['message']['text']
            if text == '/shareprofile':
                username = update['message']['from']['username'] if 'username' in update['message']['from'] else None
                await shareprofile(session, chat_id, username, db)
                return
            if text in COMMANDS:
                await COMMANDS[text](session, chat_id, db)
                return
        for keyword, handler in message_handlers.items():
            if keyword in update['message'] and cache.hexists('pairs', chat_id):
                pair = cache.hget('pairs', chat_id).decode()
                print(f"sending {keyword} from {chat_id} to {pair}.")
                await handler(session, pair, update, db)
    elif 'edited_message' in update:
        if 'text' in update['edited_message']:
            await edit_message(session, update)
        else:
            await edit_media(session, update)
    elif 'callback_query' in update and 'data' in update['callback_query']:
        await callback_handler(session, update, db)

async def get_updates(session, db):
    proccessed_offset = 0
    get_updates_url = f"{API_LINK}/getUpdates"
    
    while True:
        try:
            async with session.get(get_updates_url, params={'offset': proccessed_offset}) as response:
                if response.status == 200:
                    data = await response.json()
                    updates = data['result']
                    for update in updates:
                        await update_handler(session, update, db)
                        proccessed_offset = max(proccessed_offset, update['update_id'] + 1)
            await asyncio.sleep(0.75)
        except Exception as e:
            print(f'Error occurred: {e}')
            await asyncio.sleep(5)

async def main():
    # Get the absolute path of the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the absolute texts path
    db_path = os.path.join(current_dir, 'userdata.db')

    db = BotDB(db_path)
    await db.connect()

    async with aiohttp.ClientSession() as session:
        try:
            update_task = asyncio.create_task(get_updates(session, db))
            matching_task = asyncio.create_task(matching_system(session, db))
            await asyncio.gather(update_task, matching_task)
        except KeyboardInterrupt:
            pass
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(main())