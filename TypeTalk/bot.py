from db import BotDB

db = BotDB("./userdata.db")
db.create_table('users', ['id INTEGER PRIMARY KEY AUTOINCREMENT', 'chat_id INTEGER', 'language TEXT',
                          'TYPE INTEGER(1)', 'TYPES INTEGER(2)', 'region TEXT',
                          'age INTEGER(1)', 'min_prefered_age INTEGER(1)', 'max_prefered_age INTEGER(1)'])

db.create_table('users', ['id INTEGER PRIMARY KEY AUTOINCREMENT', 
                          'chat_id INTEGER', 
                          'language TEXT',
                          'TYPE INTEGER(1)', 
                          'TYPES INTEGER(2)', 
                          'region_lat TEXT',
                          'region_lon TEXT',
                          'age INTEGER(1)', 
                          'age_interval TEXT',
                          'rate INTEGER(1)',
                          'premium INTEGER(1)'])

db.create_table('gender_preferences', ['id INTEGER PRIMARY KEY AUTOINCREMENT', 'chat_id INTEGER' ,
                                        'gender TEXT' , 'preferred_genders TEXT', 
                                        'FOREIGN KEY(chat_id) REFERENCES users(chat_id)'])