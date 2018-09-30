#Encoding : utf-8

import asyncio

console_sync = asyncio.Lock()

async def log(message : str, mode : str = "server", file_only : bool = False):
    import time
    await console_sync.acquire()
    str_time = time.asctime()
    str_message = f"[{str_time}] : {message}"
    if not message.endswith("."):
        str_message += "."
    if not file_only:
        print(str_message)
    try:
        log_file = open(f"{mode}.log", "at")
        log_file.write(str_message + "\n")
        log_file.close()
    except Exception as e:
        print(e)
    console_sync.release()