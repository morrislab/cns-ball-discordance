import sys
import pandas as pd

def main():
  fn = sys.argv[1]
  df = pd.read_csv(fn)

  if 'agreement' in df and len(df['agreement']) > 0:
    print('<h4>Agreement: %.0f%%</h4>' % (100 * sum(df['agreement']) / len(df['agreement'])))
  html = df.to_html(index=False, classes=('table', 'table-striped', 'table-hover'))
  html = html.replace('<table ', '<table data-toggle="table" ')
  html = html.replace('<td>True</td>', "<td class='text-success bg-success'>True</td>")
  html = html.replace('<td>False</td>', "<td class='text-danger bg-danger'>False</td>")
  html = html.replace('<th>', '<th data-sortable="true">')
  print(html)

main()
