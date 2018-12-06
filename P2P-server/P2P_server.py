# Encoding: utf-8

import socket
import asyncio
from P2P_database import DataBaseServer
from concurrent.futures import TimeoutError
from P2P_lib import Logger, Extentions


_database: DataBaseServer = None


@Logger.logged()
async def _get_data(reader: asyncio.StreamReader, timeout: int=5) -> (int, bytes):
    async def _l_get_data(length: int) -> (bytes):
        data = await asyncio.wait_for(reader.read(length), timeout=timeout)
        if data:
            return data
        else:
            raise ConnectionResetError()
    length, _ = Extentions.bytes_to_int(await _l_get_data(4))
    result = await _l_get_data(length)
    return (result[0], result[1:])


@Logger.logged()
async def _send_data(writer: asyncio.StreamWriter, code: int, data: bytes=bytes()):
    data_to_send = Extentions.int_to_bytes(len(data) + 1) + bytes([code]) + data
    writer.write(data_to_send)
    await writer.drain()


@Logger.logged()
async def _on_connect(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    timeout = 5
    login = None
    client_endpoint = writer.get_extra_info("peername")
    client_ip = client_endpoint[0]
    if client_ip == "127.0.0.1":
        client_ip = socket.gethostbyname(socket.gethostname())
    client_port = client_endpoint[1]
    Logger.log(f"Accepted connection from {client_ip}:{client_port}.")
    while True:
        try:
            code, data = await _get_data(reader, timeout)
            if code == 0:   # Ping
                await _send_data(writer, 0)
                Logger.log(f"Ping was sent to {client_ip}:{client_port}.")
            elif code == 1:   # Registration
                received_login, data = Extentions.bytes_to_defstr(data)
                if received_login == "server" or received_login == "guest":
                    await _send_data(writer, 252, Extentions.defstr_to_bytes("'server' is service login!"))
                    continue
                login = received_login
                pass_hash, data = Extentions.bytes_to_defstr(data)
                if data == bytes():
                    preferred_port = "3502"
                else:
                    preferred_port, _ = Extentions.bytes_to_defstr(data)
                Logger.log(f"Registration {client_ip}:{client_port} as '{login}'...")
                if (_database.search_ip_and_last_time(login)[0] != "0.0.0.0"):
                    await _send_data(writer, 254, Extentions.defstr_to_bytes("This login is already registered."))
                    Logger.log(f"Registration {client_ip}:{client_port} as '{login}' was refused.")
                    continue
                _database.add_client(login, pass_hash, client_ip + ":" + preferred_port)
                pass_hash = None
                await _send_data(writer, 1)
                Logger.log(f"Registration {client_ip}:{client_port} as '{login}' was confirmed.")
                timeout = 60
            elif code == 2:   # Login
                received_login, data = Extentions.bytes_to_defstr(data)
                if received_login == "server" or received_login == "guest":
                    await _send_data(writer, 252, Extentions.defstr_to_bytes("'server' is service login!"))
                    continue
                login = received_login
                pass_hash, data = Extentions.bytes_to_defstr(data)
                if data == bytes():
                    preferred_port = "3502"
                else:
                    preferred_port, _ = Extentions.bytes_to_defstr(data)
                Logger.log(f"Login {client_ip}:{client_port} as '{login}'...")
                if (_database.search_password(login) != pass_hash):
                    await _send_data(writer, 255, Extentions.defstr_to_bytes("Password is incorrect."))
                    Logger.log(f"Login {client_ip}:{client_port} as '{login}' was refused.")
                    continue
                pass_hash = ""
                await _send_data(writer, 2)
                Logger.log(f"Login {client_ip}:{client_port} as '{login}' was confirmed.")
                timeout = 60
                _database.update_ip(login, client_ip + ":" + preferred_port)
            elif code == 3:   # IP updating request
                Logger.log(f"IPs was requested by {client_ip}:{client_port}")
                login_count, data = Extentions.bytes_to_int(data)
                ips = Extentions.int_to_bytes(login_count)
                while login_count > 0:
                    requested_login, data = Extentions.bytes_to_defstr(data)
                    tmp = _database.search_ip_and_last_time(requested_login)
                    if tmp[0] == "0.0.0.0":
                        requested_ip = ""
                        requested_time = ""
                    else:
                        requested_ip, requested_time = tmp
                        requested_time = requested_time.strftime("%T %d.%m.%Y")
                    requested_line = (Extentions.defstr_to_bytes(requested_ip) +
                                      Extentions.defstr_to_bytes(requested_time))
                    ips += requested_line
                    login_count -= 1
                await _send_data(writer, 3, ips)
                Logger.log(f"Requested IPs was sent to {client_ip}:{client_port}.")
            elif code == 4:   # Delete user request
                if login is None:
                    await _send_data(writer, 253, Extentions.defstr_to_bytes("You should login first."))
                else:
                    pass_hash, _ = Extentions.bytes_to_defstr(data)
                    Logger.log(f"Deleting of '{login}' was requested by {client_ip}:{client_port}...")
                    if (_database.search_password(login) != pass_hash):
                        await _send_data(writer, 255, Extentions.defstr_to_bytes("Password is incorrect."))
                        Logger.log(f"Deleting of '{login}' requested by {client_ip}:{client_port} was refused.")
                        continue
                    _database.del_client(login)
                    Logger.log(f"Deleting of '{login}' requested by {client_ip}:{client_port} was confirmed.")
                    await _send_data(writer, 4)
                    timeout = 5
                    login = ""
                    pass_hash = ""
            else:
                msg, _ = Extentions.bytes_to_str(Extentions.int_to_bytes(code) + data)
                Logger.log(f"Following message was resieved from {client_ip}:{client_port}:\n{msg}")
        except ConnectionResetError:
            Logger.log(f"Connection from {client_ip}:{client_port} closed by peer.")
            break
        except TimeoutError:
            Logger.log(f"Connection from {client_ip}:{client_port} closed by timeout.")
            break
    writer.close()

@Logger.logged()
async def _wait_for_interrupt():
    while True:
        await asyncio.sleep(1)


@Logger.logged()
def main():
    Logger.log("", file_only=True)
    global _database
    _database = DataBaseServer()
    _database.init()
    loop = asyncio.get_event_loop()
    server_gen = asyncio.start_server(_on_connect, host="0.0.0.0", port=3501)
    server = loop.run_until_complete(server_gen)
    # It seems like KeyboardInterrupt handled somewhere in
    # server() coroutine, then I have to add following line.
    loop.create_task(_wait_for_interrupt())
    _server_endpoint = server.sockets[0].getsockname()
    Logger.log(f"Listening established on {_server_endpoint[0]}:{_server_endpoint[1]}.")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        Logger.log("Server was stopped by keyboard interrupt.")
    finally:
        server.close()
        loop.close()

main()
del _database
