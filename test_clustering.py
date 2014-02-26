#!python 

from mz_cluster import mz_cluster
import sys

nacs = ['M101949648RE', 'M104311715RE'] #, 'M104318871RE', 'M180966380LE']
thresholds = {'a': 0.5, 'b': 0.75, 'c': 1.0, 'd': 1.25, 'e': 1.5}
mincounts = [1, 2, 3, 4]
truths = ['Xpert_648', 'Xpert_715', 'Xpert_648_P', 'Xpert_715_P']

for n in nacs:
    for l, t in thresholds.items():
        for c in mincounts:
            for tf in truths:
                print '{}_{}_{}_uw_{}'.format(n, l, c, tf)
                sys.stdout = file('clusters/{}_{}_{}_uw_{}.out'.format(n, l, c, tf), 'w')
                mz_cluster('clusters/{}_{}_{}_uw_{}'.format(n, l, c, tf), 'markings/{}.csv'.format(n), n, 'from_rob_2014-01-28/{}.csv'.format(tf), 'from_rob_2014-01-28/ROI_{}.tif'.format(n[-5:][:3]), t, c, 10, 3, 4.0, 0.4, 100, 30.699, 30.880, 20.200, 20.275)
                sys.stdout.close()
                sys.stdout = sys.__stdout__
