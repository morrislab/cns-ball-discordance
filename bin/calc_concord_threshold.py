import argparse
import numpy as np
import json

def _calc_acc(truth, logbf, thresh):
  pred = logbf >= thresh
  acc = np.sum(np.logical_not(np.logical_xor(pred, truth))) / len(truth)
  return acc

def _calc(truth, logbf):
  optimal_thresh = 0
  optimal_acc = -np.inf

  for thresh in np.arange(-20, 20, 0.1):
    thresh = np.round(thresh, decimals=1)
    acc = _calc_acc(truth, logbf, thresh)
    if acc > optimal_acc:
      optimal_acc = acc
      optimal_thresh = thresh
  return optimal_thresh

def main():
  parser = argparse.ArgumentParser(
    description='LOL HI THERE',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )
  parser.add_argument('discord_fns', nargs='+')
  args = parser.parse_args()

  discord = []
  for fn in args.discord_fns:
    with open(fn) as F:
      discord.append(json.load(F)['concord'])

  pts = [(samp_pair['log_bf'], samp_pair['truth_discord']) for run in discord for samp_pair in run]
  logbf = np.array(list(zip(*pts))[0])
  truth = np.array(list(zip(*pts))[1])
  optimal = _calc(truth, logbf)

  print('<h4>Sample pairs: %s</h4>' % len(truth))
  print('<table class="table table-striped table-hover"><thead><tr><th>Threshold</th><th>Agreement for log_bf &GreaterEqual; threshold</th></tr></thead><tbody>')
  for thresh in sorted((0.0, 1.0, 2.0, 3.0, 9.0, 10.0, optimal)):
    print('<tr><td>%.1f</td><td>%.1f%%</td></tr>' % (thresh, 100*_calc_acc(truth, logbf, thresh)))
  print('</tbody></table>')

if __name__ == '__main__':
  main()

