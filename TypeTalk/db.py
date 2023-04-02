import sqlite3

class BotDB:
    
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_COLNAMES, check_same_thread=False)
        self.cursor = self.conn.cursor()
    
    def create_table(self, table_name, columns):
        columns_str = ", ".join(columns)
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})"
        self.cur.execute(create_table_query)
        self.conn.commit()
    
    def insert_data(self, table_name, data_dict):
        columns = ", ".join(data_dict.keys())
        values = ", ".join(["?" for i in range(len(data_dict))])
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
        self.cursor.execute(insert_query, tuple(data_dict.values()))
        self.conn.commit()
    
    def update_data(self, table_name, data_dict, condition):
        set_clause = ", ".join([f"{key} = ?" for key in data_dict])
        update_query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
        self.cur.execute(update_query, tuple(data_dict.values()))
        self.conn.commit()

    def select_data(self, table_name, columns="*", condition=""):
        select_query = f"SELECT {columns} FROM {table_name} WHERE {condition}" if condition else f"SELECT {columns} FROM {table_name}"
        self.cur.execute(select_query)
        return self.cur.fetchall()
    
    def delete_user(self, user_id):
        delete_query = f"DELETE FROM users WHERE user_id = {user_id}"
        self.cur.execute(delete_query)
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()