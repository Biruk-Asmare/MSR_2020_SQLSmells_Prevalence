import pymysql
# ===========================
# configuration
# ==========================

class DB:
    def __init__(self):
        self.dbhost = ''
        self.dbuser = ''
        self.dbpwd = ''
       
        self.dbname = '' 
    def escape_string(self,str):
        return pymysql.escape_string(str)
    def set_db_name(self,str):
        self.dbname=str
    def connect_mysql(self):
        try:
            connection = pymysql.connect(self.dbhost, self.dbuser, self.dbpwd, self.dbname)
            cursor = connection.cursor()
            return cursor, connection
        except Exception as ex:
            print("Exception: ",ex)
            quit()

    def execute_query(self, cursor, query, conn):
        try:
            res = cursor.execute(query)
            conn.commit()
            if res!=1:
                print(res)
                return res
            return ""
        except Exception as ex:
            #print("Exception: ",ex)
            #print(query)
            return ex
    def execute_read_query(self, cursor, query):
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            return rows
        except Exception as ex:
            return ex


    def close_connection(self, conn):
        try:
            conn.close()
        except:
            print("already closed")
