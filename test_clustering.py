#!python 

from mz_cluster import mz_cluster
import sys

nacs = ['M101949648RE', 'M104311715RE', 'M104318871RE', 'M180966380LE']
thresholds = {'a': 0.5, 'b': 0.75, 'c': 1.0, 'd': 1.25, 'e': 1.5}
mincounts = [1, 2, 3, 4, 5]

for n in nacs:
    for l, t in thresholds.items():
        for c in mincounts:
            print '{}_{}_{}'.format(n, l, c)
            sys.stdout = file('clusters/{}_{}_{}_uw.out'.format(n, l, c), 'w')
            mz_cluster('clusters/{}_{}_{}_uw'.format(n, l, c), 'markings/{}.csv'.format(n), n, 'New_CC/truth.csv', 'New_CC/ROI_715.png', t, c, 10, 3, 4.0, 0.4, 100, 30.699, 30.880, 20.200, 20.275)
            sys.stdout.close()
            sys.stdout = sys.__stdout__
