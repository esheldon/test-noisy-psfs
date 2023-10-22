import numpy as np
import fitsio
import esutil as eu
import matplotlib.pyplot as mplt

# bins = 20
bins = np.linspace(0, 2500, 50)

pdf = 's2n-hist.pdf'
png = 's2n-hist.png'

fig, axs = mplt.subplots(nrows=2, ncols=2, figsize=(10, 7))

for i, band in enumerate(['g', 'r', 'i', 'z']):

    ax = axs.flatten()[i]

    ax.set(
        xlim=(-50, 2000),
        ylim=(0, 170),
        xlabel=f'S/N {band}',
    )

    print('-' * 70)
    fname = f's2n-{band}band.fits'
    print(fname)
    t = fitsio.read(fname)
    print('s2n sum')
    eu.stat.print_stats(t['s2n_sum'])
    print('s2n mom')
    eu.stat.print_stats(t['s2n_mom'])

    mom_stats = eu.stat.get_stats(t['s2n_mom'])
    sum_stats = eu.stat.get_stats(t['s2n_sum'])

    mom_text = r'mom S/N: %d $\pm$ %d' % (mom_stats['mean'], mom_stats['err'])
    sum_text = r'sum S/N: %d $\pm$ %d' % (sum_stats['mean'], sum_stats['err'])
    ax.text(1250, 140, sum_text)
    ax.text(1250, 125, mom_text)

    ax.hist(
        t['s2n_sum'],
        label='sum',
        alpha=0.5,
        bins=bins,
    )
    ax.hist(
        t['s2n_mom'],
        label='gauss mom',
        alpha=0.5,
        bins=bins,
    )

    if i == 0:
        ax.legend(loc='lower right')

print('writing:', png)
mplt.savefig(png)
print('writing:', pdf)
mplt.savefig(pdf)
