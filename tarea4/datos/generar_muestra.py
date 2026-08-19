#!/usr/bin/env python3
"""
Genera datos/muestra.csv: una muestra sintetica y DETERMINISTA.

Existe por una sola razon: que quien clone el repositorio pueda ejecutar el
trabajo completo y reproducir las cifras aunque no tenga a la mano la fuente
real. La muestra imita el rasgo que importa para T4 -unas pocas claves
concentran la mayor parte de los registros- para que el analisis de sesgo
tenga algo que analizar.

>>> LAS CIFRAS QUE SALEN DE ESTA MUESTRA SON DE DEMOSTRACION. <<<
Al cargar la fuente real del proyecto, vuelvan a correr todo el flujo y
reemplacen cada numero del informe.

Uso:
    python3 datos/generar_muestra.py
"""

import csv
import os
import random

SALIDA = os.path.join(os.path.dirname(__file__), "muestra.csv")
REGISTROS = 20000
SEMILLA = 20260814  # fija: dos ejecuciones producen el archivo identico

# Peso relativo de cada clave. Deliberadamente sesgado.
DEPARTAMENTOS = [
    ("BOGOTA D.C.", 34), ("ANTIOQUIA", 18), ("VALLE DEL CAUCA", 11),
    ("CUNDINAMARCA", 8), ("SANTANDER", 6), ("ATLANTICO", 5),
    ("BOLIVAR", 3), ("NARINO", 3), ("TOLIMA", 2), ("HUILA", 2),
    ("CALDAS", 2), ("META", 1), ("CESAR", 1), ("CAUCA", 1),
    ("BOYACA", 1), ("RISARALDA", 1), ("QUINDIO", 1),
    ("AMAZONAS", 0.3), ("VAUPES", 0.2), ("GUAINIA", 0.2),
]
MODALIDADES = ["Contratacion directa", "Licitacion publica",
               "Minima cuantia", "Seleccion abreviada"]


def formato_cop(valor):
    """1234567.89 -> '1.234.567,89' (miles con punto, decimal con coma)."""
    entero, decimal = divmod(round(valor, 2), 1)
    miles = "{:,.0f}".format(entero).replace(",", ".")
    return "%s,%02d" % (miles, round(decimal * 100))


def main():
    rng = random.Random(SEMILLA)
    claves = [d for d, _ in DEPARTAMENTOS]
    pesos = [p for _, p in DEPARTAMENTOS]

    with open(SALIDA, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id_contrato", "departamento", "entidad",
                    "modalidad", "valor_contrato", "fecha_firma"])
        for i in range(REGISTROS):
            depto = rng.choices(claves, weights=pesos, k=1)[0]
            # Distribucion lognormal: pocos contratos muy grandes, como en
            # la vida real. El promedio por clave no es trivialmente igual.
            valor = rng.lognormvariate(17.2, 1.1)
            w.writerow([
                "C-%06d" % i,
                depto,
                "Entidad %03d" % rng.randint(1, 400),
                rng.choice(MODALIDADES),
                formato_cop(valor),
                "2025-%02d-%02d" % (rng.randint(1, 12), rng.randint(1, 28)),
            ])

    print("[ok] %s con %d registros (semilla %d)" % (SALIDA, REGISTROS, SEMILLA))


if __name__ == "__main__":
    main()
