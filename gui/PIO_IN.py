
from collections import OrderedDict as OD

from util import Data, monitor_cb, util_io_cb
from .PIO_OUT import alt_cmd_cb

def get_mntr(dev):
    data = Data(name='mntr', io_cb=lambda d,c: util_io_cb(d,c,prefix='ALT'))
    data.add('pio', label='IN', wdgt='entry', state='readonly', cmd_cb=alt_cmd_cb, send=True)
    return data

def get_menu(dev):
    return OD([('Monitor', monitor_cb)])

