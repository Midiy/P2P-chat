from tkinter import *
from tkinter import scrolledtext, Menu


class P2PWindow(Tk):
    def __init__(self):
        super(P2PWindow, self).__init__()
        self.title('P2P-chat')
        # self.geometry('600x400')
        self.sticky = N+S+W+E

        lbl = Label(self, text='Friends', anchor=CENTER, font=("Arial Bold", 10))
        lbl.grid(column=0, row=0)

        self._btn = Button(self, text="Send", bg='green', fg='white', command=self.mes_send)
        self._btn.grid(column=2, row=2)

        self._txt = Entry(self, width=50)
        self._txt.grid(column=1, row=2, sticky=N+S+W+E)
        self._txt.focus()

        self._friends = Listbox(self, width=30)
        self._friends.grid(column=0, row=1, rowspan=2, sticky=N+S+W+E)
        lbl_1 = Label(self, text='Message', anchor=CENTER, font=("Arial Bold", 10))
        lbl_1.grid(column=1, row=0, columnspan=2)
        # self._friends.pack()

        self._friends.insert(END, "a list entry")

        self._messages = scrolledtext.ScrolledText(self, width=40, height=10, state=DISABLED)
        self._messages.grid(column=1, row=1, columnspan=2, sticky=N+S+W+E)

        _menu = Menu(self)
        new_item = Menu(_menu)
        new_item2 = Menu(_menu)

        new_item.add_command(label='Exit', command=exit)
        _menu.add_cascade(label='File', menu=new_item)

        # new_item2.add_command(label='Add', command=add_friend)
        # new_item2.add_command(label='Delete', command=del_friend)
        # new_item2.add_separator()
        # new_item2.add_command(label='Send file', command=send_file)
        # _menu.add_cascade(label='Friend', menu=new_item2)

        self.config(menu=_menu)

    def mes_send(self):
        self._messages.config(state=NORMAL)
        self._messages.insert(END, self._txt.get() + '\n')
        self._messages.config(state=DISABLED)
        self._txt.delete(0, 'end')


# Вывод окна window.mainloop()
window = P2PWindow()
window.mainloop()
