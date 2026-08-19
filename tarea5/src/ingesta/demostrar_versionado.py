#!/usr/bin/env python3
"""
Evidencia del versionado de la capa cruda (criterio de aceptacion 3).

No basta con decir que el versionado esta activo. Hay que demostrar que,
DESPUES de sobrescribir un objeto, la version anterior sigue ahi y se puede
leer. Eso es lo que hace este script, y deja la prueba escrita en
docs/evidencia_versionado.json y docs/evidencia_versionado.md.

POR QUE LA PRUEBA NO SE HACE SOBRE UN OBJETO DE DATOS
-----------------------------------------------------
Porque la capa cruda es inmutable. Sobrescribir el CSV del proyecto para
demostrar que se puede recuperar seria romper la regla que la tarea pide
sostener. La demostracion se hace sobre un objeto sonda propio, fuera del
prefijo de la fuente:

    _evidencia/prueba-de-versionado.txt

Empieza por guion bajo igual que _LEEME.txt: en este lago, la clave que
empieza por guion bajo no es dato, es metadato del lago. Ningun proceso que
lea la capa cruda por su convencion de rutas la va a tocar.

El script tambien COMPRUEBA, al final, que el objeto de datos real sigue
teniendo una sola version. Esa comprobacion es la otra mitad de la evidencia:
el versionado esta activo Y nadie ha sobrescrito el dato.

Uso:
    python3 src/ingesta/demostrar_versionado.py
    python3 src/ingesta/demostrar_versionado.py --activar   # si falta activarlo
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun  # noqa: E402
from botocore.exceptions import ClientError  # noqa: E402

CLAVE_SONDA = "_evidencia/prueba-de-versionado.txt"


def _texto(n, instante, extra):
    """Contenido de la sonda. Lleva el instante para que las dos versiones
    sean distinguibles a simple vista en el informe."""
    return (
        "PRUEBA DE VERSIONADO DE LA CAPA CRUDA\n"
        "=====================================\n"
        "Version logica del contenido: %d\n"
        "Escrita el: %s\n"
        "\n"
        "%s\n"
        "\n"
        "Este objeto NO es dato del proyecto. Es la sonda con la que se\n"
        "demuestra que el versionado del cubo funciona. Vive fuera del\n"
        "prefijo de la fuente justamente para no ensuciar la convencion.\n"
    ) % (n, instante.isoformat(), extra)


def _todas_las_versiones(s3, cubo, clave):
    """Versiones y marcadores de borrado de una clave, lo mas nuevo primero.

    comun.versiones() no devuelve los marcadores de borrado y aqui hacen
    falta: la mitad de la demostracion es que borrar tampoco pierde nada.
    """
    resp = s3.list_object_versions(Bucket=cubo, Prefix=clave)
    filas = []
    for v in resp.get("Versions", []):
        if v["Key"] == clave:
            filas.append({"tipo": "version", "version_id": v["VersionId"],
                          "actual": v["IsLatest"], "bytes": v["Size"],
                          "modificado": v["LastModified"].isoformat()})
    for m in resp.get("DeleteMarkers", []):
        if m["Key"] == clave:
            filas.append({"tipo": "marcador_de_borrado",
                          "version_id": m["VersionId"], "actual": m["IsLatest"],
                          "bytes": None,
                          "modificado": m["LastModified"].isoformat()})
    filas.sort(key=lambda f: f["modificado"], reverse=True)
    return filas


def _objeto_de_datos(cfg, s3, cubo):
    """La clave de datos mas reciente bajo el prefijo de la fuente.

    Se excluyen los manifiestos: interesa el dato, no su ficha tecnica.
    """
    slug = cfg["fuente"]["slug"]
    sufijo = cfg["ingesta"]["sufijo_manifiesto"]
    resp = s3.list_objects_v2(Bucket=cubo, Prefix=slug + "/")
    claves = [o for o in resp.get("Contents", [])
              if not o["Key"].endswith(sufijo)]
    if not claves:
        return None
    claves.sort(key=lambda o: o["LastModified"], reverse=True)
    return claves[0]["Key"]


def main():
    p = argparse.ArgumentParser(
        description="Demuestra que el versionado de la capa cruda recupera "
                    "una version anterior tras sobrescribir")
    p.add_argument("--config", help="ruta a lago.json")
    p.add_argument("--activar", action="store_true",
                   help="activar el versionado si estuviera apagado")
    args = p.parse_args()

    cfg = comun.cargar_config(args.config)
    s3 = comun.cliente_s3(cfg)
    cubo = comun.nombre_cubo(cfg, "cruda")

    print("=" * 68)
    print("EVIDENCIA DEL VERSIONADO - %s" % cubo)
    print("=" * 68)

    if not comun.esperar_almacenamiento(s3):
        raise SystemExit("No hay respuesta del almacenamiento. "
                         "Levantelo con:  docker compose up -d")

    try:
        s3.head_bucket(Bucket=cubo)
    except ClientError:
        raise SystemExit(
            "El cubo %s no existe todavia.\n"
            "  Ejecute primero:  python3 src/ingesta/cargar_cruda.py" % cubo)

    # -- 0. el versionado tiene que estar activo ANTES de escribir nada
    print("\n[0] estado del versionado")
    activo = comun.versionado_activo(s3, cubo)
    if not activo and args.activar:
        s3.put_bucket_versioning(
            Bucket=cubo, VersioningConfiguration={"Status": "Enabled"})
        activo = comun.versionado_activo(s3, cubo)
        print("    activado ahora -> %s" % activo)
    if not activo:
        raise SystemExit(
            "El versionado NO esta activo en %s.\n"
            "  Activelo ejecutando cargar_cruda.py, o con --activar.\n"
            "  Sin versionado esta demostracion no significa nada: lo que se\n"
            "  sobrescriba se pierde de verdad." % cubo)
    print("    GetBucketVersioning -> Status=Enabled   [OK]")

    pasos = []

    # -- 1. primera escritura
    t1 = comun.ahora_utc()
    v1_texto = _texto(1, t1, "Contenido original. Imaginen que es un dato "
                             "que alguien va a sobrescribir por error.")
    v1_bytes = v1_texto.encode("utf-8")
    r1 = s3.put_object(Bucket=cubo, Key=CLAVE_SONDA, Body=v1_bytes,
                       ContentType="text/plain; charset=utf-8")
    id1 = r1.get("VersionId")
    sha1 = comun.sha256_bytes(v1_bytes)
    print("\n[1] escritura inicial")
    print("    VersionId  %s" % id1)
    print("    sha256     %s" % sha1)
    pasos.append({"paso": 1, "accion": "escritura inicial",
                  "version_id": id1, "sha256": sha1, "bytes": len(v1_bytes)})

    if not id1 or id1 == "null":
        raise SystemExit(
            "El almacenamiento devolvio VersionId nulo. El cubo no tiene "
            "versionado real; revise el docker-compose.yml.")

    # -- 2. sobrescritura: la misma clave, contenido distinto
    t2 = comun.ahora_utc()
    v2_texto = _texto(2, t2, "Contenido que PISA al anterior. Esto es lo que "
                             "en un lago sin versionado seria una perdida.")
    v2_bytes = v2_texto.encode("utf-8")
    r2 = s3.put_object(Bucket=cubo, Key=CLAVE_SONDA, Body=v2_bytes,
                       ContentType="text/plain; charset=utf-8")
    id2 = r2.get("VersionId")
    sha2 = comun.sha256_bytes(v2_bytes)
    print("\n[2] sobrescritura de la MISMA clave")
    print("    VersionId  %s" % id2)
    print("    sha256     %s" % sha2)
    if id2 == id1:
        raise SystemExit("El VersionId no cambio al sobrescribir. "
                         "El versionado no esta funcionando.")
    pasos.append({"paso": 2, "accion": "sobrescritura",
                  "version_id": id2, "sha256": sha2, "bytes": len(v2_bytes)})

    # -- 3. lo que se lee sin pedir version es lo ultimo escrito
    actual = comun.leer_objeto(s3, cubo, CLAVE_SONDA)
    print("\n[3] lectura sin indicar version (la actual)")
    print("    coincide con la version 2: %s"
          % (comun.sha256_bytes(actual) == sha2))
    if comun.sha256_bytes(actual) != sha2:
        raise SystemExit("La lectura actual no devolvio la ultima version.")

    # -- 4. LA PRUEBA: la version anterior sigue recuperable
    recuperado = comun.leer_objeto(s3, cubo, CLAVE_SONDA, version_id=id1)
    sha_rec = comun.sha256_bytes(recuperado)
    ok_recuperacion = (sha_rec == sha1 and recuperado == v1_bytes)
    print("\n[4] recuperacion de la version ANTERIOR por VersionId")
    print("    VersionId pedido  %s" % id1)
    print("    sha256 recuperado %s" % sha_rec)
    print("    sha256 esperado   %s" % sha1)
    print("    IDENTICO BYTE A BYTE: %s" % ok_recuperacion)
    if not ok_recuperacion:
        raise SystemExit("La version anterior no se recupero intacta.")
    pasos.append({"paso": 4, "accion": "recuperacion de la version anterior",
                  "version_id": id1, "sha256": sha_rec,
                  "identico_al_original": ok_recuperacion})

    # -- 5. borrar tampoco pierde: queda un marcador, no un hueco
    s3.delete_object(Bucket=cubo, Key=CLAVE_SONDA)
    desaparecido = comun.objeto(s3, cubo, CLAVE_SONDA) is None
    tras_borrar = _todas_las_versiones(s3, cubo, CLAVE_SONDA)
    marcadores = [f for f in tras_borrar if f["tipo"] == "marcador_de_borrado"]
    tras_borrar_v2 = comun.leer_objeto(s3, cubo, CLAVE_SONDA, version_id=id2)
    print("\n[5] borrado de la clave")
    print("    head_object ya no la encuentra: %s" % desaparecido)
    print("    marcadores de borrado: %d" % len(marcadores))
    print("    la version 2 SIGUE legible por VersionId: %s"
          % (comun.sha256_bytes(tras_borrar_v2) == sha2))
    pasos.append({"paso": 5, "accion": "borrado logico",
                  "objeto_visible_tras_borrar": not desaparecido,
                  "marcadores_de_borrado": len(marcadores),
                  "version_2_sigue_legible":
                      comun.sha256_bytes(tras_borrar_v2) == sha2})

    # -- 6. restaurar: se quita el marcador y el objeto vuelve
    for m in marcadores:
        s3.delete_object(Bucket=cubo, Key=CLAVE_SONDA,
                         VersionId=m["version_id"])
    vuelto = comun.objeto(s3, cubo, CLAVE_SONDA)
    print("\n[6] restauracion (se elimina el marcador de borrado)")
    print("    el objeto vuelve a estar visible: %s" % (vuelto is not None))
    pasos.append({"paso": 6, "accion": "restauracion",
                  "objeto_restaurado": vuelto is not None})

    # -- 7. el dato real no se toco
    print("\n[7] comprobacion de inmutabilidad sobre el dato real")
    clave_datos = _objeto_de_datos(cfg, s3, cubo)
    if clave_datos is None:
        datos_info = {"clave": None,
                      "_nota": "No hay objetos de datos todavia. Ejecute "
                               "cargar_cruda.py antes para completar la "
                               "evidencia."}
        print("    no hay objetos de datos aun (ejecute cargar_cruda.py)")
    else:
        vs = comun.versiones(s3, cubo, clave_datos)
        print("    %s" % clave_datos)
        print("    versiones: %d  ->  %s" % (
            len(vs),
            "una sola, nadie lo ha sobrescrito"
            if len(vs) == 1 else
            "MAS DE UNA: alguien reescribio la clave, revisar"))
        datos_info = {
            "clave": clave_datos,
            "versiones": len(vs),
            "inmutabilidad_respetada": len(vs) == 1,
            "version_ids": [v["VersionId"] for v in vs],
        }

    versiones_sonda = _todas_las_versiones(s3, cubo, CLAVE_SONDA)

    evidencia = {
        "_generado_por": "src/ingesta/demostrar_versionado.py",
        "_no_editar": "Se regenera en cada corrida.",
        "_que_demuestra": ("Que el versionado esta activo en la capa cruda y "
                           "que, tras sobrescribir y tras borrar, el contenido "
                           "anterior sigue siendo recuperable byte a byte."),
        "instante_utc": comun.ahora_utc().isoformat(),
        "cubo": cubo,
        "versionado_activo": activo,
        "clave_sonda": CLAVE_SONDA,
        "_por_que_una_sonda": ("La capa cruda es inmutable. La demostracion no "
                               "se hace sobre el dato del proyecto: se hace "
                               "sobre un objeto de prueba fuera del prefijo de "
                               "la fuente."),
        "pasos": pasos,
        "versiones_de_la_sonda": versiones_sonda,
        "objeto_de_datos": datos_info,
        "veredicto": "VERSIONADO DEMOSTRADO" if ok_recuperacion else "FALLA",
    }

    comun.DOCS.mkdir(parents=True, exist_ok=True)
    salida_json = comun.DOCS / "evidencia_versionado.json"
    with open(salida_json, "w", encoding="utf-8") as fh:
        json.dump(evidencia, fh, ensure_ascii=False, indent=2)

    salida_md = comun.DOCS / "evidencia_versionado.md"
    with open(salida_md, "w", encoding="utf-8") as fh:
        fh.write(_informe_md(evidencia, id1, id2, sha1, sha2))

    print("\n[ok] %s" % evidencia["veredicto"])
    print("     docs/evidencia_versionado.json")
    print("     docs/evidencia_versionado.md   <- pegar en el informe")
    return 0


def _informe_md(ev, id1, id2, sha1, sha2):
    """El mismo hecho, en markdown, listo para pegar en docs/T5_lago.md.

    Se genera aqui para que nadie transcriba un VersionId a mano.
    """
    filas = "\n".join(
        "| %s | `%s` | %s | %s |" % (
            f["tipo"], f["version_id"],
            "si" if f["actual"] else "no",
            "-" if f["bytes"] is None else f["bytes"])
        for f in ev["versiones_de_la_sonda"])

    datos = ev["objeto_de_datos"]
    if datos.get("clave"):
        bloque_datos = (
            "El objeto de datos `%s` tiene **%d version(es)**. %s\n" % (
                datos["clave"], datos["versiones"],
                "Nadie lo ha sobrescrito: la capa cruda sigue siendo inmutable."
                if datos.get("inmutabilidad_respetada") else
                "**Atencion:** hay mas de una version, alguien reescribio la "
                "clave. Revisen por que antes de entregar."))
    else:
        bloque_datos = ("Todavia no hay objetos de datos en la capa cruda. "
                        "Ejecuten `cargar_cruda.py` y vuelvan a correr esta "
                        "demostracion para completar la evidencia.\n")

    return """# Evidencia del versionado de la capa cruda

<!-- GENERADO por src/ingesta/demostrar_versionado.py. No editar a mano.
     Se regenera en cada corrida. -->

Cubo: `%(cubo)s` - Generado: `%(instante)s` (UTC) - Veredicto: **%(veredicto)s**

## Que se demuestra

1. `GetBucketVersioning` sobre `%(cubo)s` devuelve `Status=Enabled`.
2. Se escribe un objeto, se **sobrescribe** con contenido distinto, y la
   version anterior se recupera **identica byte a byte** pidiendola por su
   `VersionId`.
3. Se **borra** la clave: deja de verse, pero no se pierde. Queda un marcador
   de borrado y el contenido sigue siendo legible por `VersionId`. Al quitar
   el marcador, el objeto vuelve.

## La prueba, con los identificadores reales

| | |
|---|---|
| Objeto sonda | `%(sonda)s` |
| `VersionId` de la escritura inicial | `%(id1)s` |
| `sha256` de la escritura inicial | `%(sha1)s` |
| `VersionId` tras sobrescribir | `%(id2)s` |
| `sha256` tras sobrescribir | `%(sha2)s` |
| La version inicial se recupero intacta | **si, sha256 identico** |

### Historial completo de la sonda

| Tipo | VersionId | Es la actual | Bytes |
|---|---|---|---|
%(filas)s

## Por que la prueba se hace sobre una sonda y no sobre el dato

%(por_que)s

## El dato real sigue intacto

%(bloque_datos)s

## Como reproducir esta evidencia

```bash
docker compose up -d
python3 src/ingesta/cargar_cruda.py
python3 src/ingesta/demostrar_versionado.py
```
""" % {
        "cubo": ev["cubo"],
        "instante": ev["instante_utc"],
        "veredicto": ev["veredicto"],
        "sonda": ev["clave_sonda"],
        "id1": id1, "id2": id2, "sha1": sha1, "sha2": sha2,
        "filas": filas,
        "por_que": ev["_por_que_una_sonda"],
        "bloque_datos": bloque_datos,
    }


if __name__ == "__main__":
    sys.exit(main())
