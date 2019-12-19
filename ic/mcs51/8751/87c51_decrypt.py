#!/usr/bin/env python3

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine stock encrypted dump + 0'd XOR table dump to create XOR key")
    parser.add_argument('--keysz', default=None, help="XOR encryption table size")
    #parser.add_argument('--fwsz', default=None, help="Firmware size")
    #parser.add_argument('--device', default="87C52", help="Automatically select XOR encryption table size")
    parser.add_argument('orig', help="Dump w/ untampered XOR table")
    parser.add_argument('keyfn', nargs='?', default="xor_key.bin", help="Encryption key file")
    parser.add_argument('fout', nargs='?', default='decrypted.bin', help="")
    args = parser.parse_args()

    keysz = 0x20
    if args.keysz:
        keysz = int(args.keysz, 0)
    fwsz = 0x2000

    encpat = bytearray(open(args.orig, 'rb').read()[0:fwsz])
    assert len(encpat) == fwsz, (len(encpat), fwsz)
    key = bytearray(open(args.keyfn, 'rb').read())
    assert len(key) == keysz
    buff = bytearray(fwsz)
    for i, enc in enumerate(encpat):
        buff[i] = enc ^ key[i % len(key)] ^ 0xFF
    open(args.fout, 'wb').write(buff)

    print("Done")

