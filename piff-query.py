import easyaccess
import random

TEMPLATE = r"""
select m.tilename,m.band,fai.path||'/'||fai.filename||fai.compression
from proctag t, miscfile m, desfile d1, opm_used u, desfile d2, file_archive_info fai
where t.tag='Y6A2_MEDS_V3'
    and t.pfw_attempt_id=m.pfw_attempt_id
    and m.filetype='coadd_meds'
    and m.filename=d1.filename
    and d1.wgb_task_id=u.task_id
    and u.desfile_id=d2.id
    and d2.filetype='piff_model'
    and d2.id=fai.desfile_id and m.tilename='%(tilename)s'
"""  # noqa


def load_tiles():
    with open('tiles.txt') as fobj:
        tiles = [t.strip() for t in fobj]
    return tiles


def main():
    tiles = load_tiles()
    random.shuffle(tiles)
    tiles = tiles[:100]
    # tiles = ['DES0305-5205']

    with open('piff-paths.txt', 'w') as fobj:
        conn = easyaccess.connect(section='desoper')
        for i, tile in enumerate(tiles):
            print(f'{tile} {i+1}/{len(tiles)}')
            query = TEMPLATE % {'tilename': tile}

            curs = conn.cursor()
            curs.execute(query)
            for row in curs.fetchall():
                path = row[2]
                print(row)
                print(path, file=fobj)


main()
