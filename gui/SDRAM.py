#!/usr/bin/env python3

from cmd import Cmd
import argparse, socket, struct, time, pdb, os, sys
from binascii import hexlify, unhexlify
 
host = '192.168.0.203'
port = 2540
service = 'adc'
 
def call_de0(srv, cmd):
    try:
        host, port = srv.split(':')
        port = int(port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((host,port))
        s.sendall(cmd.encode('latin-1'))
        s.shutdown(socket.SHUT_WR)
        ret = s.recv(1024)
        s.close()
        ret = ret.decode()
        ret = ret.strip('\n\r')
        return ret
    except:
        print('Call to %s failed' % srv)

def update_progress1(progress):
    sys.stdout.write('\r[{0}] {1}%'.format('#'*(int(progress/10)), '%.1f' % progress))
    sys.stdout.flush()

def update_progress2(progress):
    sys.stdout.write('\r{0}kb'.format('%.2f' % progress))
    sys.stdout.flush()

def get_file_size(name):
    b = os.path.getsize(name)
    return b

def benchmark(func):
    def wrapper(*args, **kwargs):
        t = time.time()
        res = func(*args, **kwargs)
        fname = args[1]
        sz = get_file_size(fname)
        sz = float(sz)/1024
        dt = time.time() - t
        speed = sz/dt
        print(func.__name__, '%.1fk' % sz, '%.1fs' % dt, '%.1fk/s' % speed)
        return res
    return wrapper

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield '0x' + str(l[i:i+n], 'ascii')

@benchmark
def send_file(srv, fname):
    fsz = get_file_size(fname)
    sz1 = 128
    if fsz & sz1:
        print('error: file size %% %x != 0' % sz1)
        return
    sz = 0
    f = open(fname, 'rb')
    while True:
        d = f.read(sz1)
        if len(d) != sz1:
            break
        h = hexlify(d)
        h32 = list(chunks(h, 8))
        strdata = ' '.join(h32)
        call_de0(srv, '%smm write_32 0x%x %s' % (service, sz, strdata))
        sz = sz + sz1
        #update_progress1(100*sz/fsz)
        update_progress2(float(sz)/1024)
        if sz == fsz:
            break
    try:
        f.close()
    except:
        pass
    print()
    return
 
def write_data(data, f):
    for l in data.split():
        l = l.replace('0x', '')
        b = unhexlify(l)
        f.write(b)

@benchmark
def recv_file(srv, fname, fsz):
    print(fname, fsz)
    sz1 = 256
    if fsz & sz1:
        print('error: file size %% %x != 0' % sz1)
        return
    sz = 0
    f = open(fname, 'wb')
    while True:
        strdata = call_de0(srv, '%smm read_32 0x%x 0x%x' % (service, sz, sz1/4))
        if len(strdata) == 0: break
        sz = sz + sz1
        update_progress2(float(sz)/1024)
        write_data(strdata, f)
        if sz == fsz:
            break
    f.close()
    try:
        f.close()
    except:
        pass
    print()
    return

def start_srv(de0srv):
    try:
        from xmlrpc.server import SimpleXMLRPCServer
        srv = SimpleXMLRPCServer(('', 0xDE0))
        srv.register_function(lambda cmd: call_de0(de0srv, cmd), 'call_de0')
        srv.allow_none = True
        srv.logRequests = False
        srv.serve_forever()
    except:
        pass

class Jtag_cmd(Cmd):
    def __init__(self, srv):
        super(Jtag_cmd, self).__init__(completekey=None)
        self.srv = srv
        self.prompt = 'de0@%s> ' % self.srv

    def do_stop(self, s):
        ret = call_de0(self.srv, 'exit')
        return False

    def do_exit(self, s):
        return True

    def do_send(self, s):
        send_file(self.srv, s)
        return False

    def do_recv(self, s):
        try:
            fname, fsz = s.split()
            fsz = int(fsz, 16)
        except:
            print('recv fname fsz')
            return False
        recv_file(self.srv, fname, fsz)
        return False

    def default(self, line):
        ret = call_de0(self.srv, line)
        print(ret)
        return False
    
    def do_EOF(self, line):
        print()
        return True

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='shell', help='startup mode: shell|exec|srv')
    console = '%s:%d' % (host, port)
    parser.add_argument('--console', type=str, default=console, help='de0 srv url, default %s' % console)
    parser.add_argument('--cmd', type=str, help='command to execute')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    app = Jtag_cmd(args.console)
    if args.mode == 'shell':
        app.cmdloop()
        return
    if args.mode == 'exec':
        app.onecmd(args.cmd)
        return
    if args.mode == 'srv':
        start_srv(args.de0)
        return

if __name__ == '__main__':
    main()

