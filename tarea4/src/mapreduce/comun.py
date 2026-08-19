#!/usr/bin/env python3
"""
Utilidades compartidas por mapper, combiner y reducer.

Este archivo se envia al cluster junto con los demas con la opcion -files de
Hadoop Streaming, por lo que en la tarea queda en el directorio de trabajo y
se importa normalmente. Solo biblioteca estandar: el cluster no necesita
instalar nada.

Formato del par intermedio (identico a la salida del combinador, por diseno):

    clave \t suma \t conteo

Que el mapper emita ya "suma y conteo" en vez de un valor suelto es lo que
permite que el combinador sea opcional: el reducer consume exactamente el
mismo formato venga o no venga por un combinador. Y es lo que evita el error
del promedio de promedios, porque nadie divide hasta la reduccion final.
"""

import csv
import io
import json
import os
import sys

SEP = "\t"


# --------------------------------------------------------------------------
# Configuracion
# --------------------------------------------------------------------------

def cargar_esquema(nombre="esquema.json"):
    """Lee esquema.json desde el directorio de trabajo de la tarea.

    Hadoop Streaming copia los archivos de -files al directorio de trabajo de
    cada contenedor, asi que la ruta relativa funciona tanto en local como en
    el cluster. La variable T4_ESQUEMA permite apuntar a otro archivo sin
    tocar el codigo.
    """
    ruta = os.environ.get("T4_ESQUEMA", nombre)
    if not os.path.exists(ruta):
        # Ejecucion local desde la raiz del repositorio.
        alterno = os.path.join("src", "mapreduce", nombre)
        if os.path.exists(alterno):
            ruta = alterno
        else:
            raise SystemExit(
                "No se encontro %s. En el cluster debe ir en -files; en local "
                "ejecute desde la raiz del repositorio." % nombre
            )
    with open(ruta, "r", encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
# Contadores de Hadoop
# --------------------------------------------------------------------------

def contador(nombre, incremento=1, grupo="T4"):
    """Incrementa un contador propio del trabajo.

    Hadoop Streaming lee estas lineas de stderr. Aparecen despues en la salida
    del trabajo junto a los contadores del framework, que es de donde se saca
    Reduce shuffle bytes.
    """
    sys.stderr.write("reporter:counter:%s,%s,%d\n" % (grupo, nombre, incremento))


def latido(mensaje="procesando"):
    """Evita que una tarea larga sin salida sea marcada como colgada."""
    sys.stderr.write("reporter:status:%s\n" % mensaje)


# --------------------------------------------------------------------------
# Lectura de la fuente
# --------------------------------------------------------------------------

def partir_linea(linea, delimitador=","):
    """Parte una linea respetando comillas.

    Se usa csv sobre una sola linea en lugar de linea.split(delimitador)
    porque en fuentes reales los campos de texto traen el delimitador dentro
    de comillas y un split ingenuo corre todas las columnas de lugar.
    """
    return next(csv.reader(io.StringIO(linea), delimiter=delimitador))


def normalizar_clave(valor, cfg):
    clave = valor.strip()
    if cfg.get("normalizar_clave", True):
        clave = " ".join(clave.split()).upper()
    if not clave:
        clave = cfg.get("clave_vacia", "(SIN DATO)")
    # La clave no puede contener el separador: rompería el particionador.
    return clave.replace(SEP, " ")


def a_numero(valor, cfg):
    """Convierte el campo de valor a float o devuelve None si no es numerico.

    Devolver None en vez de lanzar excepcion es deliberado: la linea de
    encabezado y las filas sucias se descartan por esta misma via y quedan
    registradas en un contador, en lugar de tumbar la tarea.
    """
    texto = valor.strip()
    if not texto:
        return None
    for simbolo in cfg.get("quitar_simbolos", ["$", " ", "%"]):
        texto = texto.replace(simbolo, "")
    if cfg.get("separador_miles"):
        texto = texto.replace(cfg["separador_miles"], "")
    if cfg.get("separador_decimal", ".") != ".":
        texto = texto.replace(cfg["separador_decimal"], ".")
    try:
        return float(texto)
    except ValueError:
        return None


def leer_par(linea, cfg):
    """Devuelve (clave, valor) o None si la linea no aporta al agregado."""
    campos = partir_linea(linea, cfg.get("delimitador", ","))
    i_clave = cfg["indice_clave"]
    i_valor = cfg["indice_valor"]
    if len(campos) <= max(i_clave, i_valor):
        return None
    numero = a_numero(campos[i_valor], cfg)
    if numero is None:
        return None
    return normalizar_clave(campos[i_clave], cfg), numero


# --------------------------------------------------------------------------
# Agregacion parcial compartida por combinador y reductor
# --------------------------------------------------------------------------

def agrupar(lineas):
    """Agrupa la entrada ya ordenada por clave y acumula suma y conteo.

    Hadoop entrega al combinador y al reductor las lineas ordenadas por clave,
    asi que basta con acumular mientras la clave no cambie: nunca se guarda en
    memoria mas de un grupo. Esa es la razon por la que el modelo escala.
    """
    clave_actual = None
    suma = 0.0
    conteo = 0
    for linea in lineas:
        linea = linea.rstrip("\n")
        if not linea:
            continue
        partes = linea.split(SEP)
        if len(partes) == 3:
            clave, s, c = partes[0], partes[1], partes[2]
        elif len(partes) == 2:  # tolera "clave \t valor" suelto
            clave, s, c = partes[0], partes[1], "1"
        else:
            contador("intermedio_malformado")
            continue
        try:
            s = float(s)
            c = int(c)
        except ValueError:
            contador("intermedio_malformado")
            continue
        if clave != clave_actual:
            if clave_actual is not None:
                yield clave_actual, suma, conteo
            clave_actual, suma, conteo = clave, 0.0, 0
        suma += s
        conteo += c
    if clave_actual is not None:
        yield clave_actual, suma, conteo


def formatear(numero):
    """Serializa la suma sin notacion cientifica y sin decimales inutiles."""
    if numero == int(numero) and abs(numero) < 1e15:
        return str(int(numero))
    return repr(round(numero, 6))
