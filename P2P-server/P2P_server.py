#Encoding: utf-8

import asyncio
import P2P_database
from concurrent.futures import TimeoutError
from P2P_lib import log, err_log

#region Extentions

# Functions, that provides conversions int->bytes, str_with_len->bytes,
# bytes->int and bytes->str_with_len

def _int_to_bytes(i: int) -> bytes:
    try:
        if i >= 2 ** 32:
            raise ValueError("Integer must be 4-byte or less.")
        return bytes([(i & 0xFF000000) >> 24, (i & 0x00FF0000) >> 16, (i & 0x0000FF00) >> 8, i & 0x000000FF])
    except Exception as e:
        err_log(e, "P2P_server._int_to_bytes()")
        raise e

def _defstr_to_bytes(st: str) -> bytes:
    try:
        return _int_to_bytes(len(st)) + bytes(st, "utf-8")
    except Exception as e:
        err_log(e, "P2P_server._defstr_to_bytes()")
        raise e

def _bytes_to_int(bts: bytes, start: int=0) -> (int, bytes):
    try:
        return bts[start] << 24 | bts[start + 1] << 16 | bts[start + 2] << 8 | bts[start + 3], bts[4:]
    except Exception as e:
        err_log(e, "P2P_server._bytes_to_int()")
        raise e

def _bytes_to_str(bts: bytes, start: int=0, length: int=-1) -> (str, bytes):
    try:
        if length == -1:
            return bts[start:].decode(), bytes()
        else:
            return bts[start:start + length].decode(), bts[start + length]
    except Exception as e:
        err_log(e, "P2P_server._bytes_to_str()")
        raise e

def _bytes_to_defstr(bts: bytes, start: int=0) -> (str, bytes):
    try:
        length, _ = _bytes_to_int(bts, start)
        start += 4
        return bts[start:start + length].decode(), bts[:start - 4] + bts[start + length:]
    except Exception as e:
        err_log(e, "P2P_server._bytes_to_defstr()")
        raise e
#endregion

async def _get_data(reader: asyncio.StreamReader, timeout: int=5) -> (int, bytes):
    try:
        async def _l_get_data(len: int) -> (bytes):
            data = await asyncio.wait_for(reader.read(len), timeout=timeout)
            if data:
                return data
            else:
                raise ConnectionAbortedError()
        length, _ = _bytes_to_int(await _l_get_data(4))
        result = await _l_get_data(length)
        return (result[0], result[1:])
    except Exception as e:
        err_log(e, "P2P_server._get_data()")
        raise e

async def _send_data(writer: asyncio.StreamWriter, code: int, data: bytes=bytes()):
    try:
        data_to_send = _int_to_bytes(len(data) + 1) + bytes([code]) + data
        writer.write(data_to_send)
        await writer.drain()
    except Exception as e:
        err_log(e, "P2P_server._send_data()")
        raise e

async def _on_connect(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        timeout = 5
        login = ""
        client_endpoint = writer.get_extra_info("peername")
        client_ip = client_endpoint[0]
        client_port = client_endpoint[1]
        log(f"Accepted connection from {client_ip}:{client_port}.")
        while True:
            try:
                code, data = await _get_data(reader, timeout)
                if code == 0:   # Ping
                    await _send_data(writer, 0)
                    log(f"Ping was sent to {client_ip}:{client_port}.")
                elif code == 1:   # Registration
                    login, data = _bytes_to_defstr(data)
                    pass_hash, _ = _bytes_to_defstr(data)
                    log(f"Registration {client_ip}:{client_port} as '{login}'...")
                    if (P2P_database.db_search_ip(login) != "0.0.0.0"):
                        await _send_data(writer, 254, _defstr_to_bytes("This login is already registered."))
                        log(f"Registration {client_ip}:{client_port} as '{login}' was refused.")
                        continue
                    P2P_database.db_add_client(login, pass_hash, client_ip)
                    pass_hash = ""
                    await _send_data(writer, 1)
                    log(f"Registration {client_ip}:{client_port} as '{login}' was confirmed.")
                    timeout = 60
                elif code == 2:   # Login
                    login, data = _bytes_to_defstr(data)
                    pass_hash, _ = _bytes_to_defstr(data)
                    log(f"Login {client_ip}:{client_port} as '{login}'...")
                    if (P2P_database.db_search_password(login) != pass_hash):
                        await _send_data(writer, 255, _defstr_to_bytes("Password is incorrect."))
                        log(f"Login {client_ip}:{client_port} as '{login}' was refused.")
                        continue
                    pass_hash = ""
                    await _send_data(writer, 2)
                    log(f"Login {client_ip}:{client_port} as '{login}' was confirmed.")
                    timeout = 60
                    P2P_database.db_update_ip(login, client_ip)
                elif code == 3:   # IP updating request
                    log(f"IPs was requested by {client_ip}:{client_port}")
                    login_count, data = _bytes_to_int(data)
                    ips = _int_to_bytes(login_count)
                    while login_count > 0:
                        requested_login, data = _bytes_to_defstr(data)
                        ips += _defstr_to_bytes(P2P_database.db_search_ip(requested_login))
                        login_count -= 1
                    await _send_data(writer, 3, ips)
                    log(f"Requested IPs was sent to {client_ip}:{client_port}.")
                elif code == 4:   # Delete user request
                    pass_hash, _ = _bytes_to_defstr(data)
                    log(f"Deleting of '{login}' was requested by {client_ip}:{client_port}...")
                    if (P2P_database.db_search_password(login) != pass_hash):
                        await _send_data(writer, 255, _defstr_to_bytes("Password is incorrect."))
                        log(f"Deleting of '{login}' requested by {client_ip}:{client_port} was refused.")
                        continue
                    P2P_database.db_del_client(login)
                    log(f"Deleting of '{login}' requested by {client_ip}:{client_port} was confirmed.")
                    await _send_data(writer, 4)
                    timeout = 5
                    login = ""
                    pass_hash = ""
                else:
                    msg, _ = _bytes_to_str(_int_to_bytes(code) + data)
                    log(f"Following message was resieved from {client_ip}:{client_port}:\n{msg}")
            except ConnectionAbortedError:
                log(f"Connection from {client_ip}:{client_port} closed by peer.")
                break
            except TimeoutError:
                log(f"Connection from {client_ip}:{client_port} closed by timeout.")
                break
        writer.close
    except Exception as e:
        err_log(e, "P2P_server._on_connect()")
        raise e

async def _wait_for_interrupt():
    while True:
        await asyncio.sleep(1)
    
if __name__ == "__main__":
    try:
        log("", file_only=True)
        P2P_database.db_init()
        loop = asyncio.get_event_loop()
        server_gen = asyncio.start_server(_on_connect, host="0.0.0.0", port=3501)
        server = loop.run_until_complete(server_gen)
        # It seems like KeyboardInterrupt handled somewhere in
        # server() coroutine, then I have to add following line.
        loop.create_task(_wait_for_interrupt())
        _server_endpoint = server.sockets[0].getsockname()
        log(f"Listening established on {_server_endpoint[0]}:{_server_endpoint[1]}.")
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            log("Server was stopped by keyboard interrupt.")
        finally:
            server.close()
            loop.close()
            P2P_database.db_fini()
    except Exception as e:
        err_log(e, "P2P_server.main()")   
        raise e