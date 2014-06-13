
from math import pi
from numpy import arange, array, sin, log10
from util import Data
from .firfilt import Firfilt
import pylab

class Fircomp(Firfilt):
    def __init__(self, title='CIC compensation'):
        self.dbmin = -120
        Firfilt.__init__(self, title=title)

    def init_custom_layout(self):
        self.pady = 1
        self.plot_add('CIC/FIR', self.plot_init_fircic, self.plot_upd_fircic, subplots=1)
        self.plot_add('Impulse/Step', self.plot_init_impz, self.plot_upd_impz)

    def bank_data(self):
        data = Data(name='Bank %d' % len(self.data))
        data.add('R', label='(R) Decimation factor', wdgt='spin', text=100, value=Data.spn(1,127), trace_cb=self.Fo_upd_trace_cb)
        data.add('M', label='(M) Differential delay', wdgt='spin', text=1, value=Data.spn(1,127))
        data.add('N', label='(N) Number of stages', wdgt='spin', text=5, value=Data.spn(1,127), msg='number of cascaded filters')
        data.add('Fs', label='Fs, MHz', wdgt='spin', text=5, value=Data.spn(1,100,.1), msg='Sampling freq in MHz before decimation', trace_cb=self.Fo_upd_trace_cb)
        data.add('Fc', label='Fc, kHz', wdgt='spin', text=1, value=Data.spn(1,1000,1), msg='Pass band edge in kHz', trace_cb=self.Fo_upd_trace_cb)
        data.add('Fo', label='Fo', wdgt='entry', state='readonly', msg='Fo = R*Fc/Fs; Normalized Cutoff freq; 0<Fo<=0.5/M')
        data.add('L', label='(L) Filter order', wdgt='spin', text=32, value=Data.spn(2,128,2), msg='Filter order; must be even')
        data.add('fmt', label='format', wdgt='combo', state='readonly', text='double', value=['double', 'int'], trace_cb=lambda *args: self.bank_update())
        data.add('nbits', label='# of bits', wdgt='spin', value=Data.spn(4, 16), text='8', trace_cb=lambda *args: self.bank_update())
        self.Fo_upd_trace_cb('R', data)
        if len(self.data):
            data.cmds['fmt'].text = self.data.get_value('fmt')
            data.cmds['nbits'].text = self.data.get_value('nbits')
            data.cmds['ntaps'].text = self.data.get_value('ntaps')
        return data

    def Fo_upd_trace_cb(self, k, data):
        try:
            R = int(data.get_value('R'))
            Fs = 1000*float(data.get_value('Fs'))
            Fc = float(data.get_value('Fc'))
            Fo = '%.03g' % (R*Fc/Fs)
            data.set_value('Fo', Fo)
        except:
            pass

    def plot_init_fircic(self, fig):
        ax = fig.get_axes()[0]
        ax.clear()
        ax.grid()
        ax.set_ylabel('Magnitude (db)')
        ax.set_xlabel(r'Normalized Frequency (x$\pi$rad/sample)')
        ax.set_title(r'Frequency response')
        ax.set_ylim(self.dbmin, 10)

    def plot_upd_fircic(self, fig):
        cmds = self.data.cmds
        print('plot_upd_fircic')
        if not hasattr(cmds, 'f') or not hasattr(cmds, 'hcic'):
            print('return')
            return
        print('plot_update')
        f = cmds.f
        hcic = cmds.hcic
        self.plot_init_fircic(fig)
        ax = fig.get_axes()[0]
        ax.plot(f,hcic)

    def design_filter(self):
        R = int(self.data.get_value('R'))   # Decimation factor
        M = int(self.data.get_value('M'))   # Differential delay
        N = int(self.data.get_value('N'))   # Number of stages
        L = int(self.data.get_value('L'))   # Filter order
        Fo = float(self.data.get_value('Fo')) # Normalized Cutoff freq

        p = 2e3
        s = 0.25/p
        fp = arange(0, Fo+s, s)
        fs = arange(Fo+s, 0.5+s, s)
        f = arange(0, 1+s, 2*s)

        Hfunc = lambda f : abs( (sin((pi*f*R)/2)) / (sin((pi*f*M)/2.)) )**N
        #HfuncC = lambda w : abs( (sin((w*M)/2.)) / (sin((w*R)/2.)) )**N

        #w = arange(L) * pi/L

        H = array(list(map(Hfunc, f)))
        G = (R*M)**N
        self.data.cmds.f = f
        self.data.cmds.hcic = 20*log10(H/G)
        #Hc = array(list(map(HfuncC, w)))
        # only use the inverse (compensation) roughly to the first null.
        #Hc[int(L*pi/R/2):] = 1e-8
        print(len(H))
        pcmds = self.pdata.cmds
        p = pcmds[pcmds.name]
        p.upd(p.fig)
        pylab.draw()
        p.fig.canvas.draw()
        '''
        plot(w, 20*log10(H/G))
        plot(w, 20*log10(Hc*G))
        grid('on')
        '''

