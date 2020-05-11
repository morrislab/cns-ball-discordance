import sys
import pandas as pd

def main():
  fn = sys.argv[1]
  df = pd.read_csv(fn)
  print(df.to_html(index=False))

main()
