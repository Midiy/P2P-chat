import sqlite3;

db_conn

def db_init():
    db_conn = sqlite3.connect('Chinook_Sqlite.sqlite')
    cur = db_conn.cursor()
    cur.execute("SHOW DATABASES")
    find_cl = False
    find_fr = False
    #
    for x in cur:
        if x[0] == 'Client':
            find_cl=True
        if x[0] == 'Friend':
            find_fr = True
    #
    if find_cl == False :
        cur.execute('CREATE TABLE clients (login STRING PRIMARY KEY UNIQUE NOT NULL, password STRING, ip STRING)')
        db_conn.commit()
        if cur.rowcount == 0 :
            return False
    if find_fr == False:
        cur.execute('CREATE TABLE friends ( client STRING PRIMARY KEY, friend STRING)')
        db_conn.commit()
        if cur.rowcount == 0:
            return False
    cur.close()
    return True

def db_fini():
    db_conn.close()


#1.1.
def db_add_client(login : str, password : str, IP : str ):
    cur = db_conn.cursor()
    cur.execute("INSERT INTO clients (login, password, ip) VALUES (%s, %s, %s)", (login, password, ip))
    status = cur.rowcount == 1
    cur.close()
    return status

#2.1.
def db_del_client(login : str):
    cur = db_conn.cursor()
    cur.execute(" DELETE FROM clients WHERE login  = % s", (login))
    status = cur.rowcount == 1
    cur.execute("DELETE FROM friends WHERE client = %s OR friend = %s", (login, login))
    cur.close()
    return status

#3.1.
def db_update_password(login : str, new_password : str):
    cur = db_conn.cursor()
    cur.execute("UPDATE clients SET password = %s WHERE login = %s", (new_password, login))
    status = cur.rowcount == 1
    cur.close()
    return status

#4.1.
def db_update_IP(login: str, IP: str):
    cur = db_conn.cursor()
    cur.execute("UPDATE clients SET ip = %s WHERE login = %s", (IP, login))
    status = cur.rowcount == 1
    cur.close()
    return status

#1.2.
#Нужно ли другу кидать клиента?
def db_add_friend(login_cl : str, login_fr : str):
    cur = db_conn.cursor()
    cur.execute("INSERT INTO friends (client, friend) VALUES (%s, %s)", (login_cl, login_fr))
    status = cur.rowcount == 1
    cur.close()
    return status

#2.2.
# В обе стороны или в одну?
def db_del_friend(login_cl : str, login_fr : str):
    cur = db_conn.cursor()
    cur.execute("DELETE FROM friends WHERE client = %s AND friend = %s", (login_cl, login_fr))
    status = cur.rowcount == 1
    cur.close()
    return status

#3.2.
def db_search_friends(login : str):
    cur = db_conn.cursor()
    cur.execute("SELECT friend FROM friends WHERE client = %s", (login))
    result = cur.fetchall()
    cur.close()
    return result

#1.3.
def db_search_password (login : str):
    cur = db_conn.cursor()
    cur.execute("SELECT password FROM clients WHERE login = %s", (login))
    result = cur.fetchone()
    cur.close()
    return result

#2.3.
def db_search_IP(login : str):
    cur = db_conn.cursor()
    cur.execute("SELECT ip FROM clients WHERE login = %s", (login))
    result = cur.fetchone()
    cur.close()
    return result
