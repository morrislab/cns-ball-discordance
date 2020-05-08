# Use this in conjunction with the Pairtree repo's `util/reorder_samples.py`.
import argparse
import json
import re

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

  xeno_suffixes = ('CNS', 'Spleen')

  idxs = []
  def add(name):
    if name in samps:
      idxs.append(samps.index(name))

  for timepoint in ('Diagnosis', 'Relapse'):
    add(timepoint)
    xeno_bm = [samp for samp in samps if re.search('^%s Xeno \d+$' % timepoint, samp)]
    xeno_bm = sorted(xeno_bm, key = lambda S: int(S.rsplit(' ', 1)[1]))
    for samp in xeno_bm:
      add(samp)
      for suffix in xeno_suffixes:
        add('%s %s' % (samp, suffix))

  remaining = set(range(len(samps))) - set(idxs)
  idxs += sorted(remaining)
  print(','.join([str(idx) for idx in idxs]))

if __name__ == '__main__':
  main()
