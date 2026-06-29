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

# ── BACKTEST CON PARKING ──────────────────────────
"""
Diferencia vs backtest anterior:
- Al detectar señal, NO entramos ese dia
- Entramos 3 dias habiles despues (simulando el parking)
- El spread puede haberse movido en nuestra contra durante esos 3 dias
- Tambien agregamos costo de transaccion del 0.5% por operacion
"""

UMBRAL_ENTRADA = 1.5
UMBRAL_SALIDA  = 0.0
PARKING_DIAS   = 3    # dias habiles de espera
COSTO_TX       = 0.5  # 0.5% por lado (ida y vuelta = 1%)

trades_sin_parking = []
trades_con_parking = []

# ── SIN PARKING (original) ────────────────────────
posicion = 0
entrada  = None
fecha_entrada = None

for i in range(1, len(df)):
    z     = df['zscore'].iloc[i]
    spread= df['residuo'].iloc[i]
    fecha = df.index[i]

    if posicion == 0:
        if z > UMBRAL_ENTRADA:
            posicion, entrada, fecha_entrada = -1, spread, fecha
        elif z < -UMBRAL_ENTRADA:
            posicion, entrada, fecha_entrada =  1, spread, fecha
    elif posicion != 0:
        if (posicion == -1 and z <= UMBRAL_SALIDA) or \
           (posicion ==  1 and z >= UMBRAL_SALIDA):
            pnl_pct = posicion * (spread - entrada) / df['MEP'].iloc[i] * 100
            pnl_pct -= COSTO_TX  # costo transaccion
            trades_sin_parking.append({
                'fecha_entrada': fecha_entrada,
                'fecha_salida':  fecha,
                'dias':          (fecha - fecha_entrada).days,
                'pnl_pct':       round(pnl_pct, 2),
            })
            posicion = 0

# ── CON PARKING ───────────────────────────────────
posicion      = 0
entrada       = None
fecha_entrada = None
señal_fecha   = None
señal_tipo    = 0

for i in range(1, len(df)):
    z     = df['zscore'].iloc[i]
    spread= df['residuo'].iloc[i]
    fecha = df.index[i]

    # Si hay señal pendiente, verificar si ya pasaron 3 dias habiles
    if señal_tipo != 0 and posicion == 0:
        dias_habiles = len(pd.bdate_range(señal_fecha, fecha)) - 1
        if dias_habiles >= PARKING_DIAS:
            # Entrar al precio de HOY (no al de la señal)
            posicion      = señal_tipo
            entrada       = spread
            fecha_entrada = fecha
            señal_tipo    = 0

    # Detectar nueva señal (solo si no hay posicion ni señal pendiente)
    if posicion == 0 and señal_tipo == 0:
        if z > UMBRAL_ENTRADA:
            señal_tipo  = -1
            señal_fecha = fecha
        elif z < -UMBRAL_ENTRADA:
            señal_tipo  =  1
            señal_fecha = fecha

    # Cerrar posicion
    elif posicion != 0:
        if (posicion == -1 and z <= UMBRAL_SALIDA) or \
           (posicion ==  1 and z >= UMBRAL_SALIDA):
            pnl_pct = posicion * (spread - entrada) / df['MEP'].iloc[i] * 100
            pnl_pct -= COSTO_TX
            trades_con_parking.append({
                'fecha_entrada': fecha_entrada,
                'fecha_salida':  fecha,
                'dias':          (fecha - fecha_entrada).days,
                'pnl_pct':       round(pnl_pct, 2),
            })
            posicion   = 0
            señal_tipo = 0

# ── COMPARACION ───────────────────────────────────
def resumen(trades, nombre):
    df_t = pd.DataFrame(trades)
    if len(df_t) == 0:
        print(f"\n{nombre}: sin trades")
        return df_t
    gan  = len(df_t[df_t['pnl_pct'] > 0])
    wr   = gan / len(df_t) * 100
    print(f"\n=== {nombre} ===")
    print(f"  Trades       : {len(df_t)}")
    print(f"  Win rate     : {wr:.0f}%")
    print(f"  PnL total    : {df_t['pnl_pct'].sum():+.2f}%")
    print(f"  PnL promedio : {df_t['pnl_pct'].mean():+.2f}%")
    print(f"  Mejor trade  : {df_t['pnl_pct'].max():+.2f}%")
    print(f"  Peor trade   : {df_t['pnl_pct'].min():+.2f}%")
    print(f"  Dias promedio: {df_t['dias'].mean():.0f}")
    return df_t

df_sin = resumen(trades_sin_parking, "SIN parking (con costo tx)")
df_con = resumen(trades_con_parking, "CON parking 3 dias habiles (con costo tx)")

# ── GRAFICO COMPARATIVO ───────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

if len(df_sin) > 0:
    df_sin['pnl_acum'] = df_sin['pnl_pct'].cumsum()
    axes[0].plot(df_sin['fecha_salida'], df_sin['pnl_acum'],
                 marker='o', label='Sin parking', color='steelblue', linewidth=2)

if len(df_con) > 0:
    df_con['pnl_acum'] = df_con['pnl_pct'].cumsum()
    axes[0].plot(df_con['fecha_salida'], df_con['pnl_acum'],
                 marker='s', label='Con parking 3 dias', color='orange', linewidth=2)

axes[0].axhline(0, color='red', linestyle='--', alpha=0.5)
axes[0].set_title('PnL acumulado — Sin parking vs Con parking')
axes[0].set_ylabel('Retorno acumulado (%)')
axes[0].legend()
axes[0].grid(alpha=0.3)

# PnL por trade comparado
x = range(max(len(df_sin), len(df_con)))
if len(df_sin) > 0:
    axes[1].bar([i - 0.2 for i in range(len(df_sin))],
                df_sin['pnl_pct'],
                width=0.4, label='Sin parking',
                color=['green' if x > 0 else 'red' for x in df_sin['pnl_pct']],
                alpha=0.7)
if len(df_con) > 0:
    axes[1].bar([i + 0.2 for i in range(len(df_con))],
                df_con['pnl_pct'],
                width=0.4, label='Con parking',
                color=['darkgreen' if x > 0 else 'darkred' for x in df_con['pnl_pct']],
                alpha=0.7)

axes[1].axhline(0, color='black', alpha=0.3)
axes[1].set_title('PnL por trade — Comparacion')
axes[1].set_xlabel('Numero de trade')
axes[1].set_ylabel('Retorno (%)')
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.show()