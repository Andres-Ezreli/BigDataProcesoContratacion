#!/usr/bin/env python3
"""
Proyeccion de almacenamiento y factor de replica — T3.

Lee src/fuente.json (los datos de la ficha T1 del equipo), calcula la
proyeccion a N meses para cada factor de replica y escribe la tabla en
docs/tabla-proyeccion.md.

Uso:
    python src/proyeccion.py

Sin dependencias externas: solo biblioteca estandar. Cualquier persona con
Python 3.8+ y este repositorio llega exactamente a las mismas cifras.

Formulas (identicas a las del enunciado, seccion 3):
    V_n     = V_0 * (1 + g) ** n          volumen logico proyectado
    S_fis   = V_n * R                     almacenamiento fisico
    bloques = ceil(tam_archivo / tam_bloque)
    fallos  = R - 1                       nodos que se pueden perder
"""

import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "src" / "fuente.json"
SALIDA = RAIZ / "docs" / "tabla-proyeccion.md"


# ---------------------------------------------------------------- calculos

def volumen_proyectado(v0: float, g: float, meses: int) -> float:
    """Crecimiento compuesto mensual. g = 0.04 significa 4 % al mes."""
    return v0 * (1 + g) ** meses


def almacenamiento_fisico(v_logico: float, r: int) -> float:
    """Cada replica es una copia completa: el disco se multiplica por R."""
    return v_logico * r


def bloques_por_archivo(tam_archivo_mb: float, tam_bloque_mb: float) -> int:
    """HDFS parte el archivo en bloques; el ultimo queda parcialmente lleno."""
    return math.ceil(tam_archivo_mb / tam_bloque_mb)


def nodos_tolerados(r: int) -> int:
    """Con factor R sobreviven R-1 caidas simultaneas sin perder el dato."""
    return r - 1


# ------------------------------------------------------------------ salida

def construir_tabla(cfg: dict) -> str:
    v0 = cfg["volumen_actual_gb"]
    g = cfg["crecimiento_mensual"]
    meses = cfg["meses_proyeccion"]
    tam_archivo = cfg["tamano_archivo_tipico_mb"]
    tam_bloque = cfg["tamano_bloque_mb"]
    costo = cfg["costo_gb_mes"]
    moneda = cfg["moneda"]

    v_n = volumen_proyectado(v0, g, meses)
    bloques = bloques_por_archivo(tam_archivo, tam_bloque)
    ultimo_bloque = tam_archivo - (bloques - 1) * tam_bloque

    lineas = []
    lineas.append("<!-- GENERADO POR src/proyeccion.py — NO EDITAR A MANO -->")
    lineas.append("")
    lineas.append("### Datos de entrada (ficha T1)")
    lineas.append("")
    lineas.append("| Parametro | Valor |")
    lineas.append("|---|---|")
    lineas.append(f"| Fuente | {cfg['fuente']} |")
    lineas.append(f"| Licencia | {cfg['licencia']} |")
    lineas.append(f"| Formato | {cfg['formato']} |")
    lineas.append(f"| Volumen actual (V0) | {v0:,.2f} GB |")
    lineas.append(f"| Crecimiento mensual (g) | {g:.2%} |")
    lineas.append(f"| Horizonte (n) | {meses} meses |")
    lineas.append(f"| Archivo tipico | {tam_archivo:,.0f} MB |")
    lineas.append(f"| Tamano de bloque HDFS | {tam_bloque:,.0f} MB |")
    lineas.append(f"| Costo de almacenamiento | {costo} {moneda} por GB-mes |")
    lineas.append("")
    lineas.append("### Volumen logico proyectado")
    lineas.append("")
    lineas.append(
        f"V{meses} = {v0:,.2f} x (1 + {g}) ^ {meses} = **{v_n:,.2f} GB** "
        f"(factor de crecimiento: {(1 + g) ** meses:.4f}x)"
    )
    lineas.append("")
    lineas.append(f"### Almacenamiento fisico por factor de replica (a {meses} meses)")
    lineas.append("")
    lineas.append(
        "| R | Almacenamiento fisico | Sobrecosto vs R=1 | Nodos que puede perder | "
        f"Costo mensual ({moneda}) | Bloques fisicos por archivo |"
    )
    lineas.append("|---|---|---|---|---|---|")
    base = almacenamiento_fisico(v_n, 1)
    for r in cfg["factores_replica"]:
        fis = almacenamiento_fisico(v_n, r)
        lineas.append(
            f"| {r} | {fis:,.2f} GB | +{fis - base:,.2f} GB | "
            f"{nodos_tolerados(r)} | {fis * costo:,.2f} | {bloques * r} |"
        )
    lineas.append("")
    lineas.append("### Bloques HDFS")
    lineas.append("")
    if bloques == 1:
        reparto = (
            f"El archivo cabe en **un solo bloque**, que queda con "
            f"{ultimo_bloque:,.2f} MB ocupados de {tam_bloque:,.0f} MB."
        )
    else:
        reparto = (
            f"Los primeros {bloques - 1} van llenos a {tam_bloque:,.0f} MB "
            f"y el ultimo queda con {ultimo_bloque:,.2f} MB ocupados."
        )
    lineas.append(
        f"ceil({tam_archivo:,.2f} MB / {tam_bloque:,.0f} MB) = "
        f"**{bloques} bloque{'s' if bloques != 1 else ''}** por archivo. {reparto} "
        f"HDFS no reserva el bloque completo en disco: el remanente no se desperdicia."
    )
    lineas.append("")
    return "\n".join(lineas)


def main() -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    tabla = construir_tabla(cfg)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(tabla + "\n", encoding="utf-8")
    print(tabla)
    print(f"\n[ok] Escrito en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
