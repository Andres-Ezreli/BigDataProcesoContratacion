# -*- coding: utf-8 -*-
"""Chequeo rapido antes de gastar 10 minutos en descargas.
Verifica que los cuatro scripts esten sanos y que el motor exponga todo lo que se le pide."""
import os, sys, re, ast, importlib

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
SCRIPTS = ["bd_s01.py", "ejecutar_todo.py", "generar_entregables.py", "construir_notebook.py"]
fallos = []

for f in SCRIPTS:
    ruta = os.path.join(AQUI, f)
    if not os.path.exists(ruta):
        fallos.append(f"falta el archivo {f}"); continue
    try:
        ast.parse(open(ruta, encoding="utf-8").read())
    except SyntaxError as e:
        fallos.append(f"{f}: error de sintaxis en la linea {e.lineno}: {e.msg}")

for paquete in ("pandas", "numpy", "psutil"):
    try:
        importlib.import_module(paquete)
    except ImportError:
        fallos.append(f"falta la libreria {paquete}  ->  pip install {paquete}")

if not fallos:
    import bd_s01
    for f in SCRIPTS[1:]:
        texto = open(os.path.join(AQUI, f), encoding="utf-8").read()
        for nombre in sorted(set(re.findall(r"\bbd\.([A-Za-z_]\w*)", texto))):
            if not hasattr(bd_s01, nombre):
                fallos.append(f"{f} usa bd.{nombre}() pero bd_s01.py no lo define")

if fallos:
    print("AUTOCOMPROBACION: FALLA")
    for x in fallos:
        print("  -", x)
    raise SystemExit(1)
print("Autocomprobacion OK · los 4 scripts estan sanos y las librerias estan instaladas.")
