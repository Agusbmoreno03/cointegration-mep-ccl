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
- **Conclusión**: Par más sólido — son esencialmente el mismo activo

### 2. Coca-Cola (KO) vs Pepsi (PEP)
- **Cointegración**: NO (p-value = 1.0)
- **Correlación promedio**: 0.634
- **Backtest**: +6% | 1 trade
- **Conclusión**: Empresas distintas con crecimientos divergentes (KO +381% vs PEP +272% desde 2010)

### 3. Google (GOOGL) vs Microsoft (MSFT)
- **Cointegración**: NO (p-value = 1.0)
- **Correlación promedio**: 0.661
- **Backtest**: +24% | 2 trades | Duración promedio: 242 días
- **Conclusión**: Google creció 2160% vs Microsoft 1498% — trayectorias muy distintas

### 4. Apple (AAPL) vs Microsoft (MSFT)
- **Cointegración**: NO (p-value = 0.57)
- **Correlación promedio**: 0.561
- **Backtest**: +45% | 6 trades | Duración promedio: 97 días
- **Conclusión**: Relación estable hasta 2022, luego se rompe con el boom de IA

## Resumen comparativo

| Par | Cointegración | PnL total | Trades | Win rate | Días promedio |
|-----|--------------|-----------|--------|----------|---------------|
| MEP/CCL | SI | +77% | 17 | 88% | 28 |
| KO/PEP | NO | +6% | 1 | 100% | — |
| GOOGL/MSFT | NO | +24% | 2 | 100% | 242 |
| AAPL/MSFT | NO | +45% | 6 | 100% | 97 |

## Modelo de Corrección de Error (ECM) — MEP/CCL
Velocidad de ajuste por régimen macroeconómico:
- Cepo estricto (2019-2023): 4.2 días
- Devaluación Massa (2023): 6.5 días
- Post Milei cepo (2024): 2.9 días
- Cepo relajado (2024-hoy): 2.5 días

Z-score actual: 0.57 — dentro del rango normal, sin oportunidad de arbitraje.

## Archivos
- cointegracion.py — análisis MEP/CCL: tests estadísticos y Z-score
- zscore.py — visualización del Z-score histórico MEP/CCL
- backtest_coint.py — backtest MEP/CCL sin restricciones
- backtest_parking.py — backtest MEP/CCL con parking 72hs y costos
- ecm.py — modelo de corrección de error por régimen macroeconómico
- pairs_stocks.py — análisis de pares de acciones (KO/PEP, GOOGL/MSFT, AAPL/MSFT)

## Fuente de datos
- ArgentinaDatos API (https://api.argentinadatos.com) — MEP y CCL histórico
- DolarApi (https://dolarapi.com) — cotización actual
- Yahoo Finance via yfinance — acciones USA

## Dependencias
pip install requests pandas numpy matplotlib statsmodels yfinance
