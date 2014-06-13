
#from . import sc
#from . import at
from util.server import proxy
from util.socketio import get_fsz, update_progress, chunks
from binascii import hexlify, unhexlify

import socket
service_uart = 'jtag_uart'
service_mm = 'jtag_mm'
service = service_uart
port = 2540

def uart(ip_addr, cmd, *args):
    try:
        alt_uart = proxy.srv.funcs['util.alt_uart']
        return alt_uart(ip_addr, cmd, *args)
    except:
        return ''

def ALT_alt_uart(ip_addr='192.168.0.203', cmd='', *args):
    '''
    ALT JTAG UART io
    '''
    if cmd == '':
        return ''
    cmd = ' '.join([cmd] + list(args))
    cmd = '%s %s' % (service, cmd)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((ip_addr,port))
        s.sendall(cmd.encode('latin-1'))
        s.shutdown(socket.SHUT_WR)
        ret = s.recv(1024)
        s.close()
        ret = ret.decode()
        ret = ret.strip('\n\r')
        return ret
    except:
        print('Call to %s failed' % ip_addr)
    return ''

def ALT_find(ip_addr='192.168.0.1', altname='fir0'):
    '''
    Find base address of %altname%
    '''
    addr = uart(ip_addr, 'find ' + altname)
    if addr in ['', None]:
        return ''
    if addr == 'FFFFFFFF':
        return ''
    return addr

def itoh(i):
    if i == '':
        return ''
    i = int(i)
    if i >= 0:
        return '%X' % i
    i = 0x10000 + i
    return '%X' % i

def htoi(h):
    if h == '':
        return ''
    tap = int(h, 16)
    if tap > 0x7FFF:
        tap -= 0x10000
    return '%d' % tap

def ALT_firii(ip_addr='192.168.0.1', altname='fir0', n='0', tap=''):
    '''
    Read/Write FIR_II taps
    '''
    addr = ALT_find(ip_addr, altname)
    if addr in ['', None]:
        return ''
    addr = int(addr, 16)
    addr += 2*int(n)
    if tap == '':
        return htoi(uart(ip_addr, 'mrh %X' % addr))
    else:
        try:
            tap = itoh(tap)
        except:
            return ''
        return htoi(uart(ip_addr, 'mwh %X %s' % (addr, tap)))

def ALT_pio(ip_addr='192.168.0.1', altname='pio_led', val=''):
    '''
    Read PIO_IN, Write PIO_OUT
    '''
    addr = ALT_find(ip_addr, altname)
    if addr in ['', None]:
        return ''
    if val == '':
        return '%d' % int(uart(ip_addr, 'mr %s' % addr), 16)
    else:
        return '%d' % int(uart(ip_addr, 'mw %s %s' % (addr, val)), 16)

def ALT_sgdma(ip_addr='192.168.0.1', altname='sgdma_0', cmd='desc 0 0', *args):
    '''
    SGDMA commands
    '''
    cmd = ' '.join([cmd] + list(args))
    addr = ALT_find(ip_addr, altname)
    if addr in ['', None]:
        return ''
    n = int(altname[-1])
    cc = cmd.split(' ')
    if cc[0] in ['start', 'stop', 'status']:
        cmd = 'dma%s %d' % (cc[0], n)
        if len(cc) > 1:
            cmd += ' ' + cc[1]
        return htoi(uart(ip_addr, cmd))
    elif cc[0] == 'desc' and len(cc) == 3:
        desc_addr = int(uart(ip_addr, 'dma%s' % cmd), 16)
        if not desc_addr:
            return ''
        desc_src = uart(ip_addr, 'mr %X' % desc_addr)
        desc_dest = uart(ip_addr, 'mr %X' % (desc_addr + 8))
        desc_next_ptr = uart(ip_addr, 'mr %X' % (desc_addr + 16))
        desc_b2t = int(uart(ip_addr, 'mr %X' % (desc_addr + 24)), 16)
        desc_b2t = '%X' % (desc_b2t & 0xFFFF)
        desc_28 = int(uart(ip_addr, 'mr %X' % (desc_addr + 28)), 16)
        desc_control = '%X' % (desc_28 >> 24)
        desc_status = '%X' % ((desc_28 >> 16) & 0xFF)
        desc_bt = '%X' % (desc_28 & 0xFFFF)
        return '|'.join(['%X' % desc_addr, desc_src, desc_dest, desc_next_ptr, desc_b2t, desc_control, desc_status, desc_bt])
    try:
        if cc[0][0] == 'R':
            cc[0] = cc[0][1:]
        r = int(cc[0])
        a = int(addr, 16)
        return htoi(uart(ip_addr, 'mr %X' % (a + r*4)))
    except:
        return ''

def ALT_send_file(ip_addr='192.168.0.203', fname=''):
    '''
    Write file to alt sdram
    '''
    fsz = get_fsz(fname)
    sz1 = 256
    if fsz & sz1:
        print('error: file size %% %x != 0' % sz1)
        return ''
    sz = 0
    f = open(fname, 'rb')
    global service
    service = service_mm
    while True:
        d = f.read(sz1)
        if len(d) != sz1:
            break
        h = hexlify(d)
        h32 = list(chunks(h, 8))
        strdata = ' '.join(h32)
        ALT_alt_uart(ip_addr, 'write_32 0x%x %s' % (sz, strdata))
        sz = sz + sz1
        update_progress(100*float(sz)/fsz)
        if sz == fsz:
            break
    service = service_uart
    try:
        f.close()
    except:
        pass
    print()
    return '0x%X' % fsz

def ALT_recv_file(ip_addr='192.168.0.203', fname='/tmp/data', fsz='0x1000'):
    '''
    Read file from alt sdram
    '''
    fsz = get_fsz(None, fsz)
    sz1 = 256
    if fsz & sz1:
        print('error: file size %% %x != 0' % sz1)
        return ''
    sz = 0
    f = open(fname, 'wb')
    def write_data(data, f):
        for l in data.split():
            l = l.replace('0x', '')
            b = unhexlify(l)
            f.write(b)
    global service
    service = service_mm
    while True:
        strdata = ALT_alt_uart(ip_addr, 'read_32 0x%x 0x%x' % (sz, sz1/4))
        if len(strdata) == 0: break
        sz = sz + sz1
        update_progress(100*float(sz)/fsz)
        write_data(strdata, f)
        if sz == fsz:
            break
    service = service_uart
    f.close()
    try:
        f.close()
    except:
        pass
    print()
    return

