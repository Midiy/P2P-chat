#Encoding : utf-8

def log(message : str, mode : str = "server", file_only : bool = False):
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