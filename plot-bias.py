import numpy as np
import esutil as eu
import argparse
import fitsio
import matplotlib.pyplot as mplt


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--s2n', nargs='+', type=int, required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--plotc', action='store_true')
    return parser.parse_args()


def main():
    args = get_args()

    dlist = []
    for s2n in args.s2n:
        print(s2n)
        fname = f'psfs2n{s2n}-fitgauss-res.fits'
        print(fname)
        data = fitsio.read(fname)
        dlist.append(data)

    data = eu.numpy_util.combine_arrlist(dlist)

    s2n = np.array(args.s2n)
    if args.plotc:
        fig, axs = mplt.subplots(nrows=2, figsize=(7, 7))
        axs[0].set(ylabel='m')
        axs[1].set(xlabel='PSF S/N', ylabel='c')
        axs[0].axhline(0, color='black')
        axs[1].axhline(0, color='black')

        axs[0].errorbar(
            s2n, data['m1'], data['m1err'], marker='o', markeredgecolor='black'
        )
        axs[1].errorbar(
            s2n, data['c2'], data['c2err'], marker='o', markeredgecolor='black'
        )
    else:
        fig, ax = mplt.subplots(figsize=(7, 4))
        ax.set(xlabel='PSF S/N', ylabel='m')

        ax.errorbar(
            s2n, data['m1'], data['m1err'], marker='o', markeredgecolor='black'
        )

    print('writing:', args.output)
    mplt.savefig(args.output)
    mplt.savefig(args.output.replace('.pdf', '.png'), dpi=150)


if __name__ == '__main__':
    main()
