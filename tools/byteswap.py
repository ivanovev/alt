#!/usr/bin/env python3

import tkinter as tk
from tkinter import messagebox
from util.control import Control
from util import Data

class Byteswap(Control):
    def __init__(self, parent=None):
        self.pady = 5
        Control.__init__(self, data=self.get_data(), parent=parent, title='Byteswap')
        self.add_fb()
        self.add_button(self.fb, 'Close', self.root.destroy)
        self.add_button(self.fb, 'Start', self.start_cb)
        self.fileext = '*'
        self.center()

    def get_data(self):
        data = Data(name='byteswap')
        data.add('srcbrowse', label='Source', wdgt='button', text='Browse...', click_cb=lambda: self.fileopen_cb('src'))
        data.add('src', wdgt='entry', columnspan=2)
        data.add('destbrowse', label='Destination', wdgt='button', text='Browse...', click_cb=lambda: self.fileopen_cb('dest'))
        data.add('dest', wdgt='entry', columnspan=2)
        data.add('wordsz', label='word size in bytes', wdgt='radio', value=['2', '4'], text=4, trace_cb=self.wordsz_cb)
        for i in range(1, 5):
            data.add('b%d' % i, label='byte[%d] ->' % i, wdgt='combo', value=['1', '2', '3', '4'], text='%d' % i, state='readonly')
        return data

    def wordsz_cb(self, *args):
        wsz = self.data.get_value('wordsz')
        if wsz == '2':
            for i in ['b1', 'b2']:
                self.data.cmds[i].w['values'] = ['1', '2']
            for i in ['b3', 'b4']:
                self.data.cmds[i].lw.grid_forget()
                self.data.cmds[i].w.grid_forget()
        elif wsz == '4':
            for i in ['b1', 'b2']:
                self.data.cmds[i].w['values'] = ['1', '2', '3', '4']
            for i in [3, 4]:
                self.data.cmds['b%d' % i].lw.grid(column=0, row=4+i, sticky=tk.NSEW)
                self.data.cmds['b%d' % i].w.grid(column=1, row=4+i, sticky=tk.NSEW)

    def fileopen(self, fname, k):
        self.data.set_value(k, fname)
        if k == 'src':
            self.data.set_value('dest', fname + '_sw')

    def start_cb(self):
        if self.swap():
            messagebox.showinfo(title='Ok', message='finished')
        else:
            messagebox.showinfo(title='Error', message='failed')

    def swap(self):
        src = self.data.get_value('src')
        dest = self.data.get_value('dest')
        try:
            fi = open(src, 'rb')
            fo = open(dest, 'wb')
        except:
            return False
        x = int(self.data.get_value('wordsz'))

        b = []
        for i in range(0, x):
            b.append(int(self.data.get_value('b%d' % (i+1))) - 1)
        while True:
            d = list(fi.read(x))
            if len(d) != x:
                break
            for i in range(0, x):
                fo.write(bytes([d[b[i]]]))
        fi.close()
        fo.close()
        return True

