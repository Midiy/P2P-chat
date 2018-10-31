# Encoding: utf-8

import asyncio
from concurrent.futures import TimeoutError
from P2P_lib import Logger, Extentions
from P2P_database import DataBaseClient


class Listener:

    _server: asyncio.AbstractServer = None
    _loop: asyncio.AbstractEventLoop = None
    _server_endpoint: str = None
    _database: DataBaseClient = None

    login: str = None
    on_receive_msg_callback = None

    @Logger.logged("client")
    def __init__(self, login: str, on_receive_msg_callback, server_endpoint: str,
                 database: DataBaseClient, listen: bool=True, port: int=3502):
        self.login = login
        self.on_receive_msg_callback = on_receive_msg_callback
        self._server_endpoint = server_endpoint
        self._database = database
        if listen:
            self.listen(3502)
        
    @staticmethod
    @Logger.logged("client")
    async def _get_data(reader: asyncio.StreamReader, timeout: int=5) -> (int, bytes):

        async def _l_get_data(length: int) -> (bytes):
            data = await asyncio.wait_for(reader.read(length), timeout=timeout)
            if data:
                return data
            else:
                raise ConnectionAbortedError()

        length, _ = Extentions._bytes_to_int(await _l_get_data(4))
        result = await _l_get_data(length)
        return (result[0], result[1:])

    @staticmethod
    @Logger.logged("client")
    async def _send_data(writer: asyncio.StreamWriter, code: int, data: bytes=bytes()):
        data_to_send = Extentions._int_to_bytes(len(data) + 1) + bytes([code]) + data
        writer.write(data_to_send)
        await writer.drain()

    @Logger.logged("client")
    def _on_connect_wrapper(self):
        async def _on_connect(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            timeout = 5
            client_login = None
            client_endpoint = writer.get_extra_info("peername")
            client_ip = client_endpoint[0]
            client_port = client_endpoint[1]
            Logger.log(f"Accepted connection from {client_ip}:{client_port}.", "client")
            while True:
                try:
                    code, data = await _get_data(reader, timeout)
                    if code == 0:   # Ping
                        await _send_data(writer, 0)
                        Logger.log(f"Ping was sent to {client_ip}:{client_port}.", "client")
                    elif code == 2:   # Login
                        received_login, _ = Extentions.bytes_to_defstr(data)
                        if received_login == "server":
                            await _send_data(writer, 252, Extentions.defstr_to_bytes("'server' is service login!"))
                            continue
                        client_login = received_login
                        await _send_data(writer, 2, Extentions.defstr_to_bytes(login))
                        timeout = 60
                        Logger.log(f"Login {client_ip}:{client_port} as '{client_login}' was confirmed.")
                    elif code == 3:   # IP updating request
                        login_count, data = Extentions.bytes_to_int(data)
                        ips = Extentions.int_to_bytes(login_count)
                        while login_count > 0:
                            requested_login, data = Extentions.bytes_to_defstr(data)
                            if requested_login == "server":
                                ips += Extentions.defstr_to_bytes(_server_endpoint)
                            else:
                                ips += Extentions.defstr_to_bytes(_database.search_ip(requested_login))
                            login_count -= 1
                        await self._send_data(writer, 3, ips)
                        Logger.log(f"Requested IPs was sent to {client_ip}:{client_port}.")
                    elif code == 5:   # Text message
                        if client_login is not None and client_login != "guest":
                            self.on_receive_msg_callback(data, client_login, client_endpoint)
                            await _send_data(5)
                            Logger.log(f"Message from '{client_login}' ({client_ip}:{client_port}) was recieved.")
                        else:
                            await _send_data(writer, 253, Extentions.defstr_to_bytes("You should login first."))
                    elif code == 6:   # File message

                        # TODO: Add handling file messages
                        pass

                    else:
                        msg, _ = Extentions._bytes_to_str(Extentions._int_to_bytes(code) + data)
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
    def listen(self, port: int = 3502):
        Logger.log("", "client", file_only=True)
        self._loop = asyncio.get_event_loop()
        server_gen = asyncio.start_server(self._on_connect_wrapper(), host="0.0.0.0", port=port)
        self._server = self._loop.run_until_complete(server_gen)
        # It seems like KeyboardInterrupt handled somewhere in
        # server() coroutine, then I have to add following 4 lines.

        async def _wait_for_interrupt():
            while True:
                await asyncio.sleep(1)

        self._loop.create_task(_wait_for_interrupt())
        _server_endpoint = self._server.sockets[0].getsockname()
        Logger.log(f"Listening established on {_server_endpoint[0]}:{_server_endpoint[1]}.", "client")
        try:
            self._loop.run_forever()
        except KeyboardInterrupt:
            Logger.log("Server was stopped by keyboard interrupt.", "client")
        finally:
            self._server.close()
            self._loop.close()

    @Logger.logged("client")
    def __del__(self):
        if self._server is not None:
            self._server.close()
        if self._loop is not None:
            self._loop.close()


class _IConnection:

    _reader: asyncio.StreamReader = None
    _writer: asyncio.StreamWriter = None
    _host: str = None
    _port: int = None

    @Logger.logged("client")
    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port
        self._recreate_connection()

    @Logger.logged("client")
    def __del__(self):
        if self._writer is not None:
            self._writer.close()

    @Logger.logged("client")
    async def _get_data(self, timeout: int=5) -> (int, bytes):

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
        data_to_send = Extentions.int_to_bytes(len(data) + 1) + bytes([code]) + data
        self._writer.write(data_to_send)
        await self._writer.drain()

    @Logger.logged("client")
    async def _check_connection(self, timeout: int=5) -> bool:
        await self._send_data(0)
        code, _ = await self._get_data(timeout)
        return code == 0

    @Logger.logged("client")
    def _recreate_connection(self):
        if self._writer is None or self._writer.is_closing() or not self._check_connection(1):
            connection = asyncio.open_connection(self._host, self._port)
            self._reader, self._writer = asyncio.run(connection)
            if self._check_connection(1):
                Logger.log(f"Connection with ({self._host}:{self._port}) was established.", "client")
                return
        _raise_customised_exception("Couldn't (re)create connection with ({self._host}:{self._port}).")

    @staticmethod
    def _raise_customised_exception(message: str):
        raise Exception(message)


class ClientToServerException(Exception): pass


class ClientToServer(_IConnection):

    @Logger.logged("client")
    def __init__(self, host: str, port: int=3501):
        super().__init__(host, port)

    @staticmethod
    def _raise_customised_exception(message: str):
        raise ClientToServerException(message)

    @Logger.logged("client")
    async def registration(self, login: str, password: str):
        self._recreate_connection()
        bts_login = Extentions.defstr_to_bytes(login)
        bts_password = Extentions.defstr_to_bytes(password)
        await self._send_data(1, bts_login + bts_password)
        code, data = await self._get_data()
        if code != 1:
            _raise_customised_exception(Extentions.bytes_to_defstr(data)[0])
        Logger.log(f"User '{login}' was successfully registered.", "client")

    @Logger.logged("client")
    async def login(self, login: str, password: str):
        self._recreate_connection()
        bts_login = Extentions.defstr_to_bytes(login)
        bts_password = Extentions.defstr_to_bytes(password)
        await self._send_data(2, bts_login + bts_password)
        code, data = await self._get_data()
        if code != 2:
            _raise_customised_exception(Extentions.bytes_to_defstr(data)[0])
        Logger.log(f"Login as '{login}' was successful.", "client")

    @Logger.logged("client")
    async def get_IPs(self, logins: list) -> list:
        self._recreate_connection()
        data = Extentions.int_to_bytes(len(logins))
        for i in range(0, len(logins)):
            data += Extentions.defstr_to_bytes(logins[i])
        await self._send_data(3, data)
        code, data = await self._get_data()
        if code != 3:
            _raise_customised_exception(Extentions.bytes_to_defstr(data)[0])
        result = []
        count, data = Extentions.bytes_to_int(data)
        while count > 0:
            ip, data = Extentions.defstr_to_bytes(data)
            result.append(ip)
            count -= 1
        Logger.log(f"Requested IPs were received.", "client")
        return result

    @Logger.logged("client")
    async def delete_user(self, login: str, password: str):
        self._recreate_connection()
        bts_login = Extentions.defstr_to_bytes(login)
        bts_password = Extentions.defstr_to_bytes(password)
        await self._send_data(4, bts_login + bts_password)
        code, data = await self._get_data()
        if code != 2:
            _raise_customised_exception(Extentions.bytes_to_defstr(data)[0])
        Logger.log(f"User '{login}' was successfully deleted.", "client")


class ClientToClientException(Exception): pass


class ClientToClient(_IConnection):

    login: str = None
    client_login: str = None

    @Logger.logged("client")
    def __init__(self, login: str, client_login: str, host: str, port: int=3502):
        self.login = login
        self.client_login = client_login
        super().__init__(host, port)

    @Logger.logged("client")
    def _recreate_connection(self):
        if super()._recreate_connection():
            self._send_data(2, Extentions.defstr_to_bytes(login))
            code, data = self._get_data()
            if code == 2 and Extentions.bytes_to_defstr(code)[0] == client_login:
                Logger.log(f"Connection with '{self.client_login}' ({self._host}:{self._port}) was established.", "client")
                return
        _raise_customised_exception("Couldn't (re)create connection with '{self.client_login}' ({self._host}:{self._port}).")

    @staticmethod
    def _raise_customised_exception(message: str):
        raise ClientToClientException(message)

    @Logger.logged("client")
    async def send_text_message(self, message: str):
        self._recreate_connection()
        await self._send_data(5, Extentions.defstr_to_bytes(message))
        code, data = await self._get_data()
        if code != 5:
            _raise_customised_exception(Extentions.bytes_to_defstr(data)[0])
        Logger.log("Message to '{self.client_login}' ({self._host}:{self._port}) was successfully sent.")

    @Logger.logged("client")
    async def get_IPs(self, logins: list) -> list:
        self._recreate_connection()
        data_to_send = Extentions.int_to_bytes(len(logins))
        for login in logins:
            data_to_send += Extentions.defstr_to_bytes(login)
        await self._send_data(3, data_to_send)
        code, data = await self._get_data()
        if code != 3:
            _raise_customised_exception(Extentions.bytes_to_defstr(data)[0])
        result = []
        for i in range(0, len(logins)):
            requested_ip, data = Extentions.bytes_to_defstr(data)
            result.append(requested_ip)
        return result

    @Logger.logged("client")
    async def get_server_IP(self) -> str:
        return self.get_IPs("server")[0]
    # TODO: Add some interaction with other client
