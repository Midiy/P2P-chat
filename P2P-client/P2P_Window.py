from tkinter import *
from tkinter import scrolledtext, Menu
import asyncio
import configparser
import threading
from datetime import datetime
sys.path.append('../P2P-lib')
from P2P_client import Client
from P2P_database import DataBaseClient


class P2PWindow(Tk):
    def __init__(self, conf):
        super(P2PWindow, self).__init__()
        self._btn = None
        self._txt = None
        self._friends = None
        self._messages = None
        self._current_friend = None
        self._exiting = False

        self.init_ui()

        self._client = Client(conf[conf.default_section]['login'], conf[conf.default_section]['password'],
                              self.on_receive_msg_callback, bool(conf[conf.default_section]['registration'] == 'True'))

        self._lst = self._client.get_contacts_list()
        # lst = ['friend_1', 'friend_2']
        for i in self._lst:
            self._friends.insert(END, i)
        self._friends.select_set(0)
        self._friends.event_generate("<<ListboxSelect>>")

        self._loop = asyncio.get_event_loop()
        self._loop.run_until_complete(self._client.establish_connections())

        # self._listner = threading.Thread(target=self.start_listner)
        # self._listner.start()

        self.context_switching()

    def init_ui(self):
        self.title('P2P-chat')
        f_1 = Frame(self)
        f_1.pack(side=LEFT, fill=Y)
        f_2 = Frame(self)
        f_2.pack(side=LEFT, fill=BOTH)
        f_3 = Frame(f_2)
        f_3.pack(side=BOTTOM, fill=BOTH)

        lbl = Label(f_1, text='Friends', anchor=CENTER, font=("Arial Bold", 10))
        lbl.pack(side=TOP)

        self._btn = Button(f_3, text="Send", bg='green', fg='white', command=self.mes_send_1)
        self._btn.pack(side=RIGHT)

        self._txt = Entry(f_3, width=50)
        self._txt.pack(side=RIGHT, fill=X)
        self._txt.focus()
        self._txt.bind('<Return>', self.mes_send_2)

        self._friends = Listbox(f_1, width=30)
        self._friends.pack(side=TOP, fill=Y)
        self._friends.bind('<<ListboxSelect>>', self.change_friend)

        lbl_1 = Label(f_2, text='Message', anchor=CENTER, font=("Arial Bold", 10))
        lbl_1.pack(side=TOP)

        self._messages = scrolledtext.ScrolledText(f_2, state=DISABLED)
        self._messages.pack(side=TOP, fill=BOTH)

        _menu = Menu(self)
        new_item = Menu(_menu)
        new_item2 = Menu(_menu)

        new_item.add_command(label='Exit', command=self.p2p_exit)
        _menu.add_cascade(label='File', menu=new_item)

        new_item2.add_command(label='Add', command=self.add_friend)
        new_item2.add_command(label='Delete', command=self.del_friend)
        new_item2.add_separator()
        new_item2.add_command(label='Send file', command=self.send_file)
        _menu.add_cascade(label='Friend', menu=new_item2)

        self.config(menu=_menu)

    def p2p_exit(self):
        self._exiting = True
        # self._listner.join()
        exit()

    def mes_send_1(self):
        self._loop.run_until_complete(self._client.send_message(self._current_friend, self._txt.get()))
        # Client.send_message должен возвращать текст в формате стальных сообщений
        self._messages.config(state=NORMAL)
        self._messages.insert(END, self._txt.get() + '\n')
        self._messages.config(state=DISABLED)
        self._txt.delete(0, 'end')

    def mes_send_2(self, tmp):
        self.mes_send_1()

    def change_friend(self, evt):
        w = evt.widget
        index = int(w.curselection()[0])
        self._current_friend = w.get(index)
        self._messages.config(state=NORMAL)
        self._messages.delete('1.0', END)
        mes_gis = self._loop.run_until_complete(self._client.get_history(self._current_friend))
        for i in mes_gis:
            self._messages.insert(END, i[-1] + '\n')
        self._messages.config(state=DISABLED)

    def on_receive_msg_callback(self, friend, time, mes):
        if friend == self._current_friend:
            self._messages.config(state=NORMAL)
            # mes должен быть в  формате стальных сообщений
            self._messages.insert(END, mes + '\n')
            self._messages.config(state=DISABLED)

    def add_friend(self):
        friend_log = self.get_friend('Введите имя нового друга:')
        if len(friend_log) != 0:
            self._lst.append(friend_log)
            self._loop.run_until_complete(self._client.add_contact(friend_log))
            self._friends.insert(END, friend_log)
            index = self._friends.get(0, "end").index(friend_log)
            self._friends.select_set(index)
            self._friends.event_generate("<<ListboxSelect>>")

    def del_friend(self):
        friend_log = self.get_friend('Введите имя удаляемого друга:')
        if (len(friend_log) != 0) and (friend_log in self._client.get_contacts_list()):
            self._lst.remove(friend_log)
            self._client.delete_contact(friend_log)
            index = self._friends.get(0, "end").index(friend_log)
            self._friends.delete(index)
            if friend_log == self._current_friend:
                self._messages.config(state=NORMAL)
                self._messages.delete('1.0', END)
                self._messages.config(state=DISABLED)
                self._friends.select_set(0)
                self._friends.event_generate("<<ListboxSelect>>")

    def send_file(self):
        pass

    def get_friend(self, mess) -> str:
        result = StringVar()
        top = Toplevel(self)
        top.geometry('240x70')
        top.title(mess)
        txt_name = Entry(top, width=38)
        txt_name.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        def ok_cmd():
            result.set(txt_name.get())
            top.destroy()

        Button(top, text='OK', command=ok_cmd).grid(row=2, column=0, padx=5, pady=5)
        Button(top, text='Cancel', command=top.destroy).grid(row=2, column=1, padx=5, pady=5)
        top.transient(self)
        top.grab_set()
        top.focus_set()
        top.wait_window()
        return result.get()

    # def start_listner(self):
    #     while not self._exiting:
    #         # Код ждун
    #         self._loop.run_until_complete(asyncio.sleep(0.05))

    def context_switching(self):
        self._loop.run_until_complete(asyncio.sleep(0.05))
        self.after(500, self.context_switching)
        lst = self._client.get_contacts_list()
        for i in lst:
            if i not in self._lst:
                self._friends.insert(END, i)
        self._lst = lst


def p2p_configure(conf):
    def button_cmd(status):
        if status is not None:
            conf[conf.default_section]['login'] = en_login.get()
            conf[conf.default_section]['password'] = en_password.get()
            conf[conf.default_section]['server'] = en_server.get()
            conf[conf.default_section]['registration'] = status
        window_2.destroy()
        result.set(status)

    window_2 = Tk()
    window_2.geometry('280x140')
    window_2.title("P2P chat configure")

    result = StringVar()
    Label(window_2, text="login").grid(row=0, column=0, padx=5, pady=5)
    en_login = Entry(window_2, width=30)
    en_login.grid(row=0, column=1, columnspan=2, padx=5, pady=5)
    if conf.has_option(conf.default_section, 'login'):
        en_login.insert(0, conf[conf.default_section]['login'])

    Label(window_2, text="password").grid(row=1, column=0, padx=5, pady=5)
    en_password = Entry(window_2, width=30)
    en_password.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
    if conf.has_option(conf.default_section, 'password'):
        en_password.insert(0, conf[conf.default_section]['password'])

    Label(window_2, text="server").grid(row=2, column=0, padx=5, pady=5)
    en_server = Entry(window_2, width=30)
    en_server.grid(row=2, column=1, columnspan=2, padx=5, pady=5)
    if not conf.has_option(conf.default_section, 'server'):
        conf[conf.default_section]['server'] = '127.0.0.1'
    en_server.insert(0, conf[conf.default_section]['server'])

    Button(window_2, text='Login', command=lambda: button_cmd('False')).grid(row=5, column=0, padx=5, pady=5)
    Button(window_2, text='Register', command=lambda: button_cmd('True')).grid(row=5, column=1, padx=5, pady=5)
    Button(window_2, text='Cancel', command=lambda: button_cmd(None)).grid(row=5, column=2, padx=5, pady=5)

    window_2.mainloop()
    return result.get()


config = configparser.ConfigParser()
config.read('P2P_client.ini')
status = p2p_configure(config)
if status != 'None':
    with open('P2P_client.ini', 'w') as configfile:
        config.write(configfile)
    if status == 'True':
        database = DataBaseClient(config[config.default_section]['login'] + ".sqlite")
        database.init()
        # database.update_ip('server', config[config.default_section]['server'], datetime.now())
        del database
    main_window = P2PWindow(config)
    main_window.mainloop()
