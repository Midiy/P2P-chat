#1.1.
def db_add_client(login : str, password : str, IP : str ):
    return True

#2.1.
def db_del_client(login : str):
    return True

#3.1.
def db_update_password(login : str, new_password : str):
    return True

#4.1.
def db_update_IP(login: str, IP: str):
    return True

#1.2.
def db_add_friend(login_cl : str, login_fr : str):
    return True

#2.2.
# В обе стороны или в одну?
def db_del_friend(login_cl : str, login_fr : str):
    return True

#3.2.
def db_search_friends(login : str):
    #result=cur.fetchall()
    return ('friend_1','friend_2')
