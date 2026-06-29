
import requests
import pandas as pd

# --- TEST 1: DolarApi (cotizacion actual) ---
print("=== DolarApi - Cotizacion actual ===")
r = requests.get("https://dolarapi.com/v1/dolares", timeout=10)
datos = r.json()
for d in datos:
    if d['casa'] in ('bolsa', 'contadoconliqui'):
        nombre = 'MEP' if d['casa'] == 'bolsa' else 'CCL'
        print(f"  {nombre}: compra=${d['compra']} | venta=${d['venta']}")

# --- TEST 2: Dolarito (historial MEP) ---
print("\n=== Dolarito - Historial MEP (ultimos 5 dias) ===")
url = "https://dolarito.ar/api/cotizaciones-historicas/mep"
headers = {"User-Agent": "Mozilla/5.0"}
r2 = requests.get(url, headers=headers, timeout=10)
print(f"  Status: {r2.status_code}")
print(f"  Respuesta: {r2.text[:200]}")


# --- TEST 3: ArgentinaDatos API (historial MEP y CCL) ---
print("\n=== ArgentinaDatos - Historial ===")
import requests

# MEP historico
url_mep = "https://api.argentinadatos.com/v1/cotizaciones/dolares/mep"
url_ccl = "https://api.argentinadatos.com/v1/cotizaciones/dolares/contadoconliqui"

r_mep = requests.get(url_mep, timeout=10)
r_ccl = requests.get(url_ccl, timeout=10)

print(f"  MEP status: {r_mep.status_code}")
print(f"  CCL status: {r_ccl.status_code}")

if r_mep.status_code == 200:
    datos_mep = r_mep.json()
    print(f"  MEP: {len(datos_mep)} registros | primero: {datos_mep[0]} | ultimo: {datos_mep[-1]}")

if r_ccl.status_code == 200:
    datos_ccl = r_ccl.json()
    print(f"  CCL: {len(datos_ccl)} registros | primero: {datos_ccl[0]} | ultimo: {datos_ccl[-1]}")

    import requests

# Probar endpoints alternativos para MEP
urls = [
    "https://api.argentinadatos.com/v1/cotizaciones/dolares/bolsa",
    "https://api.argentinadatos.com/v1/cotizaciones/dolares/mep",
    "https://api.argentinadatos.com/v1/cotizaciones/dolares",
]

for url in urls:
    r = requests.get(url, timeout=10)
    print(f"  {url.split('/')[-1]}: status={r.status_code} | {str(r.text[:100])}")