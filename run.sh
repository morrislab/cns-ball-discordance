#!/bin/sh
PTDIR=$HOME/work/pairtree
INDIR=$HOME/work/pairtree-experiments/inputs/steph.xeno.with_cns.pairtree
RESULTDIR=$PTDIR/scratch/clusters.steph

function compute_clusters {
  for conc in 1000 100 10 1 0.1 0.01 0.001 0.0001 0.00001 0.000001; do
    outd=$RESULTDIR/clusters.conc.$(echo $conc | tr . _)
    mkdir -p $outd

    for foo in $INDIR/*.ssm; do
      runid=$(basename $foo | cut -d. -f1)
      echo "python3 $PTDIR/bin/clustervars --parallel 5 --model pairwise --concentration $conc --iterations 10000 $INDIR/$runid.{ssm,params.json} $outd/$runid.params.json 2>/dev/null"
    done
  done | grep -v -e SJETV010 -e SJBALL022610 | parallel -j80 --halt 1 --eta
}

function compare_cluster_count {
  cd $RESULTDIR

  (
    allconc=$(ls -d clusters* | cut -d. -f3)
    echo "runid,$(echo $allconc | tr ' ' , | tr _ .),handbuilt"
    for foo in clusters.conc.0_01/SJ*.params.json; do
      runid=$(basename $foo | cut -d. -f1)
      echo $runid $(for conc in $allconc; do cat clusters.conc.$conc/$runid.params.json | jq '.clusters|length'; done; cat $INDIR/$runid.params.json | jq '.clusters|length') | tr ' ' ','
    done
  ) > $RESULTDIR/counts.csv
}

function plot_clusters {
  for foo in $RESULTDIR/clusters.conc.*/*.params.json; do
    runid=$(basename $foo | cut -d. -f1)
    echo "python3 $PTDIR/bin/plotvars --plot-relations --parallel 1 $INDIR/$runid.ssm $foo $(dirname $foo)/$runid.clusters.html 2>&1"
  done | parallel -j40 --halt 1 --eta | grep -v '^{'
}

function make_index {
  cd $RESULTDIR
  for foo in clusters.conc.*; do
    conc=$(echo $foo | cut -d. -f3)
    (
      echo "<h3>concentration = $(echo $conc | tr '_' '.')</h3><ul>"
      for H in $foo/*.html; do
        echo "<li><a href=$H>$(basename $H | cut -d. -f1)</a></li>"
      done
      echo "</ul>"
    )
  done > index.html
}

function run_pairtree {
  cd $RESULTDIR/clusters.conc.0_01
  for foo in *.params.json; do
    runid=$(basename $foo | cut -d. -f1)
    echo "python3 $PTDIR/bin/pairtree --seed 1337 --parallel 40 --params $foo --phi-fitter rprop $INDIR/$runid.ssm $runid.results.npz 2>$runid.stderr"
  done | parallel -j1 --halt 1 --eta
}

function main {
  compute_clusters
  #compare_cluster_count
  #plot_clusters
  #make_index
  #run_pairtree
}

main
