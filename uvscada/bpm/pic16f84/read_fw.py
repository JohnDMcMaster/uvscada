
p_p2n = {}
for k, v in dict(globals()).iteritems():
    if k[0] != 'p' or k == 'p_p2n':
        continue
    p_p2n[v] = k

if __name__ == '__main__':
    for k, v in dict(globals()).iteritems():
        if k[0] != 'p' or type(v) is not str:
            continue
        open('i87c51_read_fw/%s.bin' % k, 'w').write(v)
