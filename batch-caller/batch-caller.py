import re
import sys
import time
import asyncio
import requests

from make_tsv import iterseqs

TARGETS = [
    'http://rega:8080/RegaSubtyping/hiv/typingtool'
] * 30
MAX_PARALLEL_TASKS = len(TARGETS)


def findfirst(pattern, string, flags=0):
    return next(re.finditer(pattern, string, flags))


async def post_sequence(header, seq, target):
    fasta = '>{}\n{}\n'.format(header, seq)
    headers = {
        'Accept-Language': 'en'
    }
    resp = await loop.run_in_executor(
        None, lambda: requests.get(target, headers=headers))
    sid = findfirst(r'jsessionid=([\dA-F]+)', resp.text).group(1)
    url = '{tgt};jsessionid={sid}?wtd={sid}'.format(tgt=target, sid=sid)
    resp = await loop.run_in_executor(
        None, lambda: requests.get(url + '&js=no', headers=headers))
    seq_input = findfirst(r'seq-input-fasta_[^"]+', resp.text).group(0)
    button_run = findfirst(
        r'id="button-run_[^"]+" name="([^"]+)"', resp.text).group(1)
    resp = await loop.run_in_executor(
        None, lambda: requests.post(
            url, data={
                'request': 'page',
                'wtd': sid,
                button_run: '',
                seq_input: fasta,
            }, headers=headers
        )
    )
    try:
        jobid = findfirst(r'job/(\d+)/?;', resp.url).group(1)
    except StopIteration:
        return
    start = time.time()
    while True:
        if 'Analysis in progress...' not in resp.text:
            break
        await asyncio.sleep(1)
        resp = await loop.run_in_executor(
            None, lambda: requests.get(resp.url, headers=headers))
    print(fasta.split(None, 1)[0],
          'finished in %.2f seconds.' % (time.time() - start))
    sys.stdout.flush()
    return jobid


def iter_sequences(fasta_files):
    header = None
    seq = []
    for fasta_file in fasta_files:
        with open(fasta_file, 'r') as fp:
            for line in fp:
                if line.startswith('#'):
                    continue
                elif line.startswith('>'):
                    if seq:
                        yield header, ''.join(seq)
                    header = line[1:].strip()
                    seq = []
                else:
                    seq.append(line.strip())
    if seq:
        yield header, ''.join(seq)


def refresh_keymap(sequences):
    with open('keymap.txt', 'w') as fp:
        curkey = 1
        for header, _ in sequences:
            fp.write('SEQ{}\t{}\n'.format(curkey, header))
            curkey += 1


def get_reversed_keymap():
    reversed_keymap = {}
    with open('keymap.txt', 'r') as fp:
        for line in fp:
            key, header = line.strip().split('\t')
            reversed_keymap[header] = key
    return reversed_keymap


async def batch_run(sequences):
    reversed_keymap = get_reversed_keymap()
    known_seqs = set(row[0] for row in iterseqs('/usr/src/jobs/HIV'))
    futures = []
    hasnew = False
    for header, seq in sequences:
        if header in known_seqs:
            print('Skipped known sequence {}'.format(header))
            sys.stdout.flush()
            continue
        hasnew = True
        header = reversed_keymap[header]
        futures.append(
            post_sequence(header, seq, TARGETS[len(futures)])
        )
        if len(futures) == MAX_PARALLEL_TASKS:
            await asyncio.wait(futures)
            futures = []
    if futures:
        await asyncio.wait(futures)
    return hasnew


async def main():
    fasta_files = sys.argv[1:]
    sequences = list(iter_sequences(fasta_files))
    refresh_keymap(sequences)
    for i in range(1000):
        if not await batch_run(sequences):
            break


if __name__ == '__main__':
    start = time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
    print('All finished in %.2f seconds.' % (time.time() - start))
