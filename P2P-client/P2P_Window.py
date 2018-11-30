from tkinter import *
from tkinter import scrolledtext, Menu
import igd
import configparser
sys.path.append("../P2P-lib")
from P2P_database import DataBaseClient
from P2P_client_network import Listener, ClientToServer
from P2P_temp_client import Contact, Contact_dict


class P2PWindow(Tk):
    def __init__(self, conf):
        super(P2PWindow, self).__init__()
        self._btn = None
        self._txt = None
        self._friends = None
        self._messages = None

        self.init_ui()

        self._login = conf['login']
        self._password = conf['password']
        self._database = DataBaseClient(conf['database'])
        self._listener = Listener(self._login, self.on_receive_msg_callback, self.upgrade_ip_callback,
                                  conf['server'], self._database)
        Contact.database = self._database
        self._contact_dict = Contact_dict(self._add_new_contact)
        self._server = ClientToServer(conf['server'])

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

        # self._friends.insert(END, "asdfghjkl")
        self._friends.insert(END, "a list entry")

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
        self._messages.config(state=NORMAL)
        self._messages.insert(END, self._txt.get() + '\n')
        self._messages.config(state=DISABLED)
        self._txt.delete(0, 'end')

    def mes_send_2(self, tmp):
        self.mes_send_1()

    def change_friend(self, evt):
        w = evt.widget
        index = int(w.curselection()[0])
        value = w.get(index)
        self._messages.config(state=NORMAL)
        self._messages.insert(END, str(index) + ' ' + value + '\n')
        self._messages.config(state=DISABLED)

    def on_receive_msg_callback(self, mes, friend, client_endpoint):
        pass

    def upgrade_ip_callback(self, fr_login, fr_ip):
        pass

    def _add_new_contact(self, friend_log: str, ip: str):
        Contact.database.add_friend(friend_log, ip)
        return Contact(friend_log, self._login)

    def add_friend(self):
        friend_log = self.get_friend('Введите имя нового друга:')
        self._contact_dict[friend_log] = Contact(friend_log, self._login)
        self._friends.insert(END, friend_log)
        index = self._friends.get(0, "end").index(friend_log)
        self._friends.select_set(index)

    def del_friend(self):
        friend_log = self.get_friend('Введите имя друга:')
        self._contact_dict.remove(friend_log)
        index = self._friends.get(0, "end").index(friend_log)
        self._friends.remove(index)

    def send_file(self):
        pass

    def get_friend(self, mess) -> str:
        result = StringVar()
        top = Toplevel(self)
        top.title(mess)
        txt_name = Entry(top).grid(row=0, column=0, columnspan=2)

        def ok_cmd(result_2):
            result_2.set(txt_name.get(0, END))
            top.destroy

        Button(top, text='OK', command=ok_cmd(result)).grid(row=1, column=0)
        Button(top, text='Cancel', command=top.destroy).grid(row=1, column=1)
        top.transient(self)
        top.grab_set()
        top.focus_set()
        top.wait_window()
        return result.get()


def P2P_configure(conf):
    def button_cmd(status):
        if status is not None:
            conf['login'] = en_login.get(0, END)
            conf['password'] = en_password.get(0, END)
            conf['database'] = en_database.get(0, END)
            conf['server'] = en_server.get(0, END)
            conf['port'] = en_port.get(0, END)
        window_2.destroy
        result.set(status)

    result = StringVar()

    window_2 = Tk()
    window_2.title("P2P chat configure")

    Label(window_2, text="login").grid(row=0, column=0)
    en_login = Entry(window_2).grid(row=0, column=1, columnspan=2)
    en_login.set(conf['login'])

    Label(window_2, text="password").grid(row=1, column=0)
    en_password = Entry(window_2).grid(row=1, column=1, columnspan=2)
    en_password.set(conf['password'])

    Label(window_2, text="database").grid(row=2, column=0)
    en_database = Entry(window_2).grid(row=2, column=1, columnspan=2)
    en_database.set(conf['database'])

    Label(window_2, text="server").grid(row=3, column=0)
    en_server = Entry(window_2).grid(row=3, column=1, columnspan=2)
    en_server.set(conf['server'])

    Label(window_2, text="port").grid(row=4, column=0)
    en_port = Entry(window_2).grid(row=4, column=1, columnspan=2)
    en_port.set(conf['port'])

    Button(window_2, text='Login', command=lambda: button_cmd('ok')).grid(row=5, column=0)
    Button(window_2, text='Register', command=lambda: button_cmd('register')).grid(row=5, column=1)
    Button(window_2, text='Cancel', command=lambda: button_cmd(None)).grid(row=5, column=2)

    window_2.mainloop()
    return result.get()


config = configparser.ConfigParser()
config.read('P2P_client.ini')
status = P2P_configure(conf)
if status is not None
    config.write('P2P_client.ini')
    if status == 'register':
        pass
    else:  # ok
        pass
    main_window = P2PWindow(config)
    main_window.mainloop()
