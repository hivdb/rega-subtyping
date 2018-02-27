#! /usr/bin/env
from __future__ import print_function

import os
import re
import sys


def iterfiles(dirname):
    for dirname, _, filenames in os.walk(dirname):
        if not filenames:
            continue
        for filename in filenames:
            if filename == 'result.xml':
                yield os.path.join(dirname, filename)


def trans_subtype(subtype):
    if subtype == '2':
        return 'GroupN'
    elif subtype == '3':
        return 'GroupO'
    return subtype


def iterseqs_from_file(filename, keymap):
    regaid = os.path.split(os.path.split(filename)[0])[-1]
    with open(filename) as fp:
        currentseq = subtype = subtypedetail = support = ''
        in_conclusion = False
        for line in fp:
            if '<sequence' in line:
                match = next(re.finditer(r'<sequence name="([^"]+)"', line))
                currentseq = \
                    match.group(1).split('_', 1)[0]
                if currentseq not in keymap:
                    print('Not found: {}'.format(currentseq), file=sys.stderr)
                    continue
                currentseq = keymap[currentseq]
            if '<conclusion' in line:
                in_conclusion = True
            elif in_conclusion and '<id>' in line:
                match = next(re.finditer(r'<id>([^<]+)</id>', line))
                subtype = trans_subtype(match.group(1))
            elif in_conclusion and '<name>' in line:
                match = next(re.finditer(r'<name>([^<]+)</name>', line))
                subtypedetail = match.group(1)
            elif in_conclusion and '<support>' in line:
                match = next(re.finditer(r'<support>([^<]+)</support>', line))
                support = match.group(1)
            if '</sequence>' in line:
                yield currentseq, subtype, subtypedetail, support, regaid
                currentseq = subtype = subtypedetail = support = ''


def filterfasta(infile, outfile, excludes):
    skip = False
    for line in infile:
        if line.startswith('>'):
            skip = False
            accession = line[1:].strip()
            if accession in excludes:
                skip = True
        if skip:
            continue
        outfile.write(line)


def iterseqs(dirname='jobs/HIV'):
    keymap = {}
    with open('keymap.txt') as fp:
        for line in fp:
            key, header = line.strip().split('\t', 1)
            keymap[key] = header
    for filename in iterfiles(dirname):
        for row in iterseqs_from_file(filename, keymap):
            yield row


def main():
    knownseqs = set()
    print('\t'.join(['name', 'subtype',
                     'subtypedetail', 'support', 'regaid']))
    for row in iterseqs():
        if row[0] in knownseqs:
            continue
        if row[1]:
            knownseqs.add(row[0])
            print('\t'.join(row))


if __name__ == '__main__':
    main()
