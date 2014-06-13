
from . import gui, srv, tools
from util.columns import *
from util.misc import app_devtypes

devdata = lambda: get_devdata('ALT', get_columns([c_ip_addr, c_altname]), app_devtypes(gui))

from .tools import Byteswap, Fircalc, Fircomp

def startup_cb(apps, mode, dev):
    if mode == 'byteswap':
        return Byteswap()
    if mode == 'fircalc':
        return Fircalc(dev=dev)
    if mode == 'fircomp':
        return Fircomp()

