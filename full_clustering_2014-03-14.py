#!python 

from mz_cluster import mz_cluster
import sys

nacs = ['M104311715RE', 'M101949648RE']#, 'M104318871RE', 'M180966380LE']
#thresholds = {'a': 0.5, 'b': 0.75, 'c': 1.0, 'd': 1.25, 'e': 1.5}
thresholds = {'c': 1.0}
mincounts = [1, 2, 3, 4]
truths = ['Xpert_715', 'Xpert_648', 'Xpert_648_P', 'Xpert_715_P']
split_iters = [1, 5]

for n in nacs:
    l, t = 'c', 1.0
    c = 2
    s = 1
    print '{}_{}_{}_{}_uw'.format(n, l, c, s)
    mz_cluster('clusters/{}_full_{}_{}_{}_uw'.format(n, l, c, s), 'markings/{}.csv'.format(n), n,
               'none', 'none', t, c, 10, s, 0.25, 0.25, 100, 30.668, 30.960, 18.777, 21.148))
