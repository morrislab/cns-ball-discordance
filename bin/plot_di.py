import argparse
import scipy.stats
import numpy as np

import plotly.graph_objs as go
import plotly.io as pio

import resultserializer
import diversity_indices as di
import stephutil
import util
import json

def _calc_di(eta, clusters, struct, sampnames, pairs):
  lists = (
    ('sampnames', sampnames),
    ('cdi', di.calc_cdi(eta)),
    ('cmdi', di.calc_cmdi(eta, clusters, struct)),
  )

  results = {}
  for lname, L in lists:
    results['%s1' % lname] = [L[p[0]] for p in pairs]
    results['%s2' % lname] = [L[p[1]] for p in pairs]

  results['basenames'] = []
  for S1, S2 in zip(results['sampnames1'], results['sampnames2']):
    base = S1.rsplit(' ', 1)[0]
    assert S2.startswith(base)
    results['basenames'].append(base)

  assert len(set([len(V) for V in results.values()])) == 1
  return results

def _filter_di(di_results, sampname_start):
  filtered = {}
  sidxs = [sidx for sidx, sname in enumerate(di_results['basenames']) if sname.startswith(sampname_start)]
  for K, V in di_results.items():
    filtered[K] = [di_results[K][sidx] for sidx in sidxs]
  return filtered

def _plot_di(di_results):
  html = ''

  for K in ('cdi', 'cmdi'):
    X = di_results['%s1' % K]
    Y = di_results['%s2' % K]

    tail1 = di_results['sampnames1'][0].replace(di_results['basenames'][0], '').strip()
    tail2 = di_results['sampnames2'][0].replace(di_results['basenames'][0], '').strip()
    for S1, S2 in zip(di_results['sampnames1'], di_results['sampnames2']):
      assert S1.endswith(tail1)
      assert S2.endswith(tail2)

    T = dict(
      type = 'scatter',
      mode = 'markers',
      marker = {'size': 18, 'opacity': 0.75, 'color': '#000000'},
      x = X,
      y = Y,
      text = di_results['basenames'],
    )
    Z = np.min([np.max(X), np.max(Y)])
    layout = go.Layout(
      template = 'plotly_white',
      xaxis = {'title': f'{tail1} {K.upper()} (bits)', 'range': (0, 1.1*np.max(X))},
      yaxis = {'title': f'{tail2} {K.upper()} (bits)', 'range': (0, 1.1*np.max(Y))},
      shapes = [dict(
        type = 'line',
        x0 = 0,
        x1 = Z,
        y0 = 0,
        y1 = Z,
      )],
    )
    fig = go.Figure(data=T, layout=layout)

    html += pio.to_html(
      fig,
      include_plotlyjs=False,
      full_html=False,
      config = {
        'showLink': True,
        'toImageButtonOptions': {
          'format': 'svg',
          'width': 600,
          'height': 400,
        },
      }
    )
  return html

def _calc_test_stats(di_results):
  html = ''
  for K in ('cdi', 'cmdi'):
    html += f'<h3>{K.upper()}</h3>'
    html += '<table class="table table-striped"><thead><tr><th>Alt. hypothesis</th><th>Stat</th><th>p value</th></tr></thead><tbody>'
    for alt in ('two-sided', 'greater', 'less'):
      stat, pval = scipy.stats.wilcoxon(
        di_results['%s1' % K],
        di_results['%s2' % K],
        alternative = alt,
      )
      html += f'<tr><td>{alt}</td><td>{stat}</td><td>{pval}</td></tr>'
    html += '</tbody></table>'
  return html

def _process_di(di_results):
  di_sets = {
    'diagnosis': _filter_di(di_results, 'd'),
    'relapse': _filter_di(di_results, 'r'),
    'diagnosis + relapse': di_results,
  }
  html = ''

  for name, di_set in di_sets.items():
    html += f'<h2>{name.capitalize()}</h2>'
    if len(di_set['basenames']) == 0:
      html += '<p>(no data points)</p>'
      continue
    html += _plot_di(di_set)
    html += _calc_test_stats(di_set)

  return html

def main():
  parser = argparse.ArgumentParser(
    description='LOL HI THERE',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )
  parser.add_argument('--tree-index', type=int, default=0)
  parser.add_argument('results_fn')
  parser.add_argument('html_out_fn')
  args = parser.parse_args()

  results = resultserializer.Results(args.results_fn)
  sampnames = results.get('sampnames')
  clusters = results.get('clusters')

  phi = results.get('phi')[args.tree_index]
  struct = results.get('struct')[args.tree_index]
  K, S = phi.shape
  assert len(sampnames) == S
  eta = util.calc_eta(struct, phi)

  pairs = {
    'CNS': stephutil.find_samp_pairs(sampnames, ' BM', ' CNS'),
    'Spleen': stephutil.find_samp_pairs(sampnames, ' BM', ' Spleen'),
  }

  html = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'
  html += '<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css">'
  for name, P in pairs.items():
    di_results = _calc_di(eta, clusters, struct, sampnames, P)
    html += f'<h1>{name}</h1>'
    html += _process_di(di_results)

  with open(args.html_out_fn, 'w') as outf:
    print(html, file=outf)

if __name__ == '__main__':
  main()
