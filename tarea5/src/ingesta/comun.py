#!/usr/bin/env python3
"""
Piezas compartidas de la ingesta al lago: configuracion, cliente S3,
construccion de rutas y utilidades de integridad.

Aqui vive LA REGLA DE RUTAS. Si alguien quiere saber donde queda un objeto,
la respuesta esta en `clave_cruda()` y en nada mas. Ese es el punto: una sola
funcion, treinta lineas, que cualquiera puede leer.

No se ejecuta directo. Lo usan cargar_cruda.py, demostrar_versionado.py y
verificar_lago.py.
"""

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import boto3
    from botocore.client import Config
    from botocore.exceptions import ClientError, EndpointConnectionError
except ImportError:  # pragma: no cover
    sys.exit("Falta boto3. Instalen con:  pip install -r requisitos.txt")


# --------------------------------------------------------------------------
# Rutas del proyecto
# --------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parents[2]          # .../tarea5
CONFIG_POR_DEFECTO = RAIZ / "config" / "lago.json"
DOCS = RAIZ / "docs"

# Credenciales: las mismas del docker-compose.yml. Son de desarrollo local,
# no hay nada que proteger; se pueden sobrescribir por variable de entorno.
USUARIO_POR_DEFECTO = "minioadmin"
CLAVE_POR_DEFECTO = "minioadmin"


def cargar_config(ruta=None):
    """Lee config/lago.json. Es la unica fuente de verdad del script."""
    ruta = Path(ruta) if ruta else CONFIG_POR_DEFECTO
    if not ruta.exists():
        sys.exit("No encuentro la configuracion en %s" % ruta)
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def credenciales():
    """MINIO_ROOT_* tiene prioridad; luego AWS_*; luego el valor de desarrollo."""
    usuario = (os.environ.get("MINIO_ROOT_USER")
               or os.environ.get("AWS_ACCESS_KEY_ID")
               or USUARIO_POR_DEFECTO)
    clave = (os.environ.get("MINIO_ROOT_PASSWORD")
             or os.environ.get("AWS_SECRET_ACCESS_KEY")
             or CLAVE_POR_DEFECTO)
    return usuario, clave


def cliente_s3(cfg):
    """Cliente boto3 apuntado al almacenamiento de objetos del docker-compose."""
    alm = cfg["almacenamiento"]
    usuario, clave = credenciales()
    endpoint = os.environ.get("LAGO_ENDPOINT", alm["endpoint_url"])
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=usuario,
        aws_secret_access_key=clave,
        region_name=alm["region"],
        # path-style: MinIO no resuelve cubos por subdominio en local.
        config=Config(signature_version="s3v4",
                      s3={"addressing_style": "path"},
                      retries={"max_attempts": 3}),
    )


def esperar_almacenamiento(s3, intentos=30, espera=2):
    """MinIO tarda unos segundos en aceptar conexiones tras `docker compose up`."""
    for i in range(intentos):
        try:
            s3.list_buckets()
            return True
        except (EndpointConnectionError, ClientError, OSError) as exc:
            if i == 0:
                print("[..] esperando al almacenamiento de objetos (%s)"
                      % type(exc).__name__)
            time.sleep(espera)
    return False


# --------------------------------------------------------------------------
# LA CONVENCION DE RUTAS
# --------------------------------------------------------------------------

def nombre_cubo(cfg, capa):
    """Un cubo por capa:  <prefijo>-<capa>.  Ej: lago-cruda.

    La capa es el cubo, no un prefijo dentro del cubo. La direccion completa
    de un objeto crudo se lee entonces  s3://lago-cruda/<fuente>/anio=.../
    que es la convencion de referencia  cruda/<fuente>/anio=...  escribiendo
    la capa como nombre de cubo.
    """
    alm = cfg["almacenamiento"]
    if capa not in alm["capas"]:
        raise ValueError("Capa desconocida: %r. Las capas son %s"
                         % (capa, alm["capas"]))
    return "%s-%s" % (alm["prefijo_cubos"], capa)


def clave_cruda(slug, fecha, archivo):
    """La clave de un objeto en la capa cruda.

        <fuente>/anio=YYYY/mes=MM/dia=DD/<archivo>

    `fecha` es la FECHA DE INGESTA en UTC (ver docs/T5_lago.md, seccion 4).
    Mes y dia van con cero a la izquierda, siempre dos digitos: sin eso
    'mes=9' y 'mes=09' serian dos carpetas distintas y el orden alfabetico
    del listado dejaria de coincidir con el orden cronologico.
    """
    return "%s/anio=%04d/mes=%02d/dia=%02d/%s" % (
        slug, fecha.year, fecha.month, fecha.day, archivo)


def nombre_archivo(slug, fecha, extension, lote=1):
    """El nombre del objeto dentro de la particion.

        <fuente>_<YYYYMMDD>.<ext>          el lote 1 del dia
        <fuente>_<YYYYMMDD>_lote-02.<ext>  un segundo lote del mismo dia

    Es DETERMINISTA a proposito: dada la fuente y la fecha, el nombre se
    deduce. Si llevara la hora, reejecutar el script el mismo dia crearia un
    objeto nuevo cada vez y la capa cruda se llenaria de copias.
    """
    base = "%s_%04d%02d%02d" % (slug, fecha.year, fecha.month, fecha.day)
    if lote > 1:
        base += "_lote-%02d" % lote
    return "%s.%s" % (base, extension)


def clave_manifiesto(cfg, clave_datos):
    """El manifiesto de cualquier objeto es su misma clave mas el sufijo.

    Regla sin excepciones: si el dato esta en  ruta/archivo.csv, su ficha
    tecnica esta en  ruta/archivo.csv.manifiesto.json. No hay que buscarla.
    """
    return clave_datos + cfg["ingesta"]["sufijo_manifiesto"]


def ahora_utc():
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------
# Integridad y consultas al almacenamiento
# --------------------------------------------------------------------------

def sha256_archivo(ruta, bloque=1024 * 1024):
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        for trozo in iter(lambda: fh.read(bloque), b""):
            h.update(trozo)
    return h.hexdigest()


def sha256_bytes(datos):
    return hashlib.sha256(datos).hexdigest()


def objeto(s3, cubo, clave):
    """Devuelve los metadatos del objeto, o None si no existe."""
    try:
        return s3.head_object(Bucket=cubo, Key=clave)
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
            return None
        raise


def leer_objeto(s3, cubo, clave, version_id=None):
    kwargs = {"Bucket": cubo, "Key": clave}
    if version_id:
        kwargs["VersionId"] = version_id
    return s3.get_object(**kwargs)["Body"].read()


def versiones(s3, cubo, clave):
    """Todas las versiones de una clave, de la mas nueva a la mas vieja."""
    resp = s3.list_object_versions(Bucket=cubo, Prefix=clave)
    encontradas = [v for v in resp.get("Versions", []) if v["Key"] == clave]
    encontradas.sort(key=lambda v: v["LastModified"], reverse=True)
    return encontradas


def versionado_activo(s3, cubo):
    try:
        return s3.get_bucket_versioning(Bucket=cubo).get("Status") == "Enabled"
    except ClientError:
        return False


def humano(n_bytes):
    for unidad in ("B", "KiB", "MiB", "GiB"):
        if abs(n_bytes) < 1024 or unidad == "GiB":
            return "%.1f %s" % (n_bytes, unidad)
        n_bytes /= 1024.0
