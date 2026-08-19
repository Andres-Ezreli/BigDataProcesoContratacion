# -*- coding: utf-8 -*-
"""Construye notebooks/s01_perfilamiento.ipynb y lo EJECUTA para que quede con salidas visibles."""
import os, sys, nbformat as nbf
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(RAIZ, "notebooks", "s01_perfilamiento.ipynb")
os.makedirs(os.path.dirname(DEST), exist_ok=True)
md, code = new_markdown_cell, new_code_cell
c = []

c.append(md("""# Sesion 1 · Naturaleza de los datos masivos
### ¿Cuando un problema deja de caber en un solo computador?

**IFPN0025 · Big Data e Ingenieria de Datos** · Universidad Ean · Andres · `S01_P4_v1`

Este notebook cubre el **Nivel 1 (guiado)** y el **Nivel 2 (aplicado)**. El Nivel 3 y el reto de
negocio estan en `resultados/nivel3_matriz.md` y `resultados/reto_negocio.md`, sostenidos por las
mediciones que se producen aqui.

**Como se ejecuta:** *Kernel → Restart & Run All*. Si hay internet descarga las fuentes reales; si no,
activa el plan de contingencia de la seccion 2.4 y lo declara."""))

c.append(md("## 1.2 · Celda de verificacion del entorno\n\nSi algo falla aqui, todo lo demas fallara despues."))
c.append(code('''import sys, platform
print("Python:", sys.version.split()[0])
print("Sistema:", platform.system(), platform.release())

required_packages = ["pandas", "numpy", "psutil"]
missing_packages = []
for package_name in required_packages:
    try:
        __import__(package_name); print(f"OK · {package_name}")
    except ImportError:
        missing_packages.append(package_name); print(f"FALTA · {package_name}")
print("\\nInstale con:  pip install " + " ".join(missing_packages) if missing_packages else "\\nEntorno listo.")'''))

c.append(code('''import os, sys, math, json, time
import numpy as np, pandas as pd, psutil

def _hallar_raiz():
    """Encuentra la raiz del proyecto sin importar desde donde se lance el kernel.

    Jupyter clasico arranca el kernel en notebooks/, pero VS Code lo arranca en la
    carpeta del workspace. En vez de suponer, se busca hacia arriba la carpeta que
    contenga scripts/bd_s01.py.
    """
    candidatos = [os.getcwd()]
    archivo_vsc = globals().get("__vsc_ipynb_file__")
    if archivo_vsc:
        candidatos.append(os.path.dirname(os.path.dirname(os.path.abspath(archivo_vsc))))
    for inicio in candidatos:
        d = os.path.abspath(inicio)
        for _ in range(6):
            if os.path.isfile(os.path.join(d, "scripts", "bd_s01.py")):
                return d
            for sub in ("sesion01", "S01_entrega"):
                p = os.path.join(d, sub)
                if os.path.isfile(os.path.join(p, "scripts", "bd_s01.py")):
                    return p
            padre = os.path.dirname(d)
            if padre == d:
                break
            d = padre
    return None

RAIZ = _hallar_raiz()
if RAIZ is None:
    raise RuntimeError(
        "No encuentro scripts/bd_s01.py.\\n"
        f"Directorio actual: {os.getcwd()}\\n"
        "Ejecute antes:  import os; os.chdir(r'RUTA_A\\\\sesion01')")

sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import bd_s01 as bd

for d in ["data/raw", "data/synthetic", "resultados"]:
    os.makedirs(os.path.join(RAIZ, d), exist_ok=True)
print("Raiz del proyecto :", RAIZ)
print("Directorio actual :", os.getcwd())'''))

c.append(md("""## 3 · Las tres mediciones que sostienen todo

Definidas en `scripts/bd_s01.py` para que el notebook y los scripts usen exactamente el mismo codigo.

- **S0** — tamano real en disco, en GB.
- **k** — factor de expansion: cuantas veces crece el archivo al cargarse en memoria.
- **M** — memoria **util**, no memoria total.

> **La advertencia que decide el resultado.** `k` se mide con `df.memory_usage(deep=True).sum()`.
> Sin `deep=True`, pandas reporta 8 bytes por celda de texto (el puntero) y no la cadena apuntada.
> Todos los `k` convergen entonces a un valor bajo y falso, y **siempre por debajo**: el error empuja
> la decision hacia *todavia no hace falta invertir*, que es el sesgo mas peligroso posible."""))

c.append(code('''import inspect
for fn in (bd.get_file_size_gb, bd.measure_expansion_factor, bd.get_available_memory_gb):
    print(inspect.getsource(fn))'''))

c.append(md("### M · memoria util del equipo\n\n`M` es lo que queda, no lo que dice la etiqueta."))
c.append(code('''m_total = bd.get_total_memory_gb()
m_disp  = bd.get_available_memory_gb()
frac_so = 1 - m_disp / m_total
print(f"RAM total        : {m_total:6.2f} GB")
print(f"RAM disponible(M): {m_disp:6.2f} GB")
print(f"Consumido por SO y aplicaciones: {frac_so:.1%}")
print(f"\\nEscenario  8 GB -> M util = {bd.memoria_util(8,  frac_so):5.2f} GB")
print(f"Escenario 16 GB -> M util = {bd.memoria_util(16, frac_so):5.2f} GB")'''))

c.append(md("""## 2 · Las tres fuentes

Identificadores **verificados** contra la API de Socrata de `www.datos.gov.co` el 2026-07-24:

| Fuente | Identificador | Columnas | Filas totales | V esperada |
|---|---|---|---|---|
| SECOP II · Procesos de Contratacion | `p6dx-8zbt` | 59 | 8.878.158 | Volumen |
| IDEAM · Temperatura Ambiente del Aire | `sbwg-7ju4` | 12 | 21.710 registros **por dia** | Velocidad |
| GEIH · DANE | *sin API* | multiples archivos | por periodo | Variedad |

Patron de descarga: `https://www.datos.gov.co/resource/<ID>.csv?$limit=<N>`"""))

c.append(md("""### Nivel 1 · Pasos 1.1 y 1.2 · perfilamiento y medicion de k

El pipeline completo vive en `scripts/ejecutar_todo.py` para que sea reproducible fuera del notebook.
Esta celda **reutiliza** la corrida ya archivada; solo dispara el pipeline si aun no existe. Asi el
notebook se re-ejecuta en segundos y no vuelve a descargar 265 MB cada vez."""))
c.append(code('''import subprocess
RUTA_JSON = os.path.join(RAIZ, "resultados", "_resultados.json")
if os.path.exists(RUTA_JSON):
    print("Corrida existente encontrada. Se reutiliza (no se vuelve a descargar).")
    print("Para forzar una medicion nueva:  python scripts/ejecutar_todo.py --redescargar")
else:
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "ejecutar_todo.py")],
                       capture_output=True, text=True, cwd=RAIZ)
    print(r.stdout[-4000:]); print(r.stderr[-1500:] if r.returncode else "")

J = json.load(open(RUTA_JSON, encoding="utf-8"))
print(f"\\nEquipo   : {J['equipo']['etiqueta']} · {J['equipo']['so']} · pandas {J['equipo']['pandas']}")
print(f"Momento  : {J['equipo']['momento']}   Modo: {J['modo']}")
print(f"RAM      : {J['memoria']['total_gb']} GB totales · {J['memoria']['disponible_gb']} GB disponibles "
      f"({J['memoria']['fraccion_consumida_so']:.1%} consumido por el SO)")'''))

c.append(md("""#### Demostracion en vivo de la medicion de `k`

Para que el notebook no sea solo un lector de resultados, esta celda **vuelve a medir** `k` sobre el
archivo mas pequeno que haya en disco, y compara `deep=True` contra la version sin el argumento."""))
c.append(code('''cands = []
for sub in ("data/raw", "data/synthetic"):
    d = os.path.join(RAIZ, sub)
    if os.path.isdir(d):
        for r_, _, fs in os.walk(d):
            cands += [os.path.join(r_, f) for f in fs
                      if f.lower().endswith(".csv") and os.path.getsize(os.path.join(r_, f)) > 100_000]

if cands:
    # el archivo mas grande es el de mas texto libre: es donde deep=True mas importa
    ruta = max(cands, key=os.path.getsize)
    N = 50_000
    df_demo = pd.read_csv(ruta, nrows=N, low_memory=False)
    con_deep = df_demo.memory_usage(deep=True).sum()
    sin_deep = df_demo.memory_usage(deep=False).sum()
    n_obj = int((df_demo.dtypes == "object").sum())
    print(f"Archivo   : {os.path.relpath(ruta, RAIZ)}   (primeras {len(df_demo):,} filas)")
    print(f"Columnas  : {df_demo.shape[1]}  ·  de tipo object (texto): {n_obj}")
    print()
    print(f"  memory_usage(deep=True)  = {con_deep/1024**2:9.2f} MB   <- lo que REALMENTE ocupa")
    print(f"  memory_usage(deep=False) = {sin_deep/1024**2:9.2f} MB   <- lo que pandas reporta sin el argumento")
    print()
    if n_obj:
        print(f"  Sin deep=True se subestima la memoria {con_deep/sin_deep:.1f} veces.")
        print(f"  Diferencia absoluta: {(con_deep-sin_deep)/1024**2:,.1f} MB que no se estaban contando.")
    else:
        print("  Este archivo no tiene columnas de texto, por eso ambas cifras coinciden.")
        print("  La diferencia solo aparece cuando hay columnas object.")
    print()
    print("  El error SIEMPRE va en la misma direccion: subestima. Y por lo tanto empuja la")
    print("  conclusion hacia 'todavia no hace falta invertir', que es el sesgo mas caro")
    print("  posible en una decision de infraestructura.")
    del df_demo
else:
    print("No hay archivos en data/ para la demostracion en vivo.")
    print("Ejecute:  python scripts/ejecutar_todo.py")'''))

c.append(code('''for m in J["mediciones"]:
    f = m["fuente"]; v = J["extras"][f]["veracidad"]; ve = J["extras"][f]["velocidad"]
    print(f"— {f}")
    print(f"    volumen  : {m['filas_fuente_completa']:,} filas -> S0 proy. {m['S0_proyectado_gb']:.3f} GB, "
          f"k={m['k']} -> {m['memoria_necesaria_gb']:.2f} GB de RAM")
    print(f"    variedad : {m['columnas_texto']}/{m['columnas']} columnas de texto ({m['proporcion_texto']:.0%})")
    print(f"    veracidad: {v['prop_nulos_media']:.1%} nulos medios, {v['columnas_sobre_50pct_nulas']} columnas >50% nulas")
    print(f"    velocidad: {ve.get('registros_por_hora_observados','n/a')} registros/hora observados\\n")'''))

c.append(md("""## 5 · Nivel 2 · Horizonte de saturacion

$$t_{umbral} = \\frac{\\ln\\left(\\dfrac{M}{k \\cdot S_0}\\right)}{\\ln(1+g)}$$

**S0 es el de la fuente completa, no el de la muestra.** La muestra siempre cabe; por eso se proyecta
con `filas_totales / filas_muestra`. Y **M es la memoria util**, no la de la etiqueta."""))
c.append(code('''print(inspect.getsource(bd.compute_threshold_periods))
esc = list(J["memoria"]["escenarios"])
filas = []
for m in J["mediciones"]:
    f = m["fuente"]
    filas.append({"fuente": f, "k": m["k"], "S0_proy_GB": m["S0_proyectado_gb"],
                  "g": J["g"][f]["g"], **{f"t · M {e}": J["umbrales"][f][e] for e in esc}})
pd.DataFrame(filas)'''))

c.append(md("### Paso 2.3 · sensibilidad a `g` y a `k`\n\nUn `t_umbral` negativo no es un error: significa que la fuente **ya no cabe hoy**."))
c.append(code('''print("Sensibilidad a g (M = escenario de 16 GB):")
display(pd.DataFrame(J["sensibilidad_g"]).T)
print("\\nSensibilidad a k (misma fuente, mismo g):")
display(pd.DataFrame([J["sensibilidad_k"]]).T.rename(columns={0: "t_umbral (anos)"}))'''))

c.append(md("""**Lectura de las dos tablas.** `g` entra por `ln(1+g)` en el **denominador** y `k` por
`ln(k)` en el **numerador**. Por eso un error en `g` reescala el horizonte de forma suave, mientras
que un error en `k` puede **cambiarle el signo** — es decir, cambiar la decision de *tengo tiempo* a
*ya no cabe*. Y `k` es medible hoy en cinco minutos; `g` siempre es una proyeccion. El desarrollo
completo esta en `resultados/nivel2_sensibilidad.md`."""))

c.append(md("""### Entregables generados

Los documentos se escriben desde las cifras medidas: no hay numeros escritos a mano en ninguno."""))
c.append(code('''for f in sorted(os.listdir(os.path.join(RAIZ, "resultados"))):
    ruta = os.path.join(RAIZ, "resultados", f)
    if os.path.isfile(ruta):
        print(f"  {f:<38} {os.path.getsize(ruta)/1024:7.1f} KB")
print("\\nPara reescribirlos:  python scripts/generar_entregables.py")'''))

nb = new_notebook(cells=c, metadata={"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                     "language_info": {"name": "python"}})
nbf.write(nb, DEST)
print("escrito:", DEST)

if "--ejecutar" in sys.argv:
    from nbclient import NotebookClient
    nb = nbf.read(DEST, as_version=4)
    NotebookClient(nb, timeout=1800, kernel_name="python3",
                   resources={"metadata": {"path": os.path.join(RAIZ, "notebooks")}}).execute()
    nbf.write(nb, DEST)
    print("ejecutado con salidas visibles")
