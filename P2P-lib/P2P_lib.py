# Encoding: utf-8

from time import asctime


class Logger:
    """
    Class provides all functionality, that connected with logging.
    """

    def logged(mode: str = "server"):
        """
        Decorator intended to log unhandled exceptions in function.
        It invokes Logger.err_log().

        location - Path to decorated function (<module>.<class>.<etc>).
        """
        def _logged(func, *args, **kwargs):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as ex:
                    Logger.err_log(ex, f"{func.__module__}.{func.__qualname__}()", mode)
                    raise ex
            return wrapper
        return _logged

    @staticmethod
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

    @staticmethod
    def log(message: str, mode: str="server", file_only: bool=False):
        """
        Logging message to console and file.

        message - Message to logging.
        mode - Log file will be named "<mode>.log"; default is "server".
        file_only - if True, message will not output to console; default is False.

        Log string is "[<time.asctime()>] : <message>".
        """

        @Logger.logged(mode)
        def _log():
            str_time = asctime()
            str_message = f"[{str_time}] : {message}"
            if not file_only:
                print(str_message)
            log_file = open(f"{mode}.log", "at")
            log_file.write(str_message + "\n")
            log_file.close()

        _log()


class Extentions:
    """
    Class provides converting from/to bytes.
    """

    @staticmethod
    @Logger.logged()
    def int_to_bytes(i: int) -> bytes:
        if i >= 2 ** 32:
            raise ValueError("Integer must be 4-byte or less.")
        return bytes([(i & 0xFF000000) >> 24, (i & 0x00FF0000) >> 16, (i & 0x0000FF00) >> 8, i & 0x000000FF])

    @staticmethod
    @Logger.logged()
    def defstr_to_bytes(st: str) -> bytes:
        return Extentions.int_to_bytes(len(st)) + bytes(st, "utf-8")

    @staticmethod
    @Logger.logged()
    def bytes_to_int(bts: bytes, start: int=0) -> (int, bytes):
        return bts[start] << 24 | bts[start + 1] << 16 | bts[start + 2] << 8 | bts[start + 3], bts[4:]

    @staticmethod
    @Logger.logged()
    def bytes_to_str(bts: bytes, start: int=0, length: int=-1) -> (str, bytes):
        if length == -1:
            return bts[start:].decode(), bytes()
        else:
            return bts[start:start + length].decode(), bts[start + length]

    @staticmethod
    @Logger.logged()
    def bytes_to_defstr(bts: bytes, start: int=0) -> (str, bytes):
        length, _ = Extentions.bytes_to_int(bts, start)
        start += 4
        return bts[start:start + length].decode(), bts[:start - 4] + bts[start + length:]
