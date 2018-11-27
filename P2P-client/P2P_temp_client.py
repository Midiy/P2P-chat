# Encoding: utf-8

import asyncio
import P2P_client_network as network
from datetime import datetime
from P2P_database import DataBaseClient
from P2P_lib import Logger, Extentions
from os import system


class Contact:

    database: DataBaseClient = None

    connection: network._IConnection = None
    
    _name: str = None
    _ip: str = None
    _history: str = None
    _login: str = None

    def __init__(self, name: str, login: str):
        if Contact.database is None:
            raise Exception("You shold initialise Contact.database first!")
        self._name = name
        self._login = login
        self._ip = Contact.database.search_ip(name)
        history = Contact.database.search_messages(name)
        for time, type, text in history:
            if type:
                self._history += text + "\n"
        self._connection = network.ClientToClient(login, name, self._endpoint)

    def add_text_message(self, message: str):
        Contact.database.add_message(self._name, datetime.now(), True, message)
        self._history += message + "\n"

    async def send_text_message(self, message: str):
        await self.connection.send_text_message(message)
        self.add_text_message(f"[{datetime.now().strftime('%d.%m.%Y %T')} {login}]: {line}")

    def upgrade_ip(self, new_ip: str):
        Contact.database.update_ip(self._name, new_ip)
        self._ip = new_ip


class Contact_dict(dict):
    
    _create_new_contact_callback = None

    def __init__(self, create_new_contact):
        self._create_new_contact_callback = create_new_contact
        return super().__init__()

    def __getitem__(self, key):
        if type(key) == tuple:
            ip = key[1]
            key = key[0]
        else:
            ip = None
        if not key in self.keys():
            self[key] = self._create_new_contact_callback(key, ip)
        return super().__getitem__(key)


@Logger.logged("client")
def get_command(line: str) -> (str, str):
    i = 1
    while line[i] != " ":
        i += 1
    j == i + 1
    while line[i] == " ":
        i += 1
    return (line[:j], line[i:])


@Logger.logged("client")
async def get_ip_by_name(server: network.ClientToServer, name: str) -> str:   # DEBUG
    return await server.get_IPs([name])[0]   # DEBUG

@Logger.logged("client")
async def main():
    if input("Do you want to (l)ogin or to (r)egister? ") == "l":
        registration = False
    else:
        registration = True
    login = input("Login: ")
    password = input("Password: ")
    system("cls")   # REDO: Add supporting not only Windows.
    database = DataBaseClient()
    database.init()
    Contact.database = database
    # server_endpoint = database.search_ip("server")
    # if server_endpoint == "0.0.0.0":
    server_endpoint = "127.0.0.1"   # DEBUG
    server = network.ClientToServer(server_endpoint)
    if registration:
        await server.registration(login, password)
    else:
        await server.login(login, password)
    
    @Logger.logged("client")
    def _add_new_contact(name: str, ip: str):
        database.add_friend(name, ip)
        return Contact(name, login)
    
    contacts = Contact_dict(_add_new_contact)
    contacts_names = database.get_all_friends()
    for c in contacts_names:
        database.update_ip(c, server.get_IPs([c])[0])   # REDO: Check if server has newer IP than this client.
        contacts[c] = Contact(c, login)
    
    # TODO: Add P2P-upgrading contacts IP
    
    current_contact = None
    
    @Logger.logged("client")
    def _on_receive(data: bytes, contact_login: str, contact_ip: str):
        msg_datetime = datetime.now().strftime("%d.%m.%Y %T")
        message = f"[{msg_datetime} {contact_login}] : {Extentions.bytes_to_defstr(data)[0]}"
        if current_contact == contacts[contact_login, contact_ip]:
            print(f"[{contact_login}]: {Extentions.bytes_to_defstr(data)[0]}")
        else:
            print(f"\nNew message from {contact_login}!\n")
        contacts[contact_login].add_text_message(message)
    
    listener = network.Listener(login, _on_receive,
                                lambda name, ip: contacts[name, ip].upgrade_ip(ip),
                                server_endpoint, database)
    await listener.listen()
    while True:
        line = input()
        if line == "$refresh":
            await asyncio.sleep(1)
            continue
        if not line.startswith("$"):
            if current_contact is None:
                print("You should use '$gotodialog <username>' first")
            else:
                await current_contact.send_text_message(line)
                print(f"[{datetime.now().strftime('%d.%m.%Y %T')} {login}]: {line}")
        else:
            command, arg = get_command(line)
            if command == "$gotodialog":
                system("cls")   # REDO: Add supporting not only Windows.
                if not arg in contacts:
                    current_contact = contacts[arg, await get_ip_by_name(server, arg)]
                else:
                    current_contact = contacts[arg]
                print_history(arg)
            else:
                pass # TODO: Add some other cases.


asyncio.run(main())
