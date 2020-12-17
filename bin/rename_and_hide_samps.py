# Use this in conjunction with the Pairtree repo's `util/reorder_samples.py`.
import argparse
import json
import re

def _rename(samps):
  def _ren(S):
    if S == 'D':
      return 'Diagnosis'
    elif re.search(r'^D\d+$', S):
      return 'Diagnosis ' + S[1:]
    elif S == 'R1':
      return 'Relapse'
    elif re.search(r'^R\d+$', S):
      return 'Relapse ' + S[1:]
    elif re.search(r'^(Diagnosis|Relapse) Xeno \d+$', S):
      return '%sXeno %s BM' % (
        S[0].lower(),
        S.rsplit(' ')[-1],
      )
    elif re.search(r'^(Diagnosis|Relapse) Xeno \d+ (Spleen|CNS)$', S):
      xidx, tissue = S.rsplit(' ')[-2:]
      return '%sXeno %s %s' % (
        S[0].lower(),
        xidx,
        tissue,
      )
    else:
      return S

  return [_ren(S) for S in samps]

def _hide(samps):
  hidden = []
  def _should_hide(S):
    if S in ('Diagnosis', 'Relapse'):
      return False
    elif re.search(r'^(d|r)Xeno \d+ (BM|CNS)$', S):
      return False
    else:
      return True

  return [S for S in samps if _should_hide(S)]

def main():
  parser = argparse.ArgumentParser(
    description='LOL HI THERE',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )
  parser.add_argument('orig_params_fn')
  parser.add_argument('new_params_fn')
  args = parser.parse_args()

  with open(args.orig_params_fn) as F:
    params = json.load(F)
  samps = params['samples']

  samps = _rename(samps)
  hidden = _hide(samps)

  params['samples'] = samps
  params['hidden_samples'] = hidden
  with open(args.new_params_fn, 'w') as F:
    json.dump(params, F)

if __name__ == '__main__':
  main()
