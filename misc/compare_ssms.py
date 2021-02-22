import os
import sys
import re
import random

PAIRTREE_DIR = os.path.expanduser('~/work/pairtree')
sys.path.append(os.path.join(PAIRTREE_DIR, 'lib'))

import inputparser

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

def _map_names_to_reads(ssms, samps):
  keys = ('var_reads', 'ref_reads', 'omega_v')
  mapped = {}
  for ssm in ssms.values():
    name = ssm['name']
    mapped[name] = {K: dict(zip(samps, ssm[K])) for K in keys}
  return mapped

def _compare(ssms, samps):
  assert len(ssms) == len(samps) == 2
  assert set(samps[0]).issubset(set(samps[1]))
  ssm_samps = [_map_names_to_reads(ssm, samp) for (ssm, samp) in zip(ssms, samps)]

  # This corresponds to the RAD21 indel in SJERG009 that Steph asked me to
  # remove in April 2017. Its absence when comparing inputs is acceptable.
  blocklist = ('8_117870645',)

  A = set([ssm['name'] for ssm in ssms[0].values()]) - set(blocklist)
  B = set([ssm['name'] for ssm in ssms[1].values()]) - set(blocklist)
  assert A == B

  for name in ssm_samps[0].keys():
    if name in blocklist:
      continue
    S0, S1 = [ssm_samps[idx][name] for idx in (0,1)]
    for K in S0.keys():
      _samps = list(S0[K].keys())
      random.shuffle(_samps)
      for samp in _samps:
        #print(name, K, samp, S0[K][samp], S1[K][samp])
        assert S0[K][samp] == S1[K][samp]

def main():
  ssmfns = (sys.argv[1], sys.argv[3])
  paramfns = (sys.argv[2], sys.argv[4])

  ssms = [inputparser.load_ssms(F) for F in ssmfns]
  params = [inputparser.load_params(F) for F in paramfns]
  samps = [P['samples'] for P in params]


  samps_to_rename = (0,)
  for idx in samps_to_rename:
    samps[idx] = _rename(samps[idx])

  _compare(ssms, samps)

if __name__ == '__main__':
  main()
