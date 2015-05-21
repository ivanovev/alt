
from collections import OrderedDict as OD

from util import Data, control_cb, util_io_cb

def alt_cmd_cb(dev, cmd, val=None):
    if val == None:
        return '%s %s' % (cmd, dev['altname'])
    else:
        return '%s %s %s' % (cmd, dev['altname'], val)

def get_ctrl(dev):
    data = Data(name='ctrl', io_cb=lambda d,c: util_io_cb(d,c,prefix='ALT'))
    data.add('pio', label='PIO', wdgt='spin', value={'min':0, 'max':0xFF, 'step':1}, cmd_cb=alt_cmd_cb, send=True)
    return data

def get_menu(dev):
    return OD([('Control', control_cb)])

