#!/usr/bin/env python3
"""
Reduce de la agregacion del proyecto.

Recibe todas las parejas de una misma clave, ya ordenadas por Hadoop, y emite
una linea por clave:

    clave \t promedio \t suma \t conteo

El promedio se calcula unicamente aqui, sobre la suma total y el conteo total.
Se emiten tambien suma y conteo porque son los que permiten verificar el
resultado a mano y porque el conteo es el que revela el sesgo de la clave.

Uso local (el sort simula lo que hace la mezcla del framework):
    cat datos/muestra.csv | python3 src/mapreduce/mapper.py \
        | sort -t$'\t' -k1,1 | python3 src/mapreduce/reducer.py
"""

import sys

from comun import SEP, agrupar, cargar_esquema, contador


def main():
    # La suma en coma flotante no es asociativa: sumar en otro orden cambia
    # los ultimos bits. Con y sin combinador el orden cambia, y con otro
    # numero de splits tambien. Redondear a una precision fija es lo que
    # hace que la salida sea identica byte a byte en cualquier ejecucion,
    # que es lo que exige el criterio de reproducibilidad.
    decimales = cargar_esquema()["agregacion"].get("decimales_salida", 2)
    fmt = "%%.%df" % decimales

    salida = sys.stdout
    for clave, suma, conteo in agrupar(sys.stdin):
        if conteo == 0:
            contador("claves_sin_conteo")
            continue
        promedio = suma / conteo
        salida.write(
            "%s%s%s%s%s%s%d\n"
            % (clave, SEP, fmt % promedio, SEP, fmt % suma, SEP, conteo)
        )
        contador("claves_finales")


if __name__ == "__main__":
    main()
