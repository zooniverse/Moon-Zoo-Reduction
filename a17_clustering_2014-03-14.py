#!python 

from mz_cluster import mz_cluster
import sys

nacs = ['M104311715RE', 'M101949648RE']#, 'M104318871RE', 'M180966380LE']
#thresholds = {'a': 0.5, 'b': 0.75, 'c': 1.0, 'd': 1.25, 'e': 1.5}
thresholds = {'c': 1.0}
mincounts = [1, 2, 3, 4]
truths = ['Xpert_715', 'Xpert_648', 'Xpert_648_P', 'Xpert_715_P']
split_iters = [1, 5]

for tf in truths:
    for n in nacs:
        for l, t in thresholds.items():
            for c in mincounts:
                for s in split_iters:
                    print '{}_{}_{}_{}_uw_{}'.format(n, l, c, s, tf)
                    sys.stdout = file('clusters/{}_{}_{}_{}_uw_{}.out'.format(n, l, c, s, tf), 'w')
                    mz_cluster('clusters/{}_{}_{}_{}_uw_{}'.format(n, l, c, s, tf), 'markings/{}.csv'.format(n), n,
                               'from_rob_2014-01-28/{}.csv'.format(tf), 'from_rob_2014-01-28/ROI_{}.tif'.format(n[-5:][:3]),
                               t, c, 10, s, 0.25, 0.25, 100, 30.699, 30.880, 20.200, 20.275)
                    sys.stdout.close()
                    sys.stdout = sys.__stdout__

