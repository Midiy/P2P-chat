# Encoding: utf-8

from time import asctime
import igd
from curio import run


class Logger:
    """
    Class provides all functionality, that connected with logging.
    """

    def logged(mode: str = "server", console_only: bool=False):
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
                    Logger.err_log(ex, f"{func.__module__}.{func.__qualname__}()", mode, console_only=console_only)
                    raise ex
            return wrapper
        return _logged

    @staticmethod
    def err_log(message: str, source: str, mode: str="server", file_only: bool=False, console_only: bool=False):
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
        if not console_only:
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
    @Logger.logged(console_only=True)
    def int_to_bytes(i: int) -> bytes:
        if i >= 2 ** 32:
            raise ValueError("Integer must be 4-byte or less.")
        return bytes([(i & 0xFF000000) >> 24, (i & 0x00FF0000) >> 16, (i & 0x0000FF00) >> 8, i & 0x000000FF])

    @staticmethod
    @Logger.logged(console_only=True)
    def defstr_to_bytes(st: str) -> bytes:
        return Extentions.int_to_bytes(len(st)) + bytes(st, "utf-8")

    @staticmethod
    @Logger.logged(console_only=True)
    def bytes_to_int(bts: bytes, start: int=0) -> (int, bytes):
        return bts[start] << 24 | bts[start + 1] << 16 | bts[start + 2] << 8 | bts[start + 3], bts[4:]

    @staticmethod
    @Logger.logged(console_only=True)
    def bytes_to_str(bts: bytes, start: int=0, length: int=-1) -> (str, bytes):
        if length == -1:
            return bts[start:].decode(), bytes()
        else:
            return bts[start:start + length].decode(), bts[start + length]

    @staticmethod
    @Logger.logged(console_only=True)
    def bytes_to_defstr(bts: bytes, start: int=0) -> (str, bytes):
        length, _ = Extentions.bytes_to_int(bts, start)
        start += 4
        return bts[start:start + length].decode(), bts[:start - 4] + bts[start + length:]


class UPnP:

    class UPnPException(Exception):
        pass

    port: int = None
    is_opened: bool = None
    external_ip: int = None

    _exact: bool = None
    _gateway: igd.Gateway = None
    _internal_port: int=None

    def __init__(self, port: int=3501, is_port_exact: bool=True):
        self.port = port
        self._internal_port = port
        self.is_opened = False
        self._exact = is_port_exact
        self._gateway = run(igd.find_gateway())
        if self._gateway is None:
            raise UPnPException(f"There are no any UPnP-supporting devices!")
        self.external_ip = run(self._gateway.get_ext_ip())

    def open_port(self, description: str=""):
        if self.is_opened:
            raise UPnPException(f"Port {self.port} has already been opened!")
        port_mappings = run(self._gateway.get_port_mappings())
        opened_ports = set([i.external_port for i in port_mappings])
        while not opened_ports.isdisjoint((self.port)):
            if self._exact:
                raise UPnPException(f"Port {self.port} has been already opened by other program!")
            self.port += 1
        new_mapping = igd.proto.PortMapping('', self.popen_port, self._internal_port, 'TCP', None, True, description, -1)
        self._gateway.add_port_mapping(new_mapping)
        self.is_opened = True

    def close_port(self):
        if not self.is_opened:
            raise UPnPException(f"Port {self.port} hasn't been opened yet!")
        port_mappings = run(self._gateway.get_port_mappings())
        opened_ports = set([i.external_port for i in port_mappings])
        if not opened_ports.isdisjoint((self.port)):
            raise UPnPException(f"Port {self.port} wasn't found in list of port mappings.")
        self._gateway.delete_port_mapping(self.port, "TCP")
        self.is_opened = False
