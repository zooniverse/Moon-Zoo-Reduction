#!python 

from glob import glob
import numpy

files = glob('clusters/*.out')

names = []
collect_names = True
results = []
for f in (file(fn) for fn in files):
    stats = []
    for l in f:
        ls = l.split()
        if len(ls) == 0:
            continue
        if 'output_filename_base' in ls[0]:
            n = ls[2].replace('clusters/', '')
            stats.append(n[:12])
            stats.append(n[13:])
            if collect_names:
                names.append('nac')
                names.append('method')
        elif 'delta' in ls[0]:
            stats.append(float(ls[2]))
            if collect_names:
                names.append(ls[0])
        elif 'KS' in ls[0]:
            stats.append(float(ls[4].replace(',', '')))
            stats.append(float(ls[5]))
            if collect_names:
                names.append('KS_D')
                names.append('KS_p')
    collect_names = False
    if len(stats) > 3:
        results.append(stats)

results = [numpy.array([results[i][j] for i in xrange(len(results))]) for j in xrange(len(results[0]))]
results = numpy.rec.fromarrays(results, names=names)

results = numpy.sort(results, order=['nac', 'mad_delta']) 

with file('test_clustering_results', 'w') as fout:
    fmt = '%16s '*len(names)
    fout.write(fmt%tuple(names)+'\n')
    prevname = ''
    for r in results:
        if r[0][:12] != prevname:
            fout.write('\n')
            prevname = r[0][:12]
        fmt = '%16s %16s ' + ('%16.3f '*(len(r)-2))
        fout.write(fmt%tuple(r)+'\n')
