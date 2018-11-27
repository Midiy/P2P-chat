# Encoding: utf-8

import P2P_client_network as network
from datetime import datetime
from P2P_database import DataBaseClient
from P2P_lib import Logger, Extentions
from typing import Callable, List


class Client:
    class _Contact:

        database: DataBaseClient = None

        connection: network._IConnection = None

        _name: str = None
        _ip: str = None
        _history: str = None
        _login: str = None

        def __init__(self, name: str, login: str):
            if Client._Contact.database is None:
                raise Exception("You shold initialise Contact.database first!")
            self._name = name
            self._login = login
            self._ip = Client._Contact.database.search_ip(name)
            history = Client._Contact.database.search_messages(name)
            for time, type, text in history:
                if type:
                    self._history += text + "\n"
            self._connection = network.ClientToClient(login, name, self._endpoint)

        def add_text_message(self, message: str):
            Client._Contact.database.add_message(self._name, datetime.now(), True, message)
            self._history += message + "\n"

        async def send_text_message(self, message: str):
            await self.connection.send_text_message(message)
            self.add_text_message(f"[{datetime.now().strftime('%d.%m.%Y %T')} {self._login}]: {message}")

        def upgrade_ip(self, new_ip: str):
            Client._Contact.database.update_ip(self._name, new_ip)
            self._ip = new_ip

        def get_history(self):
            return self._history

    class _Contact_dict(dict):

        _create_new_contact_callback: Callable = None

        def __init__(self, create_new_contact: Callable):
            self._create_new_contact_callback = create_new_contact
            return super().__init__()

        def __getitem__(self, key):
            if type(key) == tuple:
                ip = key[1]
                key = key[0]
            else:
                ip = None
            if key not in self.keys():
                self[key] = self._create_new_contact_callback(key, ip)
            return super().__getitem__(key)

    login: str = None
    on_receive_callback: Callable[[str, str, str], None] = None

    _password: str = None
    _database: DataBaseClient = None
    _server: network.ClientToServer = None
    _contacts: _Contact_dict = None
    _listener: network.Listener = None

    @Logger.logged("client")
    async def __init__(self, login: str, password: str,
                       on_receive_callback: Callable[[str, str, str], None],
                       need_registration: bool=False):
        self.login = login
        self._password = password
        self.on_receive_callback = on_receive_callback
        self._database = DataBaseClient()
        self._database.init()
        self._Contact.database = self._database
        # server_endpoint = database.search_ip("server")
        # if server_endpoint == "0.0.0.0":
        server_endpoint = "127.0.0.1"   # DEBUG
        self._server = network.ClientToServer(server_endpoint)
        if need_registration:
            await self._server.registration(self.login, self.password)
        else:
            await self._server.login(self.login, self.password)

        @Logger.logged("client")
        def _add_new_contact(self):
            def _add_new_contact_wrapped(name: str, ip: str):
                self._database.add_friend(name, ip)
                return Client._Contact(name, self._login)
            return _add_new_contact_wrapped

        self._contacts = Client._Contact_dict(_add_new_contact(self))
        contacts_names = self._database.get_all_friends()
        for c in contacts_names:
            self._database.update_ip(c, self._server.get_IPs([c])[0])   # REDO: Check if server has newer IP than this client.
            self._contacts[c] = Client._Contact(c, self._login)

        # TODO: Add P2P-upgrading contacts IP

        def _on_receive_callback(data: bytes, contact_login: str, contact_endpoint: str):
            message = Extentions.bytes_to_defstr(data)[0]
            self.contacts[contact_login, contact_endpoint].add_text_message(message)
            self.on_receive_callback(message, contact_login, contact_endpoint)

        self._listener = network.Listener(login, _on_receive_callback,
                                          lambda name, ip: self._contacts[name, ip].upgrade_ip(ip),
                                          server_endpoint, self._database)
        await self._listener.listen()

    async def _get_ip_by_name(self, name: str) -> str:
        return await self._server.get_IPs([name])[0]   # DEBUG

    async def send_message(self, name: str, message: str):
        if name not in self._contacts:
            current_contact = self._contacts[name, await self._get_ip_by_name(name)]
        else:
            current_contact = self._contacts[name]
        await current_contact.send_text_message(message)

    async def get_history(self, name: str) -> str:
        if name not in self._contacts:
            current_contact = self._contacts[name, await self._get_ip_by_name(name)]
        else:
            current_contact = self._contacts[name]
        return current_contact.get_history()

    def get_contacts_list(self) -> List[str]:
        return [i for i in self._contacts]
