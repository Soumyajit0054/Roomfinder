import mysql.connector
from config import DB_CONFIG


def get_db_connection():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"]
    )


def query_all(sql, params=None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(sql, params or ())
        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def query_one(sql, params=None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(sql, params or ())
        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def execute_query(sql, params=None):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(sql, params or ())
        connection.commit()
        return cursor.lastrowid

    finally:
        cursor.close()
        connection.close()