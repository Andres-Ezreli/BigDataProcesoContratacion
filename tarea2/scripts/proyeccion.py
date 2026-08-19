#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T3 - Proyeccion de almacenamiento y factor de replica
IFPN0025 Big Data e Ingenieria de Datos - Universidad Ean - Sesion 3

Fuente unica del equipo: SECOP II (portal datos.gov.co, conjunto p6dx-8zbt).

Este script NO contiene ninguna cifra de resultado escrita a mano.
Solo contiene los DATOS DE ENTRADA (bloque ENTRADAS) y las formulas.
Cualquier persona que reemplace el bloque ENTRADAS con los datos de su
propia ficha T1 obtiene su propia proyeccion con el mismo codigo.

Uso:
    python scripts/proyeccion.py

Salidas (se escriben en resultados/):
    proyeccion.csv    tabla principal R = 1, 2, 3
    bloques.csv       conteo de bloques HDFS por escenario de particion
    proyeccion.json   todos los valores intermedios, para trazabilidad
    tabla.md          las tablas ya formateadas en Markdown
"""

from __future__ import annotations

import csv
import json
import math
import os
from datetime import date

# ---------------------------------------------------------------------------
# ENTRADAS  -- todo lo que hay que cambiar para rehacer el calculo con otra
#              fuente esta aqui y solo aqui. Cada valor cita su origen.
# ---------------------------------------------------------------------------

ENTRADAS = {
    "fuente": "SECOP II - Procesos de Contratacion",
    "conjunto": "datos.gov.co / p6dx-8zbt",
    "formato_declarado": "CSV UTF-8 delimitado por comas, esquema plano, 59 columnas",
    "licencia": "Datos Abiertos de Colombia - Ley 1712 de 2014, uso libre con atribucion",

    # --- Volumen. Medido en S01: no se descargo la fuente completa, se midio
    #     una muestra real y se escalo por el conteo exacto de filas que
    #     devuelve la API (count(*)), verificado el 2026-07-24.
    "muestra_gib": 0.194714,        # os.path.getsize(secop_sample.csv) / 1024**3
    "muestra_filas": 200_000,       # filas de la muestra descargada
    "total_filas": 8_878_158,       # count(*) via API Socrata, 2026-07-24

    # --- Tasa de crecimiento. Serie anual real de filas publicadas en el
    #     portal (evidencia_portal.secop_serie_anual de la ficha T1).
    #     Se usa CAGR 2023-2025 porque 2021-2022 refleja la migracion de
    #     SECOP I a SECOP II, no crecimiento organico de la contratacion.
    "filas_anio_base": 1_531_557,   # 2023
    "filas_anio_final": 1_934_805,  # 2025
    "anios_cagr": 2,
    "meses_proyeccion": 12,

    # --- Cota alta declarada, para el analisis de sensibilidad.
    "g_anual_cota_alta": 0.312,     # CAGR 2021-2025 de la misma serie

    # --- Parametros de la plataforma.
    "bloque_mib": 128,              # dfs.blocksize por defecto en HDFS
    "factores_replica": [1, 2, 3],
    "nodos_datanode": 3,            # clus.ter levantado en la practica de hoy

    # --- Compresion columnar. Rango medido/observado en la literatura para
    #     CSV ancho con mucho texto repetido -> Parquet + Snappy.
    "compresion_conservadora": 5.0,
    "compresion_optimista": 10.0,

    # --- Precios. Consultados el 2026-08-03. Se declaran como supuesto de
    #     costo, no como medicion propia.
    "precio_nube_usd_gb_mes": 0.023,   # AWS S3 Standard, us-east-1, primer tramo 50 TB
    "precio_disco_usd_tb": 12.00,      # HDD empresarial SATA, punto medio del rango 9-15 USD/TB (mar-2026)
    "multiplicador_tco_onprem": 3.0,   # chasis, energia, refrigeracion, operacion (supuesto)
    "trm_cop_usd": 3144.14,            # TRM Banco de la Republica, 2026-08-03
}

BYTES_POR_GIB = 1024 ** 3
BYTES_POR_GB = 10 ** 9
BLOQUE_BYTES = ENTRADAS["bloque_mib"] * 1024 * 1024


# ---------------------------------------------------------------------------
# FORMULAS
# ---------------------------------------------------------------------------

def volumen_actual_gib(muestra_gib: float, muestra_filas: int, total_filas: int) -> float:
    """S0 = tamano de la muestra escalado al numero real de filas."""
    return muestra_gib * (total_filas / muestra_filas)


def cagr(valor_inicial: float, valor_final: float, anios: int) -> float:
    """Tasa de crecimiento anual compuesta."""
    return (valor_final / valor_inicial) ** (1 / anios) - 1


def anual_a_mensual(g_anual: float) -> float:
    """Tasa mensual equivalente: (1+g_a)^(1/12) - 1. NO es g_a/12."""
    return (1 + g_anual) ** (1 / 12) - 1


def volumen_proyectado(s0: float, g_mensual: float, meses: int) -> float:
    """Formula de la guia: V = S0 * (1 + g_m)^m."""
    return s0 * (1 + g_mensual) ** meses


def almacenamiento_fisico(volumen_logico: float, r: int) -> float:
    """Formula de la guia: fisico = logico * R."""
    return volumen_logico * r


def numero_bloques(tamano_bytes: float) -> int:
    """Formula de la guia: ceil(tamano_archivo / tamano_bloque)."""
    return math.ceil(tamano_bytes / BLOQUE_BYTES)


def tolerancia(r: int) -> int:
    """Formula de la guia: con factor R el sistema tolera R-1 nodos caidos."""
    return r - 1


def gib_a_gb(x_gib: float) -> float:
    """GiB binarios -> GB decimales. Los proveedores facturan en GB decimales."""
    return x_gib * BYTES_POR_GIB / BYTES_POR_GB


# ---------------------------------------------------------------------------
# CALCULO
# ---------------------------------------------------------------------------

def calcular(e: dict) -> dict:
    s0_gib = volumen_actual_gib(e["muestra_gib"], e["muestra_filas"], e["total_filas"])
    g_anual = cagr(e["filas_anio_base"], e["filas_anio_final"], e["anios_cagr"])
    g_mensual = anual_a_mensual(g_anual)
    v12_gib = volumen_proyectado(s0_gib, g_mensual, e["meses_proyeccion"])

    # --- tabla principal
    filas = []
    for r in e["factores_replica"]:
        fisico_gib = almacenamiento_fisico(v12_gib, r)
        fisico_gb = gib_a_gb(fisico_gib)
        nube_usd_anio = fisico_gb * e["precio_nube_usd_gb_mes"] * 12
        disco_usd = (fisico_gb / 1000) * e["precio_disco_usd_tb"]
        disco_tco_usd = disco_usd * e["multiplicador_tco_onprem"]
        filas.append({
            "R": r,
            "volumen_logico_12m_gib": round(v12_gib, 4),
            "almacenamiento_fisico_gib": round(fisico_gib, 4),
            "almacenamiento_fisico_gb": round(fisico_gb, 4),
            "bloques_128mib_archivo_unico": numero_bloques(v12_gib * BYTES_POR_GIB) * r,
            "nodos_caidos_tolerados": tolerancia(r),
            "min_datanodes_requeridos": r,
            "costo_nube_usd_anio": round(nube_usd_anio, 2),
            "costo_nube_cop_anio": round(nube_usd_anio * e["trm_cop_usd"], 0),
            "costo_disco_crudo_usd": round(disco_usd, 2),
            "costo_disco_tco_usd": round(disco_tco_usd, 2),
        })

    # --- bloques: dos politicas de particion, mismo dato
    corpus_base_gib = s0_gib
    incremento_total_gib = v12_gib - s0_gib
    incrementos = []
    for i in range(1, e["meses_proyeccion"] + 1):
        inc = s0_gib * ((1 + g_mensual) ** i - (1 + g_mensual) ** (i - 1))
        incrementos.append(inc)

    bloques_archivo_unico = numero_bloques(v12_gib * BYTES_POR_GIB)
    bloques_base = numero_bloques(corpus_base_gib * BYTES_POR_GIB)
    bloques_mensuales = [numero_bloques(x * BYTES_POR_GIB) for x in incrementos]
    bloques_particionado = bloques_base + sum(bloques_mensuales)

    # --- compresion columnar
    compresion = {}
    for etiqueta, factor in (("conservadora_5x", e["compresion_conservadora"]),
                             ("optimista_10x", e["compresion_optimista"])):
        comp_gib = v12_gib / factor
        compresion[etiqueta] = {
            "factor": factor,
            "volumen_logico_gib": round(comp_gib, 4),
            "fisico_r3_gib": round(comp_gib * 3, 4),
            "bloques_r1": numero_bloques(comp_gib * BYTES_POR_GIB),
            "costo_nube_r3_usd_anio": round(
                gib_a_gb(comp_gib * 3) * e["precio_nube_usd_gb_mes"] * 12, 2),
        }

    # --- sensibilidad a g
    sensibilidad = {}
    for etiqueta, ga in (("g_base_cagr_2023_2025", g_anual),
                         ("g_cota_alta_cagr_2021_2025", e["g_anual_cota_alta"]),
                         ("g_cero_fuente_congelada", 0.0)):
        gm = anual_a_mensual(ga)
        v = volumen_proyectado(s0_gib, gm, e["meses_proyeccion"])
        sensibilidad[etiqueta] = {
            "g_anual": round(ga, 6),
            "g_mensual": round(gm, 6),
            "v12_gib": round(v, 4),
            "fisico_r3_gib": round(v * 3, 4),
        }

    # --- punto de quiebre: a que volumen la tercera replica cuesta >= umbral,
    #     y en cuantos anos se alcanza ese volumen a la tasa medida
    umbrales_usd = [100, 1_000, 10_000]
    quiebre = {}
    v12_gb = gib_a_gb(v12_gib)
    for u in umbrales_usd:
        # costo anual de UNA replica adicional = V_gb * precio * 12
        v_gb = u / (e["precio_nube_usd_gb_mes"] * 12)
        factor = v_gb / v12_gb
        quiebre[f"umbral_{u}_usd_anio"] = {
            "volumen_logico_gb": round(v_gb, 1),
            "volumen_logico_tb": round(v_gb / 1000, 3),
            "veces_el_volumen_actual": round(factor, 1),
            "anios_a_g_base": round(math.log(factor) / math.log(1 + g_anual), 1),
            "anios_a_g_cota_alta": round(
                math.log(factor) / math.log(1 + e["g_anual_cota_alta"]), 1),
        }

    # --- comparacion de palancas: comprimir vs bajar el factor de replica
    base_r3 = v12_gib * 3
    palancas = {
        "csv_plano_R3_(base)": round(base_r3, 4),
        "csv_plano_R2_(bajar_una_replica)": round(v12_gib * 2, 4),
        "csv_plano_R1_(sin_replica)": round(v12_gib * 1, 4),
        "parquet_snappy_5x_R3_(comprimir)": round(v12_gib / e["compresion_conservadora"] * 3, 4),
        "parquet_snappy_10x_R3": round(v12_gib / e["compresion_optimista"] * 3, 4),
    }
    palancas_ahorro_pct = {k: round((1 - v / base_r3) * 100, 1) + 0.0 for k, v in palancas.items()}

    return {
        "generado": date.today().isoformat(),
        "entradas": e,
        "intermedios": {
            "S0_gib": round(s0_gib, 4),
            "S0_gb": round(gib_a_gb(s0_gib), 4),
            "factor_escalado_muestra": round(e["total_filas"] / e["muestra_filas"], 5),
            "g_anual": round(g_anual, 6),
            "g_mensual": round(g_mensual, 6),
            "comprobacion_(1+gm)^12": round((1 + g_mensual) ** 12, 6),
            "V12_gib": round(v12_gib, 4),
            "V12_gb": round(gib_a_gb(v12_gib), 4),
            "incremento_anual_gib": round(incremento_total_gib, 4),
            "incremento_mes_1_mib": round(incrementos[0] * 1024, 2),
            "incremento_mes_12_mib": round(incrementos[-1] * 1024, 2),
        },
        "tabla_proyeccion": filas,
        "bloques": {
            "tamano_bloque_mib": e["bloque_mib"],
            "archivo_unico_r1": bloques_archivo_unico,
            "archivo_unico_r3": bloques_archivo_unico * 3,
            "particion_mensual_base_r1": bloques_base,
            "particion_mensual_nuevos_r1": sum(bloques_mensuales),
            "particion_mensual_total_r1": bloques_particionado,
            "particion_mensual_total_r3": bloques_particionado * 3,
            "sobrecosto_bloques_por_particionar": bloques_particionado - bloques_archivo_unico,
            "bloques_por_archivo_mensual": bloques_mensuales,
        },
        "compresion": compresion,
        "sensibilidad_g": sensibilidad,
        "punto_de_quiebre_tercera_replica": quiebre,
        "palancas_de_ahorro_gib": palancas,
        "palancas_de_ahorro_pct_vs_csv_R3": palancas_ahorro_pct,
    }


# ---------------------------------------------------------------------------
# SALIDAS
# ---------------------------------------------------------------------------

def escribir(res: dict, destino: str) -> None:
    os.makedirs(destino, exist_ok=True)

    with open(os.path.join(destino, "proyeccion.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(res["tabla_proyeccion"][0].keys()))
        w.writeheader()
        w.writerows(res["tabla_proyeccion"])

    b = res["bloques"]
    with open(os.path.join(destino, "bloques.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["escenario", "bloques_R1", "bloques_R2", "bloques_R3"])
        w.writerow(["archivo unico consolidado",
                    b["archivo_unico_r1"], b["archivo_unico_r1"] * 2, b["archivo_unico_r1"] * 3])
        w.writerow(["particion mensual (corpus base + 12 archivos)",
                    b["particion_mensual_total_r1"],
                    b["particion_mensual_total_r1"] * 2,
                    b["particion_mensual_total_r1"] * 3])

    with open(os.path.join(destino, "proyeccion.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    # tabla en markdown, por si se quiere pegar en un documento aparte
    i = res["intermedios"]
    lineas = [
        "| R | Volumen logico 12 m (GiB) | Almacenamiento fisico (GiB) | Replicas de bloque de 128 MiB | Nodos caidos tolerados | DataNodes minimos | Costo nube USD/ano |",
        "|---|---|---|---|---|---|---|",
    ]
    for fila in res["tabla_proyeccion"]:
        lineas.append(
            f"| {fila['R']} | {fila['volumen_logico_12m_gib']:.4f} | "
            f"{fila['almacenamiento_fisico_gib']:.4f} | {fila['bloques_128mib_archivo_unico']} | "
            f"{fila['nodos_caidos_tolerados']} | {fila['min_datanodes_requeridos']} | "
            f"{fila['costo_nube_usd_anio']:.2f} |"
        )
    with open(os.path.join(destino, "tabla.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")


def imprimir(res: dict) -> None:
    i = res["intermedios"]
    print("=" * 78)
    print("T3 - PROYECCION DE ALMACENAMIENTO Y FACTOR DE REPLICA")
    print(f"Fuente: {res['entradas']['fuente']}   Generado: {res['generado']}")
    print("=" * 78)
    print("\n-- Datos de entrada")
    print(f"  Muestra medida        : {res['entradas']['muestra_gib']} GiB / "
          f"{res['entradas']['muestra_filas']:,} filas")
    print(f"  Filas fuente completa : {res['entradas']['total_filas']:,}")
    print(f"  Factor de escalado    : {i['factor_escalado_muestra']}")
    print("\n-- Paso 1: volumen actual")
    print(f"  S0 = {res['entradas']['muestra_gib']} x {i['factor_escalado_muestra']} "
          f"= {i['S0_gib']} GiB  ({i['S0_gb']} GB decimales)")
    print("\n-- Paso 2: tasa de crecimiento")
    print(f"  g anual  (CAGR 2023-2025) = {i['g_anual']:.6f}  = {i['g_anual']*100:.3f} %")
    print(f"  g mensual = (1+g_a)^(1/12)-1 = {i['g_mensual']:.6f} = {i['g_mensual']*100:.4f} %")
    print(f"  comprobacion (1+g_m)^12 = {i['comprobacion_(1+gm)^12']} (debe dar 1+g_anual)")
    print("\n-- Paso 3: volumen logico a 12 meses")
    print(f"  V12 = {i['S0_gib']} x (1+{i['g_mensual']:.6f})^12 = {i['V12_gib']} GiB "
          f"({i['V12_gb']} GB decimales)")
    print(f"  Dato nuevo en el ano: {i['incremento_anual_gib']} GiB")
    print(f"  Archivo mensual: mes 1 = {i['incremento_mes_1_mib']} MiB, "
          f"mes 12 = {i['incremento_mes_12_mib']} MiB")

    print("\n-- Paso 4: tabla de proyeccion por factor de replica")
    hdr = f"  {'R':>2} {'Fisico GiB':>12} {'Fisico GB':>11} {'Bloques':>9} {'Tolera':>7} {'USD/ano':>10} {'COP/ano':>13}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for f in res["tabla_proyeccion"]:
        print(f"  {f['R']:>2} {f['almacenamiento_fisico_gib']:>12.4f} "
              f"{f['almacenamiento_fisico_gb']:>11.4f} "
              f"{f['bloques_128mib_archivo_unico']:>9} "
              f"{f['nodos_caidos_tolerados']:>7} "
              f"{f['costo_nube_usd_anio']:>10.2f} "
              f"{f['costo_nube_cop_anio']:>13,.0f}")

    b = res["bloques"]
    print("\n-- Paso 5: bloques HDFS de 128 MiB")
    print(f"  archivo unico consolidado          : {b['archivo_unico_r1']} bloques (R=1), "
          f"{b['archivo_unico_r3']} replicas de bloque (R=3)")
    print(f"  particion mensual                  : {b['particion_mensual_total_r1']} bloques (R=1) "
          f"= {b['particion_mensual_base_r1']} del corpus base + "
          f"{b['particion_mensual_nuevos_r1']} de los 12 archivos nuevos")
    print(f"  sobrecosto en bloques por particionar: +{b['sobrecosto_bloques_por_particionar']}")

    print("\n-- Paso 6: alternativa - formato columnar comprimido")
    for k, v in res["compresion"].items():
        print(f"  {k:>18}: V12 = {v['volumen_logico_gib']:.4f} GiB -> "
              f"R=3 ocupa {v['fisico_r3_gib']:.4f} GiB, "
              f"{v['bloques_r1']} bloques, USD {v['costo_nube_r3_usd_anio']:.2f}/ano")

    print("\n-- Paso 7: sensibilidad a la tasa de crecimiento")
    for k, v in res["sensibilidad_g"].items():
        print(f"  {k:>28}: g_a={v['g_anual']:.4f}  V12={v['v12_gib']:.4f} GiB  "
              f"R=3 -> {v['fisico_r3_gib']:.4f} GiB")

    print("\n-- Paso 8: punto de quiebre de la tercera replica")
    print("  Volumen logico al cual la 3a replica cuesta, por si sola, el umbral indicado,")
    print("  y anos que tarda la fuente en llegar ahi desde el volumen a 12 meses:")
    for k, v in res["punto_de_quiebre_tercera_replica"].items():
        print(f"  {k:>22}: {v['volumen_logico_tb']:>7} TB  "
              f"(x{v['veces_el_volumen_actual']} el volumen actual)  "
              f"{v['anios_a_g_base']:>5} anos a g base | "
              f"{v['anios_a_g_cota_alta']:>5} anos a la cota alta")

    print("\n-- Paso 9: que palanca ahorra mas, comprimir o bajar el factor de replica")
    for k, v in res["palancas_de_ahorro_gib"].items():
        pct = res["palancas_de_ahorro_pct_vs_csv_R3"][k]
        print(f"  {k:>34}: {v:>9.4f} GiB   ahorro vs CSV R=3: {pct:>6.1f} %")
    print()


if __name__ == "__main__":
    aqui = os.path.dirname(os.path.abspath(__file__))
    destino = os.path.join(os.path.dirname(aqui), "resultados")
    resultado = calcular(ENTRADAS)
    imprimir(resultado)
    escribir(resultado, destino)
    print(f"Escrito en: {destino}")
