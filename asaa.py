#LB
import pandas as pd

df_lb = pd.read_csv('signs_LB.csv')
signs = df_lb['sign'].unique()
signs = sorted(signs)
for s in signs:
    print(s)