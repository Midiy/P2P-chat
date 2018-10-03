#Encoding: utf-8

import asyncio
import concurrent.futures
from P2P_lib import log

async def get_data(reader : asyncio.StreamReader, timeout : int = 10) -> (int, bytes):
    async def _get_data(len : int):
        data = await asyncio.wait_for(reader.read(len), timeout=timeout)
        if data:
            return data
        else:
            raise ConnectionAbortedError()
    len = await _get_data(1)
    result = await _get_data(int(len[0]))
    return (int(result[0]), result[1:])

async def send_data(writer : asyncio.StreamReader, code : int, data : bytes):
    data_to_send = bytes([len(data) + 1, code]);
    data_to_send += data
    await writer.write(data_to_send)
    await writer.drain()

async def handle_connection(reader : asyncio.StreamReader, writer : asyncio.StreamWriter):
    peername = writer.get_extra_info("peername")
    log(f"Accepted connection from {peername}.")
    while True:
        try:
            code, data = await get_data(reader)
            # TODO: Reaction on recieved data.
        except ConnectionAbortedError:
            log(f"Connection from {peername} closed by peer.")
            break
        except concurrent.futures.TimeoutError:
            log(f"Connection from {peername} closed by timeout.")
            break
    writer.close()

async def wait_for_interrupt():
    while True:
        await asyncio.sleep(5)
    
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    server_gen = asyncio.start_server(handle_connection, port=3501)
    server = loop.run_until_complete(server_gen)
    # It seems like KeyboardInterrupt handled somewhere in
    # server() coroutine, then I have to add following line.
    loop.create_task(wait_for_interrupt())
    log(f"Listening established on {server.sockets[0].getsockname()}.")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        log("Server was stopped by keyboard interrupt.")
    finally:
        server.close()
        loop.close()