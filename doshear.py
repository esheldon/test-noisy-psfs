import numpy as np
import esutil as eu
import argparse
import fitsio


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--flist', nargs='+', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--noshear', action='store_true')
    return parser.parse_args()


def main():
    args = get_args()
    data = eu.io.read(args.flist)
    psf_data = eu.io.read(args.flist[0], ext='psf_data')

    shear_true = 0.02

    w = _select(data=data, shear_type='noshear')
    w_1p = _select(data=data, shear_type='1p')
    w_1m = _select(data=data, shear_type='1m')

    g = data['g'][w].mean(axis=0)
    gerr = data['g'][w].std(axis=0) / np.sqrt(w.size)
    g1_1p = data['g'][w_1p, 0].mean()
    g1_1m = data['g'][w_1m, 0].mean()

    R11 = (g1_1p - g1_1m)/0.02

    shear = g[0] / R11
    shear_err = gerr[0] / R11
    if not args.noshear:
        m1 = shear / shear_true - 1
        m1err = shear_err / shear_true
    else:
        c1 = g[0] / R11
        c1err = gerr[0] / R11

    c2 = g[1] / R11
    c2err = gerr[1] / R11

    s2n = data['s2n'][w].mean()
    print('S/N: %g' % s2n)
    print('PSF S/N: %g' % psf_data['psf_s2n'].mean())
    print('R11: %g' % R11)
    # print('m: %g +/- %g (99.7%% conf)' % (m, merr*3))
    # print('c: %g +/- %g (99.7%% conf)' % (c, cerr*3))
    if not args.noshear:
        _printres(m1, m1err, 'm1')
    else:
        _printres(c1, c1err, 'c1')

    _printres(c2, c2err, 'c2')

    if not args.noshear:
        _printres_range(m1, m1err, 'm')
    else:
        _printres_range(c1, c1err, 'c1')

    _printres_range(c2, c2err, 'c2')

    dtype = []
    if not args.noshear:
        dtype += [
            ('m1', 'f4'),
            ('m1err', 'f4'),
        ]
    else:
        dtype += [
            ('c1', 'f4'),
            ('c1err', 'f4'),
        ]

    dtype += [
        ('c2', 'f4'),
        ('c2err', 'f4'),
    ]

    out = np.zeros(1, dtype=dtype)
    if not args.noshear:
        out['m1'] = m1
        out['m1err'] = m1err
    else:
        out['c1'] = c1
        out['c1err'] = c1err

    out['c2'] = c2
    out['c2err'] = c2err
    print('writing:', args.output)
    fitsio.write(args.output, out, clobber=True)


def _printres(val, valerr, name):
    err3 = 3 * valerr
    print('%s = %g +/- %g (99.7%% conf)' % (name, val, err3))


def _printres_range(val, valerr, name):
    err3 = 3 * valerr
    low = val - err3
    high = val + err3

    print('%.3g < %s < %.3g  (99.7%% conf)' % (low, name, high))


def _select(data, shear_type):
    """
    select the data by shear type and size
    Parameters
    ----------
    data: array
        The array with fields shear_type and T
    shear_type: str
        e.g. 'noshear', '1p', etc.
    Returns
    -------
    array of indices
    """
    # raw moments, so the T is the post-psf T.  This the
    # selection is > 1.2 rather than something smaller like 0.5
    # for pre-psf T from one of the maximum likelihood fitters
    wtype, = np.where(data['shear_type'] == shear_type)

    w, = np.where(
        (data['flags'][wtype] == 0) &
        (data['s2n'][wtype] > 5_000_000) &
        (data['T_ratio'][wtype] > 1.2)
    )
    print('%s kept: %d/%d' % (shear_type, w.size, wtype.size))
    w = wtype[w]
    return w


if __name__ == '__main__':
    main()
