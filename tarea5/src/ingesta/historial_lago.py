#!/usr/bin/env python3
"""
Historial completo del lago: todo lo que le ha pasado a cada objeto.

Es el equivalente escrito y verificable de la captura de pantalla de la
consola de MinIO. Una captura muestra un momento; esto muestra la historia
entera, con los VersionId reales, y se puede volver a generar cuando sea.

Lo que produce:
  docs/historial_lago.md    linea de tiempo + historial objeto por objeto
  docs/historial_lago.json  lo mismo, para procesarlo

Que trae cada version:
  - el VersionId que asigno el almacenamiento
  - si es la version actual o una anterior
  - el tamano y el instante exacto
  - el sha256 que guardo la ingesta en los metadatos, cuando lo hay
  - si es un marcador de borrado en vez de un contenido

Uso:
    python3 src/ingesta/historial_lago.py
    python3 src/ingesta/historial_lago.py --sin-metadatos   # mas rapido
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun  # noqa: E402
from botocore.exceptions import ClientError  # noqa: E402


def eventos_del_cubo(s3, cubo, con_metadatos=True):
    """Todas las versiones y marcadores de borrado del cubo, paginando.

    Devuelve una lista plana de eventos. Cada escritura es un evento y cada
    borrado tambien: esa lista ES la historia del cubo.
    """
    eventos = []
    paginador = s3.get_paginator("list_object_versions")
    for pagina in paginador.paginate(Bucket=cubo):
        for v in pagina.get("Versions", []):
            eventos.append({
                "cubo": cubo,
                "clave": v["Key"],
                "tipo": "escritura",
                "version_id": v["VersionId"],
                "es_actual": bool(v["IsLatest"]),
                "bytes": v["Size"],
                "instante": v["LastModified"].isoformat(),
                "sha256": None,
            })
        for m in pagina.get("DeleteMarkers", []):
            eventos.append({
                "cubo": cubo,
                "clave": m["Key"],
                "tipo": "borrado",
                "version_id": m["VersionId"],
                "es_actual": bool(m["IsLatest"]),
                "bytes": None,
                "instante": m["LastModified"].isoformat(),
                "sha256": None,
            })

    if con_metadatos:
        for ev in eventos:
            if ev["tipo"] != "escritura":
                continue
            try:
                meta = s3.head_object(Bucket=cubo, Key=ev["clave"],
                                      VersionId=ev["version_id"])
                ev["sha256"] = (meta.get("Metadata") or {}).get("sha256")
            except ClientError:
                pass

    eventos.sort(key=lambda e: (e["instante"], e["clave"]))
    return eventos


def _clasificar(clave):
    """Que es esta clave dentro del lago."""
    if clave == "_LEEME.txt":
        return "documentacion del cubo"
    if clave.startswith("_evidencia/"):
        return "sonda de la prueba de versionado"
    if clave.startswith("_"):
        return "metadato del lago"
    if clave.endswith(".manifiesto.json"):
        return "manifiesto (ficha tecnica)"
    return "DATO del proyecto"


def _corto(vid, n=14):
    if not vid or vid == "null":
        return "(sin version)"
    return vid if len(vid) <= n else vid[:n] + "..."


def informe_md(cfg, por_cubo, versionado):
    lineas = []
    A = lineas.append

    A("# Historial del lago")
    A("")
    A("<!-- GENERADO por src/ingesta/historial_lago.py. No editar a mano.")
    A("     Se regenera en cada corrida. -->")
    A("")
    A("Generado: `%s` (UTC)" % comun.ahora_utc().isoformat())
    A("")
    A("Este archivo es el equivalente escrito de la captura de pantalla de la")
    A("consola de MinIO. Una captura muestra un instante; esto muestra **todo lo")
    A("que le ha pasado a cada objeto**, con los `VersionId` reales que asigno el")
    A("almacenamiento. Se puede contrastar contra la consola web abriendo")
    A("<http://localhost:9001> y mirando el historial de versiones de cualquier")
    A("clave: los identificadores tienen que ser los mismos.")
    A("")

    # ---- resumen
    A("## Resumen")
    A("")
    A("| Capa | Cubo | Versionado | Claves | Eventos | Bytes |")
    A("|---|---|---|---|---|---|")
    for capa in cfg["almacenamiento"]["capas"]:
        cubo = comun.nombre_cubo(cfg, capa)
        evs = por_cubo.get(cubo, [])
        claves = set(e["clave"] for e in evs)
        total = sum(e["bytes"] or 0 for e in evs if e["es_actual"])
        A("| %s | `%s` | %s | %d | %d | %s |" % (
            capa, cubo,
            "**activo**" if versionado.get(cubo) else "no",
            len(claves), len(evs), comun.humano(total)))
    A("")

    # ---- linea de tiempo
    todos = [e for evs in por_cubo.values() for e in evs]
    todos.sort(key=lambda e: (e["instante"], e["clave"]))

    A("## Línea de tiempo")
    A("")
    A("Todo lo que ha ocurrido en el lago, en orden. Cada fila es una escritura")
    A("o un borrado. Nada se ha editado: en un almacen de objetos versionado no")
    A("existe la operacion *modificar*, solo *escribir una version nueva*.")
    A("")
    A("| # | Instante (UTC) | Cubo | Clave | Qué pasó | VersionId | Bytes |")
    A("|---|---|---|---|---|---|---|")
    for i, e in enumerate(todos, 1):
        A("| %d | `%s` | `%s` | `%s` | %s | `%s` | %s |" % (
            i, e["instante"][:19], e["cubo"], e["clave"],
            "escritura" if e["tipo"] == "escritura" else "**borrado**",
            _corto(e["version_id"]),
            comun.humano(e["bytes"]) if e["bytes"] is not None else "—"))
    A("")

    # ---- historial por objeto
    A("## Historial objeto por objeto")
    A("")
    for capa in cfg["almacenamiento"]["capas"]:
        cubo = comun.nombre_cubo(cfg, capa)
        evs = por_cubo.get(cubo, [])
        A("### `%s`" % cubo)
        A("")
        if not evs:
            A("_Vacío._")
            A("")
            continue
        claves = {}
        for e in evs:
            claves.setdefault(e["clave"], []).append(e)
        for clave in sorted(claves):
            historia = sorted(claves[clave], key=lambda e: e["instante"],
                              reverse=True)
            A("#### `%s`" % clave)
            A("")
            A("%s · **%d versión(es)**" % (_clasificar(clave), len(historia)))
            A("")
            A("| VersionId | ¿Actual? | Qué es | Bytes | Instante (UTC) | sha256 |")
            A("|---|---|---|---|---|---|")
            for e in historia:
                A("| `%s` | %s | %s | %s | `%s` | %s |" % (
                    e["version_id"],
                    "**sí**" if e["es_actual"] else "no",
                    "escritura" if e["tipo"] == "escritura" else "**marcador de borrado**",
                    comun.humano(e["bytes"]) if e["bytes"] is not None else "—",
                    e["instante"][:19],
                    ("`%s…`" % e["sha256"][:16]) if e["sha256"] else "—"))
            A("")
            if len(historia) > 1:
                A("> Esta clave se escribió más de una vez. La versión anterior")
                A("> sigue siendo recuperable con `GetObject` indicando su")
                A("> `VersionId`: eso es lo que demuestra el criterio 3.")
                A("")

    # ---- lectura
    A("## Cómo leer esto")
    A("")
    A("- **El dato del proyecto tiene una sola versión.** Si alguna clave")
    A("  marcada como *DATO del proyecto* apareciera con dos, alguien habría")
    A("  sobrescrito la capa cruda y la regla de inmutabilidad estaría rota.")
    A("- **La sonda sí tiene varias**, y es a propósito: existe únicamente para")
    A("  demostrar que sobrescribir no pierde nada.")
    A("- **Un marcador de borrado no borra.** Oculta la clave y deja el")
    A("  contenido accesible por `VersionId`.")
    A("")
    A("## Cómo reproducirlo")
    A("")
    A("```bash")
    A("python3 src/ingesta/historial_lago.py")
    A("```")
    return "\n".join(lineas) + "\n"


def main():
    p = argparse.ArgumentParser(
        description="Vuelca el historial completo de versiones del lago")
    p.add_argument("--config", help="ruta a lago.json")
    p.add_argument("--sin-metadatos", action="store_true",
                   help="no consultar el sha256 de cada version")
    args = p.parse_args()

    cfg = comun.cargar_config(args.config)
    s3 = comun.cliente_s3(cfg)

    print("=" * 68)
    print("HISTORIAL DEL LAGO")
    print("=" * 68)

    if not comun.esperar_almacenamiento(s3):
        raise SystemExit("No hay respuesta del almacenamiento. "
                         "Levantelo con:  docker compose up -d")

    por_cubo = {}
    versionado = {}
    for capa in cfg["almacenamiento"]["capas"]:
        cubo = comun.nombre_cubo(cfg, capa)
        try:
            s3.head_bucket(Bucket=cubo)
        except ClientError:
            print("[--] %-16s no existe todavia" % cubo)
            por_cubo[cubo] = []
            versionado[cubo] = False
            continue
        versionado[cubo] = comun.versionado_activo(s3, cubo)
        evs = eventos_del_cubo(s3, cubo, not args.sin_metadatos)
        por_cubo[cubo] = evs
        claves = len(set(e["clave"] for e in evs))
        print("[ok] %-16s %d clave(s), %d evento(s), versionado %s"
              % (cubo, claves, len(evs),
                 "ACTIVO" if versionado[cubo] else "no"))

    comun.DOCS.mkdir(parents=True, exist_ok=True)
    with open(comun.DOCS / "historial_lago.md", "w", encoding="utf-8") as fh:
        fh.write(informe_md(cfg, por_cubo, versionado))
    with open(comun.DOCS / "historial_lago.json", "w", encoding="utf-8") as fh:
        json.dump({
            "_generado_por": "src/ingesta/historial_lago.py",
            "_no_editar": "Se regenera en cada corrida.",
            "_que_es": ("Historial completo de versiones del lago: el "
                        "equivalente escrito de la captura de la consola."),
            "instante_utc": comun.ahora_utc().isoformat(),
            "versionado_por_cubo": versionado,
            "eventos_por_cubo": por_cubo,
        }, fh, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in por_cubo.values())
    print("\n[ok] %d evento(s) en total" % total)
    print("     docs/historial_lago.md")
    print("     docs/historial_lago.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
