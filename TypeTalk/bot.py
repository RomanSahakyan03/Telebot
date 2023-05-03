from db import BotDB

db = BotDB("./TypeTalk/userdata.db")

db.create_table('users', [
    'id INTEGER PRIMARY KEY AUTOINCREMENT', 
    'chat_id INTEGER', 
    'language TEXT',
    'TYPE INTEGER(1)', 
    'TYPES INTEGER(2) DEFAULT 0', 
    'region_lat REAL',
    'region_lon REAL',
    'age INTEGER(1)', 
    'age_interval TEXT',
    'rate INTEGER(1) DEFAULT 5',
    'gender TEXT',
    'preferred_genders TEXT'
])