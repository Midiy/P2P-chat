import sqlite3 
import os
# import calendar
# import time
import unittest



class DataBaseServer():
    _db_conn = None
    _db_file = None

    def __init__(self, file: str = 'Chinook_Sqlite.sqlite'):
        self._db_file = file

    def init(self) -> bool:
        self._db_conn = sqlite3.connect(self._db_file)
        cur = self._db_conn.cursor()
        cur.execute("SELECT COUNT(sql) FROM sqlite_master WHERE type = 'table' AND name = 'clients';")
        if cur.fetchone()[0] == 0:
            cur.execute('CREATE TABLE clients (login STRING PRIMARY KEY UNIQUE NOT NULL, password STRING, ip STRING);')
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
        cur.execute("INSERT INTO clients (login, password, ip) VALUES (?, ?, ?);", (login, password, ip))
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
        cur.execute("UPDATE clients SET ip = ? WHERE login = ? ;", (ip, login))
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

    # 2.3.
    def search_ip(self, login: str) -> str:
        cur = self._db_conn.cursor()
        cur.execute("SELECT ip FROM clients WHERE login = ? ;", (login,))
        result = cur.fetchone()
        cur.close()
        if result is None:
            return '0.0.0.0'
        return result[0]


class DataBaseClient():
    _db_conn = None
    _db_file = None

    def __init__(self, file: str = 'Chinook_Sqlite.sqlite'):
        self._db_file = file

    def init(self) -> bool:
        self._db_conn = sqlite3.connect(self._db_file)
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
    def add_friend(self, login_fr: str, ip_fr: str)->bool:
        cur = self._db_conn.cursor()
        cur.execute("INSERT INTO friends (friend, ip) VALUES (?, ?);", (login_fr, ip_fr))
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
        result = cur.fetchall()
        cur.close()
        return result

    def update_ip(self, login: str, ip: str) -> bool:
        cur = self._db_conn.cursor()
        cur.execute("UPDATE friends SET ip = ? WHERE login = ? ;", (ip, login))
        _status = cur.rowcount == 1
        cur.close()
        self._db_conn.commit()
        return _status

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



# db_search_IP()
# db_update_password()
# db_update_IP()
# db_search_friends()

# db_fini()



class P2PDataBaseTest(unittest.TestCase):
    def test_server(self):
        db = DataBaseServer("test.sqlite")
        self.assertTrue(db.init())
        self.assertTrue(db.add_client('login', 'password', '222.222.222.222'))
        self.assertTrue(db.add_client('login2', '12345', '111.111.111.111'))
        self.assertTrue(db.add_client('login55', '1111', '232.232.232.232'))
        self.assertTrue(db.del_client('login55'))
        self.assertEqual(db.search_password('login55'), '-')

        self.assertEqual(db.search_password('login'), 'password')
        self.assertEqual(type(db.search_password('login2')), str)
        self.assertEqual(db.search_password('login2'), '12345')
        self.assertTrue(db.update_password('login', '1q2w3e'))
        self.assertFalse(db.update_password('login333', '6t7y8u'))
        self.assertEqual(db.search_password('login'), '1q2w3e')

        self.assertEqual(db.search_ip('login'), '222.222.222.222')
        self.assertEqual(db.search_ip('login2'), '111.111.111.111')
        self.assertTrue(db.update_ip('login', '123.123.123.123'))
        self.assertFalse(db.update_ip('login333', '121.121.121.121'))
        self.assertEqual(db.search_ip('login'), '123.123.123.123')

        del db
        db1 = DataBaseServer("test.sqlite")
        self.assertTrue(db1.init())
        self.assertEqual(db1.search_password('login'), '1q2w3e')
        del db1
        os.remove("test.sqlite")

    def test_client(self):
        pass


if __name__ == "__main__":
    unittest.main()
