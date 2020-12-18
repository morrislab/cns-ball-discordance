import argparse
import json

def main():
  parser = argparse.ArgumentParser(
    description='LOL HI THERE',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )
  parser.add_argument('discord_json_fn')
  parser.add_argument('discord_csv_fn')
  args = parser.parse_args()

  with open(args.discord_json_fn) as F:
    discord = json.load(F)['concord']

    # Hardcoding `cols` ensures we can output this as the CSV header, even if
    # no discord pairs are present in the JSON (i.e., the JSON file is empty).
    cols = (
    'samp1',
    'samp2',
    'jsd',
    'm1_llh',
    'm2_llh',
    'log_bf',
    'p_discord',
    'is_discord',
    'truth_discord',
    'agreement',
  )

  with open(args.discord_csv_fn, 'w') as F:
    print(','.join(cols), file=F)
    for row in discord:
      print(','.join([str(row[K]) for K in cols]), file=F)

if __name__ == '__main__':
  main()
