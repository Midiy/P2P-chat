# Encoding: utf-8

import asyncio
import P2P_client
from P2P_lib import Logger
from os import system
from datetime import datetime
from sys import platform


@Logger.logged("client")
def get_command(line: str) -> (str, str):
    i = 1
    while line[i] != " ":
        i += 1
        if i >= len(line):
            return (line, None)
    j = i
    while line[i] == " ":
        i += 1
        if i >= len(line):
            return (line, None)
    return (line[:j], line[i:])


@Logger.logged("client")
async def main():
    if input("Do you want to (l)ogin or to (r)egister? ") == "l":
        registration = False
    else:
        registration = True
    login = input("Login: ")
    password = input("Password: ")
    if platform == "win32":
        system("cls")
    else:
        system("clear")
    current_contact = None

    def _on_receive(sender: str, time: datetime, message: str):
        time = time.strftime("%d.%m.%Y %T")
        if current_contact == sender:
            print(f"[{time} {sender}]: {message}")
        else:
            print(f"\nNew message from {sender}!\n")

    client = P2P_client.Client(login, password, _on_receive, registration)
    await client.establish_connections()
    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, input)
        if not line.startswith("$"):
            if current_contact is None:
                print("You should use '$gotodialog <username>' first")
            else:
                if await client.send_message(current_contact, line):
                    print(f"[{datetime.now().strftime('%d.%m.%Y %T')} {login}]: {line}")
                else:
                    print(f"Message\n'{line}'\nwasn't sent. Try again.")
        else:
            command, arg = get_command(line)
            if command == "$gotodialog":
                if platform == "win32":
                    system("cls")
                else:
                    system("clear")
                current_contact = arg
                print(await client.get_history(current_contact))
            elif command == "$refresh":
                await asyncio.sleep(0.5)
            elif command == "$exit":
                break
            else:
                print(f"What is '{command}'?")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
