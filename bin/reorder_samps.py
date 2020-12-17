# Use this in conjunction with the Pairtree repo's `util/reorder_samples.py`.
import argparse
import json
import re

def reorder(samps):
  xeno_suffixes = ('CNS', 'Spleen')
  timepoints = ('Diagnosis', 'Relapse')

  idxs = []
  def add(name):
    if name in samps:
      idxs.append(samps.index(name))

  for timepoint in timepoints:
    add(timepoint)
  for timepoint in timepoints:
    xeno_bm = [samp for samp in samps if re.search('^%sXeno \d+ BM$' % timepoint[0].lower(), samp)]
    xeno_bm = sorted(xeno_bm, key = lambda S: int(S.split(' ')[1]))
    for samp in xeno_bm:
      add(samp)
      tokens = samp.split(' ')
      for suffix in xeno_suffixes:
        add(' '.join(tokens[:2] + [suffix]))

  remaining = set(range(len(samps))) - set(idxs)
  idxs += sorted(remaining)
  return idxs

def main():
  parser = argparse.ArgumentParser(
    description='LOL HI THERE',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )
  parser.add_argument('params_fn')
  args = parser.parse_args()

  with open(args.params_fn) as F:
    params = json.load(F)
  samps = params['samples']

  idxs = reorder(samps)
  print(','.join([str(idx) for idx in idxs]))

if __name__ == '__main__':
  main()
