min(timeit.repeat('idx = matchids(a, b)', 'import numpy; a = numpy.random.random_integers(1, 100000, 100000); b = a.copy(); numpy.random.shuffle(b); from matchids_orig import matchids', number=1, repeat=10))

min(timeit.repeat('idx = matchids(a, b)', 'import numpy; a = numpy.random.random_integers(1, 100000, 100000); b = a.copy(); numpy.random.shuffle(b); import pyximport; pyximport.install(); from matchids import matchids', number=1, repeat=10))
