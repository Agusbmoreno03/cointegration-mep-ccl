# Cointegración y Pairs Trading — MEP/CCL + Acciones USA

## Objetivo
Encontrar relaciones de equilibrio de largo plazo entre pares de activos financieros, identificar cuándo se rompe ese equilibrio y modelar cómo el mercado corrige esa anomalía.

## ¿Por qué Cointegración y no Correlación?
Dos series pueden estar muy correlacionadas pero no cointegradas.
- **Correlación**: mide si se mueven en la misma dirección en el corto plazo.
- **Cointegración**: significa que aunque se alejen temporalmente, existe una fuerza económica (arbitraje) que las vuelve a juntar.

## Pares analizados

### 1. Dólar MEP vs CCL (Argentina)
- **Cointegración**: SI (p-value = 0.0001)
- **Relación de equilibrio**: CCL = 2.43 + 1.0179 x MEP (R²=0.9989)
- **Backtest sin parking**: +125% | Con parking 72hs: +77% (2023-2025)
- **Trades**: 17 | Win rate: 88% | Duración promedio: 28 días
- **Conclusión**: Par más sólido estadísticamente — son esencialmente el mismo activo

### 2. Visa (V) vs Mastercard (MA)
- **Cointegración**: CASI (p-value = 0.061, muy cerca del umbral 0.05)
- **Correlación promedio**: 0.907 — la más alta de todos los pares
- **Relación de equilibrio**: Visa = -16.47 + 1.6926 x Mastercard (R²=0.9942)
- **Backtest**: +134% | 13 trades | Win rate: 100% | Duración promedio: 165 días
- **Señal actual**: Z-score = -4.02 → Visa barata vs Mastercard → long Visa / short Mastercard
- **Conclusión**: Mejor backtest de acciones — duopolio con negocio casi idéntico

### 3. Apple (AAPL) vs Microsoft (MSFT)
- **Cointegración**: NO (p-value = 0.573)
- **Correlación promedio**: 0.561
- **Backtest**: +45% | 6 trades | Win rate: 100% | Duración promedio: 97 días
- **Conclusión**: Relación estable hasta 2022, se rompe con el boom de IA

### 4. Google (GOOGL) vs Microsoft (MSFT)
- **Cointegración**: NO (p-value = 1.0)
- **Correlación promedio**: 0.661
- **Backtest**: +24% | 2 trades | Win rate: 100% | Duración promedio: 242 días
- **Conclusión**: Google creció 2160% vs Microsoft 1498% — trayectorias muy distintas

### 5. Coca-Cola (KO) vs Pepsi (PEP)
- **Cointegración**: NO (p-value = 1.0)
- **Correlación promedio**: 0.634
- **Backtest**: +6% | 1 trade
- **Conclusión**: Empresas distintas con crecimientos divergentes (KO +381% vs PEP +272%)

## Resumen comparativo

| Par | Cointegración | p-value | PnL total | Trades | Win rate | Días promedio |
|-----|--------------|---------|-----------|--------|----------|---------------|
| MEP/CCL | SI | 0.0001 | +77% | 17 | 88% | 28 |
| V/MA | CASI | 0.061 | +134% | 13 | 100% | 165 |
| AAPL/MSFT | NO | 0.573 | +45% | 6 | 100% | 97 |
| GOOGL/MSFT | NO | 1.0 | +24% | 2 | 100% | 242 |
| KO/PEP | NO | 1.0 | +6% | 1 | 100% | — |

## Conclusión principal
El p-value de cointegración no es el único indicador de un buen par para trading.
V/MA sin cointegración formal generó +134% — más que MEP/CCL con cointegración confirmada.
Lo que importa es la estabilidad de la relación y la fuerza económica que une los dos activos.

## Modelo de Corrección de Error (ECM) — MEP/CCL
Velocidad de ajuste por régimen macroeconómico:
- Cepo estricto (2019-2023): 4.2 días
- Devaluación Massa (2023): 6.5 días
- Post Milei cepo (2024): 2.9 días
- Cepo relajado (2024-hoy): 2.5 días

Z-score actual MEP/CCL: 0.57 — dentro del rango normal, sin oportunidad de arbitraje.

## Archivos
- cointegracion.py — análisis MEP/CCL: tests estadísticos y Z-score
- zscore.py — visualización del Z-score histórico MEP/CCL
- backtest_coint.py — backtest MEP/CCL sin restricciones
- backtest_parking.py — backtest MEP/CCL con parking 72hs y costos
- ecm.py — modelo de corrección de error por régimen macroeconómico
- pairs_stocks.py — análisis de pares de acciones (KO/PEP, GOOGL/MSFT, AAPL/MSFT, V/MA)

## Fuente de datos
- ArgentinaDatos API (https://api.argentinadatos.com) — MEP y CCL histórico
- DolarApi (https://dolarapi.com) — cotización actual
- Yahoo Finance via yfinance — acciones USA

## Dependencias
pip install requests pandas numpy matplotlib statsmodels yfinance
