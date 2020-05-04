import argparse
import numpy as np
import numpy.ma as ma
import scipy.special
import csv

import common
import inputparser
import resultserializer
import util

def _convert_clustering_to_assignment(clusters):
  mapping = {vid: cidx for cidx, cluster in enumerate(clusters) for vid in cluster}
  vids = common.sort_vids(mapping.keys())
  assign = np.array([mapping[vid] for vid in vids], dtype=np.int32)
  return (vids, assign)

def _find_samp_pairs(sampnames, tail=' CNS'):
  pairs = []
  for idx1, samp in enumerate(sampnames):
    if not samp.endswith(tail):
      continue
    other = samp[:-len(tail)]
    idx2 = sampnames.index(other)
    pairs.append((idx2, idx1))
  return pairs

def _calc_kld(P, Q):
  for A in (P, Q):
    assert np.all(A >= 0)
    assert np.allclose(1, np.sum(A, axis=0))
  logP = ma.log2(ma.masked_equal(P, 0))
  logQ = ma.log2(ma.masked_equal(Q, 0))
  kld = np.sum(P * (logP - logQ), axis=0)

  assert np.allclose(0, kld[kld < 0])
  kld = np.abs(kld)
  assert np.all(kld >= 0)
  return kld

def _calc_jsd(P, Q):
  M = 0.5*(P + Q)
  kld1 = _calc_kld(P, M)
  kld2 = _calc_kld(Q, M)
  jsd = 0.5*(kld1 + kld2)
  assert np.allclose(1, jsd[jsd > 1])
  jsd = np.minimum(1, jsd)
  assert np.all(jsd >= 0) and np.all(jsd <= 1)
  return jsd

def _calc_concord_jsd(eta, pairs):
  jsd = {}
  for sidx1, sidx2 in pairs:
    jsd[(sidx1, sidx2)] = _calc_jsd(eta[:,sidx1], eta[:,sidx2])
  return jsd

def _calc_data_llh(V, T_prime, C, Z, sidxs):
  V = V[:,sidxs]
  T_prime = T_prime[:,sidxs]

  phi_alpha = 0.5
  phi_beta = 0.5
  llh = 0

  for cidx in range(C):
    members = Z == cidx
    V_c = np.sum(V[members])
    T_c = np.sum(T_prime[members])
    R_c = T_c - V_c

    llh_c = 0
    llh_c += -util.lbeta(phi_alpha, phi_beta)
    llh_c += util.lbeta(phi_alpha + V_c, phi_beta + R_c)
    llh_c += np.sum(util.log_N_choose_K(T_prime[members], V[members]))
    llh += llh_c

  return llh

def _calc_bayes_factors(variants, clusters, eta, pairs):
  K, S = eta.shape
  assert len(clusters) == K - 1

  C = len(clusters)
  vids1, Z = _convert_clustering_to_assignment(clusters)
  vids2, V, T, T_prime, omega = inputparser.load_read_counts(variants)
  assert vids1 == vids2

  logbf = {}
  for pair in pairs:
    assert len(pair) == 2
    # Model 1: discordant
    # Model 2: concordant
    m1_llh = np.sum([_calc_data_llh(V, T_prime, C, Z, sidx) for sidx in pair])
    m2_llh = _calc_data_llh(V, T_prime, C, Z, pair)
    logbf[pair] = (m1_llh, m2_llh)
  return logbf

def _print_concord(variants, clusters, eta, sampnames, truth):
  pairs = _find_samp_pairs(sampnames)
  jsd = _calc_concord_jsd(eta, pairs)
  logbf = _calc_bayes_factors(variants, clusters, eta, pairs)

  assert len(pairs) == len(jsd) == len(logbf)
  fields = (
    'samp1',
    'samp2',
    'jsd',
    'm1_llh',
    'm2_llh',
    'log_bf',
    'p_discord',
    'truth_discord',
  )
  rows = []

  for pair in pairs:
    sidx1, sidx2 = pair
    key = frozenset([sampnames[sidx] for sidx in pair])
    T = truth[key] if key in truth else 'NA'

    rows.append({
      'samp1': sampnames[sidx1],
      'samp2': sampnames[sidx2],
      'jsd': jsd[pair],
      'm1_llh': logbf[pair][0],
      'm2_llh': logbf[pair][1],
      'log_bf': logbf[pair][0] - logbf[pair][1],
      'p_discord': np.exp(logbf[pair][0] - scipy.special.logsumexp(logbf[pair])),
      'truth_discord': T,
    })

  rows = sorted(rows, key = lambda R: R['log_bf'])
  print(*fields, sep=',')
  for R in rows:
    for key in ('jsd', 'p_discord'):
      R[key] = '%.3f' % R[key]
    print(*[R[key] for key in fields], sep=',')

def _parse_truth(truthfn):
  truth = {}
  with open(truthfn) as F:
    reader = csv.DictReader(F)
    for row in reader:
      pair = frozenset((row['samp1'], row['samp2']))
      truth[pair] = {'1': True, '0': False}[row['discord']]
  return truth

def main():
  parser = argparse.ArgumentParser(
    description='LOL HI THERE',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )
  parser.add_argument('--tree-index', type=int, default=0)
  parser.add_argument('ssm_fn')
  parser.add_argument('results_fn')
  parser.add_argument('truth_fn')
  args = parser.parse_args()

  variants = inputparser.load_ssms(args.ssm_fn)
  truth = _parse_truth(args.truth_fn)

  results = resultserializer.Results(args.results_fn)
  sampnames = results.get('sampnames')
  clusters = results.get('clusters')
  garbage = results.get('garbage')
  variants = inputparser.remove_garbage(variants, garbage)

  phi = results.get('phi')[args.tree_index]
  struct = results.get('struct')[args.tree_index]
  K, S = phi.shape
  assert len(sampnames) == S
  eta = util.calc_eta(struct, phi)

  _print_concord(variants, clusters, eta, sampnames, truth)

if __name__ == '__main__':
  main()
