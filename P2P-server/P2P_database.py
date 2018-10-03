import sqlite3 
import os

db_conn = None


def db_init() -> bool:
    global db_conn
    db_conn = sqlite3.connect('Chinook_Sqlite.sqlite')
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(sql) FROM sqlite_master WHERE type = 'table' AND name = 'clients';")
    if cur.fetchone()[0] == 0:
        cur.execute('CREATE TABLE clients (login STRING PRIMARY KEY UNIQUE NOT NULL, password STRING, ip STRING);')
        db_conn.commit()
        if cur.rowcount == 0:
            return False

    cur.execute("SELECT COUNT(sql) FROM sqlite_master WHERE type = 'table' AND name = 'friends';")
    if cur.fetchone()[0] == 0:
        cur.execute('CREATE TABLE friends ( client STRING PRIMARY KEY, friend STRING);')
        db_conn.commit()
        if cur.rowcount == 0:
            return False
    cur.close()
    return True


def db_fini():
    global db_conn
    db_conn.close()
    db_conn = None


# 1.1.
def db_add_client(login: str, password: str, ip: str)->bool:
    global db_conn
    cur = db_conn.cursor()
    cur.execute("INSERT INTO clients (login, password, ip) VALUES (?, ?, ?);", (login, password, ip))
    status = cur.rowcount == 1
    cur.close()
    return status


# 2.1.
def db_del_client(login: str)->bool:
    global db_conn
    cur = db_conn.cursor()
    cur.execute(" DELETE FROM clients WHERE login  = ? ;", (login,))
    status = cur.rowcount == 1
    cur.execute("DELETE FROM friends WHERE client = %s OR friend = ? ;", (login, login))
    cur.close()
    return status


# 3.1.
def db_update_password(login: str, new_password: str)->bool:
    global db_conn
    cur = db_conn.cursor()
    cur.execute("UPDATE clients SET password = %s WHERE login = ? ;", (new_password, login))
    status = cur.rowcount == 1
    cur.close()
    return status


# 4.1.
def db_update_ip(login: str, ip: str)->bool:
    global db_conn
    cur = db_conn.cursor()
    cur.execute("UPDATE clients SET ip = %s WHERE login = ? ;", (ip, login))
    status = cur.rowcount == 1
    cur.close()
    return status


# 1.2.
# Нужно ли другу кидать клиента?
def db_add_friend(login_cl: str, login_fr: str)->bool:
    global db_conn
    cur = db_conn.cursor()
    cur.execute("INSERT INTO friends (client, friend) VALUES (?, ?);", (login_cl, login_fr))
    status = cur.rowcount == 1
    cur.close()
    return status


# 2.2.
# В обе стороны или в одну?
def db_del_friend(login_cl: str, login_fr: str)->bool:
    global db_conn
    cur = db_conn.cursor()
    cur.execute("DELETE FROM friends WHERE client = ? AND friend = ?;", (login_cl, login_fr))
    status = cur.rowcount == 1
    cur.close()
    return status


# 3.2.
def db_search_friends(login: str)->list:
    global db_conn
    cur = db_conn.cursor()
    cur.execute("SELECT friend FROM friends WHERE client = ? ;", (login,))
    result = cur.fetchall()
    cur.close()
    return result


# 1.3.
def db_search_password(login: str)->str:
    global db_conn
    cur = db_conn.cursor()
    cur.execute("SELECT password FROM clients WHERE login = ? ;", (login,))
    result = cur.fetchone()
    cur.close()
    if result is None:
        return '-'
    return result[0]


# 2.3.
def db_search_ip(login: str)->str:
    global db_conn
    cur = db_conn.cursor()
    cur.execute("SELECT ip FROM clients WHERE login = ? ;", (login,))
    result = cur.fetchone()
    cur.close()
    if result is None:
        return '0.0.0.0'
    return result[0]


status = db_init()
print('db_init = ', status)
status = db_add_client('login', 'password', '222.222.222.222')
print('db_add_client = ', status)

passwd = db_search_password('login')
print(passwd)
passwd = db_search_password('fghjk')
print(passwd)

ip_now = db_search_ip('login')
print(ip_now)
ip_now = db_search_ip('fghjk')
print(ip_now)
#db_search_IP()
#db_update_password()
#db_update_IP()
#db_search_friends()

db_fini()

os.remove('Chinook_Sqlite.sqlite')