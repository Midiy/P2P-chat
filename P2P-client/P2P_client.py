# Encoding: utf-8

import asyncio
import P2P_client_network as network
from datetime import datetime
from P2P_database import DataBaseClient
from P2P_lib import Logger, Extentions
from typing import Callable, List, Tuple, Coroutine


class Client:
    class _Contact:

        database: DataBaseClient = None

        connection: network._IConnection = None
        name: str = None

        _ip: str = None
        _last_upgrade: datetime = None
        _history: List[Tuple[str, datetime, str]] = None
        _login: str = None

        def __init__(self, name: str, login: str):
            if Client._Contact.database is None:
                raise Exception("You should initialise Contact.database first!")
            self.name = name
            self._login = login
            self._ip, self._last_upgrade = Client._Contact.database.search_ip_and_last_time(name)
            history = Client._Contact.database.search_messages(name)
            self._history = []
            for time, msg_type, text in history:
                if msg_type:
                    self._history.append(time, text)
            self._connection = network.ClientToClient(login, name, self._ip)

        def add_text_message(self, message: str, sender: str):
            time = datetime.now()
            Client._Contact.database.add_message(self.name, time, True, message)
            self._history.append(sender, time, message)

        async def send_text_message(self, message: str) -> bool:
            try:
                await self.connection.send_text_message(message)
                self.add_text_message(message, self._login)
                return True
            except network.ClientToClientException:
                return False

        def upgrade_ip(self, new_ip: str, upgrade_time: datetime) -> bool:
            if upgrade_time <= self._last_upgrade:
                return False
            Client._Contact.database.update_ip(self.name, new_ip, upgrade_time)
            self._ip = new_ip
            self._last_upgrade = upgrade_time
            self._connection = network.ClientToClient(self._login, self.name, self._ip)
            return True

        def get_history(self) -> List[Tuple[str, datetime, str]]:
            return self._history

        async def get_IPs(self, names: List[str]) -> List[Tuple[str, datetime]]:
            try:
                return await self._connection.get_IPs(names)
            except network.ClientToClientException:
                return [(None, None)] * len(names)

    class _Contact_dict(dict):

        _create_new_contact_callback = None # : Callable[[str, str, datetime], Client._Contact] = None

        def __init__(self, create_new_contact): # : Callable[[str, str, datetime], Client._Contact]):
            self._create_new_contact_callback = create_new_contact
            return super().__init__()

        def __getitem__(self, key):
            if type(key) == tuple:
                ip = key[1]
                upgrade_time = key[2]
                key = key[0]
            else:
                ip = None
                upgrade_time = None
            if key not in self.keys():
                self[key] = self._create_new_contact_callback(key, ip, upgrade_time)
            return super().__getitem__(key)

    login: str = None
    on_receive_callback: Callable[[str, str, str], None] = None
    is_connected: bool = None

    _password: str = None
    _database: DataBaseClient = None
    _server: network.ClientToServer = None
    _contacts: _Contact_dict = None
    _listener: network.Listener = None
    _connect_to_server: Coroutine = None

    @Logger.logged("client")
    def __init__(self, login: str, password: str,
                       on_receive_callback: Callable[[str, str, str], None],
                       need_registration: bool=False):
        self.login = login
        self._password = password
        self.on_receive_callback = on_receive_callback
        self._database = DataBaseClient(login + ".sqlite")
        self._database.init()
        self._Contact.database = self._database
        server_endpoint = self._Contact.database.search_ip_and_last_time("server")[0]
        if server_endpoint == []:
            server_endpoint = "127.0.0.1"   # DEBUG
        else:
            server_endpoint = server_endpoint[0]
        self._server = network.ClientToServer(server_endpoint)
        if need_registration:
            self._connect_to_server = self._server.registration(self.login, self._password)
        else:
            self._connect_to_server = self._server.login(self.login, self.password)

        @Logger.logged("client")
        def _add_new_contact(name: str, ip: str, upgrade_time: datetime) -> Client._Contact:
            self._database.add_friend(name, ip)
            return Client._Contact(name, self._login, upgrade_time)

        self._contacts = Client._Contact_dict(_add_new_contact)
        def _on_receive_callback(data: bytes, contact_login: str, contact_endpoint: str):
            message = Extentions.bytes_to_defstr(data)[0]
            time = datetime.now()
            self.contacts[contact_login, contact_endpoint, time].add_text_message(message, contact_login)
            self.on_receive_callback(contact_login, time, message)

        def _upgrade_ip(name: str, ip: str):
            time = datetime.now()
            self._contacts[name, ip, time].upgrade_ip(ip, time)

        self._listener = network.Listener(login, _on_receive_callback, 
                                          _upgrade_ip, self._database)

    async def establish_connections(self) -> bool:
        try:
            await self._connect_to_server
            self.is_connected = True
        except network.ClientToServerException:
            self.is_connected = False
        contacts_names = self._database.get_all_friends()
        for n in contacts_names:
            if n == "server":
                continue
            self._contacts[n] = Client._Contact(n, self.login)
        contacts_ips = await self._get_ips_by_names(contacts_names)
        server_upgrade_time = self._database.search_ip_and_last_time("server")
        if server_upgrade_time != []:
            server_upgrade_time = server_upgrade_time[1]
        else:
            server_upgrade_time = None
        for n, i in zip(contacts_names, contacts_ips):
            if n == "server":
                if (server_upgrade_time is None or
                    i[1] != None and
                    server_upgrade_time < i[1]):
                        self._database.update_ip("server", *i)
                        server_upgrade_time = i[1]
                        self._server = network.ClientToServer(i[0])
                continue
            self._contacts[n].upgrade_ip(*i)
        contacts_ips = await self._get_ips_by_names(contacts_names)
        for n, i in zip(contacts_names, contacts_ips):
            if n == "server":
                if (server_upgrade_time is None or
                    i[1] != None and
                    server_upgrade_time < i[1]):
                        self._database.update_ip("server", *i)
                        server_upgrade_time = i[1]
                        self._server = network.ClientToServer(i[0])
                continue
            self._contacts[n].upgrade_ip(*i)
        await self._listener.listen()
        return self.is_connected

    async def _get_ips_by_names(self, names: List[str]) -> List[Tuple[str, datetime]]:
        try:
            result = await self._server.get_IPs(names)
        except network.ClientToServerException:
            result = [(None, None)] * len(names)
        for c in self._contacts:
            client_result = await c.get_IPs(names)
            for i in range(0, len(names)):
                if (result[i][0] is not None and
                    client_result[i][0] is not None and
                    result[1][1] < client_result[i][1]):
                        result[i] = client_result[i]
        return result

    async def send_message(self, name: str, message: str) -> bool:
        if name not in self._contacts:
            ip, time = await self._get_ips_by_names([name])[0]
            current_contact = self._contacts[name, ip, time]
        else:
            current_contact = self._contacts[name]
        return await current_contact.send_text_message(message)

    async def get_history(self, name: str) -> List[Tuple[str, datetime, str]]:
        if name not in self._contacts:
            ip, time = await self._get_ips_by_names([name])[0]
            current_contact = self._contacts[name, ip, time]        
        else:
            current_contact = self._contacts[name]
        return current_contact.get_history()

    def get_contacts_list(self) -> List[str]:
        return [i.name for i in self._contacts]

    async def add_contact(self, name: str):
        ip, time = await self._get_ips_by_names([name])[0]
        self._contacts[name, ip, time]

    def delete_contact(self, name: str):
        self._contacts.pop(name)
        self._database.del_friend(name)
