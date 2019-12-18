#!/usr/bin/env python3

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create encryption key from FF filled binary")
    parser.add_argument('--keysz', default=None, help="XOR encryption table size")
    parser.add_argument('--fwsz', default=None, help="Firmware size")
    parser.add_argument('--device', default="87C52", help="Automatically select XOR encryption table size")
    parser.add_argument('orig', help="Dump w/ untampered XOR table")
    parser.add_argument('fout', nargs='?', default='xor_key.bin', help="")
    args = parser.parse_args()

    keysz = 0x20
    if args.keysz:
        keysz = int(args.keysz, 0)
    fwsz = 0x2000

    encpat = bytearray(open(args.orig, 'rb').read()[0:fwsz])

    # Verify all XOR buffs are the same
    key = bytearray([x ^ 0xFF for x in encpat[-keysz:]])
    """
    TODO: try to verify by looking for repeated occurances
    for i, checkbyte in enumerate(buff):
        assert checkbyte == key[i % len(key)]
    print("Key is consistent!")
    """

    open(args.fout, 'wb').write(key)
    print("Done")
