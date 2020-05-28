#!/usr/bin/env python3
import argparse
import random
import numpy as np

import os
import sys
PAIRTREE_DIR = os.path.expanduser('~/work/pairtree')
sys.path.append(os.path.join(PAIRTREE_DIR, 'lib'))

import common
import resultserializer
import clustermaker
import inputparser

import vaf_plotter
import relation_plotter
import json
import util
import plotutil

import csv

def _choose_colours(N):
  import plotly.colors
  colours = plotly.colors.qualitative.Dark24
  chosen = [colours[idx % len(colours)] for idx in range(N)]
  random.shuffle(chosen)
  return chosen

def _write_tree_json(tree_struct, jsonfn):
  with open(jsonfn, 'w') as F:
    print(json.dumps(tree_struct), file=F)

def write_header(runid, tidx, outf):
  if runid is not None:
    title = '%s tree' % runid
  else:
    title = 'Tree'

  print('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>%s</title>' % title, file=outf)
  print('<script src="https://d3js.org/d3.v5.min.js"></script>', file=outf)
  for jsfn in ('util.js', 'highlight_table_labels.js', 'phi_plotter.js', 'eta_plotter.js', 'vaf_matrix.js', 'tree_plotter.js'):
    print('<script type="text/javascript">%s</script>' % plotutil.read_file(jsfn), file=outf)

  basedir = os.path.join(os.path.dirname(__file__), '..', 'plot_resources')
  print('<script type="text/javascript">%s</script>' % plotutil.read_file('steph_eta_plotter.js', basedir), file=outf)

  print('<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css">', file=outf)
  for cssfn in ('tree.css', 'matrix.css'):
    print('<style type="text/css">%s</style>' % plotutil.read_file(cssfn), file=outf)
  print('<style type="text/css">.container { margin: 30px; } td, th, table { padding: 5px; margin: 0; border-collapse: collapse; font-weight: normal; } span { visibility: hidden; } td:hover > span { visibility: visible; } .highlighted { background-color: black !important; color: white; }</style>', file=outf)
  print('</head><body><main>', file=outf)
  if runid is not None:
    print('<h1>%s</h1>' % runid, file=outf)

def write_footer(outf):
  print('</main></body></html>', file=outf)

def _write_tree_html(tree_data, tidx, visible_sampidxs, samp_colours, pop_colours, plot_eta, plot_phi, plot_phi_hat, plot_phi_error, plot_phi_interleaved, outf):
  tree_data['visible_sampidxs'] = visible_sampidxs
  tree_data['samp_colours'] = samp_colours
  tree_data['pop_colours'] = pop_colours

  print('''
  <script type="text/javascript">
  var tree_json = '%s';
  var results = JSON.parse(tree_json);

  if(results.visible_sampidxs !== null) {
    results.visible_eta = results.eta.map(function(E) { return results.visible_sampidxs.map(function(idx) { return E[idx]; }); });
    results.visible_phi = results.phi.map(function(P) { return results.visible_sampidxs.map(function(idx) { return P[idx]; }); });
    results.visible_samps = results.visible_sampidxs.map(function(idx) { return results.samples[idx]; });
  } else {
    results.visible_eta = results.eta;
    results.visible_phi = results.phi;
    results.visible_samps = results.samples;
  }
  </script>''' % json.dumps(tree_data), file=outf)

  print('''
  <div id="trees" class="container"><h2>Tree</h2></div>
  %s
  ''' % plotutil.js_on_load('''
    var container = '#trees';
    d3.select(container).append('h3').text('tidx=' + %s + ' nlglh=' + results.nlglh.toFixed(3) + ' prob=' + results.prob.toFixed(3));
    if(results.samp_colours) {
      d3.select(container).append('h6').text('Sample colours:');
      var colour_list = d3.select(container).append('ul');
      results.samp_colours.forEach(function(pair) { colour_list.append('li').style('color', pair[1]).text(pair[0]); });
    }
    (new TreePlotter()).plot(
      0,
      results.parents,
      results.phi,
      results.samples,
      results.samp_colours,
      results.pop_colours,
      container
    );
  ''' % tidx), file=outf)


  if plot_eta:
    print('''
    <div id="steph_eta_matrix" class="container"><h2>Steph population frequencies</h2></div>
    %s
    ''' % plotutil.js_on_load('''
    (new StephEtaPlotter()).plot(results.visible_eta, results.visible_samps, results.discord, '#steph_eta_matrix', 0, true);
    '''), file=outf)

  if plot_phi:
    print('''
    <div id="phi_matrix" class="container"><h2>Tree-constrained lineage frequencies</h2></div>
    %s
    ''' % plotutil.js_on_load('''
      (new PhiMatrix()).plot(results.visible_phi, results.visible_samps, '#phi_matrix');
    '''), file=outf)

  if plot_phi_hat:
    print('''
    <div id="phi_hat_matrix" class="container"><h2>Data-implied lineage frequencies</h2></div>
    %s
    ''' % plotutil.js_on_load('''(new PhiMatrix().plot(results.phi_hat, results.samples, '#phi_hat_matrix'));'''), file=outf)

  if plot_phi_error:
    print('''
    <div id="phi_error_matrix" class="container"><h2>Lineage frequency error</h2></div>
    %s
    ''' % plotutil.js_on_load('''(new PhiErrorMatrix()).plot(results.phi, results.phi_hat, results.samples, '#phi_error_matrix');'''), file=outf)

  if plot_phi_interleaved:
    print('''
    <div id="phi_interleaved_matrix" class="container"><h2>Interleaved lineage frequencies</h2></div>
    %s
    ''' % plotutil.js_on_load('''(new PhiInterleavedMatrix()).plot(results.phi, results.phi_hat, results.samples, '#phi_interleaved_matrix');'''), file=outf)

def write_cluster_stats(clusters, garbage, supervars, variants, outf):
  cluster_dev = []
  for C, S in zip(clusters, supervars):
    S_freq = S['vaf'] / (2*S['omega_v'])[None,:] # 1xS
    cluster_freq = np.array([variants[V]['vaf'] / (2*variants[V]['omega_v']) for V in C]) # |C|xS
    absdev = np.abs(cluster_freq - S_freq)
    cluster_dev.append(np.median(absdev))

  rows = [(cidx + 1, len(C), '%.3f' % cdev) for cidx, (C, cdev) in enumerate(zip(clusters, cluster_dev))]
  rows.append(('Garbage', len(garbage), None))
  rows.append(('Total', np.sum([len(C) for C in clusters]), None))

  print('<h2>Cluster stats</h2>', file=outf)
  print('<table class="table table-striped table-hover">', file=outf)
  print('<thead><tr><th>Cluster</th><th>Members</th><th>Deviation</th></tr></thead><tbody>', file=outf)
  for row in rows:
    rowhtml = ''.join(['<td>%s</td>' % (V if V is not None else '&mdash;') for V in row])
    print('<tr>%s</tr>' % rowhtml, file=outf)
  print('</tbody></table>', file=outf)

def _choose_plots(to_plot, to_omit, all_choices):
  # Duplicate set.
  if to_plot is None:
    plot_choices = set(all_choices)
  else:
    plot_choices = set(to_plot)

  if to_omit is not None:
    plot_choices -= to_omit

  assert plot_choices.issubset(all_choices)
  # If we want to plot any of the phi matrices, we need to also plot the
  # tree, so that the relevant data structures are generated below. This is
  # silly, so I should fix it eventually -- we should be able to plot just
  # the phis if we want.
  if len(set(('phi', 'phi_hat', 'phi_error', 'phi_interleaved')) & plot_choices) > 0:
    plot_choices.add('tree')

  return plot_choices

def _reorder_subclones(data, params):
  old_to_new = {}
  new_to_old = {}
  K = len(data['struct']) + 1
  root = 0

  nodes = [root]
  while len(nodes) > 0:
    old_idx = nodes.pop(0)
    assert old_idx not in old_to_new
    new_idx = len(new_to_old)
    assert new_idx not in new_to_old
    old_to_new[old_idx] = new_idx
    new_to_old[new_idx] = old_idx

    children = np.flatnonzero(data['struct'] == old_idx) + 1
    children = sorted(children, key = lambda I: -np.mean(data['phi'][I]))
    nodes += children
  for D in (old_to_new, new_to_old):
    assert D[root] == root
    assert set(D.keys()) == set(D.values()) == set(range(K))

  new_data = dict(data)
  new_data['clusters'] = [data['clusters'][new_to_old[idx] - 1] for idx in range(1, K)]
  new_data['phi'] = np.array([data['phi'][new_to_old[idx]] for idx in range(K)])

  new_parents = {old_to_new[idx + 1]: old_to_new[parent] for idx, parent in enumerate(data['struct'])}
  new_data['struct'] = np.array([new_parents[idx] for idx in range(1, K)], dtype=np.int)

  old_svids = new_data['clustrel_posterior'].vids
  new_svids = ['S%s' % old_to_new[int(svid[1:])] for svid in old_svids]
  new_data['clustrel_posterior'] = new_data['clustrel_posterior']._replace(vids = new_svids)

  new_params = dict(params)
  if 'pop_colours' in new_params:
    new_params['pop_colours'] = [new_params['pop_colours'][new_to_old[idx]] for idx in range(K)]

  return (new_data, new_params)

def _parse_discord(discordfn):
  with open(discordfn) as F:
    reader = csv.DictReader(F)
    rows = list(reader)
  discord = [(row['samp1'], row['samp2'], float(row['p_discord'])) for row in rows]
  return discord

def main():
  all_plot_choices = set((
    'tree',
    'pairwise_separate',
    'pairwise_mle',
    'vaf_matrix',
    'phi',
    'phi_hat',
    'phi_error',
    'phi_interleaved',
    'cluster_stats',
    'eta',
  ))
  parser = argparse.ArgumentParser(
    description='LOL HI THERE',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )
  parser.add_argument('--seed', type=int)
  parser.add_argument('--tree-index', type=int, default=0)
  parser.add_argument('--plot', dest='plot_choices', type=lambda s: set(s.split(',')),
    help='Things to plot; by default, plot everything')
  parser.add_argument('--omit-plots', dest='omit_plots', type=lambda s: set(s.split(',')),
    help='Things to omit from plotting; overrides --plot')
  parser.add_argument('--runid')
  parser.add_argument('--reorder-subclones', action='store_true',
    help='Reorder subclones according to depth-first search through tree structure')
  parser.add_argument('--tree-json', dest='tree_json_fn',
    help='Additional external file in which to store JSON, which is already stored statically in the HTML file')
  parser.add_argument('--colour-eta-uniquely', action='store_true',
    help='Choose unique colours for each population in eta plot')
  parser.add_argument('ssm_fn')
  parser.add_argument('params_fn')
  parser.add_argument('pairtree_fn')
  parser.add_argument('discord_fn')
  parser.add_argument('html_out_fn')
  args = parser.parse_args()

  if args.seed is not None:
    random.seed(args.seed)
    np.random.seed(args.seed)

  plot_choices = _choose_plots(args.plot_choices, args.omit_plots, all_plot_choices)

  results = resultserializer.Results(args.pairtree_fn)
  variants = inputparser.load_ssms(args.ssm_fn)
  params = inputparser.load_params(args.params_fn)
  discord = _parse_discord(args.discord_fn)

  data = {K: results.get(K)[args.tree_index] for K in (
    'struct',
    'count',
    'llh',
    'prob',
    'phi',
  )}
  data['garbage'] = results.get('garbage')
  data['clusters'] = results.get('clusters')
  data['samples'] = results.get('sampnames')
  data['clustrel_posterior'] = results.get_mutrel('clustrel_posterior')
  if args.reorder_subclones:
    data, params = _reorder_subclones(data, params)

  if 'hidden_samples' in params:
    hidden = set(params['hidden_samples'])
    assert hidden.issubset(set(data['samples'])) and len(hidden) < len(data['samples'])
    visible_sampidxs = [idx for idx, samp in enumerate(data['samples']) if samp not in hidden]
  else:
    visible_sampidxs = None

  samp_colours = params.get('samp_colours', None)
  pop_colours = params.get('pop_colours', None)
  if samp_colours is not None:
    assert set([S[0] for S in samp_colours]).issubset(data['samples'])
  if pop_colours is not None:
    assert len(pop_colours) == len(data['struct']) + 1

  supervars = clustermaker.make_cluster_supervars(data['clusters'], variants)
  supervars = [supervars[vid] for vid in common.sort_vids(supervars.keys())]

  with open(args.html_out_fn, 'w') as outf:
    write_header(args.runid, args.tree_index, outf)

    if 'tree' in plot_choices:
      tree_struct = util.make_tree_struct(
        data['struct'],
        data['count'],
        data['llh'],
        data['prob'],
        data['phi'],
        supervars,
        data['samples'],
      )
      tree_struct['discord'] = discord
      _write_tree_html(
        tree_struct,
        args.tree_index,
        visible_sampidxs,
        samp_colours,
        pop_colours,
        'eta' in plot_choices,
        'phi' in plot_choices,
        'phi_hat' in plot_choices,
        'phi_error' in plot_choices,
        'phi_interleaved' in plot_choices,
        outf,
      )
      if args.tree_json_fn is not None:
        _write_tree_json(full_tree_struct, args.tree_json_fn)

    if 'vaf_matrix' in plot_choices:
      vaf_plotter.plot_vaf_matrix(
        data['clusters'],
        variants,
        supervars,
        data['garbage'],
        data['phi'],
        data['samples'],
        should_correct_vaf=True,
        outf=outf,
      )

    if 'pairwise_mle' in plot_choices:
      relation_plotter.plot_ml_relations(data['clustrel_posterior'], outf)
    if 'pairwise_separate' in plot_choices:
      relation_plotter.plot_separate_relations(data['clustrel_posterior'], outf)
    if 'cluster_stats' in plot_choices:
      write_cluster_stats(data['clusters'], data['garbage'], supervars, variants, outf)

    write_footer(outf)

if __name__ == '__main__':
  main()
