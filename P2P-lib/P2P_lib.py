# Encoding: utf-8
from time import asctime


class Logger:
    """
    Class provides all functionality, that connected with logging.
    """

    def logged(location: str):
        """
        Decorator intended to log unhandled exceptions in function.
        It invokes Logger.err_log().
        
        location - Path to decorated function (<module>.<class>.<etc>).
        """
        def _logged(func, *args):
            def wrapper(*args):
                try:
                    return func(*args)
                except Exception as ex:
                    Logger.err_log(ex, f"{location}.{func.__name__}()")
                    raise ex
            return wrapper
        return _logged

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

    @logged("P2P_lib.Logger")
    def log(message: str, mode: str="server", file_only: bool=False):
        """
        Logging message to console and file.

        message - Message to logging.
        mode - Log file will be named "<mode>.log"; default is "server".
        file_only - if True, message will not output to console; default is False.

        Log string is "[<time.asctime()>] : <message>".
        """
        str_time = asctime()
        str_message = f"[{str_time}] : {message}"
        if not file_only:
            print(str_message)
        log_file = open(f"{mode}.log", "at")
        log_file.write(str_message + "\n")
        log_file.close()


class Extentions:
    """
    Class provides converting from/to bytes.
    """

    @Logger.logged("P2P_lib.Extentions")
    def _int_to_bytes(i: int) -> bytes:
        if i >= 2 ** 32:
            raise ValueError("Integer must be 4-byte or less.")
        return bytes([(i & 0xFF000000) >> 24, (i & 0x00FF0000) >> 16, (i & 0x0000FF00) >> 8, i & 0x000000FF])

    @Logger.logged("P2P_lib.Extentions")
    def _defstr_to_bytes(st: str) -> bytes:
        return Extentions._int_to_bytes(len(st)) + bytes(st, "utf-8")

    @Logger.logged("P2P_lib.Extentions")
    def _bytes_to_int(bts: bytes, start: int=0) -> (int, bytes):
        return bts[start] << 24 | bts[start + 1] << 16 | bts[start + 2] << 8 | bts[start + 3], bts[4:]

    @Logger.logged("P2P_lib.Extentions")
    def _bytes_to_str(bts: bytes, start: int=0, length: int=-1) -> (str, bytes):
        if length == -1:
            return bts[start:].decode(), bytes()
        else:
            return bts[start:start + length].decode(), bts[start + length]

    @Logger.logged("P2P_lib.Extentions")
    def _bytes_to_defstr(bts: bytes, start: int=0) -> (str, bytes):
        length, _ = Extentions._bytes_to_int(bts, start)
        start += 4
        return bts[start:start + length].decode(), bts[:start - 4] + bts[start + length:]
