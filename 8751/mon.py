from uvscada.minipro import Minipro
import md5
import binascii
import subprocess
import time

m = Minipro(device='87C51')
hs = {}
i = 0
while True:
    subprocess.check_call('clear')
    print i
    print hs
    h = binascii.hexlify(md5.new(m.read()).digest())
    print h
    hs[h] = hs.get(h, 0) + 1
    #time.sleep(0.1)
    i += 1
