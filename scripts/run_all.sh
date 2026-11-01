#!/bin/bash
# One entry point for the whole pipeline.
#   scripts/run_all.sh analyze   (default, ~10 s) re-derive tables, statistics and figures from data/raw/*.csv. No experiments.
#   scripts/run_all.sh demo      (~30 s) tiny live h2-vs-h3 run (50 ms, 0 % and 2 % loss, 3 iterations) into /tmp.
#   scripts/run_all.sh sweep     (HOURS) full 1 MB sweep in 5 parallel shards -> data/raw/sweep_new/, merged to a NEW file.
# Never overwrites data/raw/results.csv.
set -e
cd "$(dirname "$0")/.."
mode=${1:-analyze}
case "$mode" in
analyze)
  python3 scripts/analyze_crossover.py --csv data/raw/results.csv
  python3 scripts/stats_significance.py --csv data/raw/results.csv
  [ -f data/raw/results_10MB.csv ] && python3 scripts/analyze_crossover.py --csv data/raw/results_10MB.csv --cap 90 --tag _10MB \
    && python3 scripts/stats_significance.py --csv data/raw/results_10MB.csv --cap 90 --tag _10MB
  echo "outputs: data/processed/  data/results/" ;;
demo)
  scripts/testbed.sh python3 scripts/run_tests.py --out /tmp/qt_demo.csv --iterations 3 --rtts 50 --losses 0,2 --profiles static
  column -s, -t /tmp/qt_demo.csv | cut -c1-150 ;;
sweep)
  mkdir -p data/raw/sweep_new; R=sweep-$(date +%Y%m%dT%H%M%S)
  for k in 0 1 2 3 4; do
    scripts/testbed.sh python3 scripts/run_tests.py --run-id "$R" --shard $k/5 --out data/raw/sweep_new/shard_$k.csv \
      --rtts 20,50,100,150,200,300 --losses 0,0.5,1,2,3,5 > logs/sweep_new_$k.log 2>&1 &
  done
  wait
  python3 scripts/merge_results.py "data/raw/results_$R.csv" data/raw/sweep_new/shard_*.csv
  echo "merged. Analyse with: python3 scripts/analyze_crossover.py --csv data/raw/results_$R.csv --tag _$R" ;;
*) echo "usage: $0 [analyze|demo|sweep]" >&2; exit 2 ;;
esac
