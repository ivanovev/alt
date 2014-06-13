
from collections import OrderedDict as OD
from util import plot, process_cb
from .byteswap import Byteswap
from .fircalc import Fircalc
from .fircomp import Fircomp

def menus():
    menus = OD()
    menus['Byteswap'] = lambda *args: process_cb('byteswap')
    menus['separator'] = None
    menu_fir = OD()
    menu_fir['LPF'] = lambda *args: process_cb('fircalc')
    menu_fir['CIC'] = lambda *args: process_cb('fircomp')
    menus['FIR'] = menu_fir
    menus['separator2'] = None
    menus.update(plot.menus())
    return menus
