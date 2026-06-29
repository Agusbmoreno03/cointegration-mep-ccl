import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from statsmodels.tsa.stattools import adfuller

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

# ── RELACION DE EQUILIBRIO ────────────────────────
X    = add_constant(df['MEP'])
reg  = OLS(df['CCL'], X).fit()
beta = reg.params['MEP']
alfa = reg.params['const']
df['residuo'] = df['CCL'] - (alfa + beta * df['MEP'])
df['zscore']  = (df['residuo'] - df['residuo'].mean()) / df['residuo'].std()

# ── ECM GLOBAL ────────────────────────────────────
"""
Modelo de Corrección de Error:
    Δresiduo(t) = λ × residuo(t-1) + ε
    
λ negativo significa que cuando el spread está alto,
tiende a bajar — velocidad de ajuste al equilibrio.
Vida media = -log(2) / log(1 + λ) días
"""
df['delta_residuo'] = df['residuo'].diff()
df['residuo_lag']   = df['residuo'].shift(1)
df_ecm = df[['delta_residuo', 'residuo_lag']].dropna()

X_ecm = add_constant(df_ecm['residuo_lag'])
ecm   = OLS(df_ecm['delta_residuo'], X_ecm).fit()
lam   = ecm.params['residuo_lag']
vida_media = -np.log(2) / np.log(1 + lam)

print("=" * 55)
print("MODELO DE CORRECCION DE ERROR (ECM) — MEP/CCL")
print("=" * 55)
print(f"\n  Lambda (velocidad ajuste) : {lam:.4f}")
print(f"  Vida media del desarbitraje: {vida_media:.1f} dias")
print(f"  Interpretacion: el {abs(lam)*100:.1f}% del desequilibrio")
print(f"  se corrige cada dia")

# ── ECM POR REGIMEN ───────────────────────────────
regimenes = {
    'Cepo estricto (2019-2023)': ('2019-01-01', '2023-07-31'),
    'Devaluacion Massa (2023-08 a 2023-11)': ('2023-08-01', '2023-11-30'),
    'Post Milei cepo (2023-12 a 2024-06)': ('2023-12-01', '2024-06-30'),
    'Cepo relajado (2024-07 a hoy)': ('2024-07-01', '2026-12-31'),
}

print(f"\n{'─'*55}")
print(f"  VELOCIDAD DE AJUSTE POR REGIMEN MACROECONOMICO")
print(f"{'─'*55}")
print(f"  {'Regimen':<38} {'Lambda':>7} {'Vida media':>11}")
print(f"  {'─'*53}")

resultados = []
for nombre, (inicio, fin) in regimenes.items():
    sub = df_ecm[inicio:fin].copy()
    if len(sub) < 30:
        continue
    X_sub = add_constant(sub['residuo_lag'])
    ecm_sub = OLS(sub['delta_residuo'], X_sub).fit()
    lam_sub = ecm_sub.params['residuo_lag']
    if -1 < lam_sub < 0:
        vm = -np.log(2) / np.log(1 + lam_sub)
    else:
        vm = float('inf')
    resultados.append({'nombre': nombre, 'lambda': lam_sub, 'vida_media': vm})
    vm_str = f"{vm:.1f} dias" if vm != float('inf') else "indefinida"
    print(f"  {nombre:<38} {lam_sub:>7.4f} {vm_str:>11}")

# ── PREDICCION ACTUAL ─────────────────────────────
print(f"\n{'─'*55}")
print(f"  PREDICCION — Regimen actual")
print(f"{'─'*55}")

# Usar el lambda del regimen actual
reg_actual = [r for r in resultados if 'relajado' in r['nombre']]
if reg_actual:
    lam_actual = reg_actual[0]['lambda']
    vm_actual  = reg_actual[0]['vida_media']
    zscore_hoy = df['zscore'].iloc[-1]
    spread_hoy = df['residuo'].iloc[-1]

    print(f"  Z-score hoy     : {zscore_hoy:.2f}")
    print(f"  Spread hoy      : ${spread_hoy:.1f}")
    print(f"  Lambda actual   : {lam_actual:.4f}")
    print(f"  Vida media      : {vm_actual:.1f} dias")

    # Simular convergencia
    dias_sim = range(30)
    spread_sim = [spread_hoy * (1 + lam_actual)**d for d in dias_sim]
    zscore_sim = [(s - df['residuo'].mean()) / df['residuo'].std()
                  for s in spread_sim]

    print(f"\n  Proyeccion de convergencia:")
    print(f"  {'Dia':>4} {'Spread':>10} {'Z-score':>8}")
    print(f"  {'─'*25}")
    for d in [0, 3, 5, 7, 10, 14, 21, 28]:
        if d < len(spread_sim):
            print(f"  {d:>4} ${spread_sim[d]:>9.1f} {zscore_sim[d]:>8.2f}")

# ── GRAFICO ───────────────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# Z-score con regimenes
axes[0].plot(df['zscore'], linewidth=1, color='steelblue', alpha=0.7)
axes[0].axhline( 1.5, color='red',   linestyle='--', alpha=0.5)
axes[0].axhline(-1.5, color='green', linestyle='--', alpha=0.5)
axes[0].axhline(0,    color='black', linestyle='-',  alpha=0.3)

colores_reg = ['lightblue', 'lightyellow', 'lightcoral', 'lightgreen']
for (nombre, (ini, fin)), color in zip(regimenes.items(), colores_reg):
    axes[0].axvspan(pd.to_datetime(ini), pd.to_datetime(fin),
                    alpha=0.15, color=color, label=nombre)

axes[0].set_title('Z-Score por regimen macroeconomico')
axes[0].legend(fontsize=7, loc='upper left')
axes[0].grid(alpha=0.3)

# Lambda por regimen
nombres = [r['nombre'].split('(')[0].strip() for r in resultados]
lambdas = [abs(r['lambda']) for r in resultados]
vidas   = [r['vida_media'] if r['vida_media'] != float('inf') else 0
           for r in resultados]

x = range(len(resultados))
ax2 = axes[1]
bars = ax2.bar(x, vidas, color=['lightblue', 'lightyellow', 'lightcoral', 'lightgreen'],
               edgecolor='gray', alpha=0.8)
ax2.set_xticks(x)
ax2.set_xticklabels(nombres, rotation=15, ha='right', fontsize=9)
ax2.set_ylabel('Vida media del desarbitraje (dias)')
ax2.set_title('Velocidad de correccion por regimen — menor = mas rapido')
ax2.grid(alpha=0.3, axis='y')

for bar, r in zip(bars, resultados):
    vm = r['vida_media']
    if vm != float('inf'):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"{vm:.1f}d", ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.show()