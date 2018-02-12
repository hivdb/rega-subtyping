import re
import sys
import time
import asyncio
import requests

TARGETS = [
    'http://rega:8080/RegaSubtyping/hiv/typingtool'
] * 30
MAX_PARALLEL_TASKS = len(TARGETS)
SEQS_IN_BATCH = 1


def findfirst(pattern, string, flags=0):
    return next(re.finditer(pattern, string, flags))


async def post_fasta(fasta, target):
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
                seq_input: fasta
            }, headers=headers
        )
    )
    jobid = findfirst(r'job/(\d+)/?;', resp.url).group(1)
    start = time.time()
    while True:
        if 'Analysis in progress...' not in resp.text:
            break
        await asyncio.sleep(1)
        resp = await loop.run_in_executor(
            None, lambda: requests.get(resp.url, headers=headers))
    print(fasta.split(None, 1)[0],
          'finished in %.2f seconds.' % (time.time() - start))
    return jobid


async def main():
    fasta_files = sys.argv[1:]
    futures = []
    partial = []
    seqcount = -1
    for fasta_file in fasta_files:
        with open(fasta_file, 'r') as fp:
            for line in fp:
                if line.startswith('>'):
                    if seqcount == SEQS_IN_BATCH:
                        futures.append(
                            post_fasta(''.join(partial), TARGETS[len(futures)])
                        )
                        if len(futures) == MAX_PARALLEL_TASKS:
                            await asyncio.wait(futures)
                            futures = []
                        partial = []
                        seqcount = 0
                    seqcount += 1
                partial.append(line)
    if partial:
        futures.append(post_fasta(''.join(partial), TARGETS[len(futures)]))
    if futures:
        await asyncio.wait(futures)


if __name__ == '__main__':
    start = time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
    print('All finished in %.2f seconds.' % (time.time() - start))
