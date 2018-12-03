from tkinter import *
from tkinter import scrolledtext, Menu
import asyncio
import configparser
sys.path.append('../P2P-lib')
from P2P_client import Client


class P2PWindow(Tk):
    def __init__(self, conf):
        super(P2PWindow, self).__init__()
        self._btn = None
        self._txt = None
        self._friends = None
        self._messages = None
        self._current_friend = None

        self.init_ui()

        self._client = Client(conf[conf.default_section]['login'], conf[conf.default_section]['password'],
                              self.on_receive_msg_callback, bool(conf[conf.default_section]['registration']))
        # conf[conf.default_section]['database'], conf[conf.default_section]['server'],
        # conf[conf.default_section]['port']

        lst = self._client.get_contacts_list()
        lst = ['friend_1', 'friend_2']
        for i in lst:
            self._friends.insert(END, i)
        self._friends.select_set(0)
        self._friends.event_generate("<<ListboxSelect>>")

        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(self._client.establish_connections)

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

        new_item.add_command(label='Exit', command=exit)
        _menu.add_cascade(label='File', menu=new_item)

        new_item2.add_command(label='Add', command=self.add_friend)
        new_item2.add_command(label='Delete', command=self.del_friend)
        new_item2.add_separator()
        new_item2.add_command(label='Send file', command=self.send_file)
        _menu.add_cascade(label='Friend', menu=new_item2)

        self.config(menu=_menu)

    def mes_send_1(self):
        self._client.send_message(self._current_friend, self._txt.get())
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
        self._messages.insert(END, self._client.get_history(self._current_friend))
        self._messages.config(state=DISABLED)

    def on_receive_msg_callback(self, mes, friend, client_endpoint):
        if friend == self._current_friend:
            self._messages.config(state=NORMAL)
            # mes должен быть в  формате стальных сообщений
            self._messages.insert(END, mes + '\n')
            self._messages.config(state=DISABLED)

    def add_friend(self):
        friend_log = self.get_friend('Введите имя нового друга:')
        if len(friend_log) != 0:
            self._client.add_contact(friend_log)
            self._friends.insert(END, friend_log)
            index = self._friends.get(0, "end").index(friend_log)
            self._friends.select_set(index)
            self._friends.event_generate("<<ListboxSelect>>")

    def del_friend(self):
        friend_log = self.get_friend('Введите имя удаляемого друга:')
        if (len(friend_log) != 0) and (friend_log in self._client.get_contacts_list()):
            self._client.delete_contact(friend_log)
            index = self._friends.get(0, "end").index(friend_log)
            self._friends.remove(index)
            if friend_log == self._current_friend:
                self._friends.select_set(0)
                self._friends.event_generate("<<ListboxSelect>>")

    def send_file(self):
        pass

    def get_friend(self, mess) -> str:
        result = StringVar()
        top = Toplevel(self)
        top.title(mess)
        txt_name = Entry(top).grid(row=0, column=0, columnspan=2)

        def ok_cmd(result_2):
            result_2.set(txt_name.get(0, END))
            top.destroy()

        Button(top, text='OK', command=ok_cmd(result)).grid(row=1, column=0)
        Button(top, text='Cancel', command=top.destroy()).grid(row=1, column=1)
        top.transient(self)
        top.grab_set()
        top.focus_set()
        top.wait_window()
        return result.get()


def p2p_configure(conf):
    def button_cmd(status):
        if status is not None:
            conf[conf.default_section]['login'] = en_login.get()
            conf[conf.default_section]['password'] = en_password.get()
            conf[conf.default_section]['database'] = en_database.get()
            conf[conf.default_section]['server'] = en_server.get()
            conf[conf.default_section]['port'] = en_port.get()
            conf[conf.default_section]['registration'] = status
        window_2.destroy()
        result.set(status)

    window_2 = Tk()
    window_2.geometry('300x400')
    window_2.title("P2P chat configure")

    result = StringVar()
    Label(window_2, text="login").grid(row=0, column=0)
    en_login = Entry(window_2)
    en_login.grid(row=0, column=1, columnspan=2)
    if conf.has_option(conf.default_section, 'login'):
        en_login.insert(0, conf[conf.default_section]['login'])

    Label(window_2, text="password").grid(row=1, column=0)
    en_password = Entry(window_2)
    en_password.grid(row=1, column=1, columnspan=2)
    if conf.has_option(conf.default_section, 'password'):
        en_password.insert(0, conf[conf.default_section]['password'])

    Label(window_2, text="database").grid(row=2, column=0)
    en_database = Entry(window_2)
    en_database.grid(row=2, column=1, columnspan=2)
    if not conf.has_option(conf.default_section, 'database'):
        conf[conf.default_section]['database'] = 'Chinook_Sqlite.sqlite'
    en_database.insert(0, conf[conf.default_section]['database'])

    Label(window_2, text="server").grid(row=3, column=0)
    en_server = Entry(window_2)
    en_server.grid(row=3, column=1, columnspan=2)
    if not conf.has_option(conf.default_section, 'server'):
        conf[conf.default_section]['server'] = '127.0.0.1'
    en_server.insert(0, conf[conf.default_section]['server'])

    Label(window_2, text="port").grid(row=4, column=0)
    en_port = Entry(window_2)
    en_port.grid(row=4, column=1, columnspan=2)
    if not conf.has_option(conf.default_section, 'port'):
        conf[conf.default_section]['port'] = '3502'
    en_port.insert(0, conf[conf.default_section]['port'])

    Button(window_2, text='Login', command=lambda: button_cmd('False')).grid(row=5, column=0)
    Button(window_2, text='Register', command=lambda: button_cmd('True')).grid(row=5, column=1)
    Button(window_2, text='Cancel', command=lambda: button_cmd(None)).grid(row=5, column=2)

    window_2.mainloop()
    return result.get()


config = configparser.ConfigParser()
config.read('P2P_client.ini')
status = p2p_configure(config)
if status != 'None':
    with open('P2P_client.ini', 'w') as configfile:
        config.write(configfile)
    main_window = P2PWindow(config)
    main_window.mainloop()
