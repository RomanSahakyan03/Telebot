import re
from utils import cache, system_delete_message, sexes, system_edit_message, system_send_message, system_edit_types_message, main_keyboard,lang_keyboard, mbti_indexes, mbti_types, get_mbti_types_keyboard, cancel_keyboard, sex_keyboard, preferred_sexes_keyboard
from commands import settings
from load_json import texts


async def lang_setting(session, chat_id, message_id, lang, db):
    await system_delete_message(session, chat_id, message_id)
    await system_send_message(session, chat_id, texts["configuration_menus"]["lang_settings"][lang], lang_keyboard, 'Language selection menu')


async def TYPE_setting(session, chat_id, message_id, lang, db):
    await system_delete_message(session, chat_id, message_id)
    keyboard = {
    "inline_keyboard": [
        [{"text": mbti_types[bit], "callback_data": mbti_types[bit] + "_m"} for bit in range(row * 4, (row + 1) * 4) if bit < 16] for row in range((16 - 1) // 4 + 1)
    ]}

    await system_send_message(session, chat_id, texts["configuration_menus"]["type_settings"][lang], keyboard, 'MBTI type selection menu')


async def TYPES_setting(session, chat_id, message_id, lang, db):
    x = (await db.select_parameter("TYPES", f"chat_id = {chat_id}"))['TYPES']
    keyboard = get_mbti_types_keyboard(x)
    await system_send_message(session, chat_id, texts["configuration_menus"]["types_settings"][lang], keyboard, 'MBTI preffered types selection menu')


async def handle_region(session, chat_id, message_id, lang, db):
    await system_delete_message(session, chat_id, message_id)
    how_to = {"text": texts["location"]["idkhow_button"][lang], "callback_data": "idkhow"}
    reset_b = {"text": texts["location"]["reset_button"][lang], "callback_data": "resloc"}
    keyboard = cancel_keyboard(lang, "state")
    keyboard["inline_keyboard"][0].append(how_to)
    keyboard["inline_keyboard"][0].append(reset_b)
    content = await system_send_message(session, chat_id, texts["location"]["location_handle"][lang], keyboard, "set location")
    cache.hset("waiting_message", chat_id, content["result"]["message_id"])
    cache.hset('state', chat_id, 'region_collect')

async def handle_my_age(session, chat_id, message_id, lang, db):
    await system_delete_message(session, chat_id, message_id)
    content = await system_send_message(session, chat_id, texts["configuration_menus"]["age_handle"][lang], cancel_keyboard(lang, "state"), "set age menu")
    cache.hset("waiting_message", chat_id, content["result"]["message_id"])
    cache.hset('state', chat_id, 'age_collect')

async def handle_preferred_ages(session, chat_id, message_id, lang, db):
    await system_delete_message(session, chat_id, message_id)
    content = await system_send_message(session, chat_id, texts["configuration_menus"]["ages_handle"][lang], cancel_keyboard(lang, "state"), "set age interval menu")
    cache.hset("waiting_message", chat_id, content["result"]["message_id"])
    cache.hset('state', chat_id, 'age_interval')

async def handle_my_sex(session, chat_id, message_id, lang, db):
    await system_delete_message(session, chat_id, message_id)
    await system_send_message(session, chat_id, texts["configuration_menus"]["sex_settings"][lang], sex_keyboard(lang), "set sex")

async def handle_preferred_sexes(session, chat_id, message_id, lang, db):
    await system_delete_message(session, chat_id, message_id)
    await system_send_message(session, chat_id, texts["configuration_menus"]["sexes_settings"][lang], preferred_sexes_keyboard(lang), "set preferred sexes")

async def handle_clall(session, chat_id, message_id, lang, db):
    await db.upsert_user_data({"TYPES": 0}, f"chat_id = {chat_id}")
    await system_edit_types_message(session, chat_id, message_id, 0, lang)

async def handle_cancel_waiting(session, chat_id, message_id, lang, db):
    await system_delete_message(session, chat_id, message_id)
    if cache.sismember('waiting_pool', chat_id):
        cache.srem('waiting_pool', chat_id)
        await system_send_message(session, chat_id, texts["cancel_waiting"][lang], main_keyboard(lang), "waiting cancled message")

async def idkhow(session, chat_id, message_id, lang, db):
    i_know = {"text": texts["location"]["close"][lang], "callback_data": "iknow"}
    keyboard = cancel_keyboard(lang, "state")
    keyboard["inline_keyboard"][0].append(i_know)
    await system_edit_message(session, chat_id, message_id, texts["location"]["idkhow"][lang], keyboard)

async def iknow(session, chat_id, message_id, lang, db):
    idkhow = {"text": texts["location"]["idkhow_button"][lang], "callback_data": "idkhow"}
    keyboard = cancel_keyboard(lang, "state")
    keyboard["inline_keyboard"][0].append(idkhow)
    await system_edit_message(session, chat_id, message_id, texts["location"]["location_handle"][lang], keyboard)

async def handle_cancel_state(session, chat_id, message_id, lang, db):
    await system_delete_message(session, chat_id, message_id)
    if cache.hexists('state', chat_id):
        cache.hdel('state', chat_id)
        await system_send_message(session, chat_id, texts["cancel_state"][lang], main_keyboard(lang), "state cancled message")
    await settings(session, chat_id, db)

async def reset_location(session, chat_id, message_id, lang, db):
    await system_delete_message(session, chat_id, message_id)
    condition = f'chat_id = {chat_id}'
    await db.upsert_user_data({'region_lat' : None}, condition)
    await db.upsert_user_data({'region_lon' : None}, condition)
    content = await system_send_message(session, chat_id, texts["location"]["location_reset"][lang])
    cache.hdel('state', chat_id, 'region_collect')
    await settings(session, chat_id, db)

# Handle unsupported callback_data values
async def handle_unsupported_callback(update):
    print(f"Unsupported callback_data: {update['callback_query']['data']}")


# ------- handling settings -------  

async def change_type(session, chat_id, message_id, lang, mbti_type, db):
    mbti_type = mbti_type[:-2]
    index = mbti_indexes[mbti_type]
    condition = f'chat_id = {chat_id}'

    await db.upsert_user_data({'TYPE': index}, condition)
    await system_delete_message(session, chat_id, message_id)
    await system_send_message(session, chat_id, texts["success"]["type_set"][lang])
    await settings(session, chat_id, db)

async def change_p_types(session, chat_id, message_id, lang, mbti_type, db):
    mbti_type = mbti_type[:-2]
    condition = f'chat_id = {chat_id}'
    mask = 1 << mbti_indexes[mbti_type]
    current_types = (await db.select_parameter('TYPES', condition))['TYPES']
    new_types = (current_types & ~mask) | (mask & ~current_types)
    await db.upsert_user_data({'TYPES': new_types}, condition)
    await system_edit_types_message(session, chat_id, message_id, new_types, lang)

async def change_sex(session, chat_id, message_id, lang, sex, db):
    sex = sex[:-6]
    condition = f'chat_id = {chat_id}'
    sex_num = sexes.index(sex)
    
    await db.upsert_user_data({'sex': sex_num}, condition)
    await system_delete_message(session, chat_id, message_id)
    await system_send_message(session, chat_id, texts["success"]["sex_set"][lang])
    await settings(session, chat_id, db)

async def change_p_sex(session, chat_id, message_id, lang, psex, db):
    psex = psex[:-13]
    condition = f'chat_id = {chat_id}'
    sexes_num = sexes.index(psex)

    await db.upsert_user_data({'sexes': sexes_num}, condition)
    await system_delete_message(session, chat_id, message_id)
    await system_send_message(session, chat_id, texts["success"]["sexes_set"][lang])
    await settings(session, chat_id, db)

async def handle_language(session, chat_id, message_id, lang, callback_data, db):
    await system_delete_message(session, chat_id, message_id)
    await db.upsert_user_data({"language": callback_data}, f"chat_id = {chat_id}")
    await system_send_message(session, chat_id, texts["success"]["language_set"][callback_data])
    await settings(session, chat_id, db)

async def like(session, chat_id1, message_id, lang, callback_data, db):
    match = re.match(r'like_(\d+)', callback_data)
    chat_id2 = match.group(1)
    rating = (await db.select_parameter("rate", f"chat_id = {chat_id2}"))["rate"]
    new_rating = min(rating + 1, 50)
    await db.upsert_user_data({"rate" : new_rating}, f"chat_id = {chat_id2}")
    await system_edit_message(session, chat_id1, message_id, texts["rating"]["tanks_rating"][lang], None, "rating")

async def dislike(session, chat_id1, message_id, lang, callback_data, db):
    match = re.match(r'dislike_(\d+)', callback_data)
    chat_id2 = match.group(1)
    rating = (await db.select_parameter("rate", f"chat_id = {chat_id2}"))["rate"]
    new_rating = max(rating - 1, 0)
    await db.upsert_user_data({"rate" : new_rating}, f"chat_id = {chat_id2}")
    await system_edit_message(session, chat_id1, message_id, texts["rating"]["tanks_rating"][lang], None, "rating")