import argparse
import zcmp

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Impedance scanner')
    parser.add_argument('ref', help='')
    parser.add_argument('check', nargs='+', help='')
    args = parser.parse_args()

    print 'Ref: %s' % args.ref
    best = None
    best_score = None
    for check in args.check:
        score = zcmp.score(args.ref, check, verbose=False)
        print '% -60s: %0.3f' % (check, score)
        if args.ref != check and (best_score is None or score < best_score):
            best = check
            best_score = score

    print
    print 'Best'
    print '% -60s: %0.3f' % (best, best_score)
