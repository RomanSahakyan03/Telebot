import copy
from utils import cache, send_request, rate_keyboard, settings_status_bar, del_pair, system_send_message, from_coords_to_name, sexes, main_keyboard,lang_keyboard, mbti_types, cancel_keyboard
from load_json import texts

async def join(session, chat_id, db):
    params = await db.select_parameter("*", f"chat_id = {chat_id}")
    lang = params["language"]
    if await db.check_all_except_some_columns_filled(chat_id):
        lat, lon = params["region_lat"], params["region_lon"]
        name = from_coords_to_name(lat, lon, lang)
        preferred_ages = params["preferred_ages"]
        types = params["TYPES"]
        sex_index = params["sexes"]

        # if no one selected <=> all types available
        if types == 0:
            types = 65535 

        num_bits = 16
        types_list = [f"{mbti_types[bit]}" for bit in range(num_bits) if (types >> bit) & 1]


        text = f"{texts['join'][lang]}\n"
        text += f"{texts['settings']['preferred_ages'][lang]}{preferred_ages}\n"
        text += f"{texts['settings']['region'][lang]}{name}\n"
        text += f"{texts['settings']['TYPES'][lang]}{', '.join(types_list)}\n"
        text += f"{texts['settings']['sexes'][lang]}{texts['keyboards']['sex_keyboard'][sexes[sex_index]][lang]}"
        keyboard = cancel_keyboard(lang, "waiting")

        # Send the message
        await system_send_message(session, chat_id, text, keyboard, "join page")
        cache.sadd("waiting_pool", chat_id)
    else:
        print(chat_id)
        await system_send_message(session, chat_id, texts["exceptions"]["do_not_join"][lang], None, "not joining error message")

async def settings(session, chat_id, db):
    params = await db.select_parameter("*", f"chat_id = {chat_id}")
    lang = params["language"]
    keyboard = {
    "inline_keyboard": [
        [{"text": texts["settings"]["menu_lang"][lang], "callback_data": "language"},
         {"text": texts["settings"]["menu_region"][lang], "callback_data": "region"}],
        [{"text": texts["settings"]["menu_type"][lang], "callback_data": "TYPE"},
        {"text": texts["settings"]["menu_types"][lang], "callback_data": "TYPES"},],
        [{"text": texts["settings"]["menu_age"][lang], "callback_data": "my_age"},
        {"text": texts["settings"]["menu_ages"][lang], "callback_data": "prefered_ages"},],
        [{"text": texts["settings"]["menu_sex"][lang], "callback_data": "sex"},
        {"text": texts["settings"]["menu_sexes"][lang], "callback_data": "sexes"}]
        ]}
    
    text = settings_status_bar(params)
                

    await system_send_message(session, chat_id, text, keyboard, "Settings")

# async define a function to handle the /about command
async def about(session, chat_id, db):
    lang = (await db.select_parameter("language", f"chat_id = {chat_id}"))["language"]
    data = {
        "chat_id" : chat_id,
        "photo" : "https://i.pinimg.com/474x/a1/2b/8e/a12b8ebbfa769903ac48ba27c6519e9d.jpg",
        "caption" : texts["about_page"][lang],
        "reply_markup" : main_keyboard(lang)
    }

    await send_request(session, data, "sendPhoto", f"About menu opened for {chat_id}")

# async define a function to handle the /start command
async def start(session, chat_id, db):
    print(chat_id)
    if await db.is_chat_id_exists(chat_id) is False:
        await db.insert_user(chat_id)
        text = "Hey there! Welcome to TypeTalk, the anonymous chatbot based on MBTI personality types. " \
       "To get started, please select your preferred language from the options below:"
        data = {
            "chat_id" : chat_id,
            "photo" : "AgACAgIAAxkBAAIMG2R669446fymMURznmwSEwwLxzBIAAKWzDEb9zTZS1nd7Nbv63VJAQADAgADeAADLwQ",
            "caption" : text,
            "reply_markup" : lang_keyboard
        }
        await send_request(session, data, "sendPhoto", f"Start menu opened for {chat_id}")
    else:
        await join(session, chat_id, db)

async def stop(session, chat_id1, db):
    if cache.hexists('pairs', chat_id1):
        chat_id2 = cache.hget('pairs', chat_id1).decode()
        lang1 = (await db.select_parameter("language", f"chat_id = {chat_id1}"))["language"]
        lang2 = (await db.select_parameter("language", f"chat_id = {chat_id2}"))["language"]
        
        await system_send_message(session, chat_id1, texts["ended conversation"][lang1], main_keyboard(lang1))
        await system_send_message(session, chat_id2, texts["ended conversation"][lang2], main_keyboard(lang2))

        rate_keyboard_copy = copy.deepcopy(rate_keyboard)

        rate_keyboard_copy["inline_keyboard"][0][0]["callback_data"] = f"like_{chat_id2}"
        rate_keyboard_copy["inline_keyboard"][0][1]["callback_data"] = f"dislike_{chat_id2}"
        await system_send_message(session, chat_id1, texts["rating"]["rate_op"][lang1], rate_keyboard_copy)

        rate_keyboard_copy["inline_keyboard"][0][0]["callback_data"] = f"like_{chat_id1}"
        rate_keyboard_copy["inline_keyboard"][0][1]["callback_data"] = f"dislike_{chat_id1}"
        await system_send_message(session, chat_id2, texts["rating"]["rate_op"][lang2], rate_keyboard_copy)

        del_pair(chat_id1)

async def next(session, chat_id1, db):
    await stop(session, chat_id1, db)
    await join(session, chat_id1, db)

async def shareprofile(session, chat_id, username, db):
    lang = (await db.select_parameter("language", f"chat_id = {chat_id}"))["language"]
    if cache.hexists('pairs', chat_id):
        if username:
            receiver = cache.hget('pairs', chat_id).decode()
            text = "Here is the @" + username + '.'
            await system_send_message(session, receiver, text, None,'Shareprofile message')
        else:
            await system_send_message(session, chat_id, texts["exceptions"]["no_username"][lang], None, "NoShareprofile message")