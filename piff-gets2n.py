import os
import numpy as np
import random
import fitsio
import esutil as eu
import ngmix


MOM = ngmix.gaussmom.GaussMom(fwhm=1.2)


def main():
    args = get_args()
    random.seed(args.seed)
    flist = get_flist(args)

    data = np.zeros(len(flist), dtype=[('s2n_sum', 'f4'), ('s2n_mom', 'f4')])
    for i, fname in enumerate(flist):
        print(f'{fname}: {i+1}/{len(flist)}')
        piffobj = get_piff(fname)

        keys = {}
        if '_z_' in fname:
            keys['IZ_COLOR'] = 0.34
        else:
            keys['GI_COLOR'] = 1.1

        im = piffobj.draw(
            x=1000,
            y=1000,
            stamp_size=25,
            **keys
        ).array
        s2n_sum, s2n_mom = meas_s2n(im)
        data['s2n_sum'][i] = s2n_sum
        data['s2n_mom'][i] = s2n_mom
        print(f's2n_sum: {s2n_sum:g} s2n_mom: {s2n_mom:g}')

    print('s2n sum stats')
    eu.stat.print_stats(data['s2n_sum'])
    print('s2n mom stats')
    eu.stat.print_stats(data['s2n_mom'])
    print('writing:', args.output)
    fitsio.write(args.output, data, clobber=True)


def get_piff(fname):
    import piff
    piffobj = piff.read(fname)
    return piffobj


def meas_s2n(im, cut=3, buff=2):
    imc = im[cut:-cut, cut:-cut]
    pix = np.concatenate([
        imc[:, 0:buff].ravel(),
        imc[:, -buff:].ravel(),
        imc[0:buff, buff:-buff].ravel(),
        imc[-buff:, buff:-buff].ravel()
    ])
    var = np.var(pix)
    s2n_sum = np.sum(im) / np.sqrt(var * np.prod(im.shape))

    obs = get_obs(im, var)
    res = MOM.go(obs)
    s2n_mom = res['s2n']
    return s2n_sum, s2n_mom


def get_obs(im, var):
    cen = (np.array(im.shape) - 1) / 2
    jac = ngmix.DiagonalJacobian(row=cen[0], col=cen[1], scale=0.263)
    return ngmix.Observation(
        im,
        weight=im * 0 + 1/var,
        jacobian=jac,
    )


def get_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--band', required=True)
    parser.add_argument('--output', required=True)
    # parser.add_argument('--num', type=int, default=100)
    parser.add_argument('--seed', type=int, default=1234)
    return parser.parse_args()


def get_flist(args):
    indir = f'{args.band}band'
    flist = []
    for root, dirs, files in os.walk(indir, topdown=False):
        for name in files:
            if 'piff-model.fits' in name:
                path = os.path.join(root, name)
                # print(path)
                flist.append(path)
    return flist


main()
