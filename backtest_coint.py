import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant

# ── DATOS ────────────────────────────────────────
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

# ── Z-SCORE ───────────────────────────────────────
X    = add_constant(df['MEP'])
reg  = OLS(df['CCL'], X).fit()
beta = reg.params['MEP']
alfa = reg.params['const']

df['residuo'] = df['CCL'] - (alfa + beta * df['MEP'])
df['zscore']  = (df['residuo'] - df['residuo'].mean()) / df['residuo'].std()

# ── BACKTEST ──────────────────────────────────────
"""
Estrategia pairs trading:
  z > +1.5 → CCL caro → VENDER CCL, COMPRAR MEP (esperar convergencia)
  z < -1.5 → CCL barato → COMPRAR CCL, VENDER MEP (esperar convergencia)
  Cierre: cuando z vuelve a 0

Simplificacion: operamos sobre el SPREAD (CCL - MEP)
  Si spread anormalmente alto → ganamos cuando baja
  Si spread anormalmente bajo → ganamos cuando sube
  
Retorno de cada trade = cambio en el spread desde entrada hasta cierre
"""

UMBRAL_ENTRADA = 1.5
UMBRAL_SALIDA  = 0.0
CAPITAL        = 10_000  # USD ficticios

trades   = []
posicion = 0   # 1=long spread, -1=short spread, 0=sin posicion
entrada  = None
fecha_entrada = None

for i in range(1, len(df)):
    z     = df['zscore'].iloc[i]
    spread= df['residuo'].iloc[i]
    fecha = df.index[i]

    # Abrir posicion
    if posicion == 0:
        if z > UMBRAL_ENTRADA:
            # CCL caro → short spread (esperamos que baje)
            posicion = -1
            entrada  = spread
            fecha_entrada = fecha
        elif z < -UMBRAL_ENTRADA:
            # CCL barato → long spread (esperamos que suba)
            posicion = 1
            entrada  = spread
            fecha_entrada = fecha

    # Cerrar posicion cuando z vuelve a 0
    elif posicion != 0:
        if (posicion == -1 and z <= UMBRAL_SALIDA) or \
           (posicion ==  1 and z >= UMBRAL_SALIDA):
            pnl_spread = posicion * (spread - entrada)
            # Convertir a retorno porcentual sobre precio MEP
            pnl_pct = pnl_spread / df['MEP'].iloc[i] * 100
            dias    = (fecha - fecha_entrada).days
            trades.append({
                'fecha_entrada': fecha_entrada,
                'fecha_salida':  fecha,
                'tipo':          'Short spread' if posicion == -1 else 'Long spread',
                'dias':          dias,
                'pnl_spread':    round(pnl_spread, 2),
                'pnl_pct':       round(pnl_pct, 2),
            })
            posicion = 0
            entrada  = None

trades_df = pd.DataFrame(trades)

# ── RESULTADOS ────────────────────────────────────
print("\n=== BACKTEST PAIRS TRADING MEP-CCL ===")
print(f"  Periodo    : 2019-01-01 → 2026-06-27")
print(f"  Umbral     : +/- {UMBRAL_ENTRADA} sigma")
print(f"  Total trades: {len(trades_df)}")

if len(trades_df) > 0:
    ganadores = trades_df[trades_df['pnl_pct'] > 0]
    perdedores= trades_df[trades_df['pnl_pct'] < 0]
    win_rate  = len(ganadores) / len(trades_df) * 100
    pnl_total = trades_df['pnl_pct'].sum()

    print(f"  Ganadores  : {len(ganadores)} ({win_rate:.0f}%)")
    print(f"  Perdedores : {len(perdedores)}")
    print(f"  PnL total  : {pnl_total:+.2f}%")
    print(f"  PnL promedio por trade: {trades_df['pnl_pct'].mean():+.2f}%")
    print(f"  Dias promedio por trade: {trades_df['dias'].mean():.0f}")
    print(f"  Mejor trade: {trades_df['pnl_pct'].max():+.2f}%")
    print(f"  Peor trade : {trades_df['pnl_pct'].min():+.2f}%")

    print(f"\n  Detalle de trades:")
    print(f"  {'Entrada':<12} {'Salida':<12} {'Tipo':<14} {'Dias':>4} {'PnL%':>8}")
    print(f"  {'-'*55}")
    for _, t in trades_df.iterrows():
        print(f"  {str(t['fecha_entrada'])[:10]:<12} "
              f"{str(t['fecha_salida'])[:10]:<12} "
              f"{t['tipo']:<14} "
              f"{t['dias']:>4}d "
              f"{t['pnl_pct']:>+7.2f}%")

# ── GRAFICO ───────────────────────────────────────
trades_df['pnl_acum'] = trades_df['pnl_pct'].cumsum()

fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# PnL acumulado
axes[0].plot(trades_df['fecha_salida'], trades_df['pnl_acum'],
             marker='o', linewidth=2, color='steelblue')
axes[0].axhline(0, color='red', linestyle='--', alpha=0.5)
axes[0].fill_between(trades_df['fecha_salida'], trades_df['pnl_acum'],
                     where=trades_df['pnl_acum'] > 0, color='green', alpha=0.2)
axes[0].fill_between(trades_df['fecha_salida'], trades_df['pnl_acum'],
                     where=trades_df['pnl_acum'] < 0, color='red', alpha=0.2)
axes[0].set_title('PnL acumulado — Pairs Trading MEP/CCL')
axes[0].set_ylabel('Retorno acumulado (%)')
axes[0].grid(alpha=0.3)

# PnL por trade
colores = ['green' if x > 0 else 'red' for x in trades_df['pnl_pct']]
axes[1].bar(range(len(trades_df)), trades_df['pnl_pct'], color=colores, alpha=0.7)
axes[1].axhline(0, color='black', linestyle='-', alpha=0.3)
axes[1].set_title('PnL por trade (%)')
axes[1].set_xlabel('Numero de trade')
axes[1].set_ylabel('Retorno (%)')
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.show()