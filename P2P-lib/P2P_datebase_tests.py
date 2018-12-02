import unittest
import os
from datetime import datetime, MINYEAR
from P2P_database import DataBaseServer, DataBaseClient


class P2PDataBaseTest(unittest.TestCase):
    def test_server(self):
        # os.remove("test.sqlite")
        time1 = datetime.now()
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

        self.assertTrue(db.update_ip('login', '123.123.123.123'))

        time2 = datetime.now()
        lst_1 = db.search_ip_and_last_time('login')
        self.assertEqual(lst_1[0], '123.123.123.123')
        self.assertTrue(lst_1[1] <= time2)
        self.assertTrue(time1 <= lst_1[1])

        lst_3 = db.search_ip_and_last_time('login3444')
        self.assertEqual(lst_3[0], '0.0.0.0')
        self.assertEqual(lst_3[1], datetime(MINYEAR, 1, 1))

        self.assertTrue(db.update_ip('login', '133.133.133.133'))
        time2 = datetime.now()

        lst_1 = db.search_ip_and_last_time('login')
        self.assertEqual(lst_1[0], '133.133.133.133')
        self.assertTrue(lst_1[1] <= time2)
        self.assertTrue(time1 <= lst_1[1])

        del db
        db1 = DataBaseServer("test.sqlite")
        self.assertTrue(db1.init())
        self.assertEqual(db1.search_password('login'), '1q2w3e')
        del db1
        os.remove("test.sqlite")

    def test_client(self):
        # os.remove("test.sqlite")
        time1 = datetime.now()
        db = DataBaseClient("test.sqlite")

        self.assertTrue(db.init())
        self.assertTrue(db.add_friend('login', '222.222.222.222'))
        self.assertTrue(db.add_friend('login2', '111.111.111.111'))
        self.assertTrue(db.add_friend('login55', '232.232.232.232'))
        self.assertTrue(db.del_friend('login55'))
        lst = db.get_all_friends()
        self.assertEqual(len(lst), 2)
        self.assertTrue('login' in lst)
        self.assertTrue('login2' in lst)
        self.assertFalse('login55' in lst)

        time2 = datetime.now()

        lst_1 = db.search_ip_and_last_time('login')
        self.assertEqual(lst_1[0], '222.222.222.222')
        self.assertTrue(lst_1[1] <= time2)
        self.assertTrue(time1 <= lst_1[1])

        self.assertTrue(db.update_ip('login', '178.178.178.178', datetime.now()))
        time2 = datetime.now()

        lst_1 = db.search_ip_and_last_time('login')
        self.assertEqual(lst_1[0], '178.178.178.178')
        self.assertTrue(lst_1[1] <= time2)
        self.assertTrue(time1 <= lst_1[1])

        lst_3 = db.search_ip_and_last_time('login3456')
        self.assertEqual(lst_3[0], '0.0.0.0')
        self.assertEqual(lst_3[1], datetime(MINYEAR, 1, 1))

        time15 = datetime(2018, 12, 15)
        time10 = datetime(2018, 12, 10)
        time13 = datetime(2018, 12, 13)
        self.assertTrue(db.add_message('login', time10, True, 'message 1'))
        self.assertTrue(db.add_message('login2', time13, True, ':-D'))
        self.assertTrue(db.add_message('login2', time15, False, '<<^_^>>'))
        db.del_messages(time13)

        self.assertEqual(db.search_messages('login'), [])
        self.assertEqual(db.search_messages('login2'),
                         [('2018-12-13 00:00:00', True, ':-D'), ('2018-12-15 00:00:00', False, '<<^_^>>')])

        del db
        db1 = DataBaseClient("test.sqlite")
        self.assertTrue(db1.init())
        self.assertEqual(db1.search_ip_and_last_time('login')[0], '178.178.178.178')
        del db1
        os.remove("test.sqlite")


if __name__ == "__main__":
    unittest.main()

