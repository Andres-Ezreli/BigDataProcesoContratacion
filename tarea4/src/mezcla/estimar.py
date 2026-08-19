#!/usr/bin/env python3
"""
Estimacion del volumen de la mezcla, contraste contra el contador real y
analisis de sesgo de la clave.

Consume tres archivos y no pide nada mas:
    src/mapreduce/esquema.json  parametros de la fuente y del cluster
    docs/perfil.json            medicion de la fuente (perfilar.py)
    src/mezcla/medicion.json    contadores reales del trabajo ejecutado

Escribe docs/tabla_mezcla.md, que es la tabla que se pega en el informe.
Mientras los contadores esten en null, la columna de contraste queda marcada
como pendiente y el resto se calcula igual.

Uso:
    python3 src/mezcla/estimar.py
"""

import json
import math
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "src", "mapreduce"))

from comun import formatear  # noqa: E402

MB = 1024 ** 2


# --------------------------------------------------------------------------
# Modelo
# --------------------------------------------------------------------------

def pares_esperados(n, m):
    """Numero esperado de mappers que ven al menos un registro de una clave
    que aparece n veces, repartida al azar entre m mappers.

    Cada mapper falla en ver la clave con probabilidad (1 - 1/m)^n, asi que
    la probabilidad de verla es el complemento, y la esperanza sobre los m
    mappers es la suma. Con el combinador, cada mapper que ve la clave emite
    exactamente un par por ella: por eso este numero es, directamente, los
    pares que esa clave aporta a la mezcla.

    Supone reparto aleatorio. Si la fuente viene ordenada por la clave, los
    splits son contiguos y el numero real sera menor: el combinador rinde
    mas. Es un supuesto conservador.
    """
    if m <= 1:
        return 1.0
    return m * (1.0 - (1.0 - 1.0 / m) ** n)


def bytes_valor_agregado(suma, conteo):
    """Bytes del valor serializado 'suma \t conteo'."""
    return len(formatear(suma).encode("utf-8")) + 1 + len(str(int(round(conteo))))


def estimar_con_combinador(distribucion, m, overhead):
    """Devuelve (pares, bytes) esperados tras el combinador."""
    pares_tot = 0.0
    bytes_tot = 0.0
    for d in distribucion:
        pares = pares_esperados(d["conteo"], m)
        suma_parcial = d["suma"] / pares
        conteo_parcial = max(1.0, d["conteo"] / pares)
        b = d["bytes_clave"] + bytes_valor_agregado(suma_parcial, conteo_parcial)
        pares_tot += pares
        bytes_tot += pares * (b + overhead)
    return pares_tot, bytes_tot


def carga_reductores(items, reducers):
    """Reparte (clave, conteo, hash) entre reductores como el HashPartitioner
    por defecto: (hashCode & MAX_INT) % numReducers."""
    carga = [0] * reducers
    for clave, conteo, h in items:
        idx = (h & 0x7FFFFFFF) % reducers
        carga[idx] += conteo
    return carga


def java_hash(cadena):
    h = 0
    for ch in cadena:
        h = (31 * h + ord(ch)) & 0xFFFFFFFF
    if h >= 0x80000000:
        h -= 0x100000000
    return h


# --------------------------------------------------------------------------
# Informe
# --------------------------------------------------------------------------

def fmt_bytes(b):
    if b is None:
        return "pendiente"
    if b >= MB:
        return "%.2f MB" % (b / MB)
    if b >= 1024:
        return "%.1f KB" % (b / 1024)
    return "%d B" % b


def fmt_num(n):
    if n is None:
        return "pendiente"
    return "{:,.0f}".format(n).replace(",", ".")


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mappers", type=int, default=None,
                    help="fuerza M para analisis de sensibilidad")
    ap.add_argument("--reducers", type=int, default=None,
                    help="fuerza R para el analisis de particion")
    args = ap.parse_args()

    with open(os.path.join(RAIZ, "src", "mapreduce", "esquema.json"),
              encoding="utf-8") as fh:
        esquema = json.load(fh)
    with open(os.path.join(RAIZ, "docs", "perfil.json"), encoding="utf-8") as fh:
        perfil = json.load(fh)
    with open(os.path.join(RAIZ, "src", "mezcla", "medicion.json"),
              encoding="utf-8") as fh:
        medicion = json.load(fh)

    cl = esquema["cluster"]
    overhead = esquema["estimacion"]["overhead_por_registro_bytes"]
    N = perfil["registros_validos"]
    K = perfil["claves_distintas"]
    dist = perfil["distribucion"]

    # Numero de mappers: el que reporte el trabajo; si no, uno por bloque.
    M = (args.mappers
         or medicion["ejecucion"].get("mappers_reportados")
         or cl.get("mappers")
         or max(1, math.ceil(perfil["bytes_entrada"] / (cl["tamano_bloque_mb"] * MB))))
    # El analisis de particion no tiene sentido con un solo reductor: con R=1
    # todo cae en el mismo sitio por definicion y el sesgo queda invisible.
    # Por eso se analiza siempre con al menos dos.
    R = (args.reducers or medicion["ejecucion"].get("reducers_usados")
         or cl.get("reducers", 1))
    R_analisis = max(R, 2)

    # ---- Sin combinador -------------------------------------------------
    par_medio_sin = (perfil["bytes_clave_promedio"]
                     + perfil["bytes_valor_map_promedio"] + overhead)
    pares_sin = N
    bytes_sin = N * par_medio_sin

    # ---- Con combinador -------------------------------------------------
    # Cota superior segun la regla del enunciado: cada nodo ve todas las claves.
    par_agregado_medio = (
        sum(d["bytes_clave"] + bytes_valor_agregado(d["suma"] / M, d["conteo"] / M)
            for d in dist) / K) + overhead
    pares_cota = K * M
    bytes_cota = pares_cota * par_agregado_medio
    # Estimacion esperada, que si tiene en cuenta que las claves raras no
    # aparecen en todos los mappers.
    pares_con, bytes_con = estimar_con_combinador(dist, M, overhead)

    # ---- Contadores reales ----------------------------------------------
    real_sin = medicion["sin_combinador"]["reduce_shuffle_bytes"]
    real_con = medicion["con_combinador"]["reduce_shuffle_bytes"]

    def error(est, real):
        if real in (None, 0):
            return None
        return (est - real) / real

    # ---- Sesgo -----------------------------------------------------------
    items = [(d["clave"], d["conteo"], d.get("hash_java") or java_hash(d["clave"]))
             for d in dist]
    carga = carga_reductores(items, R_analisis)
    carga_max = max(carga)
    carga_ideal = N / R_analisis

    # Rediseno con salting: cada clave se parte en S cubos.
    S = max(2, math.ceil(dist[0]["conteo"] / (N / K)))
    dist_sal = []
    for d in dist:
        for b in range(S):
            clave_b = "%s#%d" % (d["clave"], b)
            dist_sal.append({
                "clave": clave_b,
                "bytes_clave": len(clave_b.encode("utf-8")),
                "conteo": d["conteo"] / S,
                "suma": d["suma"] / S,
                "hash_java": java_hash(clave_b),
            })
    pares_sal, bytes_sal = estimar_con_combinador(dist_sal, M, overhead)
    carga_sal = carga_reductores(
        [(d["clave"], d["conteo"], d["hash_java"]) for d in dist_sal], R_analisis)
    carga_max_sal = max(carga_sal)

    # ---- Salida ----------------------------------------------------------
    L = []
    a = L.append
    a("<!-- Generado por src/mezcla/estimar.py. No editar a mano: vuelvan a ejecutarlo. -->")
    a("")
    a("## Parametros de la medicion")
    a("")
    a("| Parametro | Valor | Origen |")
    a("|---|---|---|")
    a("| Registros validos (N) | %s | `docs/perfil.json` |" % fmt_num(N))
    a("| Registros descartados | %s | encabezado y filas sin valor numerico |"
      % fmt_num(perfil["registros_descartados"]))
    a("| Claves distintas (K) | %s | `docs/perfil.json` |" % fmt_num(K))
    a("| Mappers (M) | %d | %s |" % (M, "reportado por el trabajo"
      if medicion["ejecucion"].get("mappers_reportados") else "estimado por bloques"))
    a("| Reductores (R) | %d | `esquema.json` / medicion |" % R)
    if R < 2:
        a("| Reductores del analisis de sesgo | %d | R=1 oculta el desbalance |" % R_analisis)
    a("| Bytes de clave, promedio | %.1f B | medido |" % perfil["bytes_clave_promedio"])
    a("| Bytes de valor del map, promedio | %.1f B | medido, incluye `\\t1` |"
      % perfil["bytes_valor_map_promedio"])
    a("| Sobrecarga por par | %d B | `esquema.json` |" % overhead)
    a("")
    a("## Estimacion contra medicion")
    a("")
    a("| Escenario | Pares en la mezcla | Bytes estimados | Reduce shuffle bytes real | Error |")
    a("|---|---|---|---|---|")
    e = error(bytes_sin, real_sin)
    a("| Sin combinador | %s | %s | %s | %s |" % (
        fmt_num(pares_sin), fmt_bytes(bytes_sin), fmt_bytes(real_sin),
        "pendiente" if e is None else "%+.1f %%" % (100 * e)))
    a("| Con combinador, cota superior | %s | %s | — | — |"
      % (fmt_num(pares_cota), fmt_bytes(bytes_cota)))
    e = error(bytes_con, real_con)
    a("| Con combinador, esperado | %s | %s | %s | %s |" % (
        fmt_num(pares_con), fmt_bytes(bytes_con), fmt_bytes(real_con),
        "pendiente" if e is None else "%+.1f %%" % (100 * e)))
    a("")
    a("**Ahorro estimado del combinador:** %.1f %% de los bytes de mezcla "
      "(%s frente a %s)." % (100 * (1 - bytes_con / bytes_sin),
                             fmt_bytes(bytes_con), fmt_bytes(bytes_sin)))
    if real_sin and real_con:
        a("")
        a("**Ahorro medido del combinador:** %.1f %% (%s frente a %s)."
          % (100 * (1 - real_con / real_sin), fmt_bytes(real_con), fmt_bytes(real_sin)))
    else:
        a("")
        a("**Ahorro medido:** pendiente. Peguen `reduce_shuffle_bytes` de las dos "
          "ejecuciones en `src/mezcla/medicion.json` y vuelvan a ejecutar este script.")
    if M <= 1:
        a("")
        a("> **Aviso.** El calculo asume %d mapper. Con un solo mapper el combinador "
          "agrega todo el dato de una vez y el ahorro sale maximo, pero no dice nada "
          "sobre el comportamiento distribuido. Para que la comparacion sea "
          "significativa, la entrada debe ocupar varios bloques o hay que forzar "
          "mas splits (ver `docs/T4_ejecucion.md`, seccion 4)." % M)
    a("")
    a("## Sesgo de la clave")
    a("")
    s = perfil["sesgo"]
    a("| Indicador | Valor |")
    a("|---|---|")
    a("| Clave mas frecuente | `%s` |" % dist[0]["clave"])
    a("| Su participacion | %.1f %% de los registros |"
      % (100 * s["participacion_clave_mayor"]))
    a("| Participacion de las tres mayores | %.1f %% |" % (100 * s["participacion_top3"]))
    a("| Registros por clave, promedio | %.1f |" % s["conteo_promedio"])
    a("| Razon entre la mayor y el promedio | %.1fx |" % s["razon_max_promedio"])
    a("| Carga del reductor mas cargado (R=%d) | %s registros |"
      % (R_analisis, fmt_num(carga_max)))
    a("| Carga ideal por reductor | %s registros |" % fmt_num(carga_ideal))
    a("| Desbalance | %.2fx la carga ideal |" % (carga_max / carga_ideal))
    a("")
    a("### Rediseno propuesto: clave compuesta con %d cubos" % S)
    a("")
    a("La clave pasa de `%s` a `%s#b` con `b = hash(registro) %% %d`, y un segundo "
      "trabajo vuelve a agregar por el prefijo." % (dist[0]["clave"], "clave", S))
    a("")
    a("| Indicador | Clave actual | Clave compuesta |")
    a("|---|---|---|")
    a("| Pares en la mezcla, con combinador | %s | %s |"
      % (fmt_num(pares_con), fmt_num(pares_sal)))
    a("| Bytes de mezcla estimados | %s | %s |" % (fmt_bytes(bytes_con), fmt_bytes(bytes_sal)))
    a("| Reductor mas cargado | %s | %s |" % (fmt_num(carga_max), fmt_num(carga_max_sal)))
    a("| Desbalance | %.2fx | %.2fx |"
      % (carga_max / carga_ideal, carga_max_sal / carga_ideal))
    a("")
    a("El compromiso queda a la vista: el reductor mas cargado baja %.0f %%, "
      "pero la mezcla sube %.0f %% y aparece una segunda etapa que antes no existia."
      % (100 * (1 - carga_max_sal / carga_max), 100 * (bytes_sal / bytes_con - 1)))
    a("")
    a("### Las diez claves mas pesadas")
    a("")
    a("| # | Clave | Registros | % del total | Pares con combinador (esperados) |")
    a("|---|---|---|---|---|")
    for i, d in enumerate(dist[:10], 1):
        a("| %d | `%s` | %s | %.2f %% | %.1f |"
          % (i, d["clave"], fmt_num(d["conteo"]), 100 * d["conteo"] / N,
             pares_esperados(d["conteo"], M)))

    texto = "\n".join(L) + "\n"
    destino = os.path.join(RAIZ, "docs", "tabla_mezcla.md")
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(texto)
    print(texto)
    print("[ok] Escrito en docs/tabla_mezcla.md")


if __name__ == "__main__":
    main()
