# Encoding: utf-8

from P2P_lib import Extentions, Logger
from socket import socket
from os import remove


class TestClientException(Exception):

    _message: str = ""

    def __init__(self, message: str):
        self._message = message

    def __str__(self):
        return self._message    


@Logger.logged("P2P_TestClient", "test_client")
def _get_gata(sock: socket) -> (int, bytes):
    length, _ = Extentions.bytes_to_int(sock.recv(4))
    result = sock.recv(length)
    return (result[0], result[1:])

@Logger.logged("P2P_TestClient", "test_client")
def _send_data(sock: socket, code: int, data: bytes = bytes()):
    data_to_send = Extentions.int_to_bytes(len(data) + 1) + bytes([code]) + data
    sock.send(data_to_send)

@Logger.logged("P2P_TestClient", "test_client")
def main():
    remove("test_client.log")
    sock : socket = socket()
    sock.connect(("localhost", 3501))
    Logger.log("Connection with localhost:3501 was established.", "test_client")
    _send_data(sock, 0)
    Logger.log("Ping was successfully sent.", "test_client")
    code, _ = _get_gata(sock)
    if code != 0:
        raise TestClientException("Ping wasn't received!")
    Logger.log("Ping was successfully received.", "test_client")
    for i in range(0, 5):
        bts_login = Extentions.defstr_to_bytes(f"TestUser{i}")
        bts_password = Extentions.defstr_to_bytes(f"{i + 1}{i}{ (i - 1) * 2}")
        _send_data(sock, 1, bts_login + bts_password)
        Logger.log(f"Trying to register TestUser{i}...", "test_client")
        code, received_data = _get_gata(sock)
        if code != 1:
            raise TestClientException(f"TestUser{i} wasn't registered!\n{Extentions.bytes_to_defstr(received_data)}")
        Logger.log(f"TestUser{i} was successfully registered.", "test_client")
    bts_login = Extentions.defstr_to_bytes(f"TestUser3")
    bts_password = Extentions.defstr_to_bytes(f"434")
    _send_data(sock, 2, bts_login + bts_password)
    Logger.log("Trying to login as TestUser3...", "test_client")
    code, received_data = _get_gata(sock)
    if code != 2:
        raise TestClientException(f"Login as TestUser3 was failed!\n{Extentions.bytes_to_defstr(received_data)}")
    Logger.log("Login as TestUser3 was successful.", "test_client")
    requesting_logins = Extentions.int_to_bytes(4)
    requesting_logins += Extentions.defstr_to_bytes("TestUser0")
    requesting_logins += Extentions.defstr_to_bytes("TestUser1")
    requesting_logins += Extentions.defstr_to_bytes("TestUser2")
    requesting_logins += Extentions.defstr_to_bytes("TestUser4")
    _send_data(sock, 3, requesting_logins)
    Logger.log("IPs was requested.", "test_client")
    code, received_data = _get_gata(sock)
    if code != 3:
        raise TestClientException(f"IP-upgrade request failed!")
    ips_count, received_data = Extentions.bytes_to_int(received_data)
    ips_list = ["Following IPs was received:"]
    while ips_count > 0:
        requested_ip, received_data = Extentions.bytes_to_defstr(received_data)
        ips_list.append(f"TestUser{4 - ips_count} : {requested_ip}")
        ips_count -= 1
    Logger.log("\n".join(ips_list), "test_client")
    _send_data(sock, 4, Extentions.defstr_to_bytes("434"))
    Logger.log("Trying to delete TestUser3...", "test_client")
    code, received_data = _get_gata(sock)
    if code != 4:
        raise TestClientException(f"Deleting TestUser3 was failed!\n{Extentions.bytes_to_defstr(received_data)}")
    Logger.log("TestUser3 was successfully deleted.", "test_client")
    _send_data(sock, 3, Extentions.int_to_bytes(1) + Extentions.defstr_to_bytes("TestUser3"))
    _, received_data = _get_gata(sock)
    Logger.log("TestUser3's IP : " + Extentions.bytes_to_defstr(received_data[4:])[0], "test_client")
    sock.close()
    Logger.log("Test successfully ended.", "test_client")

main()