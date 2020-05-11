#!/bin/sh
set -euo pipefail

BASEDIR=$HOME/work/steph-concord
PTDIR=$HOME/work/pairtree
DATADIR=$BASEDIR/data
INDIR=$DATADIR/inputs
DISCORDTRUTHDIR=$DATADIR/discord.truth
CLUSTMODEL=pairwise
CLUSTRESULTDIR=$BASEDIR/scratch/clusters.steph.${CLUSTMODEL}.prior015
TREERESULTDIR=$BASEDIR/scratch/trees
PARALLEL=10
NCHAINS=10
PYTHON=$HOME/.apps/bin/python3

declare -A TREE_INDICES
TREE_INDICES=( ["SJBALL031"]=1 )

function compute_clusters {
  for conc in $(seq -10 3); do
    outd=$CLUSTRESULTDIR/clusters.conc.$(echo $conc | tr - _)
    mkdir -p $outd

    for foo in $INDIR/*.ssm; do
      runid=$(basename $foo | cut -d. -f1)
      cmd="$PYTHON $PTDIR/bin/clustervars"
      cmd+=" --model $CLUSTMODEL"
      cmd+=" --parallel $NCHAINS"
      cmd+=" --chains $NCHAINS"
      cmd+=" --iterations 10000"
      cmd+=" --concentration $conc"
      cmd+=" --prior 0.15"
      cmd+=" $INDIR/$runid.{ssm,params.json}"
      cmd+=" $outd/$runid.params.json"
      cmd+=" 2>/dev/null"
      echo $cmd
    done
  #done | grep -v -e SJETV010 -e SJBALL022610 | parallel -j2 --halt 1 --eta
  done | grep -e SJMLL026 -e SJMLL039 -e SJBALL031 | parallel -j8 --halt 1 --eta
}

function compare_cluster_count {
  cd $CLUSTRESULTDIR

  (
    allconc=$(ls -d clusters* | cut -d. -f3 | tr '_' '-' | sort -n)
    echo "runid,$(echo $allconc | tr ' ' , | tr _ .),handbuilt"
    for foo in clusters.conc.0/SJ*.params.json; do
      runid=$(basename $foo | cut -d. -f1)
      echo $runid $(for conc in $allconc; do cat clusters.conc.$(echo $conc | tr '-' '_')/$runid.params.json | jq '.clusters|length'; done; cat $INDIR/$runid.params.json | jq '.clusters|length') | tr ' ' ','
    done
  ) > $CLUSTRESULTDIR/counts.csv
}

function plot_clusters {
  for foo in $CLUSTRESULTDIR/clusters.conc.*/*.params.json; do
    runid=$(basename $foo | cut -d. -f1)
    echo "$PYTHON $PTDIR/bin/plotvars --plot-relations --parallel 1 $INDIR/$runid.ssm $foo $(dirname $foo)/$runid.clusters.html 2>&1"
  done | parallel -j40 --halt 1 --eta | grep -v '^{'
}

function make_cluster_index {
  cd $CLUSTRESULTDIR
  for foo in clusters.conc.*; do
    conc=$(echo $foo | cut -d. -f3)
    (
      echo "<h3>concentration = $(echo $conc | tr '_' '-')</h3><ul>"
      for H in $foo/*.html; do
        echo "<li><a href=$H>$(basename $H | cut -d. -f1)</a></li>"
      done
      echo "</ul>"
    )
  done > index.html
}

function run_pairtree {
  mkdir -p $TREERESULTDIR
  cd $TREERESULTDIR

  for paramsfn in $INDIR/*.collapsed.params.json; do
    runid=$(basename $paramsfn | cut -d. -f1)
    echo "$PYTHON $PTDIR/bin/pairtree --seed 1337 --parallel 40 --params $paramsfn --phi-fitter rprop $INDIR/$runid.ssm ${runid}.results.npz 2>${runid}.stderr"
  done | parallel -j2 --halt 1 --eta
}

function plot_trees {
  cd $TREERESULTDIR

  for resultfn in *.results.npz; do
    runid=$(basename $resultfn | cut -d. -f1)
    for task in plottree summposterior; do
      cmd="$PYTHON $PTDIR/bin/$task"
      if [[ $task == plottree ]]; then
        cmd+=" --reorder-subclones"
      fi
      if [[ $task == plottree && -v "TREE_INDICES[$runid]" ]]; then
        cmd+=" --tree-index ${TREE_INDICES[$runid]}"
      fi
      cmd+=" --runid $runid"
      cmd+=" $INDIR/$runid.ssm"
      cmd+=" $INDIR/${runid}.collapsed.params.json"
      cmd+=" $TREERESULTDIR/${runid}.results.npz"
      cmd+=" $TREERESULTDIR/${runid}.${task}.html"
      echo $cmd
    done
  done | parallel -j40 --halt 1 --eta
}

function make_tree_index {
  cd $TREERESULTDIR
  (
    echo "<h1>Trees</h1>"
    echo "<table>"
    for resultfn in *.results.npz; do
      runid=$(basename $resultfn | cut -d. -f1)
      echo "<tr><td>$runid</td><td><a href=${runid}.plottree.html>tree</a></td><td><a href=${runid}.summposterior.html>summary</a></td></tr>"
    done
    echo "</table>"
  ) > index.html
}

function calc_discord {
  cd $TREERESULTDIR
  for resultfn in *.results.npz; do
    runid=$(basename $resultfn | cut -d. -f1)
    cmd="NUMBA_DISABLE_JIT=1 PYTHONPATH=$PTDIR/lib:$PYTHONPATH $PYTHON $BASEDIR/bin/calc_concordance.py"
    if [[ -v "TREE_INDICES[$runid]" ]]; then
      cmd+=" --tree-index ${TREE_INDICES[$runid]}"
    fi
    cmd+=" $INDIR/$runid.ssm"
    cmd+=" $resultfn "
    cmd+=" $DISCORDTRUTHDIR/${runid}.discord_truth.csv"
    cmd+=" > ${runid}.discord.csv"
    echo $cmd
  done | parallel -j40 --halt 1 --eta
}

function add_discord_to_index {
  cd $TREERESULTDIR
  (
    echo "<h1>Discordance</h1>"
    for disfn in *.discord.csv; do
      runid=$(basename $disfn | cut -d. -f1)
      echo "<h3><a href=$disfn>$runid</a></h3>"
      $PYTHON $BASEDIR/bin/csv2html.py $disfn
    done
  ) >> index.html
}

function main {
  #compute_clusters
  #compare_cluster_count
  #plot_clusters
  #make_cluster_index

  #run_pairtree
  #plot_trees

  calc_discord
  make_tree_index
  add_discord_to_index
}

main
