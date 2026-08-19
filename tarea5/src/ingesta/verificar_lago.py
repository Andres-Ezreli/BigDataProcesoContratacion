#!/usr/bin/env python3
"""
Verificacion del lago contra los seis criterios de aceptacion de T5.

Este script es el arbitro. No confia en lo que diga el informe: se conecta al
almacenamiento, lista lo que hay de verdad, lo compara contra la convencion
declarada en config/lago.json y dice PASA o FALLA por cada criterio.

Sirve para tres cosas:

  1. Que el equipo sepa, antes de entregar, si la tarea esta completa.
  2. Que el profesor pueda ejecutarlo y ver el resultado sin leer el codigo.
  3. Que las cifras del informe no las escriba nadie a mano: salen de
     docs/evidencia_lago.md, que genera este script.

Codigo de salida 0 si todo pasa, 1 si algo falla. Sirve para integracion
continua tal cual esta.

Uso:
    python3 src/ingesta/verificar_lago.py
    python3 src/ingesta/verificar_lago.py --sin-integridad   # no releer objetos
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun  # noqa: E402
from botocore.exceptions import ClientError  # noqa: E402


# --------------------------------------------------------------------------
# LA CONVENCION, ESCRITA COMO EXPRESION REGULAR
#
# Esta es la unica traduccion de comun.clave_cruda() a una regla que se puede
# comprobar. Si alguien cambia la convencion en comun.py y se olvida de esta
# linea, este script falla y avisa. Es deliberado: la convencion tiene que
# estar en dos sitios que se contradigan a gritos si se separan.
# --------------------------------------------------------------------------

PATRON_CLAVE = re.compile(
    r"^(?P<fuente>[a-z0-9_]+)"
    r"/anio=(?P<anio>\d{4})"
    r"/mes=(?P<mes>\d{2})"
    r"/dia=(?P<dia>\d{2})"
    r"/(?P<archivo>[^/]+)$"
)

# <fuente>_<YYYYMMDD>[_lote-NN].<ext>
PATRON_ARCHIVO = re.compile(
    r"^(?P<fuente>[a-z0-9_]+)_(?P<fecha>\d{8})(?:_lote-(?P<lote>\d{2}))?"
    r"\.(?P<ext>[a-z0-9.]+)$"
)


class Comprobacion(object):
    """Una comprobacion con su resultado y su detalle."""

    def __init__(self, numero, titulo):
        self.numero = numero
        self.titulo = titulo
        self.pasa = True
        self.detalles = []

    def bien(self, texto):
        self.detalles.append(("ok", texto))

    def mal(self, texto):
        self.pasa = False
        self.detalles.append(("FALLA", texto))

    def nota(self, texto):
        self.detalles.append(("--", texto))

    def imprimir(self):
        estado = "PASA " if self.pasa else "FALLA"
        print("\n[%d] %s   ... %s" % (self.numero, self.titulo, estado))
        for marca, texto in self.detalles:
            print("     %-5s %s" % (marca, texto))

    def a_dict(self):
        return {"numero": self.numero, "titulo": self.titulo,
                "resultado": "PASA" if self.pasa else "FALLA",
                "detalles": [{"marca": m, "texto": t} for m, t in self.detalles]}


# --------------------------------------------------------------------------
# Inventario
# --------------------------------------------------------------------------

def listar_todo(s3, cubo):
    """Todas las claves del cubo, paginando. Devuelve lista de dicts."""
    salida = []
    token = None
    while True:
        kwargs = {"Bucket": cubo}
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)
        for o in resp.get("Contents", []):
            salida.append({"clave": o["Key"], "bytes": o["Size"],
                           "modificado": o["LastModified"].isoformat()})
        if not resp.get("IsTruncated"):
            break
        token = resp.get("NextContinuationToken")
    salida.sort(key=lambda o: o["clave"])
    return salida


def es_metadato(clave):
    """Las claves que empiezan por guion bajo no son dato: son metadato del
    lago (_LEEME.txt, _evidencia/...). No se les aplica la convencion de
    particion porque no describen un hecho fechado."""
    return clave.startswith("_")


def sha256_remoto(s3, cubo, clave, bloque=1024 * 1024):
    """Relee el objeto del almacenamiento y recalcula su sha256.

    Por bloques: un objeto de la capa cruda puede pesar cientos de MB y no
    tiene por que caber en memoria.
    """
    import hashlib
    h = hashlib.sha256()
    cuerpo = s3.get_object(Bucket=cubo, Key=clave)["Body"]
    while True:
        trozo = cuerpo.read(bloque)
        if not trozo:
            break
        h.update(trozo)
    return h.hexdigest()


# --------------------------------------------------------------------------
# Las comprobaciones
# --------------------------------------------------------------------------

def c1_capas(cfg, s3):
    """Criterio 1a y 4: las tres capas existen como cubos."""
    c = Comprobacion(1, "Las tres capas del lago existen")
    for capa in cfg["almacenamiento"]["capas"]:
        cubo = comun.nombre_cubo(cfg, capa)
        try:
            s3.head_bucket(Bucket=cubo)
            c.bien("capa %-9s -> cubo %s" % (capa, cubo))
        except ClientError:
            c.mal("capa %-9s -> falta el cubo %s" % (capa, cubo))
    return c


def c2_versionado(cfg, s3):
    """Criterio 3: versionado activo donde la configuracion dice que va."""
    c = Comprobacion(2, "El versionado esta donde la configuracion lo declara")
    declarado = cfg["almacenamiento"]["versionado_por_capa"]
    for capa in cfg["almacenamiento"]["capas"]:
        cubo = comun.nombre_cubo(cfg, capa)
        quiere = bool(declarado.get(capa))
        try:
            activo = comun.versionado_activo(s3, cubo)
        except ClientError:
            c.mal("%s: no se pudo consultar el versionado" % cubo)
            continue
        if quiere and activo:
            c.bien("%-16s versionado ACTIVO, como corresponde a la cruda" % cubo)
        elif quiere and not activo:
            c.mal("%-16s deberia tener versionado y NO lo tiene" % cubo)
        elif not quiere and activo:
            c.nota("%-16s tiene versionado sin necesitarlo (esta capa se "
                   "regenera; no es un error, pero gasta espacio)" % cubo)
        else:
            c.bien("%-16s sin versionado, correcto: esta capa se regenera"
                   % cubo)
    return c


def c3_convencion(cfg, objetos):
    """Criterio 1 y 4: toda clave de datos cumple la convencion, letra a letra."""
    c = Comprobacion(3, "Toda clave de datos cumple la convencion de rutas")
    slug = cfg["fuente"]["slug"]
    sufijo = cfg["ingesta"]["sufijo_manifiesto"]

    datos = [o for o in objetos
             if not es_metadato(o["clave"]) and not o["clave"].endswith(sufijo)]
    if not datos:
        c.mal("no hay ningun objeto de datos en la capa cruda. "
              "Ejecute src/ingesta/cargar_cruda.py")
        return c

    c.nota("objetos de datos encontrados: %d" % len(datos))
    for o in datos:
        clave = o["clave"]
        m = PATRON_CLAVE.match(clave)
        if not m:
            c.mal("%s  no encaja en <fuente>/anio=YYYY/mes=MM/dia=DD/archivo"
                  % clave)
            continue
        if m.group("fuente") != slug:
            c.mal("%s  el primer tramo es %r y la fuente configurada es %r"
                  % (clave, m.group("fuente"), slug))
            continue
        anio, mes, dia = (int(m.group("anio")), int(m.group("mes")),
                          int(m.group("dia")))
        try:
            fecha = date(anio, mes, dia)
        except ValueError:
            c.mal("%s  la particion no es una fecha real" % clave)
            continue

        ma = PATRON_ARCHIVO.match(m.group("archivo"))
        if not ma:
            c.mal("%s  el nombre del archivo no es "
                  "<fuente>_<YYYYMMDD>[_lote-NN].<ext>" % clave)
            continue
        if ma.group("fecha") != fecha.strftime("%Y%m%d"):
            c.mal("%s  el nombre dice %s y la particion dice %s: no coinciden"
                  % (clave, ma.group("fecha"), fecha.strftime("%Y%m%d")))
            continue
        c.bien("%s" % clave)
    return c


def c4_manifiestos(cfg, objetos):
    """Criterio 4: cada dato tiene su ficha tecnica al lado."""
    c = Comprobacion(4, "Cada objeto de datos tiene su manifiesto hermano")
    sufijo = cfg["ingesta"]["sufijo_manifiesto"]
    claves = set(o["clave"] for o in objetos)
    datos = [o["clave"] for o in objetos
             if not es_metadato(o["clave"]) and not o["clave"].endswith(sufijo)]
    if not datos:
        c.mal("no hay objetos de datos que comprobar")
        return c
    for clave in datos:
        esperado = clave + sufijo
        if esperado in claves:
            c.bien("%s  ->  %s" % (clave.split("/")[-1],
                                   esperado.split("/")[-1]))
        else:
            c.mal("%s  no tiene manifiesto (%s)" % (clave, esperado))
    return c


def c5_integridad(cfg, s3, cubo, objetos, saltar):
    """Criterio 1 y 6: lo que hay en el lago es lo que se subio.

    Se relee cada objeto entero y se recalcula el sha256. Es la unica forma
    de afirmar integridad sin creerle al metadato.
    """
    c = Comprobacion(5, "El contenido del lago coincide con su sha256 declarado")
    sufijo = cfg["ingesta"]["sufijo_manifiesto"]
    datos = [o for o in objetos
             if not es_metadato(o["clave"]) and not o["clave"].endswith(sufijo)]
    if not datos:
        c.mal("no hay objetos de datos que comprobar")
        return c
    if saltar:
        c.nota("saltada por --sin-integridad. Para la entrega hay que "
               "ejecutarla sin esa opcion al menos una vez.")
        return c

    for o in datos:
        clave = o["clave"]
        meta = comun.objeto(s3, cubo, clave)
        declarado = (meta.get("Metadata") or {}).get("sha256")
        if not declarado:
            c.mal("%s  no trae sha256 en sus metadatos" % clave)
            continue
        real = sha256_remoto(s3, cubo, clave)
        if real == declarado:
            c.bien("%s  sha256 %s...  (%s)"
                   % (clave.split("/")[-1], real[:16], comun.humano(o["bytes"])))
        else:
            c.mal("%s  sha256 declarado %s pero el contenido da %s"
                  % (clave, declarado, real))
    return c


def c6_leemes(cfg, s3):
    """Criterio 4: el lago se explica desde dentro, sin el repositorio."""
    c = Comprobacion(6, "Cada cubo trae su _LEEME.txt con la convencion")
    for capa in cfg["almacenamiento"]["capas"]:
        cubo = comun.nombre_cubo(cfg, capa)
        meta = None
        try:
            meta = comun.objeto(s3, cubo, "_LEEME.txt")
        except ClientError:
            pass
        if meta:
            c.bien("%-16s _LEEME.txt (%s)" % (cubo, comun.humano(meta["ContentLength"])))
        else:
            c.mal("%-16s no tiene _LEEME.txt. Quien abra el lago por la "
                  "consola no sabria que hay dentro." % cubo)
    return c


def c7_versiones(cfg, s3, cubo):
    """Criterio 3: hay evidencia de recuperacion, no solo el interruptor."""
    c = Comprobacion(7, "Hay evidencia de que una version anterior se recupera")
    resp = s3.list_object_versions(Bucket=cubo)
    por_clave = {}
    for v in resp.get("Versions", []):
        por_clave.setdefault(v["Key"], []).append(v)

    con_historial = {k: vs for k, vs in por_clave.items() if len(vs) > 1}
    if not con_historial:
        c.mal("ninguna clave tiene mas de una version. Ejecute "
              "src/ingesta/demostrar_versionado.py")
        return c

    for clave, vs in sorted(con_historial.items()):
        vs.sort(key=lambda v: v["LastModified"], reverse=True)
        anterior = vs[1]
        try:
            cuerpo = comun.leer_objeto(s3, cubo, clave,
                                       version_id=anterior["VersionId"])
            c.bien("%s  %d versiones; la anterior (%s) se leyo, %d bytes"
                   % (clave, len(vs), anterior["VersionId"][:12], len(cuerpo)))
        except ClientError as exc:
            c.mal("%s  la version anterior no se pudo leer: %s" % (clave, exc))

    fichero = comun.DOCS / "evidencia_versionado.json"
    if fichero.exists():
        c.nota("detalle completo en docs/evidencia_versionado.json")
    else:
        c.nota("falta docs/evidencia_versionado.json; ejecute "
               "demostrar_versionado.py para dejarlo escrito")
    return c


def c8_inmutabilidad(cfg, s3, cubo, objetos):
    """Criterio 5: el dato del proyecto no se ha reescrito nunca."""
    c = Comprobacion(8, "Ningun objeto de datos ha sido sobrescrito")
    sufijo = cfg["ingesta"]["sufijo_manifiesto"]
    datos = [o["clave"] for o in objetos
             if not es_metadato(o["clave"]) and not o["clave"].endswith(sufijo)]
    if not datos:
        c.mal("no hay objetos de datos que comprobar")
        return c
    for clave in datos:
        vs = comun.versiones(s3, cubo, clave)
        if len(vs) <= 1:
            c.bien("%s  una sola version" % clave.split("/")[-1])
        else:
            c.mal("%s  tiene %d versiones. Alguien reescribio un objeto de la "
                  "capa cruda. El versionado lo salvo, pero la regla se rompio: "
                  "averiguen quien y por que." % (clave, len(vs)))
    return c


def c9_sin_duplicados(cfg, objetos, s3, cubo):
    """Criterio 2: reejecutar no duplica. Dos objetos distintos no pueden
    tener el mismo contenido."""
    c = Comprobacion(9, "Reejecutar no ha duplicado el dato")
    sufijo = cfg["ingesta"]["sufijo_manifiesto"]
    datos = [o["clave"] for o in objetos
             if not es_metadato(o["clave"]) and not o["clave"].endswith(sufijo)]
    vistos = {}
    for clave in datos:
        meta = comun.objeto(s3, cubo, clave)
        sha = (meta.get("Metadata") or {}).get("sha256")
        if not sha:
            continue
        if sha in vistos:
            c.mal("%s y %s tienen el MISMO contenido con claves distintas: "
                  "la ingesta duplico" % (vistos[sha], clave))
        else:
            vistos[sha] = clave
    if c.pasa:
        c.bien("%d objeto(s) de datos, %d contenido(s) distinto(s): sin "
               "duplicados" % (len(datos), len(vistos)))
    return c


# --------------------------------------------------------------------------
# El informe generado
# --------------------------------------------------------------------------

# Mapa entre las comprobaciones de este script y los seis criterios del
# enunciado. Un criterio puede necesitar varias comprobaciones.
CRITERIOS = [
    (1, "El dato crudo esta en la capa cruda bajo "
        "`<fuente>/anio=YYYY/mes=MM/dia=DD/`", [1, 3, 5]),
    (2, "La carga es un script reproducible con boto3, reejecutable sin "
        "duplicar ni romper", [9]),
    (3, "El versionado esta activo en la capa cruda y se evidencia", [2, 7]),
    (4, "La convencion esta documentada de modo que otra persona prediga "
        "donde esta cualquier objeto", [3, 4, 6]),
    (5, "La capa cruda se declara inmutable y nadie la ha editado", [8]),
    (6, "Es reproducible: otra persona clona en limpio, ejecuta y obtiene "
        "el mismo lago", [1, 3, 4, 5, 6]),
]


def escribir_informe(cfg, cubo, comprobaciones, inventario, todo_pasa):
    comun.DOCS.mkdir(parents=True, exist_ok=True)
    por_num = {c.numero: c for c in comprobaciones}

    filas_criterios = []
    for num, texto, deps in CRITERIOS:
        ok = all(por_num[d].pasa for d in deps if d in por_num)
        filas_criterios.append(
            "| %d | %s | %s | %s |" % (
                num, texto, ", ".join("C%d" % d for d in deps),
                "**PASA**" if ok else "**FALLA**"))

    filas_comprobaciones = []
    for c in comprobaciones:
        filas_comprobaciones.append(
            "| C%d | %s | %s |" % (c.numero, c.titulo,
                                   "PASA" if c.pasa else "FALLA"))

    filas_inv = []
    for capa, objetos in inventario:
        cubo_capa = comun.nombre_cubo(cfg, capa)
        if not objetos:
            filas_inv.append("| `%s` | _(vacio)_ | - | - |" % cubo_capa)
            continue
        for o in objetos:
            filas_inv.append("| `%s` | `%s` | %s | %s |"
                             % (cubo_capa, o["clave"],
                                comun.humano(o["bytes"]), o["modificado"]))

    fallos = [c for c in comprobaciones if not c.pasa]
    if fallos:
        bloque_fallos = "\n".join(
            "- **C%d %s**\n%s" % (
                c.numero, c.titulo,
                "\n".join("    - %s" % t for m, t in c.detalles if m == "FALLA"))
            for c in fallos)
    else:
        bloque_fallos = "Ninguna. Las nueve comprobaciones pasan.\n"

    texto = """# Evidencia del lago - verificacion automatica

<!-- GENERADO por src/ingesta/verificar_lago.py. No editar a mano.
     Se regenera en cada corrida. -->

Generado: `%(instante)s` (UTC)
Capa cruda: `%(cubo)s`
Veredicto global: **%(veredicto)s**

## Los seis criterios de aceptacion

| # | Criterio | Comprobaciones | Resultado |
|---|---|---|---|
%(criterios)s

## Las nueve comprobaciones

| # | Comprobacion | Resultado |
|---|---|---|
%(comprobaciones)s

## Que fallo

%(fallos)s

## Inventario completo del lago

Todo lo que hay dentro, en el momento de generar este archivo. Las claves que
empiezan por guion bajo son metadato del lago, no dato del proyecto.

| Cubo | Clave | Tamano | Ultima modificacion |
|---|---|---|---|
%(inventario)s

## Como reproducir esta verificacion

```bash
docker compose up -d
python3 -m pip install -r requisitos.txt
python3 src/ingesta/cargar_cruda.py
python3 src/ingesta/demostrar_versionado.py
python3 src/ingesta/verificar_lago.py
```

El codigo de salida es 0 si todo pasa y 1 si algo falla.
""" % {
        "instante": comun.ahora_utc().isoformat(),
        "cubo": cubo,
        "veredicto": "PASA" if todo_pasa else "FALLA",
        "criterios": "\n".join(filas_criterios),
        "comprobaciones": "\n".join(filas_comprobaciones),
        "fallos": bloque_fallos,
        "inventario": "\n".join(filas_inv),
    }

    with open(comun.DOCS / "evidencia_lago.md", "w", encoding="utf-8") as fh:
        fh.write(texto)

    with open(comun.DOCS / "evidencia_lago.json", "w", encoding="utf-8") as fh:
        json.dump({
            "_generado_por": "src/ingesta/verificar_lago.py",
            "_no_editar": "Se regenera en cada corrida.",
            "instante_utc": comun.ahora_utc().isoformat(),
            "cubo_cruda": cubo,
            "veredicto": "PASA" if todo_pasa else "FALLA",
            "criterios": [
                {"numero": n, "texto": t,
                 "comprobaciones": d,
                 "resultado": "PASA" if all(por_num[x].pasa for x in d
                                            if x in por_num) else "FALLA"}
                for n, t, d in CRITERIOS],
            "comprobaciones": [c.a_dict() for c in comprobaciones],
            "inventario": {comun.nombre_cubo(cfg, capa): objetos
                           for capa, objetos in inventario},
        }, fh, ensure_ascii=False, indent=2)


def main():
    p = argparse.ArgumentParser(
        description="Verifica el lago contra los seis criterios de T5")
    p.add_argument("--config", help="ruta a lago.json")
    p.add_argument("--sin-integridad", action="store_true",
                   help="no releer los objetos para recalcular su sha256")
    args = p.parse_args()

    cfg = comun.cargar_config(args.config)
    s3 = comun.cliente_s3(cfg)
    cubo = comun.nombre_cubo(cfg, "cruda")

    print("=" * 68)
    print("VERIFICACION DEL LAGO")
    print("=" * 68)

    if not comun.esperar_almacenamiento(s3):
        raise SystemExit("No hay respuesta del almacenamiento. "
                         "Levantelo con:  docker compose up -d")

    # Inventario de las tres capas, para el informe.
    inventario = []
    for capa in cfg["almacenamiento"]["capas"]:
        cubo_capa = comun.nombre_cubo(cfg, capa)
        try:
            inventario.append((capa, listar_todo(s3, cubo_capa)))
        except ClientError:
            inventario.append((capa, []))

    objetos_cruda = dict(inventario).get("cruda", [])

    comprobaciones = [
        c1_capas(cfg, s3),
        c2_versionado(cfg, s3),
        c3_convencion(cfg, objetos_cruda),
        c4_manifiestos(cfg, objetos_cruda),
        c5_integridad(cfg, s3, cubo, objetos_cruda, args.sin_integridad),
        c6_leemes(cfg, s3),
        c7_versiones(cfg, s3, cubo),
        c8_inmutabilidad(cfg, s3, cubo, objetos_cruda),
        c9_sin_duplicados(cfg, objetos_cruda, s3, cubo),
    ]

    for c in comprobaciones:
        c.imprimir()

    todo_pasa = all(c.pasa for c in comprobaciones)

    print("\n" + "=" * 68)
    print("LOS SEIS CRITERIOS DE ACEPTACION")
    print("=" * 68)
    por_num = {c.numero: c for c in comprobaciones}
    for num, texto, deps in CRITERIOS:
        ok = all(por_num[d].pasa for d in deps if d in por_num)
        print("  %d. %-5s %s" % (num, "PASA" if ok else "FALLA", texto[:60]))

    escribir_informe(cfg, cubo, comprobaciones, inventario, todo_pasa)

    print("\n" + "=" * 68)
    print("VEREDICTO: %s" % ("PASA" if todo_pasa else "FALLA"))
    print("=" * 68)
    print("  docs/evidencia_lago.md    <- tabla para el informe")
    print("  docs/evidencia_lago.json")
    return 0 if todo_pasa else 1


if __name__ == "__main__":
    sys.exit(main())
