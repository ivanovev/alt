
from collections import OrderedDict as OD
try:
    from sg.regs import RegsData, regs_cb
except:
    pass

def sgdma_io_cb(dev, cmd):
    return 'alt.sgdma %s %s %s' % (dev['ip_addr'], dev['altname'], cmd)

hex_data = '''
R0||Control
R1||Status
'''

bin_data = '''
R0|0|ERROR||
R0|1|EOP_ENCOUNTERED||
R0|2|DESCRIPTOR_COMPLETED||
R0|3|CHAIN_COMPLETED||
R0|4|BUSY||
R0|5|Reserved|1|
R1|0|IE_ERROR||
R1|1|IE_EOP_ENCOUNTERED||
R1|2|IE_DESCRIPTOR_COMPLETED||
R1|3|IE_CHAIN_COMPLETED||
R1|4|IE_GLOBAL||
R1|5|RUN||
R1|6|STOP_DMA_ER||
R1|7|IE_MAX_DESC_PROCESSED||
R1|8|MAX_DESC_PROCESSED||
R1|16|SW_RESET||
R1|17|PARK||
R1|18|Reserved|1|
R1|31|CLEAR_INTERRUPT||
'''

def get_menu(dev):
    return OD([('Registers', regs_cb)])

def get_regs(dev):
    data = RegsData(io_cb=sgdma_io_cb)
    data.add_hex_data(hex_data)
    data.add_bin_data(bin_data)
    return data

