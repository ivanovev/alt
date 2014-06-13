
import tkinter as tk
import tkinter.ttk as ttk
import sys
import pylab

from collections import OrderedDict as OD
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from numpy import arange, sin, pi

from util.control import Control
from util import Data

try:
    import scipy.signal as signal
except:
    signal = None

def taps_dec(f):
    def tmp(*args, **kwargs):
        calc = args[0]
        if not len(calc.data):
            return []
        cmds = calc.data.cmds
        if not hasattr(cmds, 'taps'):
            return []
        return f(*args, **kwargs)
    return tmp

class Firfilt(Control):
    def __init__(self, dev=None, parent=None, title='FIR calc'):
        data = Data()
        self.banks = []
        self.fileext = 'txt'
        Control.__init__(self, data=data, dev=dev, parent=parent, title=title)

    def init_layout(self):
        self.init_common_layout()
        self.init_custom_layout()

    def add_menu_bank(self):
        menu = OD()
        mb = OD()
        mb['Add'] = lambda *args: self.bank_add()
        mb['Delete'] = lambda *args: self.bank_del()
        menu['Bank'] = mb
        return self.add_menus(menu)

    def update_menu_bank(self):
        newstate = tk.NORMAL if len(self.data) > 1 else tk.DISABLED
        self.menu_bank['Bank']['m'].entryconfig(1, state=newstate)

    def init_common_layout(self):
        self.add_menu_file(file_save=False)
        self.menu_bank = self.add_menu_bank()
        self.fl = tk.Frame(self.frame)
        self.fl.pack(fill=tk.BOTH, expand=1, side=tk.LEFT)
        self.fr = tk.Frame(self.frame)
        self.fr.pack(fill=tk.BOTH, expand=0, side=tk.RIGHT)
        self.pdata = Data()
        self.ptabs = ttk.Notebook(self.fl)
        self.ptabs.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)
        self.pdata.bind_tab_cb(self.ptabs, self.plot_update)
        self.tabs = ttk.Notebook(self.fr)
        self.tabs.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)
        self.bank_add()
        self.data.bind_tab_cb(self.tabs, self.plot_update)

    def plot_add(self, name, plot_init, plot_upd, subplots=2):
        fp = tk.Frame(self.ptabs)
        self.ptabs.add(fp, text=name, sticky=tk.NSEW)
        f = Figure(figsize=(5,4), dpi=100)
        if subplots == 1:
            f.add_subplot(111)
        if subplots == 2:
            f.add_subplot(211)
            f.add_subplot(212)
            f.subplots_adjust(hspace=0.5)
        plot_init(f)
        canvas = FigureCanvasTkAgg(f, master=fp)
        canvas.show()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        toolbar = NavigationToolbar2TkAgg(canvas, fp)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.pdata.add_page(name)
        self.pdata.add(name, fig=f, init=plot_init, upd=plot_upd)
        return f

    def plot_init_impz(self, fig):
        ax1, ax2 = fig.get_axes()
        taps = self.get_taps_fmt()
        for ax in [ax1,ax2]:
            ax.clear()
            ax.grid()
            if len(taps) > 1:
                ax.set_xlim(0, len(taps)-1)
        ax1.set_ylabel('Amplitude')
        ax1.set_xlabel(r'n (samples)')
        ax1.set_title(r'Impulse response')
        ax2.set_ylabel('Amplitude')
        ax2.set_xlabel(r'n (samples)')
        ax2.set_title(r'Step response')

    def plot_upd_impz(self, fig, taps, a=1):
        if not signal:
            return
        self.plot_init_impz(fig)
        ax1, ax2 = fig.get_axes()
        l = len(taps)
        impulse = pylab.repeat(0.,l); impulse[0] =1.
        x = arange(0,l)
        response = signal.lfilter(taps,a,impulse)
        ax1.stem(x, response)
        step = pylab.cumsum(response)
        ax2.stem(x, step)

    @taps_dec
    def plot_update(self, *args):
        n = self.ptabs.tabs().index(self.ptabs.select())
        cmds = self.data.cmds
        taps = cmds.taps
        pcmds = self.pdata.cmds
        p = pcmds[pcmds.name]
        p.upd(p.fig, taps)
        pylab.draw()
        p.fig.canvas.draw()

    def exit_cb(self, *args):
        self.root.withdraw()
        self.root.destroy()
        sys.exit(0)

    def bank_data(self):
        data = Data(name='Bank %d' % len(self.data))
        return data

    def bank_add(self):
        bdata = self.bank_data()
        self.data.add_page('Bank %d' % len(self.data), bdata.cmds)
        cmds = self.data.cmds
        self.add_tab(cmds, rowconfigure=False)
        self.tabs.select(cmds.tabid)
        self.update_menu_bank()
        r = len(cmds)
        btn = tk.Button(cmds.f, text='Design filter', command=self.design_filter)
        btn.grid(row=r, column=0, columnspan=2, sticky=tk.NSEW)
        f1 = tk.Frame(cmds.f, borderwidth=5)
        f1.grid(row=r+1, column=0, columnspan=2, sticky=tk.NSEW)
        cmds.f.rowconfigure(r+1, weight=1)
        cmds.lb = tk.Listbox(f1)
        self.add_widget_with_scrolls(f1, cmds.lb)

    def bank_del(self):
        if len(self.data) <= 1:
            return
        cmds = self.data.cmds
        self.tabs.forget(cmds.f)
        self.data.remove_page()
        self.update_menu_bank()
        i = 0
        for p in self.data:
            self.tabs.tab(p.tabid, text='Bank %d'%i)
            i = i + 1

    @taps_dec
    def bank_update(self, page=None):
        taps = self.get_taps_fmt()
        if not taps:
            return
        lb = self.data.cmds.lb
        lb.delete(0, tk.END)
        for t in taps:
            lb.insert(tk.END, t)

    def design_filter(self):
        return

    def get_int_taps(self, taps, nbits):
        return ['%d' % round(t*(1 << (nbits - 1))) for t in taps]

    @taps_dec
    def get_taps_fmt(self, fmt=None):
        taps = self.data.cmds.taps
        if fmt == None:
            fmt = self.data.get_value('fmt')
            if fmt == 'int':
                fmt = self.data.get_value('nbits')
        if fmt in ['double', 'dbl']:
            return ['%f' % t for t in taps]
        elif type(fmt) == str:
            try:
                nbits = int(fmt.replace('b', ''))
            except:
                return
        elif type(fmt) == int:
            nbits = fmt
        else:
            print('!!! bad fmt: ', fmt)
        return self.get_int_taps(taps, nbits)

