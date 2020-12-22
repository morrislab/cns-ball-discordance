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
NCHAINS=40
PYTHON=$HOME/.apps/bin/python3

declare -A TREE_INDICES=( ["SJBALL031"]=0 )

function munge_samples {
  # The inputs were originally taken from
  # https://github.com/morrislab/pairtree-experiments. They are no longer in
  # the most recent revision, but they live in the repo history. (See
  # https://github.com/morrislab/pairtree-experiments/commit/e3f1f5401cb72e327a71556b8af0c68f31d5cb62).
  cd $DATADIR/inputs.new

  for paramsfn in *.params.json; do
    runid=$(basename $paramsfn | cut -d. -f1)
    cmd="$PYTHON $BASEDIR/bin/rename_and_hide_samps.py"
    cmd+=" $paramsfn"
    cmd+=" $paramsfn.new"
    cmd+="&& $PYTHON $PTDIR/util/reorder_samples.py"
    cmd+=" $runid.ssm"
    cmd+=" $paramsfn.new"
    cmd+=" \$($PYTHON $BASEDIR/bin/reorder_samps.py $paramsfn.new)"
    cmd+="&& mv $paramsfn.new $paramsfn"
    echo $cmd
  done | parallel -j40 --halt 2 --eta
}

function compute_clusters {
  #for conc in $(seq -10 3); do
  for conc in -2; do
    outd=$CLUSTRESULTDIR/clusters.conc.$(echo $conc | tr - _)
    mkdir -p $outd

    for foo in $INDIR/*.ssm; do
      runid=$(basename $foo | cut -d. -f1)
      # If clusters already exist, don't run clustering.
      jq -e 'has("clusters")' $INDIR/$runid.params.json >/dev/null && continue

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
  done | parallel -j8 --halt 2 --eta
}

function compare_cluster_count {
  cd $CLUSTRESULTDIR

  (
    allconc=$(ls -d clusters* | cut -d. -f3 | tr '_' '-' | sort -n)
    firstconc=$(echo $allconc | cut -d' ' -f1)
    echo "runid,$(echo $allconc | tr ' ' , | tr _ .),handbuilt"
    for foo in clusters.conc.$(echo $firstconc | tr - _)/SJ*.params.json; do
      runid=$(basename $foo | cut -d. -f1)
      echo $runid $(for conc in $allconc; do cat clusters.conc.$(echo $conc | tr '-' '_')/$runid.params.json | jq '.clusters|length'; done; cat ~/work/pairtree-experiments/inputs/steph.xeno.pairtree/$runid.params.json | jq '.clusters|length') | tr ' ' ','
    done
  ) > $CLUSTRESULTDIR/counts.csv
}

function plot_clusters {
  for foo in $CLUSTRESULTDIR/clusters.conc.*/*.params.json; do
    runid=$(basename $foo | cut -d. -f1)
    echo "$PYTHON $PTDIR/bin/plotvars --plot-relations --parallel 1 $INDIR/$runid.ssm $foo $(dirname $foo)/$runid.clusters.html 2>&1"
  done | parallel -j40 --halt 1 --eta | grep -v '^{' || true
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

  for paramsfn in $INDIR/*.params.json; do
    runid=$(basename $paramsfn | cut -d. -f1)
    echo "$PYTHON $PTDIR/bin/pairtree --seed 1337 --tree-chains $NCHAINS --parallel 40 --params $paramsfn --phi-fitter rprop $INDIR/$runid.ssm ${runid}.results.npz 2>${runid}.stderr"
  done | parallel -j3 --halt 1 --eta
}

function plot_trees {
  cd $TREERESULTDIR

  for resultfn in *.results.npz; do
    runid=$(basename $resultfn | cut -d. -f1)
    args="--runid $runid"
    args+=" $INDIR/$runid.ssm"
    args+=" $INDIR/${runid}.params.json"
    args+=" $TREERESULTDIR/${runid}.results.npz"

    cmd="$PYTHON $PTDIR/bin/plottree"
    cmd+=" --reorder-subclones"
    cmd+=" --remove-normal"
    # The below works on my laptop's Bash, but magically stopped working on
    # SciNet after they apparently upgraded to Bash 4.2.46(2)-release.
    #if [[ -v "TREE_INDICES[$runid]" ]]; then
    # Do this stupid hackey alternative instead.
    if [[ ${TREE_INDICES[$runid]+abc} ]]; then
      cmd+=" --tree-index ${TREE_INDICES[$runid]}"
    fi
    cmd+=" $args"
    cmd+=" $TREERESULTDIR/${runid}.plottree.html"
    echo $cmd

    cmd="$PYTHON $PTDIR/bin/summposterior"
    cmd+=" $args"
    cmd+=" $TREERESULTDIR/${runid}.summposterior.html"
    echo $cmd
  done | parallel -j40 --halt 2 --eta
}

function make_tree_index {
  cd $TREERESULTDIR
  (
    echo "<h1>Trees</h1>"
    echo "<table>"
    for resultfn in *.results.npz; do
      runid=$(basename $resultfn | cut -d. -f1)
      echo "<tr><td>$runid</td><td><a href=${runid}.plottree.html>orig tree</a></td><td><a href=${runid}.stephtree.html>tree with concord</a></td><td><a href=${runid}.summposterior.html>summary</a></td><td><a href=${runid}.di.html>diversity indices</a></td></tr>"
    done
    echo "</table>"
  ) > index.html
}

function calc_concord {
  for resultfn in $TREERESULTDIR/*.results.npz; do
    runid=$(basename $resultfn | cut -d. -f1)
    truthfn="$DISCORDTRUTHDIR/${runid}.discord_truth.csv"

    cmd="cd $TREERESULTDIR && NUMBA_DISABLE_JIT=1 PYTHONPATH=$PTDIR/lib:$PYTHONPATH"
    cmd+=" $PYTHON $BASEDIR/bin/calc_concordance.py"
    if [[ ${TREE_INDICES[$runid]+abc} ]]; then
      cmd+=" --tree-index ${TREE_INDICES[$runid]}"
    fi
    if [[ -f $truthfn ]]; then
      cmd+=" --truth $truthfn"
    fi
    cmd+=" $INDIR/$runid.ssm"
    cmd+=" $resultfn "
    cmd+=" > $TREERESULTDIR/${runid}.discord.json"
    cmd+="&& $PYTHON $BASEDIR/bin/convert_discord_to_csv.py"
    cmd+="  $TREERESULTDIR/${runid}.discord.{json,csv}"
    echo $cmd
  done | parallel -j40 --halt 2 --eta
}

function plot_di {
  for resultfn in $TREERESULTDIR/*.results.npz; do
    runid=$(basename $resultfn | cut -d. -f1)
    cmd="cd $TREERESULTDIR && NUMBA_DISABLE_JIT=1 PYTHONPATH=$PTDIR/lib:$PYTHONPATH $PYTHON $BASEDIR/bin/plot_di.py"
    if [[ ${TREE_INDICES[$runid]+abc} ]]; then
      cmd+=" --tree-index ${TREE_INDICES[$runid]}"
    fi
    cmd+=" $resultfn "
    cmd+=" $TREERESULTDIR/${runid}.di.html"
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

function plot_steph_trees {
  cd $TREERESULTDIR

  for resultfn in *.results.npz; do
    runid=$(basename $resultfn | cut -d. -f1)

    cmd="$PYTHON $BASEDIR/bin/plot_steph_tree.py"
    cmd+=" --reorder-subclones"
    cmd+=" --remove-normal"
    if [[ ${TREE_INDICES[$runid]+abc} ]]; then
      cmd+=" --tree-index ${TREE_INDICES[$runid]}"
    fi
    cmd+=" --runid $runid"
    cmd+=" $INDIR/$runid.ssm"
    cmd+=" $INDIR/${runid}.params.json"
    cmd+=" $TREERESULTDIR/${runid}.results.npz"
    cmd+=" $TREERESULTDIR/${runid}.discord.json"
    cmd+=" $TREERESULTDIR/${runid}.stephtree.html"
    echo $cmd
  done | parallel -j40 --halt 2 --eta
}

function main {
  #munge_samples

  #compute_clusters
  #compare_cluster_count
  #plot_clusters
  #make_cluster_index

  #run_pairtree
  plot_trees

  calc_concord
  plot_di
  plot_steph_trees
  make_tree_index
  add_discord_to_index
}

main
