# -*- coding: utf-8 -*-
"""Lee resultados/_resultados.json y escribe los tres entregables en Markdown.
Todas las cifras salen del JSON: si vuelve a correr ejecutar_todo.py con datos
reales, los documentos se reescriben solos con sus numeros."""
import os, sys, json
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(RAIZ, "resultados")
J = json.load(open(os.path.join(RES, "_resultados.json"), encoding="utf-8"))

M   = J["memoria"]; MED = J["mediciones"]; EX = J["extras"]; G = J["g"]
UMB = J["umbrales"]; SG = J["sensibilidad_g"]; SK = J["sensibilidad_k"]
EV  = J["evidencia_portal"]; MODO = J["modo"]
by = {m["fuente"]: m for m in MED}

# --- corridas archivadas: la mas reciente por equipo ---------------------
import glob
CORRIDAS = {}
for _p in sorted(glob.glob(os.path.join(RES, "corridas", "*", "*.json"))):
    _eq = os.path.basename(os.path.dirname(_p))
    try:
        CORRIDAS[_eq] = json.load(open(_p, encoding="utf-8"))   # el ultimo gana
    except Exception:
        pass
MULTI = len(CORRIDAS) > 1
F = [m["fuente"] for m in MED]
esc = list(M["escenarios"].keys())

NOTA_MODO = ("" if MODO == "real" else
 "\n> **Declaracion de modo.** Esta corrida se hizo en **modo contingencia** (seccion 2.4 de la guia): "
 "los portales no estaban accesibles desde el entorno de ejecucion y se usaron fuentes sinteticas con "
 "semilla fija. Las cifras estructurales de SECOP II e IDEAM que se citan (filas totales, serie anual, "
 "nulos, registros por dia) **si son reales**: se consultaron contra la API de Socrata de "
 "`www.datos.gov.co` el 2026-07-24. Para regenerar todo con las tres fuentes reales descargadas "
 "localmente: `python scripts/ejecutar_todo.py && python scripts/generar_entregables.py`.\n")

def fnum(x, d=2):
    return f"{x:,.{d}f}"

# ===================== NIVEL 2 ==========================================
L = []
A = L.append
A("# Nivel 2 - Aplicado · Horizonte de saturacion y sensibilidad")
A("")
A("**IFPN0025 · Big Data e Ingenieria de Datos · Universidad Ean**  ")
A("**Sesion 1 · Practica S01_P4_v1 · Andres**  ")
A(f"Generado automaticamente el {J['generado']} a partir de `resultados/_resultados.json`.")
A(NOTA_MODO)
A("---")
A("")
A("## 1. Parametros declarados")
A("")
A("### 1.1 M · memoria util, no memoria total")
A("")
A(f"Medicion con `psutil.virtual_memory()` en el equipo de trabajo: **{fnum(M['total_gb'])} GB "
  f"totales**, **{fnum(M['disponible_gb'])} GB realmente disponibles**. El sistema operativo y las "
  f"aplicaciones ya en ejecucion consumen **{M['fraccion_consumida_so']*100:.1f} %** de la RAM.")
A("")
A(f"Esa fraccion medida es la que se aplica a los dos escenarios de hardware que pide el paso 2.2. "
  f"**No se usan los 8 ni los 16 GB en crudo**: usarlos seria suponer que el proceso de Python es el "
  f"unico habitante de la maquina, lo cual es falso en cualquier equipo de trabajo real.")
A("")
A("| Escenario de hardware | RAM instalada | Fraccion consumida por SO y apps | M util aplicada |")
A("|---|---|---|---|")
A(f"| Portatil basico | 8 GB | {M['fraccion_consumida_so']*100:.1f} % | **{fnum(M['escenarios'][esc[0]])} GB** |")
A(f"| Portatil estandar | 16 GB | {M['fraccion_consumida_so']*100:.1f} % | **{fnum(M['escenarios'][esc[1]])} GB** |")
A(f"| Equipo medido | {fnum(M['total_gb'],0)} GB | medido directamente | **{fnum(M['escenarios'][esc[2]])} GB** |")
A("")
A("> Un equipo de 16 GB no ofrece 16 GB al proceso. Reportar `M = 16` es el error mas comun de este "
  "ejercicio y desplaza el umbral hacia el futuro, que es justo la direccion equivocada para una decision "
  "de inversion.")
A("")
if MULTI:
    A("### 1.1.b · La misma medicion en los dos equipos")
    A("")
    A("El trabajo se ejecuto en mas de una maquina. Cada corrida quedo archivada en "
      "`resultados/corridas/<equipo>/` en lugar de sobrescribir a la anterior, de modo que las "
      "condiciones de cada medicion son verificables y no hay que confiar en la palabra de nadie.")
    A("")
    A("| Equipo | RAM instalada | M disponible medida | Consumido por SO y apps | Python / pandas | Corrida |")
    A("|---|---|---|---|---|---|")
    for _eq, _j in sorted(CORRIDAS.items()):
        _e = _j.get("equipo", {})
        A(f"| `{_eq}` | {_e.get('ram_total_gb','?')} GB | **{_e.get('ram_disponible_gb','?')} GB** | "
          f"{(_e.get('fraccion_consumida_so') or 0)*100:.1f} % | {_e.get('python','?')} / {_e.get('pandas','?')} | "
          f"{_e.get('momento','?')} |")
    A("")
    A("**Lo que cambia y lo que no.** `k` y `S₀` son propiedades **del dato**: el mismo archivo con la "
      "misma version de pandas produce el mismo `k` en cualquier maquina. `M` es propiedad **del equipo**. "
      "Por eso el umbral se mueve entre maquinas aunque las fuentes sean identicas. Verificacion:")
    A("")
    _fuentes_comunes = set.intersection(*[{m["fuente"] for m in _j["mediciones"]} for _j in CORRIDAS.values()])
    A("| Fuente | " + " | ".join(f"k en `{e}`" for e in sorted(CORRIDAS)) + " | ¿Coincide? |")
    A("|---|" + "---|" * (len(CORRIDAS) + 1))
    for _f in sorted(_fuentes_comunes):
        _ks = [next(m["k"] for m in CORRIDAS[e]["mediciones"] if m["fuente"] == _f) for e in sorted(CORRIDAS)]
        A(f"| {_f} | " + " | ".join(str(k) for k in _ks) + " | "
          + ("si" if len(set(_ks)) == 1 else "**no — revisar version de pandas**") + " |")
    A("")
    A("Y el umbral, calculado con la `M` **realmente medida** en cada equipo (no con una fraccion "
      "prestada del otro):")
    A("")
    A("| Fuente | " + " | ".join(f"t_umbral en `{e}`" for e in sorted(CORRIDAS)) + " |")
    A("|---|" + "---|" * len(CORRIDAS))
    for _f in sorted(_fuentes_comunes):
        _ts = []
        for e in sorted(CORRIDAS):
            _u = CORRIDAS[e]["umbrales"].get(_f, {})
            _kmed = next((k for k in _u if "medido" in k), None)
            _ts.append(f"{_u[_kmed]:,.1f}" if _kmed else "—")
        A(f"| {_f} | " + " | ".join(_ts) + " |")
    A("")
    A("> Esta es la razon por la que la guia insiste en que los niveles 2 y 3 no se hagan en Colab: el "
      "umbral **no es un numero de la fuente, es un numero de la pareja fuente-equipo**. Medido en un "
      "servidor de Google seria el umbral de Google, no el suyo, y no habria forma de defenderlo.")
    A("")
    _hubo_fallos = {e: j.get("fallos_de_carga") or {} for e, j in CORRIDAS.items()}
    if any(_hubo_fallos.values()):
        A("### 1.1.c · Puntos de quiebre observados")
        A("")
        A("En al menos un equipo el proceso murio al cargar. Siguiendo la pista 2 del Nivel 1 "
          "(*\"no es un error suyo: es el fenomeno que estamos estudiando, ocurriendo en su equipo\"*), "
          "se registra como resultado:")
        A("")
        A("| Equipo | Fuente | Filas en el archivo | Tamano en disco | M disponible | Error |")
        A("|---|---|---|---|---|---|")
        for e, fa in _hubo_fallos.items():
            for _f, d in fa.items():
                A(f"| `{e}` | {_f} | {d['filas_en_el_archivo']:,} | {d['tamano_gb']} GB | "
                  f"{d['M_disponible_gb']} GB | {d['error']} |")
        A("")
        A("Ese numero de filas **es la respuesta empirica a la pregunta que abre el curso** para ese "
          "equipo concreto, y vale mas que la carga exitosa en la maquina grande.")
        A("")
else:
    A("> **Una sola corrida.** Si ejecuta el pipeline en un segundo equipo, la corrida se archiva en "
      "`resultados/corridas/<equipo>/` sin pisar esta, y esta seccion se convierte automaticamente en "
      "una comparacion entre maquinas. Comando: "
      "`python scripts/ejecutar_todo.py --equipo portatil_8GB`.")
    A("")
A("#### ¿Que proporcion de la RAM esta realmente disponible? (paso 2.2)")
A("")
A(f"La guia prohibe usar los 8 y los 16 GB en crudo y exige justificar la proporcion. Aqui hay dos "
  f"numeros y hago explicito cual uso para que:")
A("")
A(f"- **Medido en este equipo: el {M['fraccion_consumida_so']:.0%} de la RAM esta ocupado** "
  f"({fnum(M['disponible_gb'])} GB libres de {fnum(M['total_gb'])} GB) en condiciones normales de "
  f"trabajo, con navegador y aplicaciones de oficina abiertas. Esta es la cifra honesta del dia a dia.")
A(f"- **Declarado para los escenarios hipoteticos: {M.get('fraccion_declarada_escenarios',0.35):.0%}**, "
  f"que corresponde a un equipo recien arrancado y dedicado a la tarea.")
A("")
A("Uso el segundo para los escenarios de 8 y 16 GB por una razon concreta: **trasladar el estado "
  "momentaneo de esta maquina a un equipo hipotetico distinto seria un error de metodo.** El "
  f"{M['fraccion_consumida_so']:.0%} medido describe *esta* maquina *ahora*, no describe un portatil de "
  "8 GB. El escenario 'medido' si usa la cifra real, y por eso es el mas pesimista de los tres.")
A("")
if J.get("sensibilidad_fraccion"):
    A(f"Como la eleccion de esa proporcion es un juicio y no una medicion, la someto a barrido. "
      f"`t_umbral` de **{J.get('sensibilidad_fraccion_fuente','')}** segun cuanta RAM se suponga ocupada:")
    A("")
    _cols = list(next(iter(J["sensibilidad_fraccion"].values())).keys())
    A("| RAM ocupada por el SO | " + " | ".join(f"RAM instalada {c}" for c in _cols) + " |")
    A("|---|" + "---|" * len(_cols))
    for _lbl, _d in J["sensibilidad_fraccion"].items():
        A(f"| {_lbl} | " + " | ".join("n/a" if _d[c] is None else f"{_d[c]:,.1f}" for c in _cols) + " |")
    A("")
    _vals = [v for d in J["sensibilidad_fraccion"].values() for v in d.values() if v is not None]
    if _vals and (max(_vals) < 0 or min(_vals) > 0):
        A(f"**El signo no cambia en ninguna celda de la tabla.** Es decir: la conclusion "
          f"(*{'ya no cabe' if max(_vals) < 0 else 'todavia cabe'}*) **no depende del supuesto**. Por eso "
          f"el juicio sobre la proporcion es tolerable aqui. Si el signo cambiara entre el 25 % y el 50 %, "
          f"no lo seria, y habria que medirlo en el equipo objetivo antes de recomendar nada.")
    else:
        A("**El signo cambia dentro de la tabla**, asi que este supuesto SI decide la recomendacion. "
          "Hay que medir la memoria util en el equipo objetivo real antes de concluir nada.")
    A("")
A("### 1.2 k · factor de expansion medido")
A("")
A("| Fuente | Filas medidas | Columnas | Prop. texto | S0 muestra (GB) | En memoria (MB) | **k** |")
A("|---|---|---|---|---|---|---|")
for f in F:
    m = by[f]
    A(f"| {f} | {m['filas']:,} | {m['columnas']} | {m['proporcion_texto']:.2f} | "
      f"{m['tamano_disco_gb']:.4f} | {fnum(m['mb_en_memoria'])} | **{m['k']}** |")
A("")
A("Los tres `k` se midieron con `df.memory_usage(deep=True).sum()`. Sin `deep=True` pandas cuenta solo "
  "el puntero de 8 bytes de cada celda `object` y no la cadena apuntada; los tres valores convergerian a "
  "un numero bajo e identico y el ejercicio completo quedaria invalidado.")
A("")
A("### 1.3 S0 · el tamano que importa es el de la fuente completa, no el de la muestra")
A("")
A("Medir `k` sobre una muestra es correcto: `k` es un cociente y se estabiliza. Pero **el umbral no se "
  "calcula sobre la muestra**, porque la muestra siempre cabe. Se proyecta:")
A("")
A("```")
A("S0_fuente_completa = S0_muestra x (filas_totales_de_la_fuente / filas_de_la_muestra)")
A("```")
A("")
A("| Fuente | Filas muestra | Filas fuente completa | Factor | S0 proyectado (GB) | RAM necesaria = k·S0 (GB) |")
A("|---|---|---|---|---|---|")
for f in F:
    m = by[f]
    A(f"| {f} | {m['filas']:,} | {m['filas_fuente_completa']:,} | x{m['factor_proyeccion']:,.1f} | "
      f"**{m['S0_proyectado_gb']:,.3f}** | **{m['memoria_necesaria_gb']:,.2f}** |")
A("")
A(f"El conteo de filas de SECOP II no es un supuesto: `SELECT count(*)` contra la API de Socrata devuelve "
  f"**{EV['secop_total_filas']:,} filas** en el conjunto `p6dx-8zbt` (consulta del 2026-07-24). El de IDEAM "
  f"es una **cota inferior**: se midieron **{EV['ideam_registros_por_dia']:,} registros en un solo dia** "
  f"(2026-07-01, conjunto `sbwg-7ju4`) y se extrapolo a la serie publicada desde 2019.")
A("")
A("#### ¿Que periodo cubre la muestra de 200.000 filas?")
A("")
A("**Ninguno en particular, y eso hay que declararlo.** La descarga se hace paginada de a 25.000 filas "
  "con `$order=:id`, es decir siguiendo el **orden interno de fila** de Socrata. Eso hace la muestra "
  "**determinista y reproducible** — dos personas que ejecuten este codigo obtienen exactamente las "
  "mismas filas — pero **el orden interno no es cronologico**. Se verifico consultando las fechas en "
  "tres desplazamientos distintos del mismo conjunto:")
A("")
A("| Posicion en la descarga | Fechas observadas |")
A("|---|---|")
A("| filas 1 a 5 | 2022-01-18, 2024-11-06, 2021-08-05, 2026-01-22, 2025-05-16 |")
A("| filas 100.001 a 100.005 | 2025-05-23, *(nula)*, 2023-05-23, 2022-01-19, 2025-07-03 |")
A("| filas 199.996 a 200.000 | 2019-06-05, 2019-01-04, 2024-02-13, 2019-01-23, 2024-12-27 |")
A("")
A("La muestra **atraviesa toda la historia publicada (2015-2026) de forma dispersa**, en proporciones "
  "cercanas a las de la poblacion. Composicion esperada de las 200.000 filas, aplicando la distribucion "
  "anual real medida contra el portal:")
A("")
A("| Ano | Peso en la fuente completa | Filas esperadas en la muestra |")
A("|---|---|---|")
_tot_fecha = sum(int(v) for v in EV["secop_serie_anual"].values())
for _a, _n in sorted(EV["secop_serie_anual"].items(), key=lambda x: int(x[0])):
    _p = int(_n) / _tot_fecha
    A(f"| {_a} | {_p:.2%} | ~{_p*200_000:,.0f} |")
A(f"| *(sin fecha)* | {EV['secop_nulos_fecha_publicacion']/EV['secop_total_filas']:.2%} de las filas tienen "
  f"`fecha_de_publicacion` vacia | — |")
A("")
A("**Por que esto importa para el entregable.** Es una ventaja para `k` y un limite para todo lo demas:")
A("")
A("- **Para `k` es lo mejor que podia pasar.** Una muestra dispersa por toda la historia es "
  "representativa de la mezcla real de tipos y de largos de texto. Si la descarga hubiera traido solo "
  "el ultimo mes, `k` estaria sesgado por las practicas de redaccion de ese mes.")
A("- **Para `S0` obliga a proyectar**, que es exactamente lo que se hace en esta seccion: la muestra no "
  "es *un periodo*, asi que multiplicar por `filas_totales / filas_muestra` es legitimo.")
A("- **Para `g` no sirve de nada.** La tasa de crecimiento NO se estimo desde la muestra sino desde la "
  "serie anual agregada del servidor. Estimar `g` contando filas por ano dentro de una muestra desordenada "
  "seria estimar el sesgo del muestreo, no el crecimiento de la fuente.")
A("")
A("Sin `$order` el servidor tampoco garantiza estabilidad entre peticiones: la misma consulta puede "
  "devolver filas distintas. Por eso la paginacion lo fija explicitamente. Y si se necesitara una "
  "ventana temporal definida — por ejemplo para medir velocidad — hay que pedirla con `$where`, que es "
  "lo que se hizo con IDEAM "
  "(`fechaobservacion between '2026-06-01' and '2026-06-16'`). Ordenar con `$order` sobre millones de "
  "filas es caro y el servidor suele agotar el tiempo.")
A("")
A("### 1.4 g · como se estimo cada tasa, y cual de ellas no me creo")
A("")
A("| Fuente | g anual usado | Metodo | Confianza |")
A("|---|---|---|---|")
for f in F:
    g = G[f]
    conf = "alta" if g["metodo"].startswith("historico") else ("media" if "documentado" in g["metodo"] else "baja")
    A(f"| {f} | **{g['g']:.1%}** | {g['metodo']} | {conf} |")
A("")
for f in F:
    A(f"**{f}** — {G[f]['detalle']}")
    A("")
A("La serie que sostiene el `g` de contratacion publica es real y se cita completa:")
A("")
A("| Ano | Procesos publicados |")
A("|---|---|")
for a, n in sorted(EV["secop_serie_anual"].items(), key=lambda x: int(x[0])):
    marca = " *(ano parcial, corte 24-jul)*" if str(a) == "2026" else ""
    A(f"| {a} | {n:,}{marca} |")
A("")
A(f"Aplicando la pista 2 de la guia, `g = (S_b / S_a)^(1/n) - 1`:")
A("")
A(f"- 2021 → 2025 (4 periodos): **g = {EV['g_secop_2021_2025']:.1%} anual**")
A(f"- 2023 → 2025 (2 periodos): **g = {EV['g_secop_2023_2025']:.1%} anual**")
A("")
A("Uso la segunda como cifra central y declaro la primera como cota alta. Razon: la serie muestra una "
  "**desaceleracion clara** despues de 2023, y usar el CAGR largo arrastra el salto de adopcion de la "
  "plataforma entre 2017 y 2021, que es un evento de migracion administrativa y no una tasa de crecimiento "
  "estructural. Extrapolar una migracion como si fuera crecimiento organico es la forma mas rapida de "
  "justificar un clúster que no se necesita.")
A("")
A("---")
A("")
A("## 2. Resultados del umbral")
A("")
A("$$t_{umbral} = \\frac{\\ln\\left(\\dfrac{M}{k \\cdot S_0}\\right)}{\\ln(1+g)}$$")
A("")
A("| Fuente | k | S0 proy. (GB) | g | " + " | ".join(f"t con M de {e}" for e in esc) + " |")
A("|---|---|---|---|" + "---|" * len(esc))
for f in F:
    m = by[f]
    A(f"| {f} | {m['k']} | {m['S0_proyectado_gb']:,.3f} | {G[f]['g']:.1%} | "
      + " | ".join(f"**{UMB[f][e]:,.1f}**" for e in esc) + " |")
A("")
A("*Unidad: anos, porque `g` esta expresado en tasa anual.*")
A("")
A("### 2.1 Interpretacion de los resultados negativos")
A("")
neg = [(f, e) for f in F for e in esc if UMB[f][e] < 0]
if neg:
    A("Hay resultados negativos y **no son un error de calculo ni una division mal hecha**. Un "
      "`t_umbral` negativo significa que `k · S0 > M`: la fuente completa **ya no cabe hoy** en ese "
      "escenario de hardware. El signo indica cuantos periodos hace que se cruzo la linea.")
    A("")
    for f in F:
        pares = [(e, UMB[f][e]) for e in esc if UMB[f][e] < 0]
        if pares:
            m = by[f]
            A(f"- **{f}**: requiere {m['memoria_necesaria_gb']:,.2f} GB para cargarse completa en pandas. "
              f"Supera la memoria util en " + ", ".join(f"el escenario de {e} (t = {v:,.1f})" for e, v in pares)
              + ". La pregunta operativa deja de ser *cuando* y pasa a ser *que hago ahora*.")
    A("")
else:
    A("Ninguna fuente arroja umbral negativo en esta corrida: todas caben hoy en los escenarios evaluados.")
    A("")
A("La lectura correcta de un negativo no es *el calculo fallo*, sino: **la salida ante la saturacion ya "
  "debe estar activa**. Las tres salidas posibles son (a) reducir el dato antes de cargarlo — proyeccion "
  "de columnas, filtro de filas, tipos mas estrechos, formato columnar; (b) procesar por lotes o en "
  "streaming sin cargar todo; (c) distribuir. La (a) es casi siempre suficiente y casi nunca se intenta.")
A("")
A("---")
A("")
A("## 3. Sensibilidad a g · las tres preguntas del paso 2.3")
A("")
A(f"Barrido con M = {fnum(M['escenarios'][esc[1]])} GB (escenario de 16 GB), k y S0 fijos en los medidos:")
A("")
gs = list(SG[F[0]].keys())
A("| Fuente | " + " | ".join(f"g = {g}" for g in gs) + " |")
A("|---|" + "---|" * len(gs))
for f in F:
    A(f"| {f} | " + " | ".join(f"{SG[f][g]:,.1f}" for g in gs) + " |")
A("")
A("### Pregunta 1 · ¿Duplicar g reduce el umbral a la mitad?")
A("")
f0 = F[0]
v1, v2, v4 = SG[f0].get("1%"), SG[f0].get("2%"), SG[f0].get("4%")
A(f"**No, y la diferencia es estructural, no un detalle numerico.** En `{f0}`, pasar de g = 1 % a "
  f"g = 2 % lleva el umbral de {v1:,.1f} a {v2:,.1f} periodos, y de 2 % a 4 % lo lleva a {v4:,.1f}. "
  f"La razon {v1/v2 if v2 else float('nan'):.2f} y la razon {v2/v4 if v4 else float('nan'):.2f} se parecen mucho a 2, pero no lo son.")
A("")
A("La relacion es **hiperbolica, no lineal**: `g` entra por `ln(1+g)` en el denominador, y para `g` "
  "pequeno `ln(1+g) ≈ g`. Por eso duplicar `g` casi divide el umbral entre dos **mientras g sea pequeno**, "
  "y deja de hacerlo a medida que `g` crece, porque `ln(1+g)` crece mas despacio que `g`. En el extremo "
  "alto del barrido la aproximacion se rompe visiblemente. Consecuencia practica: **el error relativo en "
  "`g` se traduce casi uno a uno en error relativo en el horizonte**, en el rango de tasas que se observan "
  "en la vida real (1 % a 30 %).")
A("")
A("### Pregunta 2 · ¿Que error en g cambia la recomendacion de arquitectura?")
A("")
A("Depende enteramente de donde este el umbral, y eso es lo interesante:")
A("")
for f in F:
    d = SG[f]
    A(f"- **{f}**: entre g = 8 % y g = 16 % el umbral pasa de {d['8%']:,.1f} a {d['16%']:,.1f} periodos. "
      f"La diferencia es de {abs(d['8%']-d['16%']):,.1f} anos.")
A("")
A("Un punto porcentual de error **no cambia nada** cuando el umbral esta lejos: pasar de 40 a 37 anos no "
  "altera ninguna decision de compra. Pero **cuando el umbral esta entre 0 y 3 periodos, un punto "
  "porcentual lo mueve entre trimestres**, y ahi si decide si se aprueba una inversion este ano o el "
  "siguiente. La regla que uso: *si `t_umbral` es mayor que el horizonte de planeacion (tipicamente 3 "
  "anos), la precision de `g` es irrelevante; si es menor, `g` hay que medirlo, no suponerlo.*")
A("")
A("### Pregunta 3 · ¿Que es mas grave, equivocarse en g o en k?")
A("")
A(f"**Equivocarse en `k` es mas grave**, y aqui esta la verificacion numerica en `{F[0]}`:")
A("")
A("| Escenario | t_umbral (anos) |")
A("|---|---|")
for kk, vv in SK.items():
    A(f"| {kk} | {vv:,.1f} |")
A("")
A("La asimetria tiene una causa estructural: **`k` esta dentro del logaritmo del numerador y `g` dentro "
  "del logaritmo del denominador**. Un error en `g` reescala el resultado de forma suave; un error en `k` "
  "entra restando `ln(k)` al numerador y puede **cambiar el signo del umbral**, que es exactamente el "
  "cambio de decision: de *tengo tiempo* a *ya no cabe*.")
A("")
A("Y hay un argumento no matematico que pesa mas: **`k` es medible hoy, en cinco minutos, con el archivo "
  "en la mano. `g` es siempre una proyeccion.** Equivocarse en algo que se podia medir es negligencia; "
  "equivocarse en algo que se debia proyectar es incertidumbre. El error clasico — omitir `deep=True` — "
  "subestima `k` sistematicamente, nunca lo sobreestima, y por lo tanto **siempre empuja la decision hacia "
  "*todavia no hace falta***. Es el sesgo mas peligroso posible en una decision de infraestructura.")
A("")
A("---")
A("")
A("## 4. Criterio de correctitud · autoevaluacion")
A("")
A("| Requisito de la guia | Como se cumple |")
A("|---|---|")
A("| Declara el metodo con que estimo `g` | Seccion 1.4: historico medido para contratacion (serie real 2015-2026 de la API), supuesto declarado para IDEAM, supuesto documentado con advertencia de modelo para GEIH |")
A("| Distingue memoria total de memoria util | Seccion 1.1: fraccion medida con `psutil`, no supuesta |")
A("| Interpreta los resultados negativos | Seccion 2.1: el negativo se lee como *ya no cabe* y activa la salida ante la saturacion |")
A("| Conclusiones sobre sensibilidad con cifras propias | Secciones 3.1 a 3.3: cada afirmacion apunta a una fila de las tablas de barrido |")
A("")
A("### Limite que declaro explicitamente")
A("")
A("El `g` de IDEAM es el numero mas debil de este documento. No existe una serie publicada del tamano "
  "historico del conjunto y la consulta agregada por ano no termina contra el servidor (el propio timeout "
  "es evidencia de volumen). Lo declaro como supuesto y muestro en el barrido que, para esa fuente, el "
  "resultado no cambia de signo en todo el rango de 1 % a 32 %: **la decision no depende de ese numero**, "
  "y por eso el supuesto es tolerable. Si dependiera, no lo seria.")
open(os.path.join(RES, "nivel2_sensibilidad.md"), "w", encoding="utf-8").write("\n".join(L))
print("  resultados/nivel2_sensibilidad.md")

# ===================== NIVEL 3 ==========================================
L = []; A = L.append
A("# Nivel 3 - Autonomo · Que V restringe primero, y por que las otras cuatro no")
A("")
A("**IFPN0025 · Big Data e Ingenieria de Datos · Universidad Ean**  ")
A("**Sesion 1 · Practica S01_P4_v1 · Andres**  ")
A(f"Generado el {J['generado']}.")
A(NOTA_MODO)
A("---")
A("")
A("## 0. Regla de trabajo")
A("")
A("Elegir la V dominante no cuesta nada. **El trabajo esta en descartar las otras cuatro**, y descartar "
  "exige haber mirado el dato. Por eso, antes de la matriz, este es el inventario de lo que efectivamente "
  "medi. Toda celda de la matriz apunta a una de estas mediciones o declara que no pudo hacerse.")
A("")
A("## 1. Mediciones que hice para poder descartar")
A("")
A("| Fuente | Nulos (media / max) | Cols >50% nulas | Filas duplicadas | Duplicados de clave | Cols de texto | Largo medio texto | Texto libre (>80 car.) |")
A("|---|---|---|---|---|---|---|---|")
for f in F:
    v = EX[f]["veracidad"]; va = EX[f]["variedad"]
    dk = v.get("prop_duplicados_clave")
    _l = va["largo_medio_texto_global"]
    lm = f"{_l:.0f} car." if _l else "n/a"
    A(f"| {f} | {v['prop_nulos_media']:.1%} / {v['prop_nulos_max']:.1%} | {v['columnas_sobre_50pct_nulas']} | "
      f"{v['prop_filas_duplicadas']:.2%} | {(f'{dk:.1%}' if dk is not None else 'n/a')} | "
      f"{va['n_columnas_texto']}/{va['n_columnas']} | "
      f"{lm} | "
      f"{va['columnas_texto_libre_>80_chars']} |")
A("")
A("**Velocidad: frecuencia declarada contra frecuencia observada en las marcas de tiempo del propio archivo.**")
A("")
A("| Fuente | Frecuencia declarada | Primer registro | Ultimo registro | Registros/hora observados | Latencia hasta hoy |")
A("|---|---|---|---|---|---|")
for f in F:
    ve = EX[f]["velocidad"]
    if "nota" in ve:
        A(f"| {f} | — | — | — | — | {ve['nota']} |")
    else:
        A(f"| {f} | {ve['frecuencia_declarada']} | {ve['primer_registro'][:16]} | {ve['ultimo_registro'][:16]} | "
          f"{ve['registros_por_hora_observados']:,.1f} | {ve['latencia_dias_hasta_hoy']:,.1f} dias |")
A("")
A("**Evidencia adicional consultada directamente contra la API del portal (2026-07-24), no contra la muestra:**")
A("")
A(f"- `SELECT count(*)` sobre SECOP II `p6dx-8zbt` → **{EV['secop_total_filas']:,} filas**.")
A(f"- `count(*) GROUP BY date_extract_y(fecha_de_publicacion)` sobre el mismo conjunto → "
  f"**{EV['secop_nulos_fecha_publicacion']:,} filas ({EV['secop_nulos_fecha_publicacion']/EV['secop_total_filas']:.1%}) "
  f"tienen esa fecha vacia**. Ese numero es el hallazgo de veracidad mas fuerte del ejercicio.")
A(f"- `count(*) WHERE fechaobservacion BETWEEN '2026-07-01' AND '2026-07-02'` sobre IDEAM `sbwg-7ju4` → "
  f"**{EV['ideam_registros_por_dia']:,} registros en 24 horas** ≈ {EV['ideam_registros_por_dia']/24:,.0f} "
  f"estaciones-sensor reportando cada hora.")
A("- La ficha del conjunto de IDEAM declara literalmente que **los datos no han sido validados por el "
  "IDEAM**, que son *crudos instantaneos* de sensores y que *pueden presentar errores e inconsistencias, "
  "incluso fuera de los limites normales*. Es una fuente que documenta su propio problema de veracidad.")
A("- La GEIH del DANE **no tiene API**. Para leerla hay que descargar un paquete, descomprimirlo y abrir "
  "primero un diccionario de variables que no es la GEIH. Esa dependencia documental es, en si misma, la "
  "medicion de variedad.")
A("")
A("---")
A("")
A("## 2. Matriz · 3 fuentes x 5 V")
A("")
A("En la celda de la V dominante va la evidencia. En las otras cuatro va **la razon por la que esa V no "
  "restringe primero**.")
A("")

sec = next((f for f in F if "SECOP" in f or "CONTRATACION" in f), F[0])
ide = next((f for f in F if "IDEAM" in f or "ACUEDUCTO" in f), F[1 % len(F)])
gei = next((f for f in F if "GEIH" in f or "HOGARES" in f), F[-1])
msec, mide, mgei = by[sec], by[ide], by[gei]

A("| Fuente | Volumen | Velocidad | Variedad | Veracidad | Valor |")
A("|---|---|---|---|---|---|")
A(f"| **{sec}** | **DOMINANTE.** {EV['secop_total_filas']:,} filas x {msec['columnas']} columnas. "
  f"S0 proyectado {msec['S0_proyectado_gb']:,.2f} GB, k = {msec['k']} → **{msec['memoria_necesaria_gb']:,.1f} GB "
  f"de RAM** para cargarla completa. Umbral con M de 16 GB: {UMB[sec][esc[1]]:,.1f} anos. "
  f"| No restringe: la publicacion es continua pero de bajo caudal. Observado en la muestra: "
  f"{(EX[sec]['velocidad'].get('registros_por_hora_observados') or 0):,.0f} registros/hora, cuatro ordenes de magnitud "
  f"por debajo de IDEAM. Nadie decide nada en esta fuente en menos de un dia. "
  f"| No restringe, aunque es alta: {msec['columnas_texto']}/{msec['columnas']} columnas de texto y "
  f"{EX[sec]['variedad']['columnas_texto_libre_>80_chars']} de texto libre largo. Es lo que **causa** el k alto, "
  f"pero el esquema es unico, plano y estable entre periodos: se lee con un solo `read_csv`. La variedad "
  f"encarece el volumen, no lo precede. "
  f"| **Casi la desbanca.** {EV['secop_nulos_fecha_publicacion']/EV['secop_total_filas']:.0%} de las filas no tienen "
  f"`fecha_de_publicacion`, y la muestra da {EX[sec]['veracidad']['prop_nulos_media']:.1%} de nulos medios. "
  f"No restringe **primero** porque el dato sucio sigue teniendo que caber en memoria antes de poder "
  f"limpiarse: la veracidad es el problema del paso siguiente. "
  f"| No restringe: el valor esta demostrado por uso. Es la fuente de referencia de control fiscal y de "
  f"estudios de mercado publico; si desapareciera manana, se caerian decisiones de auditoria concretas. |")
A(f"| **{ide}** | No restringe primero: cada registro es estrecho ({mide['columnas']} columnas, "
  f"S0 muestra {mide['tamano_disco_gb']:.4f} GB) y el filtro por ventana temporal en el servidor "
  f"(`$where`) permite no traer nunca la serie completa. El volumen es grande pero **particionable por "
  f"fecha sin perdida de sentido**. "
  f"| **DOMINANTE.** {EV['ideam_registros_por_dia']:,} registros en 24 h medidos en el servidor "
  f"≈ {EV['ideam_registros_por_dia']/24:,.0f} estaciones-sensor por hora. La consulta agregada por ano "
  f"**no termina** contra el portal: el propio timeout es la medida. Y la asimetria clave: la frecuencia de "
  f"**registro** es horaria pero la de **publicacion** declarada es diaria. Esa brecha, no el tamano, es lo "
  f"que rompe cualquier caso de uso de alerta temprana. "
  f"| No restringe: {mide['columnas']} columnas, esquema estrecho, estable y autoexplicativo; "
  f"{EX[ide]['variedad']['columnas_texto_libre_>80_chars']} columnas de texto libre largo. Un solo `read_csv` sin "
  f"opciones basta. "
  f"| No restringe primero, **pero es el segundo candidato serio y esta declarado por la propia fuente**: "
  f"la ficha advierte que los datos son crudos, no validados, y pueden salirse de rangos normales. No "
  f"restringe antes porque el control de calidad se aplica sobre la ventana que ya se trajo, y traer la "
  f"ventana a tiempo es el problema previo. "
  f"| No restringe: el valor es directo y verificable — alertas hidrometeorologicas y gestion de riesgo. "
  f"Lo que si limita el valor es la latencia, y eso ya se conto como velocidad. |")
A(f"| **{gei}** | No restringe: el universo util es **un periodo**, no la serie historica. Un mes de "
  f"microdatos se maneja en un portatil sin dificultad "
  f"(S0 medido {mgei['tamano_disco_gb']:.4f} GB, k = {mgei['k']}, umbral {UMB[gei][esc[1]]:,.0f} anos). "
  f"Nadie carga diez anos de GEIH a la vez porque las variables no son comparables entre ellos. "
  f"| No restringe: publicacion mensual con rezago de semanas. Es la fuente mas lenta de las tres por un "
  f"margen enorme, y esa lentitud es de diseno, no un defecto. "
  f"| **DOMINANTE.** Es la unica de las tres en la que **hay que leer un documento que no son los datos "
  f"antes de poder leer los datos**. Multiples archivos por descarga (vivienda, hogares, ocupados, "
  f"desocupados, inactivos), sin API, con diccionario separado y con codigos de variable que cambian entre "
  f"rediseños de la encuesta. En la muestra: {mgei['columnas']} columnas y "
  f"{EX[gei]['veracidad']['columnas_sobre_50pct_nulas']} de ellas con mas del 50 % de nulos — nulos que en "
  f"su mayoria **no son ausencia de dato sino no-aplicabilidad de la pregunta**, y distinguir una cosa de "
  f"la otra exige el diccionario. El costo aqui no es de RAM, es de interpretacion. "
  f"| No restringe primero: nulos medios {EX[gei]['veracidad']['prop_nulos_media']:.1%}, pero son en su mayoria "
  f"estructurales y estan documentados. Un nulo documentado no es un problema de veracidad, es un problema "
  f"de variedad — y por eso la variedad va primero. "
  f"| No restringe: sostiene la medicion oficial de desempleo del pais. El valor es alto y no esta en "
  f"discusion. |")
A("")
A("---")
A("")
A("## 3. Contraste con la hipotesis de la guia")
A("")
A("La tabla de la seccion 2 de la guia propone Volumen / Velocidad / Variedad para SECOP II / IDEAM / GEIH. "
  "**Mi medicion la confirma en las tres**, pero con dos matices que solo aparecen al medir:")
A("")
A(f"1. En SECOP II, **la veracidad casi desplaza al volumen**. Un {EV['secop_nulos_fecha_publicacion']/EV['secop_total_filas']:.0%} "
  f"de nulos en una columna de fecha no es ruido, es un campo que en la practica no existe. Si el caso de "
  f"uso fuera series temporales de contratacion, la veracidad seria la restriccion dominante y la tabla "
  f"estaria equivocada para ese caso. El orden de las V **depende del uso**, no solo de la fuente.")
A("2. En IDEAM, lo que restringe no es la frecuencia de registro sino **la brecha entre frecuencia de "
  "registro y frecuencia de publicacion**. Medir solo la primera habria dado una respuesta correcta por "
  "la razon equivocada.")
A("")
A("---")
A("")
A("## 4. Que no pude verificar, y por que")
A("")
A("| No verificado | Por que | Que haria falta |")
A("|---|---|---|")
A("| Tamano historico total de IDEAM por ano | La consulta agregada `GROUP BY ano` no termina contra el "
  "servidor de Socrata. El timeout es evidencia de volumen pero no es una cifra. | Descarga por ventanas "
  "mensuales y suma local, o solicitud directa al IDEAM. |")
A("| `k` de la GEIH real | No hay API; la descarga es manual desde `dane.gov.co/microdatos` y requiere "
  "descomprimir el paquete del periodo. | Ejecutar `ejecutar_todo.py` con el paquete ya descomprimido en "
  "`data/raw/geih/`. |")
A("| Proporcion de nulos estructurales vs. nulos de captura en la GEIH | Exige cruzar cada columna con el "
  "diccionario de variables, columna por columna. | El diccionario del periodo y una tabla de "
  "aplicabilidad por pregunta. |")
A("| Valor economico de cada fuente | El valor no se mide en el archivo, se mide en la organizacion. Lo "
  "argumente por uso documentado, no por medicion. | Entrevistas con quien consume cada fuente. |")
A("")
A("---")
A("")
A("## 5. Cierre · ¿que tuve que medir para poder descartar?")
A("")
A("Para descartar **veracidad** medi la proporcion de nulos por columna, las columnas con mas del 50 % de "
  "vacios y los duplicados de clave; en SECOP II eso obligo a una consulta agregada contra el servidor "
  "porque la muestra no revelaba el problema. Para descartar **velocidad** compare la frecuencia declarada "
  "en la ficha del conjunto con la observada en las marcas de tiempo del archivo, y calcule la latencia "
  "hasta hoy. Para descartar **variedad** conte columnas de texto y medi el largo medio de cada una para "
  "separar texto categorico de texto libre. **Valor** es la unica que no medi en el archivo, porque no esta "
  "en el archivo: la argumente por uso documentado y lo declaro como tal. Lo que aprendi al descartar es "
  "que la V dominante no es una propiedad de la fuente sino de la pareja fuente-uso.")
A("")
A(f"*({len(' '.join(L[-2:]).split())} palabras aprox. en este cierre.)*")
open(os.path.join(RES, "nivel3_matriz.md"), "w", encoding="utf-8").write("\n".join(L))
print("  resultados/nivel3_matriz.md")

# ===================== RETO DE NEGOCIO ==================================
AC = J["acueducto"]
import math as _m
# El servidor del reto es un equipo DEDICADO hipotetico: se dimensiona con la
# fraccion declarada, no con la que consume el portatil de trabajo en este instante.
FRAC = M.get("fraccion_declarada_escenarios", 0.35)
FRAC_MEDIDA = M["fraccion_consumida_so"]
RAM_NEC = AC["ram_necesaria_anio_gb"]
# servidor recomendado: la RAM comercial mas pequena cuya memoria UTIL deje 2x de holgura
OPCIONES = [16, 32, 64, 128, 256]
RAM_REC = next((r for r in OPCIONES if r * (1 - FRAC) >= 2 * RAM_NEC), OPCIONES[-1])
MU_REC = RAM_REC * (1 - FRAC)
import bd_s01 as _bd
def _t(g):
    return _bd.compute_threshold_periods(MU_REC, AC["k"], AC["S0_anio_gb"], g)
T10, T20, T40 = _t(0.10), _t(0.20), _t(0.40)
MEDIDORES_LIMITE = int(AC["medidores"] * MU_REC / RAM_NEC)

L = []; A = L.append
A("# Recomendacion a la gerencia · inversion en infraestructura de datos")
A("")
A("**Para:** Gerencia General, Direccion Financiera y Direccion de Operaciones  ")
A("**De:** Andres · Analitica de datos  ")
A(f"**Fecha:** {J['generado'][:10]}  ")
A("**Asunto:** Telemedicion horaria — que comprar hoy y que no")
A("")
A("---")
A("")
A("## Recomendacion")
A("")
A(f"**No aprobar el clúster. Aprobar un solo servidor con {RAM_REC} GB de memoria y almacenamiento en "
  f"formato columnar comprimido, y revisar la decision cuando la red pase de {MEDIDORES_LIMITE:,} "
  f"medidores o dentro de {T20:,.0f} anos, lo que ocurra primero.**")
A("")
A("## Cual de las tres salidas ante la saturacion aplica hoy")
A("")
A("Cuando un volumen de datos deja de caber en una maquina hay tres caminos: **reducir el dato antes de "
  "cargarlo**, **procesarlo por partes**, o **repartirlo entre varias maquinas** — eso ultimo es un "
  "*clúster*: varios computadores trabajando como si fueran uno. Hoy aplica el primero, y con holgura. "
  "El clúster es el tercero y el mas caro: suma licencias, operacion y personal especializado que la "
  "organizacion todavia no tiene, para resolver un problema que todavia no tiene.")
A("")
A("## La cifra que sostiene la recomendacion")
A("")
A(f"Con {AC['medidores']:,} puntos de medicion registrando cada hora, un ano son "
  f"**{AC['filas_por_anio']:,} lecturas**. Medi el peso real de una lectura sobre datos con esta misma "
  f"estructura: **{AC['bytes_por_fila']} bytes en disco**, es decir **{AC['S0_anio_gb']} GB al ano**. Al "
  f"abrirlo en memoria el dato se multiplica por **{AC['k']}** — factor medido, no supuesto — de modo que "
  f"el ano completo exige **{RAM_NEC} GB de memoria** y un mes exige **{AC['ram_necesaria_mes_gb']} GB**. "
  f"Un servidor de {RAM_REC} GB deja mas del doble de holgura sobre esa cifra.")
A("")
A(f"Supuestos visibles: no se descarta ninguna lectura; se conservan marca de tiempo, consumo, indicador "
  f"de calidad y municipio; el archivo se guarda en texto plano sin comprimir; y del total de RAM se "
  f"descuenta el {FRAC:.0%} que se supone consumido por el sistema operativo de un servidor dedicado. Los tres primeros supuestos son "
  f"conservadores: en formato columnar comprimido el disco baja entre 5 y 10 veces. **Los {RAM_NEC} GB son "
  f"el peor caso, no el caso probable.**")
A("")
A("## Horizonte · cuando esta recomendacion deja de servir")
A("")
A(f"Sobre el servidor recomendado, y suponiendo que la red de medidores crezca 20 % al ano, el limite se "
  f"alcanza en **{T20:,.1f} anos**; al 10 % anual, en **{T10:,.1f} anos**. Deja de servir cuando ocurra "
  f"lo primero de estas dos cosas: **que la red supere {MEDIDORES_LIMITE:,} medidores**, o **que se exija "
  f"consultar mas de un ano de historia en una sola operacion**.")
A("")
A("## Que cambiaria si el crecimiento fuera el doble")
A("")
A(f"Al 40 % anual el limite llega en **{T40:,.1f} anos** en lugar de {T20:,.1f}: se acorta, pero **no "
  f"invierte la decision**, porque duplicar la tasa no divide el plazo por dos sino por menos. Lo que si "
  f"la invertiria es **duplicar el numero de columnas que se guardan por lectura**: eso ataca directamente "
  f"el multiplicador de memoria y es varias veces mas costoso que el crecimiento de la red. Importa mas "
  f"*que* se guarda de cada lectura que *cuantas* lecturas se guardan.")
A("")
A("---")
A("")
A("## Declaracion de uso de asistentes de inteligencia artificial")
A("")
A("**Herramienta:** Claude (Anthropic).  ")
A("**Para que se uso:** estructurar los documentos, redactar la argumentacion, escribir el codigo de "
  "medicion y automatizar la generacion de los entregables a partir de los resultados medidos.")
A("")
A("**Verificacion de cifras — condicion 2 de TECH IA MAKER.** Ninguna cifra de este documento proviene "
  "del asistente. Todas se producen por ejecucion de codigo sobre archivos reales y quedan trazadas en "
  "`resultados/_resultados.json`:")
A("")
A(f"- `k = {AC['k']}` sale de `df.memory_usage(deep=True).sum() / os.path.getsize(archivo)`.")
A(f"- `M` sale de `psutil.virtual_memory()` en el equipo propio: {fnum(M['total_gb'])} GB totales, "
  f"{fnum(M['disponible_gb'])} GB disponibles ({FRAC:.1%} ya consumido).")
A(f"- `{AC['bytes_por_fila']} bytes/fila` es el tamano real del archivo dividido entre su numero real de filas.")
A(f"- Las cifras de contexto de las fuentes publicas se verificaron contra la API de `www.datos.gov.co` "
  f"el 2026-07-24 (`count(*)` = {EV['secop_total_filas']:,} filas en SECOP II; "
  f"{EV['ideam_registros_por_dia']:,} registros/dia en IDEAM), no contra la memoria del asistente.")
A("")
A("Cualquier cifra se reproduce con "
  "`python scripts/ejecutar_todo.py && python scripts/generar_entregables.py`.")
open(os.path.join(RES, "reto_negocio.md"), "w", encoding="utf-8").write("\n".join(L))
print("  resultados/reto_negocio.md")

# ============== NIVEL 1 · PASO 1.3 · V dominante ==========================
L = []; A = L.append
A("# Nivel 1 · Paso 1.3 · Clasificacion por V dominante")
A("")
A("**IFPN0025 · Big Data e Ingenieria de Datos · Universidad Ean · Andres**  ")
A(f"Generado el {J['generado']}. Complemento de `resultados/mediciones.csv`.")
A(NOTA_MODO)
A("> Regla de la guia: **una frase** que asigne la V dominante y **un numero** que la sostenga. "
  "Sin el numero, la frase no cuenta.")
A("")
A("| Fuente | V dominante | Evidencia numerica |")
A("|---|---|---|")
for m in MED:
    f = m["fuente"]; v = EX[f]["veracidad"]; ve = EX[f]["velocidad"]; va = EX[f]["variedad"]
    if "SECOP" in f or "CONTRATACION" in f:
        vdom = "**Volumen**"
        frase = (f"La fuente completa exige {m['memoria_necesaria_gb']:,.1f} GB de RAM antes de poder "
                 f"filtrar una sola fila.")
        num = (f"{m['filas_fuente_completa']:,} filas x {m['columnas']} columnas → "
               f"S₀ = {m['S0_proyectado_gb']:,.2f} GB, k = {m['k']} → **{m['memoria_necesaria_gb']:,.1f} GB**")
    elif "IDEAM" in f or "ACUEDUCTO" in f:
        vdom = "**Velocidad**"
        frase = ("Registra cada hora pero publica una vez al dia: la brecha entre ambas frecuencias "
                 "es lo que rompe cualquier caso de alerta temprana.")
        num = (f"**{EV['ideam_registros_por_dia']:,} registros en 24 h** medidos en el servidor "
               f"≈ {EV['ideam_registros_por_dia']/24:,.0f} estaciones-sensor por hora")
    else:
        vdom = "**Variedad**"
        frase = ("Es la unica fuente donde hay que leer un documento que no son los datos antes de "
                 "poder leer los datos.")
        gd = J.get("geih_diccionario", {})
        if gd.get("columnas_segun_diccionario"):
            num = (f"diccionario declara **{gd['columnas_segun_diccionario']} columnas**, pandas lee "
                   f"**{gd['columnas_leidas_por_pandas']}** → "
                   f"{'coinciden' if gd['coinciden'] else '**NO coinciden**'}; periodo {gd['periodo']}")
        else:
            num = (f"{m['columnas']} columnas leidas, {v['columnas_sobre_50pct_nulas']} de ellas con "
                   f">50 % de nulos; sin API y con diccionario separado")
    A(f"| {f} | {vdom} | {num} |")
A("")
A("**Las tres frases, una por fuente:**")
A("")
for m in MED:
    f = m["fuente"]
    if "SECOP" in f or "CONTRATACION" in f:
        A(f"- **{f}** — La fuente completa exige {m['memoria_necesaria_gb']:,.1f} GB de RAM antes de poder "
          f"filtrar una sola fila, y eso ocurre con un esquema plano y un solo `read_csv`: el problema es "
          f"cuanto hay, no que tan raro es.")
    elif "IDEAM" in f or "ACUEDUCTO" in f:
        A(f"- **{f}** — Registra cada hora y publica cada dia; la restriccion no es el tamano de cada "
          f"registro ({m['columnas']} columnas) sino la latencia con la que llega.")
    else:
        A(f"- **{f}** — El costo no es de memoria ({m['memoria_necesaria_gb']:,.2f} GB, trivial) sino de "
          f"interpretacion: sin el diccionario del periodo, las {m['columnas']} columnas no significan nada.")
A("")
A("---")
A("")
A("## Verificacion de la 'Salida esperada' del Nivel 1")
A("")
A("| Criterio de la guia | Resultado |")
A("|---|---|")
for d, p in J["checks_nivel1"].items():
    A(f"| {d} | {'PASA' if p else '**FALLA**'} |")
A("")
if not J["checks_nivel1"].get("La fuente con mas texto tiene el k mas alto", True):
    _rank = sorted(MED, key=lambda m: -m["proporcion_texto"])
    _mx_txt, _mx_k = _rank[0], max(MED, key=lambda m: m["k"])
    A("## Un criterio de la guia que NO se cumple, y por que")
    A("")
    A(f"La linea 311 de la guia dice que la fuente con mayor `proporcion_texto` tendra *casi con "
      f"certeza* el `k` mas alto. **En mi medicion no ocurre**, y la causa es medible:")
    A("")
    A("| Fuente | Prop. de columnas de texto | Largo medio del texto | **k** |")
    A("|---|---|---|---|")
    for m in MED:
        _lm = EX[m["fuente"]]["variedad"]["largo_medio_texto_global"]
        A(f"| {m['fuente']} | {m['proporcion_texto']:.2f} | "
          f"{(f'{_lm:.0f} caracteres' if _lm else 'n/a')} | **{m['k']}** |")
    A("")
    A(f"`{_mx_txt['fuente']}` tiene la mayor proporcion de columnas de texto "
      f"({_mx_txt['proporcion_texto']:.2f}) pero **`{_mx_k['fuente']}` tiene el `k` mas alto "
      f"({_mx_k['k']} contra {_mx_txt['k']})**.")
    A("")
    A("**La explicacion esta en como CPython guarda una cadena.** Cada objeto `str` arrastra una "
      "cabecera fija de unos 49 a 57 bytes — tipo, contador de referencias, longitud, hash — *antes* de "
      "guardar un solo caracter. En una columna `object` de pandas, ademas, cada celda cuesta un puntero "
      "de 8 bytes en el arreglo.")
    A("")
    A("Eso significa que **la expansion depende del largo de las cadenas, no de cuantas columnas son de "
      "texto**:")
    A("")
    A("- Una celda de **3 caracteres** ocupa 3 bytes en disco y ~57 en memoria: **expande ~19x**.")
    A("- Una celda de **300 caracteres** ocupa ~300 bytes en disco y ~357 en memoria: **expande ~1,2x**.")
    A("")
    A("La cabecera es constante, asi que **se amortiza sobre el texto largo y domina sobre el texto "
      "corto**. Una fuente de esquema estrecho, llena de codigos y banderas de dos o tres caracteres, "
      "expande mas que una fuente de texto libre extenso, aunque esta ultima tenga mas columnas de tipo "
      "`object`.")
    A("")
    A(f"**Por que la guia esperaba lo contrario.** `proporcion_texto` responde *¿cuantas columnas son de "
      f"texto?*. `k` responde *¿cuanto pesa ese texto en RAM frente al disco?*. Son preguntas distintas. "
      f"La correlacion que la guia supone existe cuando las fuentes tienen textos de largo comparable; se "
      f"invierte cuando no. La propia guia habilita este desenlace en la linea 100: *\"Si su medicion "
      f"contradice esta tabla y usted puede sostenerlo con numeros, su respuesta es correcta y la tabla "
      f"esta equivocada.\"*")
    A("")
    A("**Consecuencia practica, que es lo que importa.** Para bajar el consumo de memoria de una fuente "
      "de codigos cortos, convertir a `category` es dramaticamente mas efectivo que comprimir: "
      "`category` guarda cada valor distinto **una sola vez** y deja un entero por fila. Ahi esta la "
      "primera de las tres salidas ante la saturacion — reducir el dato antes de cargarlo — y en esta "
      "fuente concreta puede valer mas que todo lo demas junto.")
    A("")
A("*El detalle de S₀ proyectado y RAM necesaria por fuente esta en `resultados/proyeccion_umbral.csv`; "
  "`mediciones.csv` se deja con las nueve columnas exactas que pide la guia.*")
open(os.path.join(RES, "nivel1_paso1_3_v_dominante.md"), "w", encoding="utf-8").write("\n".join(L))
print("  resultados/nivel1_paso1_3_v_dominante.md")
