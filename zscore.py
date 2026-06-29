import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant

def descargar(casa):
    url = f"https://api.argentinadatos.com/v1/cotizaciones/dolares/{casa}"
    r   = requests.get(url, timeout=15)
    df  = pd.DataFrame(r.json())
    df['fecha'] = pd.to_datetime(df['fecha'])
    df = df.set_index('fecha').sort_index()
    df['precio'] = (df['compra'] + df['venta']) / 2
    return df[['precio']]

mep = descargar('bolsa').rename(columns={'precio': 'MEP'})
ccl = descargar('contadoconliqui').rename(columns={'precio': 'CCL'})
df  = mep.join(ccl, how='inner').dropna()
df  = df[df.index >= '2019-01-01']

X   = add_constant(df['MEP'])
reg = OLS(df['CCL'], X).fit()
beta = reg.params['MEP']
alfa = reg.params['const']

df['residuo'] = df['CCL'] - (alfa + beta * df['MEP'])
df['zscore']  = (df['residuo'] - df['residuo'].mean()) / df['residuo'].std()

UMBRAL = 1.5

plt.figure(figsize=(14, 6))
plt.plot(df['zscore'], linewidth=1, color='steelblue')
plt.axhline( UMBRAL, color='red',   linestyle='--', label=f'+{UMBRAL} sigma (CCL caro)')
plt.axhline(-UMBRAL, color='green', linestyle='--', label=f'-{UMBRAL} sigma (CCL barato)')
plt.axhline(0, color='black', linestyle='-', alpha=0.3)
plt.fill_between(df.index, df['zscore'],
                 where=df['zscore'] >  UMBRAL, color='red',   alpha=0.3)
plt.fill_between(df.index, df['zscore'],
                 where=df['zscore'] < -UMBRAL, color='green', alpha=0.3)
plt.title('Z-Score MEP-CCL — Oportunidades de arbitraje historicas')
plt.legend()
plt.grid(alpha=0.3)

# Marcar momentos clave
eventos = {
    '2019-09-01': 'Cepo cambiario',
    '2023-08-01': 'Devaluacion Massa',
    '2023-12-01': 'Milei asume',
}
for fecha, label in eventos.items():
    if fecha in df.index.strftime('%Y-%m-%d').tolist():
        plt.axvline(pd.to_datetime(fecha), color='orange',
                    linestyle=':', alpha=0.7, label=label)

plt.tight_layout()
plt.show()

# Cuantos dias estuvo fuera del rango
dias_caro   = (df['zscore'] >  UMBRAL).sum()
dias_barato = (df['zscore'] < -UMBRAL).sum()
print(f"Dias con CCL caro (z>{UMBRAL}):    {dias_caro} ({dias_caro/len(df)*100:.1f}%)")
print(f"Dias con CCL barato (z<-{UMBRAL}): {dias_barato} ({dias_barato/len(df)*100:.1f}%)")