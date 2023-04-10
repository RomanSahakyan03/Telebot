import sqlite3

class BotDB:
    
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_COLNAMES, check_same_thread=False)
        self.cursor = self.conn.cursor()
    
    def create_table(self, columns):
        columns_str = ", ".join(columns)
        create_table_query = f"CREATE TABLE IF NOT EXISTS users ( {columns_str} );"
        self.cursor.execute(create_table_query)
        self.conn.commit()
    
    def insert_user_data(self, data_dict):
        columns = ", ".join(data_dict.keys())
        values = ", ".join(["?" for i in range(len(data_dict))])
        insert_query = f"INSERT INTO users ({columns}) VALUES ({values})"
        self.cursor.execute(insert_query, tuple(data_dict.values()))
        self.conn.commit()

    def extract_data(self, chat_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (chat_id,))
        user_params = dict(zip([column[0] for column in self.cursor.description], self.cursor.fetchone()))
        return user_params

    def check_exist(self, chat_id):
        select_query = f"SELECT * FROM users WHERE chat_id = ?"
        self.cursor.execute(select_query, (chat_id,))
        row = self.cursor.fetchone()
        if row is None:
            return False
        for value in row:
            if value is None:
                return False
        return True
    
    def update_user_data(self, data_dict, condition):
        set_clause = ", ".join([f"{key} = ?" for key in data_dict])
        update_query = f"UPDATE users SET {set_clause} WHERE {condition}"
        self.cursor.execute(update_query, tuple(data_dict.values()))
        self.conn.commit()

    def select_parameter(self, columns="*", condition=""):
        select_query = f"SELECT {columns} FROM users WHERE {condition}" if condition else f"SELECT {columns} FROM users"
        self.cursor.execute(select_query)
        return self.cursor.fetchall()
    
    def delete_user(self, chat_id):
        delete_query = f"DELETE FROM users WHERE chat_id = {chat_id}"
        self.cursor.execute(delete_query)
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()