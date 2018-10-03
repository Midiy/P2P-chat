#Encoding : utf-8

def log(message : str, mode : str = "server", file_only : bool = False):
    """
    Logging message to console and file.

    message - Message to logging.
    mode - Log file will be named "<mode>.log"; default is "server".
    file_only - if True, message will not output to console; default is False.

    Log string is "[<time.asctime()>] : <message>".
    """
    from time import asctime
    str_time = asctime()
    str_message = f"[{str_time}] : {message}"
    if not file_only:
        print(str_message)
    try:
        log_file = open(f"{mode}.log", "at")
        log_file.write(str_message + "\n")
        log_file.close()
    except Exception as e:
        print(e)