import pymysql

conn = pymysql.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="Aa123456",
    database="nutrition_supplement_db"
)
print("连接成功")
print("1")
conn.close()
