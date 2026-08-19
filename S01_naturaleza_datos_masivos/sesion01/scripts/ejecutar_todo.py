# -*- coding: utf-8 -*-
"""
Orquestador de la practica S01_P4. Ejecuta Nivel 1 + Nivel 2 y deja todo medido.

  python ejecutar_todo.py              -> intenta descargar las fuentes reales
  python ejecutar_todo.py --contingencia -> usa el generador sintetico (seccion 2.4)
  python ejecutar_todo.py --filas 50000  -> baja el $limit si la conexion es lenta

Salidas:
  resultados/mediciones.csv     (Nivel 1)
  resultados/_resultados.json   (insumo para generar_entregables.py)
"""
import os, sys, json, time, argparse, urllib.request
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bd_s01 as bd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(RAIZ, "data", "raw")
SYN = os.path.join(RAIZ, "data", "synthetic")
RES = os.path.join(RAIZ, "resultados")
for d in (RAW, SYN, RES):
    os.makedirs(d, exist_ok=True)

# --- Serie real de crecimiento de SECOP II -------------------------------
# Consultada el 2026-07-24 contra la API de Socrata:
#   SELECT date_extract_y(fecha_de_publicacion_del) AS anio, count(*) GROUP BY anio
SECOP_SERIE = {2015: 5528, 2016: 9904, 2017: 43728, 2018: 194742, 2019: 186082,
               2020: 419702, 2021: 652937, 2022: 1038591, 2023: 1531557,
               2024: 1670367, 2025: 1934805, 2026: 1060386}  # 2026 parcial
SECOP_TOTAL_FILAS = 8_878_158
SECOP_NULOS_FECHA_PUB = 8_811_110   # nulos en 'fecha_de_publicacion'
IDEAM_REGISTROS_DIA = 21_710        # medido para 2026-07-01, dataset sbwg-7ju4
IDEAM_ANIOS_SERIE = 7               # publicado desde 2019-07
IDEAM_FILAS_TOTALES = IDEAM_REGISTROS_DIA * 365 * IDEAM_ANIOS_SERIE  # cota inferior

# Filas totales de la fuente COMPLETA (no de la muestra). S0 real = S0_muestra * factor.
FILAS_TOTALES = {
    "SECOP II": SECOP_TOTAL_FILAS,
    "IDEAM": IDEAM_FILAS_TOTALES,
    "GEIH": None,                      # un mes es el universo util; factor 1
    "CONTRATACION (sintetico)": SECOP_TOTAL_FILAS,
    "ACUEDUCTO (sintetico, 2.4)": 5000 * 24 * 365,   # 5.000 medidores, un ano horario
    "ENCUESTA HOGARES (sintetico)": None,
}


def hay_internet(timeout=8):
    try:
        urllib.request.urlopen("https://www.datos.gov.co/resource/p6dx-8zbt.csv?$limit=1",
                               timeout=timeout).read(64)
        return True
    except Exception:
        return False


def fuentes_sinteticas(n_filas):
    """Contingencia: tres fuentes sinteticas con FORMAS distintas.
    Declaradas como sinteticas en todos los entregables."""
    rng = np.random.default_rng(42)
    rutas = {}

    # 1) Acueducto (literal de la seccion 2.4 de la guia) - esquema estrecho, numerico
    n_meters = max(500, min(5000, n_filas // 168))
    df = bd.generate_meter_readings(n_meters=n_meters, n_hours=168, seed=42)
    p = os.path.join(SYN, "lecturas_acueducto.csv"); df.to_csv(p, index=False)
    rutas["ACUEDUCTO (sintetico, 2.4)"] = p

    # 2) Forma tipo contratacion publica: mucho texto libre
    n = min(n_filas, 60_000)
    pal = ("PRESTACION DE SERVICIOS PROFESIONALES ESPECIALIZADOS PARA APOYAR "
           "JURIDICAMENTE LOS PROCESOS DE COBRO RECAUDO Y RECUPERACION DE CARTERA "
           "DEL MUNICIPIO CONFORME AL PLAN DE ACCION EN SALUD VIGENCIA").split()
    pool = [" ".join(rng.choice(pal, size=int(rng.integers(12, 45)))) for _ in range(400)]
    obj = np.array(pool, dtype=object)[rng.integers(0, 400, n)]
    df2 = pd.DataFrame({
        "id_proceso": [f"CO1.PCCNTR.{i:07d}" for i in range(n)],
        "entidad": rng.choice(["MUNICIPIO DE SOLEDAD", "ESE HOSPITAL DEPARTAMENTAL UNIVERSITARIO DEL QUINDIO",
                               "DEPARTAMENTO ADMINISTRATIVO NACIONAL DE ESTADISTICA (DANE)"], size=n),
        "descripcion_del_procedimiento": obj,
        "objeto_del_contrato": obj,
        "modalidad": rng.choice(["Contratacion directa", "Licitacion publica", "Minima cuantia"], size=n),
        "fecha_de_publicacion": pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 900, n), unit="D"),
        "precio_base": rng.integers(1_000_000, 900_000_000, n),
        "urlproceso": ["https://community.secop.gov.co/Public/Tendering/OpportunityDetail/Index?noticeUID=CO1.NTC.%d" % i for i in range(n)],
    })
    p2 = os.path.join(SYN, "forma_contratacion.csv"); df2.to_csv(p2, index=False)
    rutas["CONTRATACION (sintetico)"] = p2

    # 3) Forma tipo encuesta de hogares: muchas columnas, mezcla de tipos, nulos
    n3 = min(n_filas, 80_000)
    d3 = {"directorio": rng.integers(1, 60000, n3), "secuencia_p": rng.integers(1, 9, n3),
          "orden": rng.integers(1, 12, n3)}
    for i in range(1, 26):
        if i % 3 == 0:
            v = rng.choice(["1", "2", "9", None], size=n3, p=[.45, .35, .1, .1]).astype(object)
        elif i % 3 == 1:
            v = rng.normal(1_000_000, 400_000, n3).round(1)
            v[rng.random(n3) < 0.25] = np.nan
        else:
            v = rng.integers(0, 99, n3)
        d3[f"p65{i:02d}"] = v
    df3 = pd.DataFrame(d3)
    p3 = os.path.join(SYN, "forma_encuesta_hogares.csv"); df3.to_csv(p3, index=False)
    rutas["ENCUESTA HOGARES (sintetico)"] = p3
    return rutas


def descargar_reales(n_filas, redescargar=False):
    rutas = {}

    def _marca(ruta):
        return ruta + ".completo"

    def _ya_esta(ruta):
        """Solo reutiliza si la descarga anterior TERMINO y el tamano coincide."""
        if redescargar or not os.path.exists(ruta) or not os.path.exists(_marca(ruta)):
            return False
        try:
            m = json.load(open(_marca(ruta)))
        except Exception:
            return False
        if not isinstance(m, dict):      # sello del formato viejo
            return False
        if os.path.getsize(ruta) != m.get("bytes"):
            print(f"  !! {os.path.basename(ruta)} cambio de tamano desde la ultima descarga. Se rehace.")
            return False
        if m.get("pedidas") and m.get("filas") and m["filas"] < m["pedidas"] * 0.999:
            print(f"  !! {os.path.basename(ruta)} quedo con {m['filas']:,} de {m['pedidas']:,} filas. Se rehace.")
            return False
        return True

    def _sellar(ruta, filas=None):
        json.dump({"bytes": os.path.getsize(ruta), "filas": filas, "pedidas": n_filas},
                  open(_marca(ruta), "w"))

    p = os.path.join(RAW, "secop_sample.csv")
    if _ya_esta(p):
        print(f"  SECOP II ya descargado ({os.path.getsize(p)/1e6:.1f} MB) - se reutiliza. "
              f"Use --redescargar para bajarlo de nuevo.")
    else:
        print(f"  descargando SECOP II (p6dx-8zbt, $limit={n_filas}) ...", flush=True)
        b, fl = bd.descargar_socrata(bd.DATASETS["SECOP II"]["id"], p, n=n_filas)
        _sellar(p, fl)
        if fl < n_filas:
            print(f"    !! El portal entrego {fl:,} de {n_filas:,} filas. La proyeccion lo compensa,")
            print(f"       pero se declara en el entregable.")
    rutas["SECOP II"] = p

    p = os.path.join(RAW, "ideam_sample.csv")
    if _ya_esta(p):
        print(f"  IDEAM ya descargado ({os.path.getsize(p)/1e6:.1f} MB) - se reutiliza.")
    else:
        print(f"  descargando IDEAM (sbwg-7ju4, ventana de 15 dias) ...", flush=True)
        b, fl = bd.descargar_socrata(bd.DATASETS["IDEAM"]["id"], p, n=n_filas,
                                     where="fechaobservacion between '2026-06-01T00:00:00' and '2026-06-16T00:00:00'")
        _sellar(p, fl)
    rutas["IDEAM"] = p

    # GEIH: descarga manual. Se toma el archivo mas grande que haya en data/raw/geih/
    geih_dir = os.path.join(RAW, "geih")
    cand = []
    IGNORAR = {"leeme.txt", "readme.txt", "leeme.md", ".gitkeep"}
    if os.path.isdir(geih_dir):
        for r, _, fs in os.walk(geih_dir):
            for f in fs:
                if f.lower() in IGNORAR:
                    continue
                if not f.lower().endswith((".csv", ".txt", ".dta", ".sav")):
                    continue
                ruta_c = os.path.join(r, f)
                # un microdato real nunca pesa menos de 100 KB
                if os.path.getsize(ruta_c) < 100 * 1024:
                    continue
                cand.append(ruta_c)
    if cand:
        # Linea 145 de la guia: el paquete es de UN MES CUALQUIERA, no de varios.
        meses = sorted({os.path.basename(os.path.dirname(c)) for c in cand})
        rutas["GEIH"] = max(cand, key=os.path.getsize)
        print(f"  GEIH local: {os.path.basename(rutas['GEIH'])}")
        print(f"  Periodo(s) detectado(s) en data/raw/geih/: {', '.join(meses) or 'raiz'}")
        if len(meses) > 1:
            print("  !! ADVERTENCIA: la guia pide el paquete de UN SOLO mes. Hay mas de uno.")
    else:
        print("  !! GEIH ausente. Descarguela de www.dane.gov.co/microdatos a data/raw/geih/")
        print("     Se usa la forma sintetica de encuesta de hogares como sustituto DECLARADO.")
        rng = np.random.default_rng(7)
        n3 = 80_000
        d3 = {"directorio": rng.integers(1, 60000, n3), "secuencia_p": rng.integers(1, 9, n3), "orden": rng.integers(1, 12, n3)}
        for i in range(1, 26):
            if i % 3 == 0:
                d3[f"p65{i:02d}"] = rng.choice(["1", "2", "9", None], size=n3, p=[.45, .35, .1, .1]).astype(object)
            elif i % 3 == 1:
                v = rng.normal(1e6, 4e5, n3).round(1); v[rng.random(n3) < .25] = np.nan; d3[f"p65{i:02d}"] = v
            else:
                d3[f"p65{i:02d}"] = rng.integers(0, 99, n3)
        p3 = os.path.join(SYN, "geih_sustituto.csv"); pd.DataFrame(d3).to_csv(p3, index=False)
        rutas["GEIH (sustituto sintetico)"] = p3
    return rutas


CLAVES = {"SECOP II": "id_del_proceso", "IDEAM": "codigoestacion",
          "ACUEDUCTO (sintetico, 2.4)": "meter_id", "CONTRATACION (sintetico)": "id_proceso"}
FECHAS = {"SECOP II": ("fecha_de_publicacion_del", "continua / diaria"),
          "IDEAM": ("fechaobservacion", "horaria por estacion, publicacion diaria"),
          "ACUEDUCTO (sintetico, 2.4)": ("reading_ts", "horaria"),
          "CONTRATACION (sintetico)": ("fecha_de_publicacion", "continua")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contingencia", action="store_true")
    ap.add_argument("--filas", type=int, default=200_000)
    ap.add_argument("--redescargar", action="store_true",
                    help="Fuerza volver a bajar los CSV aunque ya esten en data/raw/")
    ap.add_argument("--equipo", type=str, default=None,
                    help="Etiqueta del equipo, p. ej. 'portatil_16GB'. Si se omite se deduce.")
    a = ap.parse_args()

    print("=" * 72)
    print("S01_P4 - Naturaleza de los datos masivos - ejecucion completa")
    print("=" * 72)
    EQ = bd.identificar_equipo(a.equipo)
    print(f"\nEquipo: {EQ['etiqueta']}  ({EQ['so']} · Python {EQ['python']} · "
          f"pandas {EQ['pandas']} · {EQ['ram_total_gb']} GB)")

    modo = "contingencia"
    if not a.contingencia:
        print("\n[0] Probando conectividad con www.datos.gov.co ...", flush=True)
        if hay_internet():
            modo = "real"; print("    OK, hay conexion.")
        else:
            print("    Sin conexion. Se activa el plan de contingencia (seccion 2.4).")

    print(f"\n[1] Obteniendo fuentes  (modo = {modo})")
    rutas = descargar_reales(a.filas, a.redescargar) if modo == "real" else fuentes_sinteticas(a.filas)

    # --- M: memoria util ---------------------------------------------------
    m_disp = bd.get_available_memory_gb()
    m_total = bd.get_total_memory_gb()
    frac_so = 1 - (m_disp / m_total)
    print(f"\n[2] Memoria    total = {m_total:.2f} GB   disponible (M) = {m_disp:.2f} GB"
          f"   consumida por SO+apps = {frac_so:.1%}")

    # --- Nivel 1 -----------------------------------------------------------
    print("\n[3] Nivel 1: perfilamiento y medicion de k")
    mediciones, extras, fallos = [], {}, {}
    for nombre, ruta in rutas.items():
        t0 = time.time()
        try:
            k, df = bd.measure_expansion_factor(ruta, low_memory=False)
        except (MemoryError, OSError) as e:
            filas_arch = sum(1 for _ in open(ruta, encoding="utf-8", errors="ignore")) - 1
            fallos[nombre] = {"error": type(e).__name__, "mensaje": str(e)[:200],
                              "filas_en_el_archivo": filas_arch,
                              "tamano_gb": round(bd.get_file_size_gb(ruta), 4),
                              "M_disponible_gb": round(bd.get_available_memory_gb(), 2)}
            print(f"    {nombre:<32} !! {type(e).__name__} al cargar {filas_arch:,} filas "
                  f"({bd.get_file_size_gb(ruta):.3f} GB en disco).")
            print(f"       Guia linea 336: esto NO es un error suyo, es el fenomeno de la sesion.")
            print(f"       Punto de quiebre registrado. Reintente con --filas {max(10_000, filas_arch//2)}")
            continue
        prof = bd.profile_source(df, nombre)
        prof["tamano_disco_gb"] = round(bd.get_file_size_gb(ruta), 6)
        prof["mb_en_memoria"] = round(df.memory_usage(deep=True).sum() / 1024**2, 2)
        prof["k"] = round(k, 2)
        tot = FILAS_TOTALES.get(nombre)
        factor = (tot / prof["filas"]) if tot else 1.0
        prof["filas_fuente_completa"] = int(tot) if tot else prof["filas"]
        prof["factor_proyeccion"] = round(factor, 2)
        prof["S0_proyectado_gb"] = round(prof["tamano_disco_gb"] * factor, 4)
        prof["memoria_necesaria_gb"] = round(prof["S0_proyectado_gb"] * prof["k"], 4)
        mediciones.append(prof)
        col_f, freq = FECHAS.get(nombre, (None, None))
        extras[nombre] = {
            "veracidad": bd.medir_veracidad(df, CLAVES.get(nombre)),
            "velocidad": bd.medir_velocidad(df, col_f, freq) if col_f else {"nota": "sin columna temporal"},
            "variedad": bd.medir_variedad(df),
            "segundos_carga": round(time.time() - t0, 2),
            "ruta": os.path.relpath(ruta, RAIZ),
        }
        print(f"    {nombre:<32} filas={prof['filas']:>8,}  cols={prof['columnas']:>3}  "
              f"txt={prof['proporcion_texto']:.2f}  S0m={prof['tamano_disco_gb']:.4f}GB  k={prof['k']}  "
              f"S0proy={prof['S0_proyectado_gb']:.3f}GB  RAM_nec={prof['memoria_necesaria_gb']:.2f}GB")
        del df

    dfm = pd.DataFrame(mediciones)
    # La guia (linea 308) exige NUEVE columnas y TRES filas en mediciones.csv.
    cols9 = ["fuente", "filas", "columnas", "columnas_texto", "proporcion_texto",
             "tipos", "tamano_disco_gb", "mb_en_memoria", "k"]
    dfm[cols9].to_csv(os.path.join(RES, "mediciones.csv"), index=False)
    assert len(cols9) == 9, "mediciones.csv debe tener 9 columnas"
    # La proyeccion a fuente completa es trabajo del Nivel 2: archivo aparte.
    dfm[["fuente", "k", "tamano_disco_gb", "filas", "filas_fuente_completa",
         "factor_proyeccion", "S0_proyectado_gb", "memoria_necesaria_gb"]].to_csv(
        os.path.join(RES, "proyeccion_umbral.csv"), index=False)
    dfm = dfm[cols9 + ["filas_fuente_completa", "factor_proyeccion",
                       "S0_proyectado_gb", "memoria_necesaria_gb"]]
    ok, checks = bd.verify_level_1(dfm)
    checks["mediciones.csv tiene 9 columnas y 3 filas"] = (len(cols9) == 9 and len(dfm) == 3)
    _mx_txt = dfm.loc[dfm["proporcion_texto"].idxmax(), "fuente"]
    _mx_k = dfm.loc[dfm["k"].idxmax(), "fuente"]
    checks["La fuente con mas texto tiene el k mas alto"] = bool(_mx_txt == _mx_k)
    ok = all(checks.values())
    print("\n    Autoverificacion Nivel 1:")
    for d, p in checks.items():
        print(f"      {'PASA ' if p else 'FALLA'} - {d}")

    # --- Nivel 2 -----------------------------------------------------------
    print("\n[4] Nivel 2: umbral de saturacion y sensibilidad")
    g_secop_largo = bd.cagr(SECOP_SERIE[2021], SECOP_SERIE[2025], 4)
    g_secop_corto = bd.cagr(SECOP_SERIE[2023], SECOP_SERIE[2025], 2)
    G = {}
    for nombre in rutas:
        if "SECOP" in nombre or "CONTRATACION" in nombre:
            G[nombre] = {"g": round(g_secop_corto, 4), "metodo": "historico medido",
                         "detalle": f"CAGR 2023-2025 de la serie real de SECOP II "
                                    f"({SECOP_SERIE[2023]:,} -> {SECOP_SERIE[2025]:,} filas/ano). "
                                    f"CAGR 2021-2025 = {g_secop_largo:.1%} se reporta como cota alta."}
        elif "IDEAM" in nombre or "ACUEDUCTO" in nombre:
            G[nombre] = {"g": 0.08, "metodo": "supuesto declarado",
                         "detalle": "No hay serie historica de tamano publicada. El volumen crece con el "
                                    "numero de estaciones-sensor activas, no con el tiempo. Se supone 8% anual "
                                    "de expansion de red. Es el numero mas debil del entregable y se declara."}
        else:
            G[nombre] = {"g": 0.03, "metodo": "supuesto documentado",
                         "detalle": "El archivo de un periodo no crece; crece el acumulado, y lo hace de forma "
                                    "LINEAL, no geometrica. Se usa 3% por el crecimiento de la muestra y de "
                                    "columnas entre rediseños. La formula sobreestima aqui: se declara."}

    # Los escenarios HIPOTETICOS de 8 y 16 GB usan una fraccion DECLARADA y justificada.
    # Usar la fraccion medida en este instante seria trasladar el estado momentaneo de
    # esta maquina (navegador, Docker, Teams abiertos) a un equipo hipotetico distinto.
    FRAC_DECLARADA = 0.35
    escenarios_M = {"8 GB": bd.memoria_util(8, FRAC_DECLARADA),
                    "16 GB": bd.memoria_util(16, FRAC_DECLARADA),
                    f"medido ({m_total:.0f} GB)": m_disp}
    if frac_so > 0.60:
        print(f"\n    !! ADVERTENCIA: el equipo tiene el {frac_so:.0%} de la RAM ocupada y solo")
        print(f"       {m_disp:.2f} GB libres de {m_total:.2f} GB. El escenario 'medido' sera pesimista.")
        print(f"       Para una medicion limpia: cierre navegador, Docker y Teams, y repita.")
        print(f"       Los escenarios de 8 y 16 GB NO se ven afectados (usan {FRAC_DECLARADA:.0%} declarado).")
    umbrales = {}
    for r in mediciones:
        f = r["fuente"]
        umbrales[f] = {}
        for et, mu in escenarios_M.items():
            if r["S0_proyectado_gb"] <= 0 or r["k"] <= 0:
                umbrales[f][et] = None
                continue
            umbrales[f][et] = round(bd.compute_threshold_periods(mu, r["k"], r["S0_proyectado_gb"], G[f]["g"]), 2)

    sens = {}
    for r in mediciones:
        f = r["fuente"]
        if r["S0_proyectado_gb"] <= 0:
            sens[f] = {}
            continue
        sens[f] = {f"{g:.0%}": round(bd.compute_threshold_periods(
            escenarios_M["16 GB"], r["k"], r["S0_proyectado_gb"], g), 1)
            for g in (0.01, 0.02, 0.04, 0.08, 0.16, 0.32)}
    # Sensibilidad a la FRACCION consumida por el SO (paso 2.2: "justifique que
    # proporcion considera realmente disponible y por que")
    sens_frac = {}
    _ref = max(mediciones, key=lambda m: m["memoria_necesaria_gb"])
    for _fr in (0.25, 0.35, 0.50, round(frac_so, 2)):
        _lbl = f"{_fr:.0%}" + (" (medido en este equipo)" if abs(_fr - round(frac_so, 2)) < 1e-9 else "")
        sens_frac[_lbl] = {}
        for _ram in (8, 16, 32):
            _mu = _ram * (1 - _fr)
            if _ref["S0_proyectado_gb"] <= 0:
                sens_frac[_lbl][f"{_ram} GB"] = None; continue
            sens_frac[_lbl][f"{_ram} GB"] = round(bd.compute_threshold_periods(
                _mu, _ref["k"], _ref["S0_proyectado_gb"], G[_ref["fuente"]]["g"]), 1)
    sens_frac_fuente = _ref["fuente"]

    sens_k = {}
    base = mediciones[0]
    for mult in (0.5, 1.0, 2.0, 4.0):
        sens_k[f"k x{mult}"] = round(bd.compute_threshold_periods(
            escenarios_M["16 GB"], base["k"] * mult, base["S0_proyectado_gb"], G[base["fuente"]]["g"]), 1)

    # --- Diccionario de la GEIH: columnas DECLARADAS vs columnas LEIDAS -----
    # Guia linea 146: "Antes de cargar nada, abra el diccionario de variables y
    # anote cuantas columnas tiene el archivo que va a usar."
    dicc_path = os.path.join(RAIZ, "config_geih.json")
    dicc = {}
    if os.path.exists(dicc_path):
        dicc = json.load(open(dicc_path, encoding="utf-8"))
    geih_key = next((k for k in rutas if "GEIH" in k or "HOGARES" in k), None)
    if geih_key:
        leidas = next(m["columnas"] for m in mediciones if m["fuente"] == geih_key)
        declaradas = dicc.get("columnas_segun_diccionario")
        dicc_res = {"periodo": dicc.get("periodo", "no declarado"),
                    "columnas_segun_diccionario": declaradas,
                    "columnas_leidas_por_pandas": leidas,
                    "coinciden": (declaradas == leidas) if declaradas else None,
                    "archivo": os.path.basename(rutas[geih_key])}
        print("\n[3b] Diccionario de la GEIH (paso 2.3.4 de la guia)")
        if declaradas is None:
            print("     Sin declarar. Edite config_geih.json con el periodo y el numero de")
            print("     columnas que dice el diccionario ANTES de cargar el archivo.")
        else:
            print(f"     periodo {dicc_res['periodo']} · diccionario dice {declaradas} columnas · "
                  f"pandas lee {leidas} · {'COINCIDEN' if dicc_res['coinciden'] else 'NO COINCIDEN'}")
            if not dicc_res["coinciden"]:
                print("     La discrepancia ES el hallazgo de variedad: reportela, no la corrija.")
    else:
        dicc_res = {"periodo": "n/a"}

    # --- Caso del acueducto (reto de negocio): se mide SIEMPRE ------------
    print("\n[4b] Caso del acueducto (reto de negocio)")
    p_ac = os.path.join(SYN, "lecturas_acueducto.csv")
    if not os.path.exists(p_ac):
        bd.generate_meter_readings().to_csv(p_ac, index=False)
    k_ac, df_ac = bd.measure_expansion_factor(p_ac, low_memory=False)
    n_ac, s0_ac = len(df_ac), bd.get_file_size_gb(p_ac)
    bytes_fila = os.path.getsize(p_ac) / n_ac
    MEDIDORES, HORAS_ANIO = 5_000, 24 * 365
    filas_anio = MEDIDORES * HORAS_ANIO
    s0_anio = bytes_fila * filas_anio / 1024**3
    acue = {
        "medidores": MEDIDORES, "filas_muestra": n_ac, "k": round(k_ac, 2),
        "bytes_por_fila": round(bytes_fila, 1),
        "filas_por_anio": filas_anio,
        "S0_anio_gb": round(s0_anio, 3),
        "ram_necesaria_anio_gb": round(s0_anio * k_ac, 2),
        "ram_necesaria_mes_gb": round(s0_anio * k_ac / 12, 2),
        "s0_muestra_gb": round(s0_ac, 5),
    }
    for et, mu in escenarios_M.items():
        for g_ in (0.10, 0.20, 0.40):
            try:
                acue[f"t_{et}_g{int(g_*100)}"] = round(
                    bd.compute_threshold_periods(mu, k_ac, s0_anio, g_), 2)
            except ValueError:
                pass
    del df_ac
    print(f"    {MEDIDORES:,} medidores x {HORAS_ANIO:,} h = {filas_anio:,} filas/ano")
    print(f"    {acue['bytes_por_fila']} bytes/fila -> S0 = {acue['S0_anio_gb']} GB/ano, "
          f"k = {acue['k']} -> RAM necesaria = {acue['ram_necesaria_anio_gb']} GB")

    out = {
        "equipo": EQ,
        "fallos_de_carga": fallos,
        "geih_diccionario": dicc_res,
        "acueducto": acue,
        "generado": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "modo": modo, "filas_solicitadas": a.filas,
        "memoria": {"total_gb": round(m_total, 2), "disponible_gb": round(m_disp, 2),
                    "fraccion_consumida_so": round(frac_so, 4),
                    "fraccion_declarada_escenarios": FRAC_DECLARADA,
                    "equipo_cargado": bool(frac_so > 0.60),
                    "escenarios": {k: round(v, 2) for k, v in escenarios_M.items()}},
        "mediciones": mediciones, "extras": extras, "g": G,
        "umbrales": umbrales, "sensibilidad_g": sens, "sensibilidad_k": sens_k,
        "sensibilidad_fraccion": sens_frac, "sensibilidad_fraccion_fuente": sens_frac_fuente,
        "checks_nivel1": checks,
        "evidencia_portal": {
            "secop_serie_anual": SECOP_SERIE, "secop_total_filas": SECOP_TOTAL_FILAS,
            "secop_nulos_fecha_publicacion": SECOP_NULOS_FECHA_PUB,
            "ideam_registros_por_dia": IDEAM_REGISTROS_DIA,
            "g_secop_2021_2025": round(g_secop_largo, 4), "g_secop_2023_2025": round(g_secop_corto, 4),
        },
    }
    with open(os.path.join(RES, "_resultados.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, default=str)

    # --- archivado de la corrida ------------------------------------------
    dir_corrida = os.path.join(RES, "corridas", EQ["etiqueta"])
    os.makedirs(dir_corrida, exist_ok=True)
    sello = pd.Timestamp.now().strftime("%Y%m%d-%H%M")
    with open(os.path.join(dir_corrida, f"{sello}.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, default=str)
    dfm[cols9].to_csv(os.path.join(dir_corrida, f"{sello}_mediciones.csv"), index=False)
    print(f"\n    Corrida archivada en resultados/corridas/{EQ['etiqueta']}/{sello}.json")

    for f, d in umbrales.items():
        print(f"    {f:<32} " + "  ".join(
            f"{k}: {'   n/a  ' if v is None else format(v, '>7.2f')} periodos" for k, v in d.items()))
    if fallos:
        print("\n    PUNTOS DE QUIEBRE REGISTRADOS (resultado valido, no fallo):")
        for n, d in fallos.items():
            print(f"      {n}: murio con {d['filas_en_el_archivo']:,} filas "
                  f"({d['tamano_gb']} GB) y M = {d['M_disponible_gb']} GB")
    print(f"\n    resultados/mediciones.csv y resultados/_resultados.json escritos.")
    print("\n[5] Ahora ejecute:  python scripts/generar_entregables.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
