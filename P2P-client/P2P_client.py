# Encoding: utf-8

import P2P_client_network as network
from datetime import datetime
from P2P_database import DataBaseClient
from P2P_lib import Logger, Extentions
from typing import Callable, List, Tuple


class Client:
    class _Contact:

        database: DataBaseClient = None

        connection: network._IConnection = None

        _name: str = None
        _ip: str = None
        _last_upgrade: datetime = None
        _history: str = None
        _login: str = None

        def __init__(self, name: str, login: str):
            if Client._Contact.database is None:
                raise Exception("You should initialise Contact.database first!")
            self._name = name
            self._login = login
            self._ip, self._last_upgrade = Client._Contact.database.search_ip_and_last_time(name)
            history = Client._Contact.database.search_messages(name)
            for time, type, text in history:
                if type:
                    self._history += text + "\n"
            self._connection = network.ClientToClient(login, name, self._ip)

        def add_text_message(self, message: str):
            Client._Contact.database.add_message(self._name, datetime.now(), True, message)
            self._history += message + "\n"

        async def send_text_message(self, message: str):
            await self.connection.send_text_message(message)
            self.add_text_message(f"[{datetime.now().strftime('%d.%m.%Y %T')} {self._login}]: {message}")

        def upgrade_ip(self, new_ip: str) -> bool:
            if upgrade_time <= self._last_upgrade:
                return False
            Client._Contact.database.update_ip(self._name, new_ip)
            self._ip = new_ip
            self._last_upgrade = upgrade_time
            self._connection = network.ClientToClient(self._login, self._name, self._ip)
            return True

        def get_history(self):
            return self._history

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
        def _add_new_contact(name: str, ip: str, upgrade_time: datetime) -> Client._Contact:
            self._database.add_friend(name, ip)
            return Client._Contact(name, self._login, upgrade_time)

        self._contacts = Client._Contact_dict(_add_new_contact)
        contacts_names = self._database.get_all_friends()
        contacts_ips = await self._get_ips_by_names(contacts_names)
        for n in contacts_names, i in contacts_ips:
            self._contacts[c] = Client._Contact(c, self.login)
            self._contacts[c].upgrade_ip(*i)

        # TODO: Add P2P-upgrading contacts IP

        def _on_receive_callback(data: bytes, contact_login: str, contact_endpoint: str):
            message = Extentions.bytes_to_defstr(data)[0]
            self.contacts[contact_login, contact_endpoint, datetime.now()].add_text_message(message)
            self.on_receive_callback(message, contact_login, contact_endpoint)

        def _upgrade_ip(name: str, ip: str):
            time = datetime.now()
            self._contacts[name, ip, time].upgrade_ip(ip, time)

        self._listener = network.Listener(login, _on_receive_callback, _upgrade_ip,
                                          server_endpoint, self._database)
        await self._listener.listen()

    async def _get_ips_by_names(self, names: List[str]) -> List[Tuple[str, datetime]]:
        return await self._server.get_IPs(names)   # DEBUG

    async def send_message(self, name: str, message: str):
        if name not in self._contacts:
            ip, time = await self._get_ips_by_names([name])[0]
            current_contact = self._contacts[name, ip, time]
        else:
            current_contact = self._contacts[name]
        await current_contact.send_text_message(message)

    async def get_history(self, name: str) -> str:
        if name not in self._contacts:
            ip, time = await self._get_ips_by_names([name])[0]
            current_contact = self._contacts[name, ip, time]        
        else:
            current_contact = self._contacts[name]
        return current_contact.get_history()

    def get_contacts_list(self) -> List[str]:
        return [i for i in self._contacts]
