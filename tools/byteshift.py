
import sys
import struct

if __name__ == '__main__':
    fin = open(sys.argv[1], 'rb')
    fout = open(sys.argv[1] + '_sh', 'wb')
    while True:
        x = fin.read(2)
        if not x:
            break
        x = struct.unpack('H', x)[0]
        #print(hex(x))
        x = x << 7
        if x > 0xFFFF:
            x = 0xFFFF
        #print(hex(x))
        fout.write(struct.pack('H', x))
    fin.close()
    fout.close()

