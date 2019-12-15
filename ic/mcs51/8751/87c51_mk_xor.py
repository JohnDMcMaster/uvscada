#!/usr/bin/env python3

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine stock encrypted dump + 0'd XOR table dump to create XOR key")
    parser.add_argument('--keysz', default=None, help="XOR encryption table size")
    parser.add_argument('--fwsz', default=None, help="Firmware size")
    parser.add_argument('--device', default="87C52", help="Automatically select XOR encryption table size")
    parser.add_argument('orig', help="Dump w/ untampered XOR table")
    parser.add_argument('zeroed', help="Dump w/ XOR table set to 0")
    parser.add_argument('fout', nargs='?', default='xor_key.bin', help="")
    args = parser.parse_args()

    keysz = 0x20
    fwsz = 0x2000

    encpat = bytearray(open(args.orig, 'rb').read()[0:fwsz])
    enc00 = bytearray(open(args.zeroed, 'rb').read()[0:fwsz])
    buff = bytearray(fwsz)
    for i, (a, b) in enumerate(zip(encpat, enc00)):
        buff[i] = a ^ b

    # Verify all XOR buffs are the same
    key = buff[0:keysz]
    for i, checkbyte in enumerate(buff):
        assert checkbyte == key[i % len(key)]
    print("Key is consistent!")

    open(args.fout, 'wb').write(buff[0:keysz])
    print("Done")

