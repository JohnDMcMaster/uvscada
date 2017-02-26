from uvscada.util import add_bool_arg

import argparse
import zcmp

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Impedance scanner')
    add_bool_arg(parser, '--inf', default=True, help='')
    parser.add_argument('ref', help='')
    parser.add_argument('check', nargs='+', help='')
    args = parser.parse_args()

    results = []
    print 'Ref: %s' % args.ref
    for check in args.check:
        score = zcmp.score(args.ref, check, inf=args.inf, verbose=False)
        results.append((score, check))

    results = sorted(results)
    for score, check in results:
        print '% -60s: %0.3f' % (check, score)

    best_score, best = results[1]
    print
    print 'Best'
    print '% -60s: %0.3f' % (best, best_score)
