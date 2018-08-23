def parse_size(size_str):
    size = 1
    if 'k' in size_str:
        size *= 1000
    if 'K' in size_str:
        size *= 1024
    size *= int(size_str, 0)
    return size

def run(fout, size=None):
    open(fout, 'w').write('\x00' * size)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--size', required=True, help='')
    parser.add_argument('fout', help='')
    args = parser.parse_args()

    run(args.fout, size=parse_size(args.size))

