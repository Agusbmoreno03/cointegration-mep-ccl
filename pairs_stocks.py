"""
PAIRS TRADING — Acciones
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant

# ══════════════════════════════════════════════
# 1. DATOS
# ══════════════════════════════════════════════

PAR    = ('AAPL', 'MSFT')
INICIO = '2010-01-01'
NOMBRE = {'AAPL': 'Apple', 'MSFT': 'Microsoft'}

print(f"Descargando {NOMBRE[PAR[0]]} vs {NOMBRE[PAR[1]]}...")

raw = yf.download(list(PAR), start=INICIO, auto_adjust=True, progress=False)
precios = raw['Close'].dropna()
precios.columns = [NOMBRE[t] for t in PAR]

A, B = precios.columns[0], precios.columns[1]

crec_A = (precios[A].iloc[-1] / precios[A].iloc[0] - 1) * 100
crec_B = (precios[B].iloc[-1] / precios[B].iloc[0] - 1) * 100

print(f"\n  {A}: ${precios[A].iloc[0]:.2f} → ${precios[A].iloc[-1]:.2f} | Crecimiento: {crec_A:.1f}%")
print(f"  {B}: ${precios[B].iloc[0]:.2f} → ${precios[B].iloc[-1]:.2f} | Crecimiento: {crec_B:.1f}%")
print(f"  Observaciones: {len(precios)}")

# ══════════════════════════════════════════════
# 2. VISUALIZACION
# ══════════════════════════════════════════════

fig, axes = plt.subplots(3, 1, figsize=(14, 12))

# Precios normalizados (base 100)
norm = precios / precios.iloc[0] * 100
axes[0].plot(norm[A], label=A, linewidth=1.5)
axes[0].plot(norm[B], label=B, linewidth=1.5)
axes[0].axhline(100, color='gray', linestyle='--', alpha=0.5)
axes[0].set_title(f'{A} vs {B} — Precio normalizado (base 100)')
axes[0].legend()
axes[0].grid(alpha=0.3)

# Ratio de precios
precios['ratio'] = precios[A] / precios[B]
axes[1].plot(precios['ratio'], color='purple', linewidth=1)
axes[1].axhline(precios['ratio'].mean(), color='red', linestyle='--',
                label=f'Promedio: {precios["ratio"].mean():.3f}')
axes[1].set_title(f'Ratio {A}/{B}')
axes[1].legend()
axes[1].grid(alpha=0.3)

# Correlacion rolling 252 dias
corr_rolling = precios[A].rolling(252).corr(precios[B])
axes[2].plot(corr_rolling, color='steelblue', linewidth=1)
axes[2].axhline(corr_rolling.mean(), color='red', linestyle='--',
                label=f'Correlacion promedio: {corr_rolling.mean():.3f}')
axes[2].set_title('Correlacion rolling 252 dias')
axes[2].set_ylim(0, 1)
axes[2].legend()
axes[2].grid(alpha=0.3)

plt.tight_layout()
plt.show()

# ══════════════════════════════════════════════
# 3. TESTS ESTADISTICOS
# ══════════════════════════════════════════════

print(f"\n=== TEST ADF ===")
for nombre, serie in [(A, precios[A]), (B, precios[B])]:
    res = adfuller(serie.dropna())
    p   = res[1]
    print(f"  {nombre}: ADF={res[0]:.4f} | p={p:.4f} → {'NO estacionaria' if p > 0.05 else 'Estacionaria'}")

print(f"\n=== TEST COINTEGRACION (Engle-Granger) ===")
score, p_coint, _ = coint(precios[A], precios[B])
conclusion = "HAY cointegracion" if p_coint < 0.05 else "NO hay cointegracion"
print(f"  Score: {score:.4f} | p-value: {p_coint:.4f} → {conclusion}")

# ══════════════════════════════════════════════
# 4. Z-SCORE Y SEÑALES
# ══════════════════════════════════════════════

X   = add_constant(precios[B])
reg = OLS(precios[A], X).fit()
beta = reg.params[B]
alfa = reg.params['const']

print(f"\n=== RELACION DE EQUILIBRIO ===")
print(f"  {A} = {alfa:.2f} + {beta:.4f} x {B}")
print(f"  R² = {reg.rsquared:.4f}")

precios['residuo'] = precios[A] - (alfa + beta * precios[B])
precios['zscore']  = (precios['residuo'] - precios['residuo'].mean()) / precios['residuo'].std()

UMBRAL = 1.5
print(f"\n=== Z-SCORE ACTUAL ===")
print(f"  Z-score hoy: {precios['zscore'].iloc[-1]:.2f}")
if precios['zscore'].iloc[-1] > UMBRAL:
    print(f"  SEÑAL: {A} cara vs {B} → considerar short {A} / long {B}")
elif precios['zscore'].iloc[-1] < -UMBRAL:
    print(f"  SEÑAL: {A} barata vs {B} → considerar long {A} / short {B}")
else:
    print(f"  SEÑAL: dentro del rango normal")

# Grafico zscore
plt.figure(figsize=(14, 5))
plt.plot(precios['zscore'], linewidth=1, color='steelblue')
plt.axhline( UMBRAL, color='red',   linestyle='--', label=f'+{UMBRAL} sigma')
plt.axhline(-UMBRAL, color='green', linestyle='--', label=f'-{UMBRAL} sigma')
plt.axhline(0, color='black', linestyle='-', alpha=0.3)
plt.fill_between(precios.index, precios['zscore'],
                 where=precios['zscore'] >  UMBRAL, color='red',   alpha=0.3)
plt.fill_between(precios.index, precios['zscore'],
                 where=precios['zscore'] < -UMBRAL, color='green', alpha=0.3)
plt.title(f'Z-Score {A} vs {B} — Oportunidades de pairs trading')
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# ══════════════════════════════════════════════
# 5. BACKTEST
# ══════════════════════════════════════════════

trades   = []
posicion = 0
entrada  = None
fecha_entrada = None
COSTO_TX = 0.3  # 0.3% por lado (mercado USA mas liquido)

for i in range(1, len(precios)):
    z      = precios['zscore'].iloc[i]
    spread = precios['residuo'].iloc[i]
    fecha  = precios.index[i]

    if posicion == 0:
        if z > UMBRAL:
            posicion, entrada, fecha_entrada = -1, spread, fecha
        elif z < -UMBRAL:
            posicion, entrada, fecha_entrada =  1, spread, fecha
    elif posicion != 0:
        if (posicion == -1 and z <= 0) or (posicion == 1 and z >= 0):
            pnl_pct = posicion * (spread - entrada) / precios[B].iloc[i] * 100
            pnl_pct -= COSTO_TX
            trades.append({
                'fecha_entrada': fecha_entrada,
                'fecha_salida':  fecha,
                'tipo':          'Short spread' if posicion == -1 else 'Long spread',
                'dias':          (fecha - fecha_entrada).days,
                'pnl_pct':       round(pnl_pct, 2),
            })
            posicion = 0

trades_df = pd.DataFrame(trades)

print(f"\n=== BACKTEST {A} vs {B} ===")
if len(trades_df) > 0:
    gan    = len(trades_df[trades_df['pnl_pct'] > 0])
    wr     = gan / len(trades_df) * 100
    print(f"  Trades       : {len(trades_df)}")
    print(f"  Win rate     : {wr:.0f}%")
    print(f"  PnL total    : {trades_df['pnl_pct'].sum():+.2f}%")
    print(f"  PnL promedio : {trades_df['pnl_pct'].mean():+.2f}%")
    print(f"  Mejor trade  : {trades_df['pnl_pct'].max():+.2f}%")
    print(f"  Peor trade   : {trades_df['pnl_pct'].min():+.2f}%")
    print(f"  Dias promedio: {trades_df['dias'].mean():.0f}")

    trades_df['pnl_acum'] = trades_df['pnl_pct'].cumsum()
    plt.figure(figsize=(14, 5))
    plt.plot(trades_df['fecha_salida'], trades_df['pnl_acum'],
             marker='o', linewidth=2, color='steelblue')
    plt.axhline(0, color='red', linestyle='--', alpha=0.5)
    plt.fill_between(trades_df['fecha_salida'], trades_df['pnl_acum'],
                     where=trades_df['pnl_acum'] > 0, color='green', alpha=0.2)
    plt.fill_between(trades_df['fecha_salida'], trades_df['pnl_acum'],
                     where=trades_df['pnl_acum'] < 0, color='red',   alpha=0.2)
    plt.title(f'PnL acumulado — Pairs Trading {A} vs {B}')
    plt.ylabel('Retorno acumulado (%)')
    plt.grid(alpha=0.3)
    plt.show()