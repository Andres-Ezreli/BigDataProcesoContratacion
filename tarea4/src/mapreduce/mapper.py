#!/usr/bin/env python3
"""
Map de la agregacion del proyecto.

Lee la fuente por stdin, linea a linea, y emite un par por registro valido:

    clave \t valor \t 1

Emite ya el par (suma, conteo) y no el valor suelto para que el combinador y
el reductor consuman el mismo formato, y para que el promedio se calcule solo
al final. El mapper no guarda estado entre lineas: cualquier registro se
procesa con memoria constante, que es lo que permite partir la entrada en
tantos bloques como haga falta.

Uso local:
    cat datos/muestra.csv | python3 src/mapreduce/mapper.py | head
"""

import sys

from comun import SEP, cargar_esquema, contador, formatear, leer_par


def main():
    cfg = cargar_esquema()["fuente"]
    salida = sys.stdout
    for linea in sys.stdin:
        par = leer_par(linea, cfg)
        if par is None:
            # Encabezado, fila sucia o valor no numerico. Queda contado para
            # poder justificar despues la diferencia entre registros de
            # entrada y registros de salida del map.
            contador("registros_descartados")
            continue
        clave, valor = par
        salida.write("%s%s%s%s1\n" % (clave, SEP, formatear(valor), SEP))
        contador("registros_emitidos")


if __name__ == "__main__":
    main()
