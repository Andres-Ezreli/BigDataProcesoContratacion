# Recomendacion a la gerencia · inversion en infraestructura de datos

**Para:** Gerencia General, Direccion Financiera y Direccion de Operaciones  
**De:** Andres · Analitica de datos  
**Fecha:** 2026-07-24  
**Asunto:** Telemedicion horaria — que comprar hoy y que no

---

## Recomendacion

**No aprobar el clúster. Aprobar un solo servidor con 32 GB de memoria y almacenamiento en formato columnar comprimido, y revisar la decision cuando la red pase de 10,452 medidores o dentro de 4 anos, lo que ocurra primero.**

## Cual de las tres salidas ante la saturacion aplica hoy

Cuando un volumen de datos deja de caber en una maquina hay tres caminos: **reducir el dato antes de cargarlo**, **procesarlo por partes**, o **repartirlo entre varias maquinas** — eso ultimo es un *clúster*: varios computadores trabajando como si fueran uno. Hoy aplica el primero, y con holgura. El clúster es el tercero y el mas caro: suma licencias, operacion y personal especializado que la organizacion todavia no tiene, para resolver un problema que todavia no tiene.

## La cifra que sostiene la recomendacion

Con 5,000 puntos de medicion registrando cada hora, un ano son **43,800,000 lecturas**. Medi el peso real de una lectura sobre datos con esta misma estructura: **51.8 bytes en disco**, es decir **2.111 GB al ano**. Al abrirlo en memoria el dato se multiplica por **4.71** — factor medido, no supuesto — de modo que el ano completo exige **9.95 GB de memoria** y un mes exige **0.83 GB**. Un servidor de 32 GB deja mas del doble de holgura sobre esa cifra.

Supuestos visibles: no se descarta ninguna lectura; se conservan marca de tiempo, consumo, indicador de calidad y municipio; el archivo se guarda en texto plano sin comprimir; y del total de RAM se descuenta el 35% que se supone consumido por el sistema operativo de un servidor dedicado. Los tres primeros supuestos son conservadores: en formato columnar comprimido el disco baja entre 5 y 10 veces. **Los 9.95 GB son el peor caso, no el caso probable.**

## Horizonte · cuando esta recomendacion deja de servir

Sobre el servidor recomendado, y suponiendo que la red de medidores crezca 20 % al ano, el limite se alcanza en **4.0 anos**; al 10 % anual, en **7.7 anos**. Deja de servir cuando ocurra lo primero de estas dos cosas: **que la red supere 10,452 medidores**, o **que se exija consultar mas de un ano de historia en una sola operacion**.

## Que cambiaria si el crecimiento fuera el doble

Al 40 % anual el limite llega en **2.2 anos** en lugar de 4.0: se acorta, pero **no invierte la decision**, porque duplicar la tasa no divide el plazo por dos sino por menos. Lo que si la invertiria es **duplicar el numero de columnas que se guardan por lectura**: eso ataca directamente el multiplicador de memoria y es varias veces mas costoso que el crecimiento de la red. Importa mas *que* se guarda de cada lectura que *cuantas* lecturas se guardan.

---

## Declaracion de uso de asistentes de inteligencia artificial

**Herramienta:** Claude (Anthropic).  
**Para que se uso:** estructurar los documentos, redactar la argumentacion, escribir el codigo de medicion y automatizar la generacion de los entregables a partir de los resultados medidos.

**Verificacion de cifras — condicion 2 de TECH IA MAKER.** Ninguna cifra de este documento proviene del asistente. Todas se producen por ejecucion de codigo sobre archivos reales y quedan trazadas en `resultados/_resultados.json`:

- `k = 4.71` sale de `df.memory_usage(deep=True).sum() / os.path.getsize(archivo)`.
- `M` sale de `psutil.virtual_memory()` en el equipo propio: 15.64 GB totales, 2.08 GB disponibles (35.0% ya consumido).
- `51.8 bytes/fila` es el tamano real del archivo dividido entre su numero real de filas.
- Las cifras de contexto de las fuentes publicas se verificaron contra la API de `www.datos.gov.co` el 2026-07-24 (`count(*)` = 8,878,158 filas en SECOP II; 21,710 registros/dia en IDEAM), no contra la memoria del asistente.

Cualquier cifra se reproduce con `python scripts/ejecutar_todo.py && python scripts/generar_entregables.py`.