# Encoding: utf-8

import socket
import P2P_client_network as network
from datetime import datetime
from P2P_database import DataBaseClient
from P2P_lib import Logger, Extentions
from typing import Callable, List, Tuple


class Client:
    class _Contact:

        database: DataBaseClient = None

        connection: network._IConnection = None
        name: str = None

        _ip: str = None
        _last_update: datetime = None
        _history: List[Tuple[str, datetime, str]] = None
        _login: str = None

        @Logger.logged("client")
        def __init__(self, name: str, login: str):
            if Client._Contact.database is None:
                raise Exception("You should initialise Contact.database first!")
            self.name = name
            self._login = login
            self._ip, self._last_update = Client._Contact.database.search_ip_and_last_time(name)
            history = Client._Contact.database.search_messages(name)
            self._history = []
            for time, msg_type, text in history:
                if msg_type:
                    self._history.append((None, time, text))   # DEBUG
            self.connection = network.ClientToClient(login, name, self._ip)

        @Logger.logged("client")
        def add_text_message(self, message: str, sender: str):
            time = datetime.now()
            Client._Contact.database.add_message(self.name, time, True, message)
            self._history.append((sender, time, message))

        @Logger.logged("client")
        async def send_text_message(self, message: str) -> bool:
            try:
                await self.connection.send_text_message(message)
                self.add_text_message(message, self._login)
                return True
            except network.ClientToClientException:
                return False
            
        @Logger.logged("client")
        def update_ip(self, new_ip: str, update_time: datetime) -> bool:
            if new_ip is None or update_time <= self._last_update:
                return False
            Client._Contact.database.update_ip(self.name, new_ip, update_time)
            self._ip = new_ip
            self._last_update = update_time
            self.connection = network.ClientToClient(self._login, self.name, self._ip)
            return True
        
        @Logger.logged("client")
        def get_history(self) -> List[Tuple[str, datetime, str]]:
            return self._history

        async def get_IPs(self, names: List[str]) -> List[Tuple[str, datetime]]:
            try:
                return await self.connection.get_IPs(names)
            except network.ClientToClientException:
                return [(None, None)] * len(names)

    class _Contact_dict(dict):

        _create_new_contact_callback = None
        
        @Logger.logged("client")
        def __init__(self, create_new_contact):
            self._create_new_contact_callback = create_new_contact
            return super().__init__()
        
        @Logger.logged("client")
        def __getitem__(self, key):
            if type(key) == tuple:
                ip = key[1]
                update_time = key[2]
                key = key[0]
            else:
                ip = None
                update_time = None
            if key not in self.keys():
                self[key] = self._create_new_contact_callback(key, ip, update_time)
            return super().__getitem__(key)

    login: str = None
    on_receive_callback: Callable[[str, str, str], None] = None
    is_connected: bool = None

    _password: str = None
    _database: DataBaseClient = None
    _server: network.ClientToServer = None
    _contacts: _Contact_dict = None
    _listener: network.Listener = None
    _need_registration: bool = None

    @Logger.logged("client")
    def __init__(self, login: str, password: str,
                 on_receive_callback: Callable[[str, datetime, str], None],
                 need_registration: bool=False):
        """
        Класс, инкапсулирующий всю логику работы клиента.

        login: str - логин пользователя.
        password: str - пароль пользователя.
        on_receive_callback: function(str, datetime, str) - функция, которая будет вызвана
        при получении нового сообщения; должна принимать три аргумента: логин отправителя,
        время получения и текст сообщения.
        need_registration: bool - True для создания и регистрации на сервере
        нового пользователя; по умолчанию False.
        """
        self.login = login
        self._password = password
        self.on_receive_callback = on_receive_callback
        self._need_registration = need_registration
        self._database = DataBaseClient(login + ".sqlite")
        self._database.init()
        self._Contact.database = self._database

        @Logger.logged("client")
        def _add_new_contact(name: str, ip: str, update_time: datetime) -> Client._Contact:
            self._database.add_friend(name, ip, update_time)
            return Client._Contact(name, self.login)

        self._contacts = Client._Contact_dict(_add_new_contact)
        
        @Logger.logged("client")
        def _on_receive_callback(data: bytes, contact_login: str, contact_endpoint: str):
            message = Extentions.bytes_to_defstr(data)[0]
            time = datetime.now()
            self._contacts[contact_login, contact_endpoint, time].add_text_message(message, contact_login)
            self.on_receive_callback(contact_login, time, message)
            
        @Logger.logged("client")
        def _update_ip(name: str, ip: str):
            time = datetime.now()
            self._contacts[name, ip, time].update_ip(ip, time)

        self._listener = network.Listener(login, _on_receive_callback,
                                          _update_ip, self._database)
    
    @Logger.logged("client")
    async def _discover_server(self) -> bool:
        internal_ip = socket.gethostbyname(socket.gethostname())
        template_ip = internal_ip[:internal_ip.rfind(".") + 1]
        for i in range(0, 256):
            c = network.ClientToServer(f"{template_ip}{i}:3501")
            Logger.log(f"Trying to find server at {template_ip}{i}:3501...", "client")
            try:
                await c.get_IPs([])
                self._server = c
                self._database.add_friend("server", f"{template_ip}{i}:3501", datetime.now())
                Logger.log(f"Server was found at {template_ip}{i}:3501.", "client")
                return True
            except network.ClientToServerException as ex:
                if ex.code == 251:
                    continue
                raise ex
        return False

    @Logger.logged("client")
    async def _discover_contacts(self, names: List[str]) -> bool:
        result = False
        internal_ip = socket.gethostbyname(socket.gethostname())
        template_ip = internal_ip[:internal_ip.rfind(".") + 1]
        for i in range(0, 256):
            if f"{template_ip}{i}" == internal_ip:
                continue
            c = network.ClientToClient("guest", "", f"{template_ip}{i}:3502")
            Logger.log(f"Trying to find client at {template_ip}{i}:3502...", "client")
            try:
                ips = await c.get_IPs(names)
                Logger.log(f"Client was found at {template_ip}{i}:3502.", "client")
                for n, i in zip(names, ips):
                    if i[0] == "0.0.0.0":
                        continue
                    if n == "server":
                        if not result:
                            self._server = network.ClientToServer(i[0])
                            self._database.add_friend("server", *i)
                            result = True
                        elif self._database.get_ip_and_last_time("server")[1] < i[1]:
                            self._server = network.ClientToServer(i[0])
                            self._database.update_ip("server", *i)
                    else:
                        self._contacts[n].update_ip(*i)
            except network.ClientToClient:
                continue
        return result

    @Logger.logged("client")
    async def establish_connections(self) -> bool:
        """
        Асинхронный метод, устанавливающий соединение с сервером и пользователями
        из списка контактов и обновляющий IP-адреса. Должен быть однократно вызван
        до использования любого другого метода класса Client кроме, разве что, конструктора.

        Возвращаемое значение указывает, удалось ли установить соединение с сервером.
        """
        contacts_names = self._database.get_all_friends()
        for n in contacts_names:
            if n == "server":
                continue
            self._contacts[n] = Client._Contact(n, self.login)
        server_endpoint = self._Contact.database.search_ip_and_last_time("server")[0]
        if server_endpoint == "0.0.0.0":
            if not await self._discover_server():
                if not await self._discover_contacts():
                    self._server = network.ClientToServer("0.0.0.0")
        else:
            server_endpoint = server_endpoint
            self._server = network.ClientToServer(server_endpoint)
        if self._need_registration:
            try:
                await self._server.registration(self.login, self._password)
                self.is_connected = True
            except network.ClientToServerException as ex:
                if ex.code == 251:
                    self.is_connected = False
                else:
                    raise ex
        else:
            try:
                await self._server.login(self.login, self._password)
                self.is_connected = True
            except network.ClientToServerException as ex:
                if ex.code == 251:
                    self.is_connected = False
                else:
                    raise ex
        contacts_ips = await self._get_ips_by_names(contacts_names)
        server_update_time = self._database.search_ip_and_last_time("server")
        if server_update_time[0] != "0.0.0.0":
            server_update_time = server_update_time[1]
        else:
            server_update_time = None
        for n, i in zip(contacts_names, contacts_ips):
            if n == "server":
                if (server_update_time is None
                    or i[1] is not None
                    and server_update_time < i[1]):
                        self._database.update_ip("server", *i)
                        server_update_time = i[1]
                        self._server = network.ClientToServer(i[0])
                continue
            self._contacts[n].update_ip(*i)
        contacts_ips = await self._get_ips_by_names(contacts_names)
        for n, i in zip(contacts_names, contacts_ips):
            if n == "server":
                if (server_update_time is None
                    or i[1] is not None
                    and server_update_time < i[1]):
                        self._database.update_ip("server", *i)
                        server_update_time = i[1]
                        self._server = network.ClientToServer(i[0])
                continue
            self._contacts[n].update_ip(*i)
        await self._listener.listen()
        return self.is_connected

    @Logger.logged("client")
    async def _get_ips_by_names(self, names: List[str]) -> List[Tuple[str, datetime]]:
        try:
            result = await self._server.get_IPs(names)
        except network.ClientToServerException as ex:
            if ex.code == 251:
                result = [(None, None)] * len(names)
            else:
                raise ex
        for c in self._contacts:
            client_result = await self._contacts[c].get_IPs(names)
            for i in range(0, len(names)):
                if (result[i][0] is not None and
                    client_result[i][0] is not None and
                    result[1][1] < client_result[i][1]):
                        result[i] = client_result[i]
        return result

    @Logger.logged("client")
    async def send_message(self, name: str, message: str) -> bool:
        """
        Асинхронный метод для отправки указанного текстового сообщения указанному пользователю.
        Если пользователя нет в списке контактов, то он будет туда добавлен.

        name: str - логин получателя сообщения.
        message: str - текст отправляемого сообщения.

        Возвращаемое значение указывает, было ли доставлено сообщение.
        """
        if name not in self._contacts:
            ip, time = (await self._get_ips_by_names([name]))[0]
            current_contact = self._contacts[name, ip, time]
        else:
            current_contact = self._contacts[name]
        return await current_contact.send_text_message(message)

    @Logger.logged("client")
    async def get_history(self, name: str) -> List[Tuple[str, datetime, str]]:
        """
        Асинхронный метод, позволяющий получить историю переписки с заданным пользователем.

        name: str - логин пользователя, диалог с которым должен быть получен.

        Возвращаемое значение является списком кортежей вида
        (отправитель, время, текст), описывающих каждое сообщение.
        """
        if name not in self._contacts:
            ip, time = (await self._get_ips_by_names([name]))[0]
            current_contact = self._contacts[name, ip, time]
        else:
            current_contact = self._contacts[name]
        return current_contact.get_history()

    @Logger.logged("client")
    def get_contacts_list(self) -> List[str]:
        """
        Метод для получения списка контактов.

        Возвращаемое значение - список строк, каждая из которых
        является логином пользователя из списка контактов.
        """
        return [i.name for i in self._contacts]

    @Logger.logged("client")
    async def add_contact(self, name: str):
        """
        Метод, позволяющий добавить пользователя в список контактов.
    
        name: str - логин добавляемого пользователя.
        """
        ip, time = (await self._get_ips_by_names([name]))[0]
        self._contacts[name, ip, time]

    @Logger.logged("client")
    def delete_contact(self, name: str):
        """
        Метод, позволяющий удалить пользователя из списка контактов.
    
        name: str - логин удаляемого пользователя.
        """
        self._contacts.pop(name)
        self._database.del_friend(name)
