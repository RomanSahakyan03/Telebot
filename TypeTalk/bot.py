from db import BotDB

db = BotDB("/dbs/userdata.db")
db.create_table('users', ['id INTEGER PRIMARY KEY', 'chat_id INTEGER', 'language TEXT',
                          'TYPE INTEGER(1)', 'TYPES INTEGER(2)', 'region TEXT',
                          'age INTEGER(1)', 'min_prefered_age INTEGER(1)', 'max_prefered_age INTEGER(1)',
                          ''])

genders = BotDB('/dbs/genders.db')
genders.create_table('gender_preferences', ['id INTEGER PRIMARY KEY', 'user_id INTEGER' ,
                                            'gender TEXT' , 'preferred_genders TEXT', 
                                            'FOREIGN KEY(user_id) REFERENCES users(user_id)'])