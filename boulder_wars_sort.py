import numpy as np
from math import floor
import time
import os

# The damping procedure was been extensively tested, and the default parameters
# are those found to demonstrate most efficient convergence with realistic simulations

class WarsSort:
    def __init__(self, competitors=None, winners=None, losers=None, maxniter=10,
                 progressive=True, damping_factor=1.0,
                 progress_figure=False, truth=None):

        self.competitors = self._asarray(competitors)
        self.winners = self._asarray(winners)
        self.losers = self._asarray(losers)
        self.maxniter = maxniter
        self.progressive = progressive
        self.initial_damping_factor = damping_factor
        self.damping_factor = damping_factor
        self.progress_figure = progress_figure
        self.truth = truth

        self._consistency_check()

        self._setup_internal_variables()
        
        if self.truth is not None:
            self._setup_progress_figure()

    def _asarray(self, x):
        return np.asarray(x) if (x is not None) else np.zeros(1)
            
    def _consistency_check(self):
        if self.winners.shape != self.losers.shape:
            raise ValueError("Winners and losers arrays are not"
                             "the same shape")

        if self.winners.ndim != 1:
            raise ValueError("Winners and losers arrays are not"
                             "the correct shape")

        if self.competitors.ndim != 1:
            raise ValueError("Winners and losers arrays are not"
                             "the correct shape")

        if self.progress_figure and (self.truth is None):
            raise ValueError("To create progress figure you must"
                             "supply a 'truth' ranking")

        if not set(self.winners).issubset(self.competitors):
            raise ValueError("Some winners are not in competitors array")

        if not set(self.losers).issubset(self.competitors):
            raise ValueError("Some losers are not in competitors array")

    def _setup_internal_variables(self):
        self.ncomp = self.competitors.shape[0]
        self.nwars = self.winners.shape[0]
        self.niter = 0
        self.nbattle = 0
        self.nswap = 0
        self.ranking = np.random.permutation(self.competitors)
        self.progress_figure_points = None
        self.progress_figure_previter_points = None
        self.progress_figure_label = None
        self.progress_figure_line = None
        self.progress_figure_fig = None
        self.mad = None
        self.madlist = []
        self.bias = None
        self.biaslist = []

    def _update_damping_factor(self):
        if self.progressive:
            #self.damping_factor = self.initial_damping_factor * self.niter
            self.damping_factor = 1 - np.exp(-(self.niter*self.initial_damping_factor))
        else:
            self.damping_factor = self.initial_damping_factor

    def _mad(self):
        return np.absolute(self.ranking - self.truth).mean() / self.ncomp * 100

    def _bias(self):
        mid = self.ncomp//2
        r = self.ranking
        t = self.truth
        return ((np.median(r[:mid] - t[:mid]) - np.median(r[mid:] - t[mid:]))
                / float(self.ncomp) * 100)

    def _setup_progress_figure(self):
        global plt
        import matplotlib
        matplotlib.use('TkAgg')
        from matplotlib import pyplot as plt
        import matplotlib.gridspec as gridspec
        if self.progress_figure:
            plt.ion()
        if self.progress_figure_fig is None:
            self.progress_figure_fig = plt.figure(figsize=(8,12))
        else:
            self.progress_figure_fig.clear()
        gs = gridspec.GridSpec(4, 3)
        ax = plt.subplot(gs[:3, :], aspect=1.0)
        plt.xlabel('true rank')
        plt.ylabel('estimated rank')
        title = ''
        if self.initial_damping_factor > 0:
            title += 'damped'
            if self.progressive:
                title += ' progressive'
        plt.title(title)
        plt.plot([0.0, self.ncomp], [0.0, self.ncomp], 'k-')
        ax.scatter(self.truth, self.ranking, c='b', zorder=1, alpha=0.2)
        self.progress_figure_previter_points = ax.scatter([], [], c='r',
                                                          zorder=2, alpha=0.4)
        self.progress_figure_points = ax.scatter(self.truth, self.ranking, c='g',
                                                 zorder=3, alpha=0.8)
        self.progress_figure_label = ax.text(self.ncomp*0.05, self.ncomp*0.8,
                                    '%4i %5i %5i\n%5.2f %5.2f %5.2f'%(0, 0, 0, 0, 0, 0),
                                    backgroundcolor='w', fontsize='small')
        self.progress_figure_label.set_bbox(dict(alpha=0.5, color='w',
                                                 edgecolor='w'))
        color='red',
        plt.axis((0, self.ncomp, 0, self.ncomp))
        
        ax = plt.subplot(gs[3:, :])
        plt.axis((0, self.nwars*self.maxniter, 0, 30))
        plt.hlines([5,10,15,20,25], 0, self.nwars*self.maxniter, linestyles='dotted')
        plt.hlines(self.nwars*np.arange(1, self.maxniter), 0, 30, linestyles='dotted')
        plt.xlabel('battle number')
        plt.ylabel('scatter')
        self.progress_figure_line = ax.plot([0],[0])[0]
        plt.tight_layout()
        if self.progress_figure:
            plt.draw()

    def _update_progress_figure(self):
        if self.progress_figure_fig is None:
            self._setup_progress_figure()
        self.progress_figure_previter_points.set_offsets(
            np.transpose([self.truth, self.previous_ranking]))
        self.progress_figure_points.set_offsets(
            np.transpose([self.truth, self.ranking]))
        status = '%4i %5i %5i\n%5.2f %5.2f %5.2f'%(self.niter, self.nbattle,
                                self.nswap, self.damping_factor, self.mad, self.bias)
        self.progress_figure_label.set_text(status)
        x, y = self.progress_figure_line.get_data()
        x = np.concatenate((x, [self.nwars*self.niter + self.nbattle]))
        y = np.concatenate((y, [self.mad]))
        self.progress_figure_line.set_data(x, y)
        if self.progress_figure:
            plt.draw()

    def _update_progress(self):
        if self.truth is not None:
            self.mad = self._mad()
            self.bias = self._bias()
            self._update_progress_figure()
    
    def iteration(self):
        self._update_damping_factor()
        self.nbattle = 0
        self.nswap = 0
        self.previous_ranking = self.ranking.copy()
        for b, battle in enumerate(np.random.permutation(self.nwars)):
            self.nbattle += 1
            w = self.winners[battle]
            l = self.losers[battle]
            iw = (self.ranking == w).nonzero()[0][0]
            il = (self.ranking == l).nonzero()[0][0]
            if iw < il:
                if self.initial_damping_factor > 0:
                    damp = int(floor((il - iw) * self.damping_factor))
                    ild = il - max(damp, 0)
                    iwd = iw + damp
                    self.ranking[ild+1:il+1] = self.ranking[ild:il]
                    self.ranking[ild] = w
                    self.ranking[iw:iwd] = self.ranking[iw+1:iwd+1]
                    self.ranking[iwd] = l
                else:
                    self.ranking[il] = w
                    self.ranking[iw] = l
                self.nswap += 1
                self._update_progress()
        self.niter += 1
        self.madlist.append(self.mad)
        self.biaslist.append(self.bias)
                
    def iterate(self, maxniter=None):
        if maxniter is None:
            maxniter = self.maxniter
        for i in range(maxniter):
            self.iteration()
        return self.ranking

    def close(self):
        if not self.progress_figure_fig is None:
            plt.close(self.progress_figure_fig)

    def save_progress_figure(self, figname):
        self._update_progress_figure()
        self.progress_figure_fig.savefig(figname)

    def sort_battles(self, results_filename='csv/mz_results_boulders.csv',
                     images_filename='csv/mz_images_boulders.csv',
                     out_filename='csv/mz_boulders_rank.csv'):
        p = np.recfromcsv(images_filename, names=True)
        objid = p.field('id')
        rank = np.zeros(objid.shape, np.int) - 1
        fracrank = np.zeros(objid.shape) - 1
        battles = np.recfromcsv(results_filename, names=True)
        # currently does not do anything with inconclusive battles
        battles = battles[battles.field('winner') > 0]
        first = battles['first_asset_id']
        second = battles['second_asset_id']
        winner = battles['winner']
        w = np.where(winner == 1, first, second)
        l = np.where(winner == 1, second, first)
        competitors = np.unique(np.concatenate((w, l)))
        self.competitors = self._asarray(competitors)
        self.winners = self._asarray(w)
        self.losers = self._asarray(l)
        self._consistency_check()
        self._setup_internal_variables()
        print('ncomp = %i, nwars = %i'%(self.ncomp, self.nwars))
        self.iterate()
        for r, id in enumerate(self.ranking):
            idx = (objid == id).nonzero()[0]
            if len(idx) < 1:
                print('Could not find objid match for id={}, rank={}'.format(id, r))
            idx = idx[0]
            rank[idx] = r
            fracrank[idx] = float(r) / self.ncomp
        np.savetxt(out_filename, np.asarray((objid, rank, fracrank)).T,
                   fmt='%d,%d,%.3f',
                   header=("objid,rank,fracrank"))

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()


if __name__ == '__main__':
    wars_sort = WarsSort()
    wars_sort.sort_battles()
