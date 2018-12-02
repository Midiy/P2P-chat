import sqlite3
from datetime import datetime, MINYEAR


class DataBaseServer:
    def __init__(self, file: str = 'Chinook_Sqlite.sqlite'):
        self._db_file = file
        self._db_conn = None

    def init(self) -> bool:
        self._db_conn = sqlite3.connect(self._db_file)
        cur = self._db_conn.cursor()
        cur.execute("SELECT COUNT(sql) FROM sqlite_master WHERE type = 'table' AND name = 'clients';")
        if cur.fetchone()[0] == 0:
            cur.execute('CREATE TABLE clients (login STRING PRIMARY KEY UNIQUE NOT NULL, password STRING, ip STRING,'
                        ' last_time DATETIME);')
            self._db_conn.commit()
            if cur.rowcount == 0:
                return False
        cur.close()
        return True

    def __del__(self):
        if not (self._db_conn is None):
            self._db_conn.close()

    # 1.1.
    def add_client(self, login: str, password: str, ip: str)->bool:
        cur = self._db_conn.cursor()
        cur.execute("INSERT INTO clients (login, password, ip, last_time) VALUES (?, ?, ?, ?);",
                    (login, password, ip, datetime.now()))
        _status = cur.rowcount == 1
        cur.close()
        self._db_conn.commit()
        return _status

    # 2.1.
    def del_client(self, login: str)->bool:
        cur = self._db_conn.cursor()
        cur.execute(" DELETE FROM clients WHERE login  = ? ;", (login,))
        _status = cur.rowcount == 1
        cur.close()
        self._db_conn.commit()
        return _status

    # 3.1.
    def update_password(self, login: str, new_password: str)->bool:
        cur = self._db_conn.cursor()
        cur.execute("UPDATE clients SET password = ? WHERE login = ? ;", (new_password, login))
        _status = cur.rowcount == 1
        cur.close()
        self._db_conn.commit()
        return _status

    # 4.1.
    def update_ip(self, login: str, ip: str)->bool:
        cur = self._db_conn.cursor()
        cur.execute("UPDATE clients SET ip = ?, last_time = ? WHERE login = ? ;", (ip, datetime.now(), login))
        _status = cur.rowcount == 1
        cur.close()
        self._db_conn.commit()
        return _status

    # 1.3.
    def search_password(self, login: str) -> str:
        cur = self._db_conn.cursor()
        cur.execute("SELECT password FROM clients WHERE login = ? ;", (login,))
        result = cur.fetchone()
        cur.close()
        if result is None:
            return '-'
        return str(result[0])

    # 2.3 + 3.3
    def search_ip_and_last_time(self, login: str) -> (str, datetime):
        cur = self._db_conn.cursor()
        cur.execute("SELECT ip, last_time FROM clients WHERE login = ? ;", (login, ))
        result = cur.fetchall()
        cur.close()
        if len(result) == 0:
            return '0.0.0.0', datetime(MINYEAR, 1, 1)
        return result[0][0], datetime.strptime(result[0][1], '%Y-%m-%d %H:%M:%S.%f')


class DataBaseClient:
    def __init__(self, file: str = 'Chinook_Sqlite.sqlite'):
        self._db_file = file
        self._db_conn = None

    def init(self) -> bool:
        self._db_conn = sqlite3.connect(self._db_file)
        cur = self._db_conn.cursor()
        cur.execute("SELECT COUNT(sql) FROM sqlite_master WHERE type = 'table' AND name = 'friends';")
        if cur.fetchone()[0] == 0:
            cur.execute('CREATE TABLE friends ( friend STRING, ip STRING, last_time DATETIME );')
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
    def add_friend(self, login_fr: str, ip_fr: str)->bool:
        cur = self._db_conn.cursor()
        cur.execute("INSERT INTO friends (friend, ip, last_time) VALUES (?, ?, ?);", (login_fr, ip_fr, datetime.now()))
        _status = cur.rowcount == 1
        cur.close()
        self._db_conn.commit()
        return _status

    # 2.2.
    # В обе стороны или в одну?
    def del_friend(self, login_fr: str)->bool:
        cur = self._db_conn.cursor()
        cur.execute("DELETE FROM friends WHERE friend = ?;", (login_fr,))
        _status = cur.rowcount == 1
        cur.execute("DELETE FROM history WHERE friend = ?;", (login_fr,))
        cur.close()
        self._db_conn.commit()
        return _status

    # 3.2.
    def get_all_friends(self)->list:
        cur = self._db_conn.cursor()
        cur.execute("SELECT friend FROM friends ;")
        lst = cur.fetchall()
        cur.close()
        result = []
        for i in lst:
            result += i
        return result

    def update_ip(self, login: str, ip: str, d_time) -> bool:
        cur = self._db_conn.cursor()
        cur.execute("UPDATE friends SET ip = ?, last_time = ? WHERE friend = ? ;", (ip, d_time, login))
        _status = cur.rowcount == 1
        cur.close()
        self._db_conn.commit()
        return _status

    def search_ip_and_last_time(self, login: str) -> (str, datetime):
        cur = self._db_conn.cursor()
        cur.execute("SELECT ip, last_time FROM friends WHERE friend = ? ;", (login, ))
        result = cur.fetchall()
        cur.close()
        if len(result) == 0:
            return '0.0.0.0', datetime(MINYEAR, 1, 1)
        return result[0][0], datetime.strptime(result[0][1], '%Y-%m-%d %H:%M:%S.%f')

    def add_message(self, login_fr: str, time, type_m: bool, mess)->bool:
        cur = self._db_conn.cursor()
        cur.execute("INSERT INTO history (friend, time, type, message) VALUES (?, ?, ?, ?);",
                    (login_fr, time, type_m, mess))
        _status = cur.rowcount == 1
        cur.close()
        self._db_conn.commit()
        return _status

    def del_messages(self, date):
        cur = self._db_conn.cursor()
        cur.execute(" DELETE FROM history WHERE time  < ? ;", (date,))
        cur.close()
        self._db_conn.commit()

    def search_messages(self, login_fr: str):
        cur = self._db_conn.cursor()
        cur.execute("SELECT time, type, message FROM history WHERE friend = ? ORDER BY time ;", (login_fr,))
        result = cur.fetchall()
        cur.close()
        return result
