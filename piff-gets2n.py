import os
import numpy as np
import random
import fitsio
import esutil as eu
import ngmix


MOM = ngmix.gaussmom.GaussMom(fwhm=1.2)


def main():
    args = get_args()

    rng = np.random.RandomState(args.seed)
    random.seed(rng.randint(0, 2**30))

    flist = get_flist(args)
    # flist = flist[:3]

    dtype = [
        ('s2n_sum', 'f4'),
        ('s2n_mom', 'f4'),
        ('s2n_mom_fitvar', 'f4')
    ]
    data = np.zeros(len(flist), dtype=dtype)
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

        if args.show:
            show(im)

        s2n_sum, s2n_mom, var = meas_s2n(im)
        # s2n_fit = meas_s2n_fit(rng=rng, im=im, varguess=var)
        fitvar = meas_fitvar(rng=rng, im=im, varguess=var)
        print(f'var: {var:g} fitvar: {fitvar:g}')
        _, s2n_mom_fitvar, _ = meas_s2n(im, var=fitvar)

        data['s2n_sum'][i] = s2n_sum
        data['s2n_mom'][i] = s2n_mom
        data['s2n_mom_fitvar'][i] = s2n_mom_fitvar
        # data['s2n_fit'][i] = s2n_fit
        print(
            f's2n_sum: {s2n_sum:g} '
            f's2n_mom: {s2n_mom:g} '
            f's2n_mom_fitvar: {s2n_mom_fitvar:g}'
        )

    print('s2n sum stats')
    eu.stat.print_stats(data['s2n_sum'])
    print('s2n mom stats')
    eu.stat.print_stats(data['s2n_mom'])
    print('s2n_mom_fitvar stats')
    eu.stat.print_stats(data['s2n_mom_fitvar'])

    print('writing:', args.output)
    fitsio.write(args.output, data, clobber=True)


def show(im):
    import matplotlib.pyplot as mplt
    fig, ax = mplt.subplots()
    # ax.imshow(np.log10(im.clip(min=0.001)))
    ax.imshow(np.log10(np.abs(im)))
    mplt.savefig('/astro/u/esheldon/www/tmp/plots/tmp.png', dpi=150)
    ii = input('hit a key (q to quit): ')
    if ii == 'q':
        raise KeyboardInterrupt('stopping')


def get_piff(fname):
    import piff
    piffobj = piff.read(fname)
    return piffobj


def meas_s2n(im, cut=3, buff=2, var=None):
    imc = im[cut:-cut, cut:-cut]

    if var is None:
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
    return s2n_sum, s2n_mom, var


def meas_s2n_fit(rng, im, varguess, cut=3, ngauss=5):
    imc = im[cut:-cut, cut:-cut]

    fitter = ngmix.fitting.CoellipFitter(ngauss=ngauss)
    guesser = ngmix.guessers.CoellipPSFGuesser(
        rng=rng,
        ngauss=ngauss,
    )
    runner = ngmix.runners.PSFRunner(
        fitter,
        guesser=guesser,
        ntry=20,
    )

    res = None
    var = varguess
    for i in range(2):
        if i > 0:
            model_im = res.make_image()
            var = (model_im - imc).var()

        obs = get_obs(imc, var)
        res = runner.go(obs)

    return res['s2n']


def meas_fitvar(rng, im, varguess, cut=3, ngauss=5):
    imc = im[cut:-cut, cut:-cut]

    fitter = ngmix.fitting.CoellipFitter(ngauss=ngauss)
    guesser = ngmix.guessers.CoellipPSFGuesser(
        rng=rng,
        ngauss=ngauss,
    )
    runner = ngmix.runners.PSFRunner(
        fitter,
        guesser=guesser,
        ntry=20,
    )

    obs = get_obs(imc, varguess)
    res = runner.go(obs)

    model_im = res.make_image()
    var = (model_im - imc).var()

    return var


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
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--show', action='store_true')
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
