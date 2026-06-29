"""
ANÁLISIS DE COINTEGRACIÓN — Dólar MEP vs CCL
Objetivo: detectar relación de largo plazo y oportunidades de arbitraje
"""

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant

# ══════════════════════════════════════════════
# 1. DESCARGAR DATOS
# ══════════════════════════════════════════════

def descargar(casa):
    url = f"https://api.argentinadatos.com/v1/cotizaciones/dolares/{casa}"
    r   = requests.get(url, timeout=15)
    df  = pd.DataFrame(r.json())
    df['fecha'] = pd.to_datetime(df['fecha'])
    df = df.set_index('fecha').sort_index()
    df['precio'] = (df['compra'] + df['venta']) / 2
    return df[['precio']]

print("Descargando datos...")
mep = descargar('bolsa').rename(columns={'precio': 'MEP'})
ccl = descargar('contadoconliqui').rename(columns={'precio': 'CCL'})

# Unir y filtrar desde 2019 (más datos post cepo)
df = mep.join(ccl, how='inner').dropna()
df = df[df.index >= '2019-01-01']

print(f"Datos: {len(df)} observaciones | {df.index[0].date()} -> {df.index[-1].date()}")
print(f"MEP actual:  ${df['MEP'].iloc[-1]:,.1f}")
print(f"CCL actual:  ${df['CCL'].iloc[-1]:,.1f}")
print(f"Brecha:      {((df['CCL'].iloc[-1]/df['MEP'].iloc[-1])-1)*100:.2f}%")

# ══════════════════════════════════════════════
# 2. VISUALIZACIÓN INICIAL
# ══════════════════════════════════════════════

fig, axes = plt.subplots(3, 1, figsize=(14, 12))

# Serie de precios
axes[0].plot(df['MEP'], label='MEP', linewidth=1.2)
axes[0].plot(df['CCL'], label='CCL', linewidth=1.2)
axes[0].set_title('Dólar MEP vs CCL — Serie histórica')
axes[0].legend()
axes[0].grid(alpha=0.3)

# Brecha porcentual
df['brecha'] = (df['CCL'] / df['MEP'] - 1) * 100
axes[1].fill_between(df.index, df['brecha'], alpha=0.4, color='orange')
axes[1].axhline(df['brecha'].mean(), color='red', linestyle='--',
                label=f'Promedio: {df["brecha"].mean():.1f}%')
axes[1].set_title('Brecha CCL/MEP (%)')
axes[1].legend()
axes[1].grid(alpha=0.3)

# Spread absoluto
df['spread'] = df['CCL'] - df['MEP']
axes[2].fill_between(df.index, df['spread'], alpha=0.4, color='purple')
axes[2].axhline(df['spread'].mean(), color='red', linestyle='--',
                label=f'Promedio: ${df["spread"].mean():.1f}')
axes[2].set_title('Spread absoluto CCL - MEP ($)')
axes[2].legend()
axes[2].grid(alpha=0.3)

plt.tight_layout()
plt.show()

# ══════════════════════════════════════════════
# 3. TEST DE ESTACIONARIEDAD (ADF)
# ══════════════════════════════════════════════

print("\n=== TEST ADF (Augmented Dickey-Fuller) ===")
print("H0: la serie tiene raiz unitaria (no estacionaria)")
print("Si p-value > 0.05 → no estacionaria → candidata a cointegracion\n")

for nombre, serie in [('MEP', df['MEP']), ('CCL', df['CCL'])]:
    resultado = adfuller(serie.dropna())
    p = resultado[1]
    conclusion = "NO estacionaria" if p > 0.05 else "Estacionaria"
    print(f"  {nombre}: ADF={resultado[0]:.4f} | p-value={p:.4f} → {conclusion}")

# ══════════════════════════════════════════════
# 4. TEST DE COINTEGRACIÓN (Engle-Granger)
# ══════════════════════════════════════════════

print("\n=== TEST DE COINTEGRACION (Engle-Granger) ===")
print("H0: no hay cointegracion")
print("Si p-value < 0.05 → hay cointegracion → relacion de largo plazo\n")

score, p_value, _ = coint(df['MEP'], df['CCL'])
conclusion = "HAY cointegracion" if p_value < 0.05 else "NO hay cointegracion"
print(f"  Score: {score:.4f} | p-value: {p_value:.4f} → {conclusion}")

# ══════════════════════════════════════════════
# 5. SPREAD NORMALIZADO (Z-SCORE)
# ══════════════════════════════════════════════

# Regresion para encontrar la relacion de equilibrio
X   = add_constant(df['MEP'])
reg = OLS(df['CCL'], X).fit()
beta = reg.params['MEP']
alfa = reg.params['const']

print(f"\n=== RELACION DE EQUILIBRIO ===")
print(f"  CCL = {alfa:.2f} + {beta:.4f} * MEP")
print(f"  R²  = {reg.rsquared:.4f}")

# Residuo = desviacion del equilibrio
df['residuo']  = df['CCL'] - (alfa + beta * df['MEP'])
df['zscore']   = (df['residuo'] - df['residuo'].mean()) / df['residuo'].std()

# Señales de trading
UMBRAL = 1.5
df['senal'] = 0
df.loc[df['zscore'] >  UMBRAL, 'senal'] = -1  # CCL muy caro vs MEP → vender CCL
df.loc[df['zscore'] < -UMBRAL, 'senal'] =  1  # CCL muy barato vs MEP → comprar CCL

print(f"\n=== Z-SCORE ACTUAL ===")
print(f"  Z-score hoy: {df['zscore'].iloc[-1]:.2f}")
print(f"  Umbral:      +/- {UMBRAL}")
if df['zscore'].iloc[-1] > UMBRAL:
    print(f"  SEÑAL: CCL sobrevaluado vs MEP → brecha anormalmente alta")
elif df['zscore'].iloc[-1] < -UMBRAL:
    print(f"  SEÑAL: CCL subvaluado vs MEP → brecha anormalmente baja")
else:
    print(f"  SEÑAL: dentro del rango normal")

# Grafico zscore
plt.figure(figsize=(14, 5))
plt.plot(df['zscore'], linewidth=1)
plt.axhline( UMBRAL, color='red',   linestyle='--', label=f'+{UMBRAL} sigma')
plt.axhline(-UMBRAL, color='green', linestyle='--', label=f'-{UMBRAL} sigma')
plt.axhline(0, color='black', linestyle='-', alpha=0.3)
plt.fill_between(df.index, df['zscore'],
                 where=df['zscore'] >  UMBRAL, color='red',   alpha=0.3, label='CCL caro')
plt.fill_between(df.index, df['zscore'],
                 where=df['zscore'] < -UMBRAL, color='green', alpha=0.3, label='CCL barato')
plt.title('Z-Score del spread MEP-CCL — Oportunidades de arbitraje')
plt.legend()
plt.grid(alpha=0.3)
plt.show()

print("\nAnalisis completado.")