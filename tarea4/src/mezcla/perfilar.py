#!/usr/bin/env python3
"""
Paso previo a la estimacion: medir la fuente en lugar de suponerla.

Recorre el archivo de entrada una sola vez y escribe docs/perfil.json con lo
que la estimacion de la mezcla necesita: cuantos registros hay, cuantas claves
distintas, cuanto pesa en bytes cada par que emitiria el map y como esta
repartida la carga entre claves.

No estima nada: solo mide. La estimacion vive en estimar.py.

Uso:
    python3 src/mezcla/perfilar.py
    python3 src/mezcla/perfilar.py --entrada datos/fuente_real.csv
"""

import argparse
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "src", "mapreduce"))

from comun import formatear, leer_par  # noqa: E402


def java_hash(cadena):
    """Reproduce String.hashCode de Java.

    Se necesita porque el particionador por defecto de Hadoop reparte con
    (clave.hashCode() & MAX_INT) % numReducers. Simularlo aqui permite
    predecir la carga de cada reductor antes de ejecutar nada.
    """
    h = 0
    for ch in cadena:
        h = (31 * h + ord(ch)) & 0xFFFFFFFF
    if h >= 0x80000000:  # a entero con signo de 32 bits
        h -= 0x100000000
    return h


def perfilar(ruta, cfg_fuente):
    total = validos = descartados = 0
    bytes_clave = 0
    bytes_valor_map = 0
    por_clave = {}

    with open(ruta, "r", encoding="utf-8", errors="replace") as fh:
        for linea in fh:
            total += 1
            par = leer_par(linea, cfg_fuente)
            if par is None:
                descartados += 1
                continue
            clave, valor = par
            validos += 1
            bytes_clave += len(clave.encode("utf-8"))
            bytes_valor_map += len(formatear(valor).encode("utf-8")) + 2  # "\t1"
            acc = por_clave.setdefault(clave, [0.0, 0])
            acc[0] += valor
            acc[1] += 1

    if validos == 0:
        raise SystemExit(
            "Cero registros validos. Revisen indice_clave, indice_valor y "
            "delimitador en src/mapreduce/esquema.json."
        )

    distribucion = sorted(
        ({"clave": k, "conteo": v[1], "suma": v[0],
          "bytes_clave": len(k.encode("utf-8")),
          "hash_java": java_hash(k)}
         for k, v in por_clave.items()),
        key=lambda d: -d["conteo"],
    )
    conteos = [d["conteo"] for d in distribucion]
    K = len(distribucion)

    return {
        "_nota": "Generado por src/mezcla/perfilar.py. No editar a mano.",
        "entrada": os.path.relpath(ruta, RAIZ).replace("\\", "/"),
        "bytes_entrada": os.path.getsize(ruta),
        "registros_leidos": total,
        "registros_validos": validos,
        "registros_descartados": descartados,
        "claves_distintas": K,
        "bytes_clave_promedio": bytes_clave / validos,
        "bytes_valor_map_promedio": bytes_valor_map / validos,
        "sesgo": {
            "conteo_maximo": conteos[0],
            "conteo_minimo": conteos[-1],
            "conteo_promedio": validos / K,
            "razon_max_promedio": conteos[0] / (validos / K),
            "participacion_clave_mayor": conteos[0] / validos,
            "participacion_top3": sum(conteos[:3]) / validos,
        },
        "distribucion": distribucion,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default=None,
                    help="ruta de la fuente; por defecto la de esquema.json")
    ap.add_argument("--esquema",
                    default=os.path.join(RAIZ, "src", "mapreduce", "esquema.json"))
    ap.add_argument("--salida", default=os.path.join(RAIZ, "docs", "perfil.json"))
    args = ap.parse_args()

    with open(args.esquema, "r", encoding="utf-8") as fh:
        esquema = json.load(fh)
    ruta = args.entrada or os.path.join(RAIZ, esquema["fuente"]["ruta_local"])

    perfil = perfilar(ruta, esquema["fuente"])
    os.makedirs(os.path.dirname(args.salida), exist_ok=True)
    with open(args.salida, "w", encoding="utf-8") as fh:
        json.dump(perfil, fh, ensure_ascii=False, indent=2)

    s = perfil["sesgo"]
    print("Fuente:              %s (%.2f MB)"
          % (perfil["entrada"], perfil["bytes_entrada"] / 1024 ** 2))
    print("Registros validos:   %d  (descartados: %d)"
          % (perfil["registros_validos"], perfil["registros_descartados"]))
    print("Claves distintas:    %d" % perfil["claves_distintas"])
    print("Clave mas frecuente: %s con %.1f%% de los registros"
          % (perfil["distribucion"][0]["clave"], 100 * s["participacion_clave_mayor"]))
    print("Razon max/promedio:  %.1fx" % s["razon_max_promedio"])
    print("\n[ok] Escrito en %s" % os.path.relpath(args.salida, RAIZ))


if __name__ == "__main__":
    main()
