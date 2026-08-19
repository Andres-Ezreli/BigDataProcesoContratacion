#!/usr/bin/env python3
"""
Combinador: agregacion local en el nodo del map, antes de la mezcla.

Emite exactamente el mismo formato que recibe:

    clave \t suma_parcial \t conteo_parcial

NO PROMEDIA. Es el error que el enunciado marca como silencioso: el promedio
de promedios no es el promedio, salvo que todos los grupos tengan el mismo
tamano. Como suma y conteo si son asociativos y conmutativos, el combinador
puede ejecutarse cero, una o varias veces sobre los mismos datos sin cambiar
el resultado final. El framework no garantiza cuantas veces lo llama, y esa es
justamente la razon por la que la operacion tiene que ser asociativa.

El efecto sobre la mezcla es que cada nodo deja de emitir un par por registro
y pasa a emitir un par por clave distinta que vio.
"""

import sys

from comun import SEP, agrupar, contador, formatear


def main():
    salida = sys.stdout
    for clave, suma, conteo in agrupar(sys.stdin):
        salida.write("%s%s%s%s%d\n" % (clave, SEP, formatear(suma), SEP, conteo))
        contador("claves_combinadas")


if __name__ == "__main__":
    main()
