# Encoding: utf-8

import asyncio
from concurrent.futures import TimeoutError
from P2P_lib import Logger, Extentions


class Listener:

    @staticmethod
    @Logger.logged("P2P_client.Listener")
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
    @Logger.logged("P2P_client.Listener")
    async def _send_data(writer: asyncio.StreamWriter, code: int, data: bytes=bytes()):
        data_to_send = Extentions._int_to_bytes(len(data) + 1) + bytes([code]) + data
        writer.write(data_to_send)
        await writer.drain()

    @staticmethod
    @Logger.logged("P2P_client.Listener")
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

    @Logger.logged("P2P_client.Listener")
    def main():
        Logger.log("", "client", file_only=True)
        loop = asyncio.get_event_loop()
        server_gen = asyncio.start_server(Listener._on_connect, host="0.0.0.0", port=3501)
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
