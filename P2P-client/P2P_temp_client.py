# Encoding: utf-8

import P2P_client_network as network
from P2P_database import DataBaseClient
from P2P_lib import Logger, Extentions
from os import system


@Logger.logged("client")
def on_receive(data: bytes, contact_login: str, contact_endpoint):
    print(f"[{contact_login}]: {Extentions.bytes_to_defstr(data)[0]")   # REDO: Not print, but add to history.

@Logger.logged("client")
def get_contact(contact_login: str) -> str:
    pass   # DEBUG


@Logger.logged("client")
def print_history(contact_login: str):
    pass   # DEBUG


@Logger.logged("client")
def get_command(line: str) -> (str, str):
    i = 1
    while line[i] != " ":
        i += 1
    j == i + 1
    while line[i] == " ":
        i += 1
    return (line[:j], line[i:])


if input("Do you want to (l)ogin or to (r)egister?") == "l":
    registration = False
else:
    registration = True
login = input("Login: ")
password = input("Password: ")
system("cls")
database = DataBaseClient()
server_endpoint = database.search_ip("server")
if server_endpoint == "0.0.0.0":
    server_endpoint = "127.0.0.1"   # DEBUG
server = ClientToServer(server_endpoint)
if registration:
    server.registration(login, password)
else:
    server.login(login, password)

# TODO: Add upgrading contacts IP

listener = network.Listener(login, on_receive, database, server)
contacts = {}
current_contact = None
while True:
    line = input()
    if not line.startswith("$"):
        if current_contact is None:
            print("You should use '$gotodialog <username>' first")
        else:
            current_contact.send_text_message(line)
            print(f"[{login}]: {line}")
    else:
        command, arg = get_command(line)
        if command == "$gotodialog"
            system("cls")
            if not contacts.__contains__(arg):
                contact_ip = get_contact(arg)
                contacts["arg"] = network.ClientToClient(login, arg, contact_ip)
            current_contact = contacts["arg"]
            print_history(arg)
        else:
            pass # TODO: Add some other cases.