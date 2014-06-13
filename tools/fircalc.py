
import tkinter as tk
import tkinter.ttk as ttk

from collections import OrderedDict as OD
from copy import deepcopy
from math import ceil
from numpy import arange

from util.control import Control
from util import Data
from .firfilt import Firfilt, taps_dec

import pylab
try:
    import scipy.signal as signal
except:
    signal = None

class Fircalc(Firfilt):
    def __init__(self, dev=None, parent=None, title='FIR LPF calc'):
        self.dbmin = -80
        if dev != None:
            title += ' (' + '.'.join([dev['name'], dev['type'], dev['altname']]) + ')'
        Firfilt.__init__(self, dev=dev, parent=parent, title=title)

    def init_io(self):
        del self.io[:]
        self.io.add(self.fircalc_cb1, self.fircalc_cb2, self.fircalc_cb3, self.cmdio_thread)

    def init_custom_layout(self):
        self.plot_add('Frequency/Phase', self.plot_init_mfreqz, self.plot_upd_mfreqz)
        self.plot_add('Impulse/Step', self.plot_init_impz, self.plot_upd_impz)
        if hasattr(self.data, 'dev'):
            self.add_fb()
            self.add_button(self.fb, 'Write', self.write_cb)
            self.add_button(self.fb, 'Read', self.read_cb)
            self.pb = ttk.Progressbar(self.fb, orient=tk.HORIZONTAL, maximum=10)
            self.pb.pack(fill=tk.X, expand=0, padx=5, pady=5)
    
    def plot_init_mfreqz(self, fig):
        ax1, ax2 = fig.get_axes()
        for ax in [ax1,ax2]:
            ax.clear()
            ax.grid()
            ax.set_xlim(0, 1)
            ax.set_xticks(list(arange(0,1.1,.1)))
        ax1.set_ylim(self.dbmin, 10)
        ax1.set_ylabel('Magnitude (db)')
        ax1.set_xlabel(r'Normalized Frequency (x$\pi$rad/sample)')
        ax1.set_title(r'Frequency response')
        ax2.set_ylabel('Phase (radians)')
        ax2.set_xlabel(r'Normalized Frequency (x$\pi$rad/sample)')
        ax2.set_title(r'Phase response')

    def plot_upd_mfreqz(self, fig, taps, a=1):
        if not signal:
            return
        self.plot_init_mfreqz(fig)
        ax1, ax2 = fig.get_axes()
        w,h = signal.freqz(taps,a)
        if sum(abs(h)) == 0:
            return
        h_dB = 20 * pylab.log10 (abs(h))
        ax1.plot(w/max(w),h_dB)
        h_Phase = pylab.unwrap(pylab.arctan2(pylab.imag(h),pylab.real(h)))
        ax2.plot(w/max(w),h_Phase)

    def get_fmt_from_fname(self, fname):
        ll = fname.split('.')
        if 'dbl' in ll:
            return 'dbl'
        fmt = None
        for l in ll:
            if l[0] == 'b':
                return l

    def get_cutoff_from_fname(self, fname):
        ll = fname.split('.')
        c = list(filter(lambda x: x[0] == 'c', ll))
        if len(c) == 0:
            return
        c = [i.replace('c', '') for i in c]
        c = ['%g' % (float(i)/10) for i in c]
        return c

    def fileopen(self, fname, *args):
        fmt = self.get_fmt_from_fname(fname)
        cc = self.get_cutoff_from_fname(fname)
        if fmt == None:
            return
        while len(self.banks) > 1:
            self.bank_del()
        f = open(fname)
        i = 0
        for l in f.readlines():
            l = l.strip()
            self.set_taps(i, l, fmt)
            if i < len(cc):
                self.data.set_value('cutoff', cc[i])
            i += 1
        f.close()
        self.plot_update()

    def bank_data(self):
        data = Data(name='Bank %d' % len(self.data))
        data.add('cutoff', label='cutoff', wdgt='spin', text='0.3', value=Data.spn(.1,.9,.1))
        data.add('ntaps', label='# of taps', wdgt='spin', text=33, value=Data.spn(1,127))
        windows = ['boxcar','triang','blackman','hamming','hann','bartlett','flattop','parzen','bohman','blackmanharris','nuttall','barthann']
        data.add('window', label='window', wdgt='combo', state='readonly', text='hamming', value=windows)
        data.add('fmt', label='format', wdgt='combo', state='readonly', text='double', value=['double', 'int'], trace_cb=lambda *args: self.bank_update())
        data.add('nbits', label='# of bits', wdgt='spin', value=Data.spn(4, 16), text='8', trace_cb=lambda *args: self.bank_update())
        if len(self.data):
            data.cmds['fmt'].text = self.data.get_value('fmt')
            data.cmds['nbits'].text = self.data.get_value('nbits')
            data.cmds['ntaps'].text = self.data.get_value('ntaps')
        return data

    def save_fmt_data(self):
        bdata = self.bank_data()
        fdata = Data()
        fdata.add_page('fmt1', cmds=OD((k,bdata.cmds[k]) for k in ['fmt', 'nbits']))
        return fdata

    def banks_list(self):
        return ['Bank %d' % i for i in range(0, len(self.data))] + ['All']

    @taps_dec
    def get_initialfile(self, read=True):
        if not read:
            fdata = self.save_fmt_data()
            fdata.add('bank', label='Bank #', wdgt='combo', state='readonly', text='Bank %d' % self.data.cur, value=self.banks_list())
            sd = Control(data=fdata, parent=self.root, title='Save format')
            sd.add_buttons_ok_cancel()
            sd.center()
            sd.do_modal()
            if not hasattr(sd, 'kw'):
                return
            if sd.kw['fmt'] == 'double':
                fmt = 'dbl'
            else:
                b = int(sd.kw['nbits'])
                fmt = 'b%d' % b
            bank = sd.kw['bank']
            self.cur = self.data.cur
            if bank != 'All':
                bank = int(bank.split()[1])
                cmds = self.data.cmds
                c = 'c' + self.data.get_value('cutoff').replace('.', '')
            else:
                c = '.'.join(['c' + self.data.select(i).get_value('cutoff').replace('.', '') for i in range(0, len(self.data))])
                self.data.select(self.cur)
            t = self.data.get_value('ntaps')
            dflt = 'fir.%s.t%s.%s.txt' % (c, t, fmt)
            self.bank = bank
            self.fmt = fmt
            return dflt
        else:
            return 'fir.data.%s' % self.fileext

    def filesave(self, fname):
        f = open(fname, 'w')
        pages = range(0, len(self.data)) if self.bank == 'All' else [self.cur]
        for p in pages:
            self.data.select(p)
            taps = self.get_taps_fmt(self.fmt)
            ts = ','.join(taps)
            f.write(ts + '\n')
        self.data.select(self.cur)
        f.close()
        if hasattr(self, 'filename'):
            delattr(self, 'filename')

    def set_taps(self, n, taps, fmt):
        if len(self.data) == n:
            self.bank_add()
        if len(self.data) < n + 1:
            return
        self.data.select(n)
        cmds = self.data.cmds
        tt = taps.split(',')
        if fmt in ['double', 'dbl']:
            taps = [float(i) for i in tt]
            self.data.set_value('fmt', 'double')
        else:
            b = int(fmt.replace('b', ''))
            taps = [float(i)/(1 << (b - 1)) for i in tt]
            self.data.set_value('fmt', 'int')
            self.data.set_value('nbits', b)
        cmds.taps = taps
        self.bank_update()
        self.data.set_value('ntaps', len(tt))

    def bank_add(self):
        Firfilt.bank_add(self)
        self.data.add('tap', t=tk.StringVar(), send=True)

    def design_filter(self):
        if not signal:
            return
        ntaps = int(self.data.get_value('ntaps'))
        cutoff = float(self.data.get_value('cutoff'))
        window = self.data.get_value('window')
        taps = signal.firwin(ntaps, cutoff, window=window)
        self.data.cmds.taps = taps
        self.bank_update()
        self.plot_update()

    def fircalc_cb1(self):
        cmd = 'read' if self.read else 'write'
        bdata = self.bank_data()
        tdata = Data()
        tdata.add_page('taps', cmds=OD((k,bdata.cmds[k]) for k in ['ntaps', 'nbits']))
        tdata.add('nbank', label='bank #', wdgt='combo', state='readonly', text='0', value=['0', '1'])
        dlg = Control(data=tdata, parent=self.root, title='%s taps' % cmd)
        dlg.add_buttons_ok_cancel()
        dlg.center()
        dlg.do_modal()
        if not hasattr(dlg, 'kw'):
            return
        ntaps = dlg.kw['ntaps']
        self.nbits = int(dlg.kw['nbits'])
        nbank = int(dlg.kw['nbank'])
        n = ceil(int(ntaps)/2)
        offset = n if nbank else 0
        dev = self.data.dev
        if self.read:
            self.taps = []
            for i in range(0, n):
                self.qo.put('tap ALT.firii %s %s %d' % (dev['ip_addr'], dev['altname'], i + offset))
        else:
            taps = self.get_taps_fmt(fmt=self.nbits)
            taps[n:] = []
            for i in range(0, n):
                self.qo.put('tap ALT.firii %s %s %d %s' % (dev['ip_addr'], dev['altname'], i + offset, taps[i]))
        self.pb['maximum'] = self.qo.qsize()
        return True

    def fircalc_cb2(self):
        if self.read:
            self.ctrl_cb2()
            tap = self.data.get_value('tap')
            self.taps.append(tap)
            return True

    def fircalc_cb3(self, *args):
        if not self.read:
            return
        taps2 = deepcopy(self.taps)
        taps2 = list(reversed(taps2))
        taps2.pop(0)
        self.taps += taps2
        ntaps = len(self.taps)
        n = self.data.cur
        l = ','.join(['%s' % i for i in self.taps])
        fmt = '%db' % self.nbits
        self.set_taps(n, l, fmt)
        self.plot_update()

