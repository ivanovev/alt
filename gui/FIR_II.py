
from collections import OrderedDict as OD
from util import process_cb
from ..tools import Fircalc

def startup_cb(apps, mode, dev):
    if mode == 'fircalc':
        return Fircalc(dev=dev)

def get_menu(dev):
    menu = OD()
    menu['FIR LPF'] = lambda dev: process_cb('fircalc', dev)
    return menu

