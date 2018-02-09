#! /bin/sh
pip install requests
sleep 10
echo "start"
python /usr/src/batch-caller.py data.fasta
