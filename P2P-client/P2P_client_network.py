# Encoding: utf-8

import asyncio
import socket
from concurrent.futures import TimeoutError
from P2P_lib import Logger, Extentions
from P2P_database import DataBaseClient
from typing import Callable, List, Tuple
from datetime import datetime


class Listener:

    _server: asyncio.AbstractServer = None
    _loop: asyncio.AbstractEventLoop = None
    _server_endpoint: Tuple[str, datetime] = None
    _database: DataBaseClient = None

    login: str = None
    on_receive_msg_callback: Callable[[bytes, str, str], None] = None
    update_ip_callback: Callable[[str, str], None] = None

    @Logger.logged("client")
    def __init__(self, login: str,
                 on_receive_msg_callback: Callable[[bytes, str, str], None],
                 update_ip_callback: Callable[[str, str], None],
                 database: DataBaseClient, port: int=3502):
        self.login = login
        self.on_receive_msg_callback = on_receive_msg_callback
        self.update_ip_callback = update_ip_callback
        self._database = database
        self._server_endpoint = self._database.search_ip_and_last_time("server")

    @staticmethod
    @Logger.logged("client")
    async def _get_data(reader: asyncio.StreamReader, timeout: int=5) -> (int, bytes):

        async def _l_get_data(length: int) -> (bytes):
            data = await asyncio.wait_for(reader.read(length), timeout=timeout)
            if data:
                return data
            else:
                raise ConnectionAbortedError()

        length, _ = Extentions.bytes_to_int(await _l_get_data(4))
        result = await _l_get_data(length)
        return (result[0], result[1:])

    @staticmethod
    @Logger.logged("client")
    async def _send_data(writer: asyncio.StreamWriter, code: int, data: bytes=bytes()):
        data_to_send = Extentions.int_to_bytes(len(data) + 1) + bytes([code]) + data
        writer.write(data_to_send)
        await writer.drain()

    @Logger.logged("client")
    def _on_connect_wrapper(self) -> Callable[[asyncio.StreamReader, asyncio.StreamWriter], None]:
        async def _on_connect(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            timeout = 5
            client_login = None
            client_endpoint = writer.get_extra_info("peername")
            client_ip = client_endpoint[0]
            client_port = client_endpoint[1]
            Logger.log(f"Accepted connection from {client_ip}:{client_port}.", "client")
            while True:
                try:
                    code, data = await self._get_data(reader, timeout)
                    if code == 0:   # Ping
                        await self._send_data(writer, 0)
                        Logger.log(f"Ping was sent to {client_ip}:{client_port}.", "client")
                    elif code == 2:   # Login
                        received_login, data = Extentions.bytes_to_defstr(data)
                        if data == bytes():
                            preferred_port = "3502"
                        else:
                            preferred_port, _ = Extentions.bytes_to_defstr(data)
                        if received_login == "server":
                            await self._send_data(writer, 252, Extentions.defstr_to_bytes("'server' is service login!"))
                            continue
                        client_login = received_login
                        self.update_ip_callback(client_login, client_ip + ":" + preferred_port)
                        await self._send_data(writer, 2, Extentions.defstr_to_bytes(self.login))
                        timeout = 60
                        Logger.log(f"Login {client_ip}:{client_port} as '{client_login}' was confirmed.")
                    elif code == 3:   # IP updating request
                        login_count, data = Extentions.bytes_to_int(data)
                        ips = Extentions.int_to_bytes(login_count)
                        while login_count > 0:
                            requested_login, data = Extentions.bytes_to_defstr(data)
                            if requested_login == "server":
                                if self._server_login == []:
                                    requested_ip = ""
                                    requested_time = ""
                                else:
                                    requested_ip, requested_time = self._server_login
                                    requested_time = requested_time.strftime("%T %d.%m.%Y")
                                requested_line = (Extentions.defstr_to_bytes(requested_ip) +
                                                  + Extentions.defstr_to_bytes(requested_time))
                                ips += requested_line
                            elif requested_login == self.login:
                                requested_ip = socket.gethostbyname(socket.gethostname())
                                requested_time = datetime.now().strftime("%T %d.%m.%Y")
                                requested_line = (Extentions.defstr_to_bytes(requested_ip) +
                                                  + Extentions.defstr_to_bytes(requested_time))
                                ips += requested_line
                            else:
                                tmp = self._database.search_ip_and_last_time(requested_login)
                                if tmp[0] == "0.0.0.0":
                                    requested_ip = ""
                                    requested_time = ""
                                else:
                                    requested_ip, requested_time = tmp
                                    requested_time = requested_time.strftime("%T %d.%m.%Y")
                                requested_line = (Extentions.defstr_to_bytes(requested_ip) +
                                                  + Extentions.defstr_to_bytes(requested_time))
                                ips += requested_line
                            login_count -= 1
                        await self._send_data(writer, 3, ips)
                        Logger.log(f"Requested IPs was sent to {client_ip}:{client_port}.")
                    elif code == 5:   # Text message
                        if client_login is not None and client_login != "guest":
                            self.on_receive_msg_callback(data, client_login, client_ip + ":" + preferred_port)
                            await self._send_data(5)
                            Logger.log(f"Message from '{client_login}' ({client_ip}:{client_port}) was recieved.")
                        else:
                            await self._send_data(writer, 253, Extentions.defstr_to_bytes("You should login first."))
                    elif code == 6:   # File message
                        pass   # TODO: Add handling file messages
                    else:
                        msg, _ = Extentions.bytes_to_str(Extentions.int_to_bytes(code) + data)
                        Logger.log(f"Following message was resieved from {client_ip}:{client_port}:\n{msg}", "client")
                except ConnectionAbortedError:
                    Logger.log(f"Connection from {client_ip}:{client_port} closed by peer.", "client")
                    break
                except TimeoutError:
                    Logger.log(f"Connection from {client_ip}:{client_port} closed by timeout.", "client")
                    break
            writer.close()
        return _on_connect

    @Logger.logged("client")
    async def listen(self, port: int = 3502):
        self._server = await asyncio.start_server(self._on_connect_wrapper(), host="0.0.0.0", port=port)
        # await self._server.start_serving()   # REDO Recognize, why it doesn'n work.
        _endpoint = self._server.sockets[0].getsockname()
        Logger.log(f"Listening established on {_endpoint[0]}:{_endpoint[1]}.", "client")

    @Logger.logged("client")
    def __del__(self):
        if self._server is not None:
            self._server.close()


class _IException(Exception):
    message: str = None
    code: int = None

    def __init__(self, message, code):
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self):
        return self.message


class _IConnection:

    _reader: asyncio.StreamReader = None
    _writer: asyncio.StreamWriter = None
    _host: str = None
    _port: int = None

    @Logger.logged("client")
    def __init__(self, host: str, port: int):
        if (self.__class__ == _IConnection):
            _IConnection.__raise_not_implemented_error()
        i = host.find(":")
        if i != -1:
            self._port = int(host[i + 1:])
            self._host = host[:i]
        else:
            self._host = host
            self._port = port

    @Logger.logged("client")
    def __del__(self):
        if self._writer is not None:
            self._writer.close()

    @Logger.logged("client")
    async def _get_data(self, timeout: int=5) -> (int, bytes):
        if (self.__class__ == _IConnection):
            self._raise_not_implemented_error()

        async def _l_get_data(length: int) -> (bytes):
            data = await asyncio.wait_for(self._reader.read(length), timeout=timeout)
            if data:
                return data
            else:
                raise ConnectionAbortedError()

        length, _ = Extentions.bytes_to_int(await _l_get_data(4))
        result = await _l_get_data(length)
        return (result[0], result[1:])

    @Logger.logged("client")
    async def _send_data(self, code: int, data: bytes=bytes()):
        if (self.__class__ == _IConnection):
            self._raise_not_implemented_error()
        data_to_send = Extentions.int_to_bytes(len(data) + 1) + bytes([code]) + data
        self._writer.write(data_to_send)
        await self._writer.drain()

    @Logger.logged("client")
    async def _check_connection(self, timeout: int=5) -> bool:
        if (self.__class__ == _IConnection):
            self._raise_not_implemented_error()
        await self._send_data(0)
        try:
            code, _ = await self._get_data(timeout)
        except ConnectionAbortedError:
            return False
        return code == 0

    @Logger.logged("client")
    async def _recreate_connection(self):
        if (self.__class__ == _IConnection):
            self._raise_not_implemented_error()
        if self._writer is None or not await self._check_connection(1):
            try:
                connection = await asyncio.wait_for(asyncio.open_connection(self._host, self._port), 1)
            except (OSError, TimeoutError):
                self._raise_customised_exception(f"Couldn't (re)create connection with ({self._host}:{self._port}).", 251)
                return
            self._reader, self._writer = connection
            if await self._check_connection(1):
                Logger.log(f"Connection with ({self._host}:{self._port}) was established.", "client")
                return
        self._raise_customised_exception("Couldn't (re)create connection with ({self._host}:{self._port}).", 251)

    @staticmethod
    def _raise_customised_exception(message: str, code: int):
        raise _IException(message, code)

    @staticmethod
    def _raise_not_implemented_error():
        raise NotImplementedError("'_IConnection' was conceived as abstract." +
                                  + "\nYou mustn't use it directly; instead, inherit from it.")


class ClientToServerException(_IException):
    pass


class ClientToServer(_IConnection):

    @Logger.logged("client")
    def __init__(self, host: str, port: int=3501):
        super().__init__(host, port)

    @staticmethod
    def _raise_customised_exception(message: str, code: int):
        raise ClientToServerException(message, code)

    @Logger.logged("client")
    async def registration(self, login: str, password: str):
        await self._recreate_connection()
        bts_login = Extentions.defstr_to_bytes(login)
        bts_password = Extentions.defstr_to_bytes(password)
        await self._send_data(1, bts_login + bts_password)
        code, data = await self._get_data()
        if code != 1:
            self._raise_customised_exception(Extentions.bytes_to_defstr(data)[0], code)
        Logger.log(f"User '{login}' was successfully registered.", "client")

    @Logger.logged("client")
    async def login(self, login: str, password: str):
        await self._recreate_connection()
        bts_login = Extentions.defstr_to_bytes(login)
        bts_password = Extentions.defstr_to_bytes(password)
        await self._send_data(2, bts_login + bts_password)
        code, data = await self._get_data()
        if code != 2:
            self._raise_customised_exception(Extentions.bytes_to_defstr(data)[0], code)
        Logger.log(f"Login as '{login}' was successful.", "client")

    @Logger.logged("client")
    async def get_IPs(self, logins: List[str]) -> List[Tuple[str, datetime]]:
        await self._recreate_connection()
        data = Extentions.int_to_bytes(len(logins))
        for i in range(0, len(logins)):
            data += Extentions.defstr_to_bytes(logins[i])
        await self._send_data(3, data)
        code, data = await self._get_data()
        if code != 3:
            self._raise_customised_exception(Extentions.bytes_to_defstr(data)[0], code)
        result = []
        count, data = Extentions.bytes_to_int(data)
        while count > 0:
            ip, data = Extentions.defstr_to_bytes(data)
            time, data = Extentions.defstr_to_bytes(data)
            if ip == "":
                result.append((None, None))
            else:
                result.append((ip, datetime.strptime(time, "%T %d.%m.%Y")))
            count -= 1
        Logger.log(f"Requested IPs were received.", "client")
        return result

    @Logger.logged("client")
    async def delete_user(self, login: str, password: str):
        await self._recreate_connection()
        bts_login = Extentions.defstr_to_bytes(login)
        bts_password = Extentions.defstr_to_bytes(password)
        await self._send_data(4, bts_login + bts_password)
        code, data = await self._get_data()
        if code != 2:
            self._raise_customised_exception(Extentions.bytes_to_defstr(data)[0], code)
        Logger.log(f"User '{login}' was successfully deleted.", "client")


class ClientToClientException(_IException):
    pass


class ClientToClient(_IConnection):

    login: str = None
    client_login: str = None

    @Logger.logged("client")
    def __init__(self, login: str, client_login: str, host: str, port: int=3502):
        self.login = login
        self.client_login = client_login
        super().__init__(host, port)

    @Logger.logged("client")
    async def _recreate_connection(self):
        if await super()._recreate_connection():
            await self._send_data(2, Extentions.defstr_to_bytes(self.login))
            code, data = await self._get_data()
            if code == 2 and (Extentions.bytes_to_defstr(code)[0] == self.client_login or self.login == "guest"):
                Logger.log(f"Connection with '{self.client_login}' ({self._host}:{self._port}) was established.", "client")
                return
        self._raise_customised_exception("Couldn't (re)create connection with '{self.client_login}' ({self._host}:{self._port}).", 251)

    @staticmethod
    def _raise_customised_exception(message: str, code: int):
        raise ClientToClientException(message, code)

    @Logger.logged("client")
    async def send_text_message(self, message: str):
        await self._recreate_connection()
        await self._send_data(5, Extentions.defstr_to_bytes(message))
        code, data = await self._get_data()
        if code != 5:
            self._raise_customised_exception(Extentions.bytes_to_defstr(data)[0], code)
        Logger.log("Message to '{self.client_login}' ({self._host}:{self._port}) was successfully sent.")

    @Logger.logged("client")
    async def get_IPs(self, logins: List[str]) -> List[Tuple[str, datetime]]:
        await self._recreate_connection()
        data_to_send = Extentions.int_to_bytes(len(logins))
        for login in logins:
            data_to_send += Extentions.defstr_to_bytes(login)
        await self._send_data(3, data_to_send)
        code, data = await self._get_data()
        if code != 3:
            self._raise_customised_exception(Extentions.bytes_to_defstr(data)[0], code)
        result = []
        for i in range(0, len(logins)):
            requested_ip, data = Extentions.bytes_to_defstr(data)
            requested_time, data = Extentions.bytes_to_defstr(data)
            if requested_ip == "":
                result.append((None, None))
            else:
                result.append((requested_ip, datetime.strptime(requested_time, "%T %d.%m.%Y")))
        return result

    @Logger.logged("client")
    async def get_server_IP(self) -> (str, datetime):
        return self.get_IPs(["server"])[0]
