# Cointegración MEP vs CCL — Pairs Trading Argentina

## Objetivo
Encontrar la relación de equilibrio de largo plazo entre el Dólar MEP y el Dólar CCL, identificar cuándo se rompe ese equilibrio y modelar cómo el mercado corrige esa anomalía.

## Metodología
- Test ADF (Augmented Dickey-Fuller) para verificar no estacionariedad
- Test de Engle-Granger para confirmar cointegración
- Modelo de Corrección de Error (ECM) para estimar velocidad de ajuste
- Backtest de estrategia pairs trading con y sin restricciones regulatorias

## Resultados principales
- Cointegración confirmada con p-value = 0.0001
- Relación de equilibrio: CCL = 2.43 + 1.0179 x MEP (R²=0.9989)
- Backtest sin parking: +125% | Con parking 72hs: +77% (2023-2025)
- Vida media del desarbitraje según régimen:
  - Cepo estricto (2019-2023): 4.2 días
  - Devaluación Massa (2023): 6.5 días
  - Post Milei (2024): 2.9 días
  - Cepo relajado (2024-hoy): 2.5 días

## Archivos
- cointegracion.py — análisis principal y tests estadísticos
- zscore.py — visualización del Z-score histórico
- backtest_coint.py — backtest sin restricciones regulatorias
- backtest_parking.py — backtest con parking de 72hs y costos de transacción
- ecm.py — modelo de corrección de error por régimen macroeconómico

## Fuente de datos
- ArgentinaDatos API (https://api.argentinadatos.com)
- DolarApi (https://dolarapi.com)

## Dependencias
pip install requests pandas numpy matplotlib statsmodels
