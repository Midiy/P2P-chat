import sqlite3 
import os


class DataBaseServer():
    _db_conn = None

    def db_init(self) -> bool:
        self._db_conn = sqlite3.connect('Chinook_Sqlite.sqlite')
        cur = self._db_conn.cursor()
        cur.execute("SELECT COUNT(sql) FROM sqlite_master WHERE type = 'table' AND name = 'clients';")
        if cur.fetchone()[0] == 0:
            cur.execute('CREATE TABLE clients (login STRING PRIMARY KEY UNIQUE NOT NULL, password STRING, ip STRING);')
            self._db_conn.commit()
            if cur.rowcount == 0:
                return False

    def __del__(self):
        if not (self._db_conn is None):
            self._db_conn.close()

    # 1.1.
    def db_add_client(self, login: str, password: str, ip: str)->bool:
        cur = self._db_conn.cursor()
        cur.execute("INSERT INTO clients (login, password, ip) VALUES (?, ?, ?);", (login, password, ip))
        _status = cur.rowcount == 1
        cur.close()
        return _status

    # 2.1.
    def db_del_client(self, login: str)->bool:
        cur = self._db_conn.cursor()
        cur.execute(" DELETE FROM clients WHERE login  = ? ;", (login,))
        _status = cur.rowcount == 1
        cur.execute("DELETE FROM friends WHERE client = %s OR friend = ? ;", (login, login))
        cur.close()
        return _status

    # 3.1.
    def db_update_password(self, login: str, new_password: str)->bool:
        cur = self._db_conn.cursor()
        cur.execute("UPDATE clients SET password = %s WHERE login = ? ;", (new_password, login))
        _status = cur.rowcount == 1
        cur.close()
        return _status

    # 4.1.
    def db_update_ip(self, login: str, ip: str)->bool:
        cur = self._db_conn.cursor()
        cur.execute("UPDATE clients SET ip = %s WHERE login = ? ;", (ip, login))
        _status = cur.rowcount == 1
        cur.close()
        return _status

    # 1.3.
    def db_search_password(self, login: str) -> str:
        cur = self._db_conn.cursor()
        cur.execute("SELECT password FROM clients WHERE login = ? ;", (login,))
        result = cur.fetchone()
        cur.close()
        if result is None:
            return '-'
        return result[0]

    # 2.3.
    def db_search_ip(self, login: str) -> str:
        cur = self._db_conn.cursor()
        cur.execute("SELECT ip FROM clients WHERE login = ? ;", (login,))
        result = cur.fetchone()
        cur.close()
        if result is None:
            return '0.0.0.0'
        return result[0]


class DataBaseClient():
    _db_conn = None

    def db_init(self) -> bool:
        self._db_conn = sqlite3.connect('Chinook_Sqlite.sqlite')
        cur = self._db_conn.cursor()
        cur.execute("SELECT COUNT(sql) FROM sqlite_master WHERE type = 'table' AND name = 'friends';")
        if cur.fetchone()[0] == 0:
            cur.execute('CREATE TABLE friends ( friend STRING, ip STRING );')
            self._db_conn.commit()
            if cur.rowcount == 0:
                return False
        cur.execute("SELECT COUNT(sql) FROM sqlite_master WHERE type = 'table' AND name = 'history';")
        if cur.fetchone()[0] == 0:
            cur.execute('CREATE TABLE history ( friend STRING, time DATETIME, type BOOL, message BLOB);')
            self._db_conn.commit()
            if cur.rowcount == 0:
                return False
        cur.close()
        return True

    def __del__(self):
        if not (self._db_conn is None):
            self._db_conn.close()

    # 1.2.
    # Нужно ли другу кидать клиента?
    def db_add_friend(self, login_fr: str, ip_fr: str)->bool:
        cur = self._db_conn.cursor()
        cur.execute("INSERT INTO friends (friend, ip) VALUES (?, ?);", (login_fr, ip_fr))
        _status = cur.rowcount == 1
        cur.close()
        return _status

    # 2.2.
    # В обе стороны или в одну?
    def db_del_friend(self, login_fr: str)->bool:
        cur = self._db_conn.cursor()
        cur.execute("DELETE FROM friends WHERE friend = ?;", (login_fr,))
        _status = cur.rowcount == 1
        cur.execute("DELETE FROM history WHERE friend = ?;", (login_fr,))
        cur.close()
        return _status

    # 3.2.
    def db_get_all_friends(self)->list:
        cur = self._db_conn.cursor()
        cur.execute("SELECT friend FROM friends ;")
        result = cur.fetchall()
        cur.close()
        return result

    def db_update_ip(self, login: str, ip: str) -> bool:
        cur = self._db_conn.cursor()
        cur.execute("UPDATE friends SET ip = ? WHERE login = ? ;", (ip, login))
        _status = cur.rowcount == 1
        cur.close()
        return _status

    def db_add_message(self, login_fr: str, time, type: bool, mess)->bool:
        cur = self._db_conn.cursor()
        cur.execute("INSERT INTO history (friend, time, type, message) VALUES (?, ?, ?, ?);",
                    (login_fr, time, type, mess))
        _status = cur.rowcount == 1
        cur.close()
        return _status

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