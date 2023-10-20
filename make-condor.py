import os
import numpy as np
import argparse


TOP = """Universe = vanilla

Notification = Never

# Run this exe with these args
Executable = run.sh

# Image_Size =  2500000
request_memory = 2G

GetEnv = True

kill_sig = SIGINT

should_transfer_files = YES
transfer_input_files = %(config_file)s

# so transfer when the job completes
when_to_transfer_output = ON_EXIT

environment = "OMP_NUM_THREADS=1"

+Experiment = "astro"

"""

TEMPLATE = """
+job_name = "%(job_name)s"
Arguments = %(seed)d
Queue
"""

RUN_TEMPLATE = r"""#!/usr/bin/env bash
export OMP_NUM_THREADS=1

seed=$1

python /astro/u/esheldon/lensing/test-noisy-psf/test.py \
    --seed ${seed} \
    --ntrial %(ntrial)d \
    --output %(front)s-${seed}.fits \
    --config %(config_file)s
"""


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--ntrial', type=int, default=10000)
    parser.add_argument('--njobs', type=int, default=1000)
    return parser.parse_args()


def main():
    args = get_args()

    rng = np.random.RandomState(args.seed)
    outdir = os.path.dirname(args.config)
    outfile = os.path.join(outdir, 'go.condor')
    runfile = os.path.join(outdir, 'run.sh')

    config_base = os.path.basename(args.config)
    front = config_base.replace('.yaml', '').replace('config-', '')

    print('writing:', runfile)
    with open(runfile, 'w') as fobj:
        run_text = RUN_TEMPLATE % {
            'config_file': config_base,
            'ntrial': args.ntrial,
            'front': front,
        }
        fobj.write(run_text)

    print('writing:', outfile)

    with open(outfile, 'w') as fobj:
        top = TOP % {'config_file': config_base}
        fobj.write(top)

        for i in range(args.njobs):
            seed = rng.randint(0, 2**29)
            job_name = '%s-%s' % (front, seed)
            text = TEMPLATE % {'seed': seed, 'job_name': job_name}

            fobj.write(text)

    os.system('chmod 755 ' + runfile)


main()
