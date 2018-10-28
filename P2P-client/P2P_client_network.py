# Encoding: utf-8

import asyncio
from concurrent.futures import TimeoutError
from P2P_lib import Logger, Extentions


class Listener:

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

    @staticmethod
    @Logger.logged("client")
    async def _on_connect(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        timeout = 5
        login = ""
        client_endpoint = writer.get_extra_info("peername")
        client_ip = client_endpoint[0]
        client_port = client_endpoint[1]
        Logger.log(f"Accepted connection from {client_ip}:{client_port}.", "client")
        while True:
            try:
                code, data = await Listener._get_data(reader, timeout)
                if code == 0:   # Ping
                    await Listener._send_data(writer, 0)
                    Logger.log(f"Ping was sent to {client_ip}:{client_port}.", "client")
                elif code == 2:   # Login

                    # TODO: Add handling other cases
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

    @Logger.logged("client")
    def listen(port: int = 3502):
        Logger.log("", "client", file_only=True)
        loop = asyncio.get_event_loop()
        server_gen = asyncio.start_server(Listener._on_connect, host="0.0.0.0", port=port)
        server = loop.run_until_complete(server_gen)
        # It seems like KeyboardInterrupt handled somewhere in
        # server() coroutine, then I have to add following line.

        async def _wait_for_interrupt():
            while True:
                await asyncio.sleep(1)

        loop.create_task(Listener._wait_for_interrupt())
        _server_endpoint = server.sockets[0].getsockname()
        Logger.log(f"Listening established on {_server_endpoint[0]}:{_server_endpoint[1]}.", "client")
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            Logger.log("Server was stopped by keyboard interrupt.", "client")
        finally:
            server.close()
            loop.close()


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
            Logger.log(f"Connection with ({self._host}:{self._port}) was established.", "client")


class ClientToServerException(Exception): pass


class ClientToServer(_IConnection):

    @Logger.logged("client")
    def __init__(self, host: str, port: int=3501):
        super().__init__(host, port)

    @Logger.logged("client")
    async def registration(self, login: str, password: str):
        self._recreate_connection()
        bts_login = Extentions.defstr_to_bytes(login)
        bts_password = Extentions.defstr_to_bytes(password)
        await self._send_data(1, bts_login + bts_password)
        code, data = self._get_data()
        if code != 1:
            raise ClientToServerException(Extentions.bytes_to_defstr(data))
        Logger.log(f"User '{login}' was successfully registered.", "client")

    @Logger.logged("client")
    async def login(self, login: str, password: str):
        self._recreate_connection()
        bts_login = Extentions.defstr_to_bytes(login)
        bts_password = Extentions.defstr_to_bytes(password)
        await self._send_data(2, bts_login + bts_password)
        code, data = self._get_data()
        if code != 2:
            raise ClientToServerException(Extentions.bytes_to_defstr(data))
        Logger.log(f"Login as '{login}' was successful.", "client")

    @Logger.logged("client")
    async def get_IPs(self, logins: list) -> list:
        self._recreate_connection()
        data = Extentions.int_to_bytes(len(logins))
        for i in range(0, len(logins)):
            data += Extentions.defstr_to_bytes(logins[i])
        self._send_data(3, data)
        code, data = self._get_data()
        if code != 3:
            raise ClientToServerException(Extentions.bytes_to_defstr(data))
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
        code, data = self._get_data()
        if code != 2:
            raise ClientToServerException(Extentions.bytes_to_defstr(data))
        Logger.log(f"User '{login}' was successfully deleted.", "client")


class ClientToClientException(Exception): pass


class ClientToClient(_IConnection):

    @Logger.logged("client")
    def __init__(self, host: str, port: int=3502):
        super().__init__(host, port)

    # TODO: Add some interaction with other client
