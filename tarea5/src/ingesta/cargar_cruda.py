#!/usr/bin/env python3
"""
Ingesta de la fuente cruda del proyecto a la capa cruda del lago.

Que hace, en orden:
  1. Crea los tres cubos del lago si no existen.
  2. Activa el versionado en la capa cruda.
  3. Deja un _LEEME.txt en la raiz de cada cubo con la convencion de rutas,
     para que quien abra el lago por la consola no dependa del repositorio.
  4. Descarga la fuente del portal (o toma un archivo local con --archivo).
  5. La carga bajo  <fuente>/anio=YYYY/mes=MM/dia=DD/  con su manifiesto.

Es reejecutable. Correrlo dos veces seguidas NO crea un segundo objeto ni una
segunda version: la segunda corrida compara el sha256 y se detiene.

Uso:
    python3 src/ingesta/cargar_cruda.py
    python3 src/ingesta/cargar_cruda.py --filas 200000
    python3 src/ingesta/cargar_cruda.py --archivo /ruta/a/fuente.csv
    python3 src/ingesta/cargar_cruda.py --fecha 2026-08-19     # reponer una particion
    python3 src/ingesta/cargar_cruda.py --nuevo-lote           # segundo lote del dia
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun  # noqa: E402
from botocore.exceptions import ClientError  # noqa: E402

DESCARGAS = comun.RAIZ / ".descargas"
VERSION_SCRIPT = "T5-v1"


# --------------------------------------------------------------------------
# 1-3. El lago
# --------------------------------------------------------------------------

def plantilla_leeme(cfg, capa):
    alm = cfg["almacenamiento"]
    fuente = cfg["fuente"]
    versionado = "ACTIVO" if alm["versionado_por_capa"].get(capa) else "no activo"
    cubos = ", ".join(comun.nombre_cubo(cfg, c) for c in alm["capas"])

    comun_txt = (
        "LAGO DEL PROYECTO - CAPA %s\n"
        "%s\n\n"
        "Las tres capas del lago son tres cubos:\n"
        "  %s\n"
        "El nombre del cubo ES la capa. No hay carpetas: lo que parece una\n"
        "carpeta es un prefijo de la clave del objeto.\n\n"
        "Versionado en esta capa: %s\n\n"
    ) % (capa.upper(), "=" * 60, cubos, versionado)

    if capa == "cruda":
        propio = (
            "QUE HAY AQUI\n"
            "  El dato tal como lo entrego la fuente. Sin limpiar, sin convertir,\n"
            "  sin corregir. Bytes identicos a los que devolvio el portal.\n\n"
            "DONDE ESTA CADA COSA\n"
            "  <fuente>/anio=YYYY/mes=MM/dia=DD/<fuente>_<YYYYMMDD>.<ext>\n\n"
            "  <fuente>  el identificador de la fuente en minusculas, sin acentos\n"
            "            ni espacios. La de este proyecto es: %s\n"
            "  anio/mes/dia  la FECHA DE INGESTA en UTC: el dia en que el objeto\n"
            "            entro al lago. NO es la fecha del dato.\n"
            "            Mes y dia siempre con dos digitos.\n\n"
            "  Ejemplo real:\n"
            "    %s/anio=2026/mes=08/dia=19/%s_20260819.%s\n\n"
            "  Si el mismo dia entra un segundo lote, el nombre lleva sufijo:\n"
            "    %s_20260819_lote-02.%s\n"
            "  Nunca se sobrescribe el lote anterior.\n\n"
            "CADA OBJETO TIENE FICHA TECNICA\n"
            "  El manifiesto de cualquier objeto es su misma clave mas\n"
            "  '%s'. Trae la URL exacta de descarga, la fecha,\n"
            "  el sha256, el numero de filas y las columnas. Si necesita saber\n"
            "  de donde salio un archivo, lea su manifiesto: no pregunte.\n\n"
            "REGLA DE ORO: ESTA CAPA ES INMUTABLE\n"
            "  Nada de lo que hay aqui se edita, se corrige ni se borra.\n"
            "  Un dato equivocado en el origen se queda equivocado aqui, porque\n"
            "  aqui se guarda lo que la fuente dijo, no lo que deberia haber dicho.\n"
            "  Las correcciones se hacen en la capa refinada, con la regla escrita\n"
            "  en el codigo que la construye. Si el origen publica una correccion,\n"
            "  esa correccion entra como un LOTE NUEVO, no como una edicion.\n"
            "  El versionado de este cubo es la red de seguridad de esa regla:\n"
            "  si alguien se equivoca y sobrescribe, la version anterior sigue ahi.\n\n"
            "LA FUENTE\n"
            "  %s\n"
            "  Portal:     %s\n"
            "  Organismo:  %s\n"
            "  Licencia:   %s\n"
        ) % (fuente["slug"], fuente["slug"], fuente["slug"], fuente["extension"],
             fuente["slug"], fuente["extension"],
             cfg["ingesta"]["sufijo_manifiesto"],
             fuente["nombre"], fuente["portal"], fuente["organismo"],
             fuente["licencia"])
    elif capa == "refinada":
        propio = (
            "QUE HAY AQUI\n"
            "  El dato de la capa cruda ya tipado, deduplicado y convertido a\n"
            "  Parquet. Aqui SI se corrigen los errores del origen, y la regla de\n"
            "  cada correccion vive en el codigo que genera esta capa.\n\n"
            "DONDE ESTA CADA COSA\n"
            "  <fuente>/anio=YYYY/mes=MM/parte-NNN.parquet\n\n"
            "  Ojo a la diferencia con la cruda: aqui anio/mes es la FECHA DEL\n"
            "  NEGOCIO (la del dato, no la de la carga), porque esta capa se\n"
            "  consulta por rango de fechas del hecho.\n\n"
            "  Esta capa se REGENERA. Si se borra entera, se reconstruye\n"
            "  ejecutando el pipeline desde la cruda. Por eso no lleva versionado.\n"
        )
    else:
        propio = (
            "QUE HAY AQUI\n"
            "  Productos de datos listos para consumir: agregados, tablas de\n"
            "  negocio, lo que alimenta un tablero o un modelo.\n\n"
            "DONDE ESTA CADA COSA\n"
            "  <dominio>/<producto>/anio=YYYY/mes=MM/parte-NNN.parquet\n\n"
            "  Ejemplo:\n"
            "    contratacion/valor_por_departamento/anio=2026/mes=08/parte-000.parquet\n\n"
            "  Esta capa se REGENERA desde la refinada. No lleva versionado.\n"
        )

    pie = ("\n%s\nEl mapa completo del lago esta en docs/T5_lago.md del repositorio\n"
           "del equipo. Este archivo se genera desde config/lago.json y se\n"
           "actualiza solo cuando cambia la convencion.\n") % ("-" * 60)

    return comun_txt + propio + pie


def preparar_lago(cfg, s3):
    """Crea los cubos, activa el versionado y deja el LEEME. Idempotente."""
    alm = cfg["almacenamiento"]
    resumen = []

    for capa in alm["capas"]:
        cubo = comun.nombre_cubo(cfg, capa)

        # -- cubo
        try:
            s3.head_bucket(Bucket=cubo)
            estado_cubo = "ya existia"
        except ClientError:
            try:
                s3.create_bucket(Bucket=cubo)
                estado_cubo = "creado"
            except ClientError as exc:
                codigo = exc.response["Error"]["Code"]
                if codigo in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                    estado_cubo = "ya existia"
                else:
                    raise
        print("[cubo] %-16s %s" % (cubo, estado_cubo))

        # -- versionado
        quiere = bool(alm["versionado_por_capa"].get(capa))
        activo = comun.versionado_activo(s3, cubo)
        if quiere and not activo:
            s3.put_bucket_versioning(
                Bucket=cubo, VersioningConfiguration={"Status": "Enabled"})
            activo = comun.versionado_activo(s3, cubo)
            print("[ver.] %-16s versionado ACTIVADO -> %s" % (cubo, activo))
        elif quiere:
            print("[ver.] %-16s versionado ya activo" % cubo)
        else:
            print("[ver.] %-16s sin versionado (esta capa se regenera)" % cubo)

        # -- LEEME: solo se escribe si falta o si cambio, para no generar
        #    una version nueva en cada corrida.
        texto = plantilla_leeme(cfg, capa).encode("utf-8")
        actual = None
        try:
            actual = comun.leer_objeto(s3, cubo, "_LEEME.txt")
        except ClientError:
            pass
        if actual != texto:
            s3.put_object(Bucket=cubo, Key="_LEEME.txt", Body=texto,
                          ContentType="text/plain; charset=utf-8")
            print("[docs] %-16s _LEEME.txt escrito" % cubo)
        else:
            print("[docs] %-16s _LEEME.txt sin cambios" % cubo)

        resumen.append({"capa": capa, "cubo": cubo, "estado": estado_cubo,
                        "versionado": activo})
    return resumen


# --------------------------------------------------------------------------
# 4. La fuente
# --------------------------------------------------------------------------

def _pedir(url, tiempo_espera, reintentos, espera):
    cabeceras = {"User-Agent": "IFPN0025-T5-ingesta/%s" % VERSION_SCRIPT,
                 "Accept": "text/csv"}
    token = os.environ.get("SOCRATA_APP_TOKEN")
    if token:
        cabeceras["X-App-Token"] = token
    ultimo = None
    for intento in range(1, reintentos + 1):
        try:
            pet = urllib.request.Request(url, headers=cabeceras)
            with urllib.request.urlopen(pet, timeout=tiempo_espera) as resp:
                return resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            ultimo = exc
            if intento < reintentos:
                print("     intento %d/%d fallo (%s); reintento en %ds"
                      % (intento, reintentos, exc, espera))
                time.sleep(espera)
    raise SystemExit(
        "No se pudo descargar la fuente tras %d intentos.\n"
        "  Ultimo error: %s\n"
        "  URL: %s\n"
        "  Si no hay salida a internet, use --archivo con una copia local."
        % (reintentos, ultimo, url))


def descargar(cfg, filas, destino):
    """Descarga la fuente del portal, paginando, a un CSV local.

    La UNICA operacion mecanica es unir las paginas conservando un solo
    encabezado. No se cambia ni un byte del contenido de las filas. Si el
    encabezado de una pagina no coincide con el de la primera, el script se
    detiene: significa que el esquema del portal cambio a mitad de descarga.
    """
    d = cfg["descarga"]
    base = cfg["fuente"]["endpoint_datos"]
    por_pagina = min(d["filas_por_pagina"], filas)
    destino.parent.mkdir(parents=True, exist_ok=True)

    encabezado = None
    urls = []
    total_filas = 0
    with open(destino, "wb") as salida:
        desplazamiento = 0
        while desplazamiento < filas:
            lote = min(por_pagina, filas - desplazamiento)
            consulta = urllib.parse.urlencode(
                {"$limit": lote, "$offset": desplazamiento, "$order": d["orden"]})
            url = "%s?%s" % (base, consulta)
            print("  [get] filas %d-%d" % (desplazamiento + 1, desplazamiento + lote))
            crudo = _pedir(url, d["tiempo_espera_s"], d["reintentos"],
                           d["espera_entre_reintentos_s"])
            urls.append(url)

            if not crudo.strip():
                print("     el portal no devolvio mas filas; se corta aqui")
                break

            lineas = crudo.split(b"\n", 1)
            cabecera_pag = lineas[0]
            cuerpo = lineas[1] if len(lineas) > 1 else b""

            if encabezado is None:
                encabezado = cabecera_pag
                salida.write(encabezado + b"\n")
            elif cabecera_pag != encabezado:
                raise SystemExit(
                    "El encabezado cambio entre paginas. El esquema del portal\n"
                    "se movio durante la descarga; vuelva a ejecutar.\n"
                    "  esperado: %s\n  recibido: %s"
                    % (encabezado[:200], cabecera_pag[:200]))

            if not cuerpo.strip():
                print("     pagina vacia; el portal no tiene mas filas")
                break
            if not cuerpo.endswith(b"\n"):
                cuerpo += b"\n"
            salida.write(cuerpo)
            filas_pag = cuerpo.count(b"\n")
            total_filas += filas_pag
            desplazamiento += lote
            if filas_pag < lote:
                print("     ultima pagina (%d filas)" % filas_pag)
                break

    if encabezado is None:
        raise SystemExit("El portal no devolvio nada. Revise la conectividad.")
    return {"urls": urls, "filas_aprox": total_filas,
            "columnas": encabezado.decode("utf-8", "replace").strip().split(",")}


def contar_filas_y_columnas(ruta):
    """Cuenta lineas de datos y columnas del encabezado. Lectura por bloques.

    Es un conteo de LINEAS, no de registros CSV: un campo con salto de linea
    dentro de comillas cuenta de mas. Se declara asi en el manifiesto.
    """
    with open(ruta, "rb") as fh:
        primera = fh.readline()
        columnas = primera.decode("utf-8", "replace").rstrip("\r\n").split(",")
        lineas = 0
        while True:
            trozo = fh.read(1024 * 1024)
            if not trozo:
                break
            lineas += trozo.count(b"\n")
        # si el archivo no termina en \n, la ultima linea no se conto
        fh.seek(0, os.SEEK_END)
        tam = fh.tell()
        if tam > len(primera):
            fh.seek(-1, os.SEEK_END)
            if fh.read(1) != b"\n":
                lineas += 1
    return lineas, columnas


# --------------------------------------------------------------------------
# 5. La carga
# --------------------------------------------------------------------------

def resolver_clave(cfg, s3, cubo, fecha, sha_nuevo, nuevo_lote):
    """Decide en que clave escribir, o si no hay que escribir nada.

    Devuelve (clave, accion) donde accion es 'cargar', 'omitir' o 'conflicto'.
    """
    slug = cfg["fuente"]["slug"]
    ext = cfg["fuente"]["extension"]

    lote = 1
    while True:
        archivo = comun.nombre_archivo(slug, fecha, ext, lote)
        clave = comun.clave_cruda(slug, fecha, archivo)
        meta = comun.objeto(s3, cubo, clave)

        if meta is None:
            return clave, "cargar"

        sha_guardado = (meta.get("Metadata") or {}).get("sha256")
        if sha_guardado == sha_nuevo:
            return clave, "omitir"

        if not nuevo_lote:
            return clave, "conflicto"
        lote += 1
        if lote > 99:
            raise SystemExit("Mas de 99 lotes el mismo dia. Revise que pasa.")


def construir_manifiesto(cfg, clave, fecha_ingesta, sha, tam, filas, columnas,
                         origen, urls):
    f = cfg["fuente"]
    return {
        "_que_es_esto": ("Ficha tecnica del objeto hermano. Su clave es la de "
                         "los datos mas '%s'."
                         % cfg["ingesta"]["sufijo_manifiesto"]),
        "clave_datos": clave,
        "capa": "cruda",
        "inmutable": True,
        "fuente": {
            "slug": f["slug"],
            "nombre": f["nombre"],
            "organismo": f["organismo"],
            "dataset_id": f["dataset_id"],
            "portal": f["portal"],
            "licencia": f["licencia"],
            "atribucion": f["atribucion"],
        },
        "ingesta": {
            "instante_utc": fecha_ingesta.isoformat(),
            "fecha_particion": "anio=%04d/mes=%02d/dia=%02d"
                               % (fecha_ingesta.year, fecha_ingesta.month,
                                  fecha_ingesta.day),
            "origen": origen,
            "urls_descarga": urls,
            "script": "src/ingesta/cargar_cruda.py",
            "version_script": VERSION_SCRIPT,
        },
        "contenido": {
            "formato": f["formato"],
            "bytes": tam,
            "sha256": sha,
            "filas_datos": filas,
            "_nota_filas": ("Conteo de lineas menos el encabezado. Un campo con "
                            "salto de linea entre comillas contaria de mas."),
            "columnas_n": len(columnas),
            "columnas": columnas,
        },
        "linaje": {
            "transformaciones": ["union de paginas conservando un solo encabezado"]
                                if origen == "portal" else [],
            "_nota": ("La capa cruda no transforma contenido. Lo unico que se "
                      "hace al descargar por paginas es pegar las paginas y "
                      "quitar los encabezados repetidos."),
        },
    }


def main():
    p = argparse.ArgumentParser(description="Ingesta a la capa cruda del lago")
    p.add_argument("--config", help="ruta a lago.json")
    p.add_argument("--archivo", help="usar un CSV local en vez de descargar")
    p.add_argument("--filas", type=int, help="filas a descargar del portal")
    p.add_argument("--fecha", help="fecha de particion YYYY-MM-DD (por defecto hoy UTC)")
    p.add_argument("--nuevo-lote", action="store_true",
                   help="si ya hay un objeto distinto ese dia, escribir un lote nuevo")
    p.add_argument("--solo-lago", action="store_true",
                   help="crear cubos y versionado, sin cargar datos")
    args = p.parse_args()

    cfg = comun.cargar_config(args.config)
    s3 = comun.cliente_s3(cfg)

    print("=" * 68)
    print("INGESTA A LA CAPA CRUDA - %s" % cfg["fuente"]["nombre"])
    print("=" * 68)

    if not comun.esperar_almacenamiento(s3):
        raise SystemExit(
            "No hay respuesta del almacenamiento de objetos en %s\n"
            "  Levantelo con:  docker compose up -d"
            % os.environ.get("LAGO_ENDPOINT", cfg["almacenamiento"]["endpoint_url"]))

    capas = preparar_lago(cfg, s3)
    if args.solo_lago:
        print("\n[ok] lago preparado. Sin cargar datos (--solo-lago).")
        return 0

    # -- fecha de particion
    if args.fecha:
        try:
            fecha = datetime.strptime(args.fecha, "%Y-%m-%d").replace(
                tzinfo=timezone.utc)
        except ValueError:
            raise SystemExit("--fecha debe ser YYYY-MM-DD")
    else:
        fecha = comun.ahora_utc()
    instante = comun.ahora_utc()

    # -- obtener la fuente
    print("\n[fuente]")
    if args.archivo:
        local = Path(args.archivo).expanduser().resolve()
        if not local.exists():
            raise SystemExit("No existe el archivo: %s" % local)
        origen, urls = "archivo_local", []
        print("  archivo local: %s" % local)
    else:
        filas = args.filas or cfg["descarga"]["filas_a_descargar"]
        local = DESCARGAS / ("%s_%s.%s" % (cfg["fuente"]["slug"],
                                           fecha.strftime("%Y%m%d"),
                                           cfg["fuente"]["extension"]))
        print("  descargando %d filas de %s" % (filas, cfg["fuente"]["portal"]))
        info = descargar(cfg, filas, local)
        origen, urls = "portal", info["urls"]

    filas_datos, columnas = contar_filas_y_columnas(local)
    filas_datos = max(filas_datos - 1, 0)          # menos el encabezado
    tam = local.stat().st_size
    sha = comun.sha256_archivo(local)
    print("  %s | %d filas | %d columnas" % (comun.humano(tam), filas_datos,
                                             len(columnas)))
    print("  sha256 %s" % sha)

    # -- decidir donde escribir
    cubo = comun.nombre_cubo(cfg, "cruda")
    clave, accion = resolver_clave(cfg, s3, cubo, fecha, sha, args.nuevo_lote)

    print("\n[destino]")
    print("  s3://%s/%s" % (cubo, clave))

    if accion == "omitir":
        vs = comun.versiones(s3, cubo, clave)
        print("\n[ok] ese objeto ya esta en el lago con el mismo sha256.")
        print("     No se carga nada. Versiones de la clave: %d" % len(vs))
        print("     Esto es la reejecucion sin duplicar: la segunda corrida")
        print("     no crea un objeto nuevo ni una version nueva.")
        escribir_evidencia(cfg, capas, cubo, clave, sha, tam, filas_datos,
                           len(columnas), instante, "omitida_por_identica")
        return 0

    if accion == "conflicto":
        raise SystemExit(
            "\nCONFLICTO. Ya hay un objeto en esa clave con contenido DISTINTO.\n"
            "  clave: s3://%s/%s\n\n"
            "  La capa cruda es inmutable: este script no lo sobrescribe.\n"
            "  Si de verdad es un lote nuevo del mismo dia (el portal publico\n"
            "  una correccion, o descargaron mas filas), vuelvan a ejecutar con:\n"
            "      python3 src/ingesta/cargar_cruda.py --nuevo-lote\n"
            "  y quedara como *_lote-02.%s, sin tocar el anterior."
            % (cubo, clave, cfg["fuente"]["extension"]))

    # -- cargar
    print("  subiendo...")
    with open(local, "rb") as fh:
        s3.put_object(
            Bucket=cubo, Key=clave, Body=fh,
            ContentType="text/csv; charset=utf-8",
            Metadata={"sha256": sha,
                      "filas": str(filas_datos),
                      "origen": origen,
                      "ingesta-utc": instante.isoformat(),
                      "version-script": VERSION_SCRIPT},
        )

    manifiesto = construir_manifiesto(cfg, clave, instante, sha, tam,
                                      filas_datos, columnas, origen, urls)
    clave_man = comun.clave_manifiesto(cfg, clave)
    s3.put_object(Bucket=cubo, Key=clave_man,
                  Body=json.dumps(manifiesto, ensure_ascii=False,
                                  indent=2).encode("utf-8"),
                  ContentType="application/json; charset=utf-8")

    # -- comprobar lo cargado leyendo de vuelta
    meta = comun.objeto(s3, cubo, clave)
    if meta["ContentLength"] != tam:
        raise SystemExit("El objeto subido no mide lo mismo que el archivo local.")
    if (meta.get("Metadata") or {}).get("sha256") != sha:
        raise SystemExit("El sha256 del objeto no coincide con el local.")

    print("\n[ok] cargado y verificado")
    print("     datos      s3://%s/%s" % (cubo, clave))
    print("     manifiesto s3://%s/%s" % (cubo, clave_man))
    escribir_evidencia(cfg, capas, cubo, clave, sha, tam, filas_datos,
                       len(columnas), instante, "cargada")
    return 0


def escribir_evidencia(cfg, capas, cubo, clave, sha, tam, filas, n_col,
                       instante, resultado):
    comun.DOCS.mkdir(parents=True, exist_ok=True)
    salida = comun.DOCS / "evidencia_ingesta.json"
    with open(salida, "w", encoding="utf-8") as fh:
        json.dump({
            "_generado_por": "src/ingesta/cargar_cruda.py",
            "_no_editar": "Se regenera en cada corrida.",
            "instante_utc": instante.isoformat(),
            "resultado": resultado,
            "capas": capas,
            "objeto": {"cubo": cubo, "clave": clave, "uri": "s3://%s/%s" % (cubo, clave),
                       "sha256": sha, "bytes": tam, "filas": filas, "columnas": n_col},
        }, fh, ensure_ascii=False, indent=2)
    print("     evidencia  docs/evidencia_ingesta.json")


if __name__ == "__main__":
    sys.exit(main())
