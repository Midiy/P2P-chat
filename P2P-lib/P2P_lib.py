#Encoding : utf-8

from time import asctime

def log(message: str, mode: str="server", file_only: bool=False):
    """
    Logging message to console and file.

    message - Message to logging.
    mode - Log file will be named "<mode>.log"; default is "server".
    file_only - if True, message will not output to console; default is False.

    Log string is "[<time.asctime()>] : <message>".
    """
    try:
        str_time = asctime()
        str_message = f"[{str_time}] : {message}"
        if not file_only:
            print(str_message)
        log_file = open(f"{mode}.log", "at")
        log_file.write(str_message + "\n")
        log_file.close()
    except Exception as e:
        err_log(e.args[0], "P2P_lib.log()")
        raise e

def err_log(message: str, source: str, mode: str="server", file_only: bool=False):
    """
    Logging occured exception to console and file.

    message - Message to logging.
    source - Function, where exception occured
    mode - Log file will be named "<mode>.log"; default is "server".
    file_only - if True, message will not output to console; default is False.

    Log string is "[<time.asctime()>] : Unhandled exception in <source>: <message>".
    """
    str_time = asctime()
    str_message = f"[{str_time}] : Unhandled exception in {source}: {message}"
    if not file_only:
        print(str_message)
    try:
        log_file = open(f"{mode}.log", "at")
        log_file.write(str_message + "\n")
        log_file.close()
    except Exception as e:   # DEBUG
        print(e)