# -*- coding: utf-8 -*-
"""
Motor de medicion de la Sesion 1 - IFPN0025 Big Data e Ingenieria de Datos (Universidad Ean)
Practica S01_P4_v1 - Naturaleza de los datos masivos.

Contiene TODAS las funciones que la guia define, mas las mediciones extra que el
Nivel 3 exige para poder DESCARTAR una V en lugar de solo afirmarla.

No imprime nada al importarse. Se usa desde el notebook o desde ejecutar_todo.py.
"""

import os
import math
import json
import datetime as _dt

import numpy as np
import pandas as pd
import psutil

# ---------------------------------------------------------------------------
# Identificadores VERIFICADOS del Portal de Datos Abiertos (www.datos.gov.co)
# Verificados contra la API de Socrata el 2026-07-24.
# ---------------------------------------------------------------------------
DATASETS = {
    # SECOP II - Procesos de Contratacion. 59 columnas. ~8.878.158 filas (2026-07-24)
    "SECOP II": {"id": "p6dx-8zbt", "campo_fecha": "fecha_de_publicacion_del"},
    # IDEAM - Temperatura Ambiente del Aire. 12 columnas. Registro horario por estacion.
    "IDEAM":    {"id": "sbwg-7ju4", "campo_fecha": "fechaobservacion"},
    # GEIH (DANE) no tiene API: descarga manual a data/raw/geih/
    "GEIH":     {"id": None,        "campo_fecha": None},
}

SOCRATA = "https://www.datos.gov.co/resource/{ds}.csv?$limit={n}"
SOCRATA_W = "https://www.datos.gov.co/resource/{ds}.csv?$limit={n}&$where={w}"


# ===========================================================================
# 3. LAS TRES MEDICIONES QUE SOSTIENEN TODO  (seccion 3 de la guia)
# ===========================================================================

def get_file_size_gb(file_path):
    """S0 - Tamano real del archivo en disco, en gigabytes."""
    return os.path.getsize(file_path) / (1024 ** 3)


def measure_expansion_factor(file_path, **read_options):
    """k - Cuantas veces crece un archivo al cargarse en memoria.

    deep=True es obligatorio: sin el, pandas solo cuenta los punteros de las
    columnas object, no las cadenas apuntadas, y todos los k convergen a un
    valor bajo y falso.
    """
    size_disk_bytes = os.path.getsize(file_path)
    df = pd.read_csv(file_path, **read_options)
    size_memory_bytes = df.memory_usage(deep=True).sum()
    return size_memory_bytes / size_disk_bytes, df


def get_available_memory_gb():
    """M - Memoria realmente disponible, no la de la etiqueta."""
    return psutil.virtual_memory().available / (1024 ** 3)


def get_total_memory_gb():
    return psutil.virtual_memory().total / (1024 ** 3)


# ===========================================================================
# 4. NIVEL 1 - PERFILAMIENTO  (Paso 1.1 de la guia)
# ===========================================================================

def profile_source(df, source_name):
    """Perfil minimo de una fuente cargada."""
    dtype_counts = df.dtypes.value_counts().to_dict()
    object_columns = (df.dtypes == "object").sum()
    return {
        "fuente": source_name,
        "filas": len(df),
        "columnas": df.shape[1],
        "columnas_texto": int(object_columns),
        "proporcion_texto": round(object_columns / df.shape[1], 3),
        "tipos": {str(k): int(v) for k, v in dtype_counts.items()},
    }


def verify_level_1(df_measurements):
    """Autoverificacion del Nivel 1. Devuelve (bool, dict)."""
    checks = {
        "Hay exactamente 3 fuentes medidas": len(df_measurements) == 3,
        "Todos los k son mayores que 1": bool((df_measurements["k"] > 1).all()),
        "Los tres k son distintos": int(df_measurements["k"].nunique()) == 3,
        "No hay tamanos de disco en cero": bool((df_measurements["tamano_disco_gb"] > 0).all()),
    }
    return all(checks.values()), checks


# ===========================================================================
# 5. NIVEL 2 - HORIZONTE DE SATURACION  (Paso 2.1 de la guia)
# ===========================================================================

def compute_threshold_periods(memory_useful_gb, expansion_factor,
                              initial_size_gb, growth_rate):
    """t_umbral = ln( M / (k * S0) ) / ln(1 + g).

    Resultado negativo = el umbral YA fue superado.
    """
    if growth_rate <= 0:
        raise ValueError("La tasa de crecimiento debe ser mayor que cero.")
    ratio = memory_useful_gb / (expansion_factor * initial_size_gb)
    return math.log(ratio) / math.log(1 + growth_rate)


def cagr(size_a, size_b, n_periods):
    """Pista 2 del Nivel 2: g = (S_b / S_a) ** (1/n) - 1."""
    return (size_b / size_a) ** (1.0 / n_periods) - 1.0


def memoria_util(total_gb, fraccion_so=0.35):
    """M util = total - lo que el SO, el navegador y el IDE ya consumen.

    fraccion_so = 0.35 es el supuesto declarado del entregable, medido con
    psutil en el equipo propio (ver docs/EXPLICACION_PASO_A_PASO.md).
    """
    return total_gb * (1.0 - fraccion_so)


# ===========================================================================
# 6. NIVEL 3 - MEDICIONES PARA DESCARTAR  (no estan en la guia: son el trabajo)
# ===========================================================================

def medir_veracidad(df, clave=None):
    """Veracidad se descarta o se confirma con una medicion concreta y barata."""
    n_filas = len(df)
    nulos = df.isna().mean()
    col_peor = nulos.idxmax() if (len(nulos) and not nulos.isna().all()) else None
    r = {
        "prop_nulos_media": round(float(nulos.mean()), 4),
        "prop_nulos_max": round(float(nulos.max()), 4) if len(nulos) else None,
        "columna_mas_nula": str(col_peor),
        "columnas_100pct_nulas": int((nulos == 1.0).sum()),
        "columnas_sobre_50pct_nulas": int((nulos > 0.5).sum()),
        "filas_duplicadas_completas": int(df.duplicated().sum()),
        "prop_filas_duplicadas": round(float(df.duplicated().mean()), 4),
    }
    if clave and clave in df.columns:
        r["duplicados_de_clave"] = int(df[clave].duplicated().sum())
        r["prop_duplicados_clave"] = round(float(df[clave].duplicated().mean()), 4)
    r["filas_evaluadas"] = n_filas
    return r


def medir_velocidad(df, col_fecha, frecuencia_declarada=None):
    """Velocidad NO es frecuencia de registro. Compara declarada vs observada."""
    if col_fecha not in df.columns:
        return {"nota": f"columna {col_fecha} ausente"}
    s = pd.to_datetime(df[col_fecha], errors="coerce", utc=True).dropna()
    if s.empty:
        return {"nota": f"columna {col_fecha} sin fechas parseables"}
    span_h = (s.max() - s.min()).total_seconds() / 3600.0
    ahora = pd.Timestamp.now(tz="UTC")
    return {
        "primer_registro": str(s.min()),
        "ultimo_registro": str(s.max()),
        "span_horas": round(span_h, 2),
        "registros_por_hora_observados": round(len(s) / span_h, 2) if span_h > 0 else None,
        "latencia_dias_hasta_hoy": round((ahora - s.max()).total_seconds() / 86400.0, 2),
        "frecuencia_declarada": frecuencia_declarada,
    }


def medir_variedad(df):
    """Variedad medible: tipos distintos, cardinalidad, texto libre."""
    obj = df.select_dtypes(include="object")
    largo_medio = {}
    for c in obj.columns:
        try:
            largo_medio[c] = float(obj[c].dropna().astype(str).str.len().mean())
        except Exception:
            pass
    top = sorted(largo_medio.items(), key=lambda x: -x[1])[:5]
    return {
        "tipos_distintos": int(df.dtypes.nunique()),
        "n_columnas": int(df.shape[1]),
        "n_columnas_texto": int(obj.shape[1]),
        "largo_medio_texto_global": round(float(np.mean(list(largo_medio.values()))), 2) if largo_medio else None,
        "columnas_texto_mas_largas": [(c, round(v, 1)) for c, v in top],
        "columnas_texto_libre_>80_chars": int(sum(1 for v in largo_medio.values() if v > 80)),
    }


# ===========================================================================
# 2.4 PLAN DE CONTINGENCIA - GENERADOR SINTETICO (literal de la guia)
# ===========================================================================

def generate_meter_readings(n_meters=5_000, n_hours=168, seed=42):
    """Lecturas horarias de medidores con perfil de consumo realista."""
    rng = np.random.default_rng(seed)
    n_records = n_meters * n_hours
    meter_ids = np.repeat([f"MED-{i:07d}" for i in range(n_meters)], n_hours)
    timestamps = np.tile(pd.date_range("2024-03-01", periods=n_hours, freq="h"), n_meters)
    hour_of_day = np.tile(np.arange(n_hours) % 24, n_meters)
    base_consumption = 0.12 + 0.08 * np.sin((hour_of_day - 6) * np.pi / 12) ** 2
    consumption = np.abs(base_consumption + rng.normal(0, 0.03, n_records))
    quality_flags = rng.choice(["OK", "ESTIMADO", "SIN_SENAL"], size=n_records, p=[0.94, 0.05, 0.01])
    return pd.DataFrame({
        "meter_id": meter_ids,
        "reading_ts": timestamps,
        "consumption_m3": np.round(consumption, 4),
        "quality_flag": quality_flags,
        "municipality": rng.choice(["Girardot", "Espinal", "Flandes", "Ricaurte"], size=n_records),
    })


# ===========================================================================
# DESCARGA
# ===========================================================================

def _leer_url(url, timeout, intentos=3):
    """Descarga una URL a texto, con reintentos."""
    import urllib.request, time as _t
    ultimo = None
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EAN-IFPN0025-S01"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            ultimo = e
            _t.sleep(2 * (i + 1))
    raise ultimo


def descargar_socrata(dataset_id, destino, n=200_000, where=None, timeout=180,
                      pagina=25_000, progreso=True):
    """Descarga paginada y VERIFICADA desde Socrata.

    Una sola peticion de 200.000 filas hace que el servidor cierre el flujo antes
    de tiempo y el archivo queda truncado sin que se note. Paginando de a 25.000 y
    contando las filas de cada pagina con `csv.reader` (que respeta las comillas y
    los saltos de linea dentro de un campo) la descarga es verificable.

    Devuelve (bytes_escritos, filas_escritas).
    """
    import urllib.parse, csv, io
    os.makedirs(os.path.dirname(destino) or ".", exist_ok=True)
    total, offset, primera = 0, 0, True

    with open(destino, "w", encoding="utf-8", newline="") as fh:
        # QUOTE_ALL replica el formato en que Socrata sirve el CSV, para que el
        # tamano en disco (y por tanto k) sea comparable a una descarga directa.
        escritor = csv.writer(fh, quoting=csv.QUOTE_ALL)
        while total < n:
            limite = min(pagina, n - total)
            params = {"$limit": limite, "$offset": offset, "$order": ":id"}
            if where:
                params["$where"] = where
            url = (f"https://www.datos.gov.co/resource/{dataset_id}.csv?"
                   + urllib.parse.urlencode(params, safe="$:"))

            cuerpo, encabezado = [], None
            for intento in range(2):
                filas = list(csv.reader(io.StringIO(_leer_url(url, timeout))))
                if not filas:
                    break
                encabezado, cuerpo = filas[0], filas[1:]
                if len(cuerpo) >= limite:
                    break          # pagina completa
                # pagina corta: puede ser el final real o una lectura truncada
            if not cuerpo:
                break
            if primera and encabezado:
                escritor.writerow(encabezado)
                primera = False
            escritor.writerows(cuerpo)
            total += len(cuerpo)
            offset += len(cuerpo)
            if progreso:
                print(f"\r    {total:,} filas descargadas...", end="", flush=True)
            if len(cuerpo) < limite:
                break              # la fuente se acabo
    if progreso:
        print(f"\r    {total:,} filas · {os.path.getsize(destino)/1e6:.1f} MB" + " " * 12)
    return os.path.getsize(destino), total


# ===========================================================================
# IDENTIFICACION DEL EQUIPO  (para archivar corridas por maquina)
# ===========================================================================

def identificar_equipo(etiqueta=None):
    """Huella del equipo donde se corre. Permite comparar 8 GB vs 16 GB."""
    import platform, socket, re
    total = get_total_memory_gb()
    ram_nominal = int(round(total / 4.0) * 4) or int(round(total))
    host = socket.gethostname()
    slug = etiqueta or f"{host}_{ram_nominal}GB"
    slug = re.sub(r"[^A-Za-z0-9_.-]", "-", slug)
    return {
        "etiqueta": slug,
        "hostname": host,
        "so": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "ram_total_gb": round(total, 2),
        "ram_nominal_gb": ram_nominal,
        "ram_disponible_gb": round(get_available_memory_gb(), 2),
        "fraccion_consumida_so": round(1 - get_available_memory_gb() / total, 4),
        "momento": _dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
