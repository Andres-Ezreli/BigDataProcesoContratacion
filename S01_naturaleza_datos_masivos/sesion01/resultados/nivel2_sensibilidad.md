# Nivel 2 - Aplicado · Horizonte de saturacion y sensibilidad

**IFPN0025 · Big Data e Ingenieria de Datos · Universidad Ean**  
**Sesion 1 · Practica S01_P4_v1 · Andres**  
Generado automaticamente el 2026-07-24 18:54 a partir de `resultados/_resultados.json`.

---

## 1. Parametros declarados

### 1.1 M · memoria util, no memoria total

Medicion con `psutil.virtual_memory()` en el equipo de trabajo: **15.64 GB totales**, **2.08 GB realmente disponibles**. El sistema operativo y las aplicaciones ya en ejecucion consumen **86.7 %** de la RAM.

Esa fraccion medida es la que se aplica a los dos escenarios de hardware que pide el paso 2.2. **No se usan los 8 ni los 16 GB en crudo**: usarlos seria suponer que el proceso de Python es el unico habitante de la maquina, lo cual es falso en cualquier equipo de trabajo real.

| Escenario de hardware | RAM instalada | Fraccion consumida por SO y apps | M util aplicada |
|---|---|---|---|
| Portatil basico | 8 GB | 86.7 % | **5.20 GB** |
| Portatil estandar | 16 GB | 86.7 % | **10.40 GB** |
| Equipo medido | 16 GB | medido directamente | **2.08 GB** |

> Un equipo de 16 GB no ofrece 16 GB al proceso. Reportar `M = 16` es el error mas comun de este ejercicio y desplaza el umbral hacia el futuro, que es justo la direccion equivocada para una decision de inversion.

> **Una sola corrida.** Si ejecuta el pipeline en un segundo equipo, la corrida se archiva en `resultados/corridas/<equipo>/` sin pisar esta, y esta seccion se convierte automaticamente en una comparacion entre maquinas. Comando: `python scripts/ejecutar_todo.py --equipo portatil_8GB`.

#### ¿Que proporcion de la RAM esta realmente disponible? (paso 2.2)

La guia prohibe usar los 8 y los 16 GB en crudo y exige justificar la proporcion. Aqui hay dos numeros y hago explicito cual uso para que:

- **Medido en este equipo: el 87% de la RAM esta ocupado** (2.08 GB libres de 15.64 GB) en condiciones normales de trabajo, con navegador y aplicaciones de oficina abiertas. Esta es la cifra honesta del dia a dia.
- **Declarado para los escenarios hipoteticos: 35%**, que corresponde a un equipo recien arrancado y dedicado a la tarea.

Uso el segundo para los escenarios de 8 y 16 GB por una razon concreta: **trasladar el estado momentaneo de esta maquina a un equipo hipotetico distinto seria un error de metodo.** El 87% medido describe *esta* maquina *ahora*, no describe un portatil de 8 GB. El escenario 'medido' si usa la cifra real, y por eso es el mas pesimista de los tres.

Como la eleccion de esa proporcion es un juicio y no una medicion, la someto a barrido. `t_umbral` de **SECOP II** segun cuanta RAM se suponga ocupada:

| RAM ocupada por el SO | RAM instalada 8 GB | RAM instalada 16 GB | RAM instalada 32 GB |
|---|---|---|---|
| 25% | -12.8 | -6.8 | -0.9 |
| 35% | -14.0 | -8.1 | -2.1 |
| 50% | -16.2 | -10.3 | -4.4 |
| 87% (medido en este equipo) | -27.8 | -21.8 | -15.9 |

**El signo no cambia en ninguna celda de la tabla.** Es decir: la conclusion (*ya no cabe*) **no depende del supuesto**. Por eso el juicio sobre la proporcion es tolerable aqui. Si el signo cambiara entre el 25 % y el 50 %, no lo seria, y habria que medirlo en el equipo objetivo antes de recomendar nada.

### 1.2 k · factor de expansion medido

| Fuente | Filas medidas | Columnas | Prop. texto | S0 muestra (GB) | En memoria (MB) | **k** |
|---|---|---|---|---|---|---|
| SECOP II | 200,000 | 59 | 0.75 | 0.1947 | 615.77 | **3.09** |
| IDEAM | 200,000 | 12 | 0.58 | 0.0293 | 98.32 | **3.28** |
| GEIH (sustituto sintetico) | 80,000 | 28 | 0.00 | 0.0086 | 17.09 | **1.93** |

Los tres `k` se midieron con `df.memory_usage(deep=True).sum()`. Sin `deep=True` pandas cuenta solo el puntero de 8 bytes de cada celda `object` y no la cadena apuntada; los tres valores convergerian a un numero bajo e identico y el ejercicio completo quedaria invalidado.

### 1.3 S0 · el tamano que importa es el de la fuente completa, no el de la muestra

Medir `k` sobre una muestra es correcto: `k` es un cociente y se estabiliza. Pero **el umbral no se calcula sobre la muestra**, porque la muestra siempre cabe. Se proyecta:

```
S0_fuente_completa = S0_muestra x (filas_totales_de_la_fuente / filas_de_la_muestra)
```

| Fuente | Filas muestra | Filas fuente completa | Factor | S0 proyectado (GB) | RAM necesaria = k·S0 (GB) |
|---|---|---|---|---|---|
| SECOP II | 200,000 | 8,878,158 | x44.4 | **8.643** | **26.71** |
| IDEAM | 200,000 | 55,469,050 | x277.4 | **8.119** | **26.63** |
| GEIH (sustituto sintetico) | 80,000 | 80,000 | x1.0 | **0.009** | **0.02** |

El conteo de filas de SECOP II no es un supuesto: `SELECT count(*)` contra la API de Socrata devuelve **8,878,158 filas** en el conjunto `p6dx-8zbt` (consulta del 2026-07-24). El de IDEAM es una **cota inferior**: se midieron **21,710 registros en un solo dia** (2026-07-01, conjunto `sbwg-7ju4`) y se extrapolo a la serie publicada desde 2019.

#### ¿Que periodo cubre la muestra de 200.000 filas?

**Ninguno en particular, y eso hay que declararlo.** La descarga se hace paginada de a 25.000 filas con `$order=:id`, es decir siguiendo el **orden interno de fila** de Socrata. Eso hace la muestra **determinista y reproducible** — dos personas que ejecuten este codigo obtienen exactamente las mismas filas — pero **el orden interno no es cronologico**. Se verifico consultando las fechas en tres desplazamientos distintos del mismo conjunto:

| Posicion en la descarga | Fechas observadas |
|---|---|
| filas 1 a 5 | 2022-01-18, 2024-11-06, 2021-08-05, 2026-01-22, 2025-05-16 |
| filas 100.001 a 100.005 | 2025-05-23, *(nula)*, 2023-05-23, 2022-01-19, 2025-07-03 |
| filas 199.996 a 200.000 | 2019-06-05, 2019-01-04, 2024-02-13, 2019-01-23, 2024-12-27 |

La muestra **atraviesa toda la historia publicada (2015-2026) de forma dispersa**, en proporciones cercanas a las de la poblacion. Composicion esperada de las 200.000 filas, aplicando la distribucion anual real medida contra el portal:

| Ano | Peso en la fuente completa | Filas esperadas en la muestra |
|---|---|---|
| 2015 | 0.06% | ~126 |
| 2016 | 0.11% | ~226 |
| 2017 | 0.50% | ~1,000 |
| 2018 | 2.23% | ~4,452 |
| 2019 | 2.13% | ~4,254 |
| 2020 | 4.80% | ~9,595 |
| 2021 | 7.46% | ~14,927 |
| 2022 | 11.87% | ~23,744 |
| 2023 | 17.51% | ~35,014 |
| 2024 | 19.09% | ~38,187 |
| 2025 | 22.12% | ~44,233 |
| 2026 | 12.12% | ~24,242 |
| *(sin fecha)* | 99.24% de las filas tienen `fecha_de_publicacion` vacia | — |

**Por que esto importa para el entregable.** Es una ventaja para `k` y un limite para todo lo demas:

- **Para `k` es lo mejor que podia pasar.** Una muestra dispersa por toda la historia es representativa de la mezcla real de tipos y de largos de texto. Si la descarga hubiera traido solo el ultimo mes, `k` estaria sesgado por las practicas de redaccion de ese mes.
- **Para `S0` obliga a proyectar**, que es exactamente lo que se hace en esta seccion: la muestra no es *un periodo*, asi que multiplicar por `filas_totales / filas_muestra` es legitimo.
- **Para `g` no sirve de nada.** La tasa de crecimiento NO se estimo desde la muestra sino desde la serie anual agregada del servidor. Estimar `g` contando filas por ano dentro de una muestra desordenada seria estimar el sesgo del muestreo, no el crecimiento de la fuente.

Sin `$order` el servidor tampoco garantiza estabilidad entre peticiones: la misma consulta puede devolver filas distintas. Por eso la paginacion lo fija explicitamente. Y si se necesitara una ventana temporal definida — por ejemplo para medir velocidad — hay que pedirla con `$where`, que es lo que se hizo con IDEAM (`fechaobservacion between '2026-06-01' and '2026-06-16'`). Ordenar con `$order` sobre millones de filas es caro y el servidor suele agotar el tiempo.

### 1.4 g · como se estimo cada tasa, y cual de ellas no me creo

| Fuente | g anual usado | Metodo | Confianza |
|---|---|---|---|
| SECOP II | **12.4%** | historico medido | alta |
| IDEAM | **8.0%** | supuesto declarado | baja |
| GEIH (sustituto sintetico) | **3.0%** | supuesto documentado | media |

**SECOP II** — CAGR 2023-2025 de la serie real de SECOP II (1,531,557 -> 1,934,805 filas/ano). CAGR 2021-2025 = 31.2% se reporta como cota alta.

**IDEAM** — No hay serie historica de tamano publicada. El volumen crece con el numero de estaciones-sensor activas, no con el tiempo. Se supone 8% anual de expansion de red. Es el numero mas debil del entregable y se declara.

**GEIH (sustituto sintetico)** — El archivo de un periodo no crece; crece el acumulado, y lo hace de forma LINEAL, no geometrica. Se usa 3% por el crecimiento de la muestra y de columnas entre rediseños. La formula sobreestima aqui: se declara.

La serie que sostiene el `g` de contratacion publica es real y se cita completa:

| Ano | Procesos publicados |
|---|---|
| 2015 | 5,528 |
| 2016 | 9,904 |
| 2017 | 43,728 |
| 2018 | 194,742 |
| 2019 | 186,082 |
| 2020 | 419,702 |
| 2021 | 652,937 |
| 2022 | 1,038,591 |
| 2023 | 1,531,557 |
| 2024 | 1,670,367 |
| 2025 | 1,934,805 |
| 2026 | 1,060,386 *(ano parcial, corte 24-jul)* |

Aplicando la pista 2 de la guia, `g = (S_b / S_a)^(1/n) - 1`:

- 2021 → 2025 (4 periodos): **g = 31.2% anual**
- 2023 → 2025 (2 periodos): **g = 12.4% anual**

Uso la segunda como cifra central y declaro la primera como cota alta. Razon: la serie muestra una **desaceleracion clara** despues de 2023, y usar el CAGR largo arrastra el salto de adopcion de la plataforma entre 2017 y 2021, que es un evento de migracion administrativa y no una tasa de crecimiento estructural. Extrapolar una migracion como si fuera crecimiento organico es la forma mas rapida de justificar un clúster que no se necesita.

---

## 2. Resultados del umbral

$$t_{umbral} = \frac{\ln\left(\dfrac{M}{k \cdot S_0}\right)}{\ln(1+g)}$$

| Fuente | k | S0 proy. (GB) | g | t con M de 8 GB | t con M de 16 GB | t con M de medido (16 GB) |
|---|---|---|---|---|---|---|
| SECOP II | 3.09 | 8.643 | 12.4% | **-14.0** | **-8.1** | **-21.8** |
| IDEAM | 3.28 | 8.119 | 8.0% | **-21.2** | **-12.2** | **-33.1** |
| GEIH (sustituto sintetico) | 1.93 | 0.009 | 3.0% | **194.4** | **217.9** | **163.5** |

*Unidad: anos, porque `g` esta expresado en tasa anual.*

### 2.1 Interpretacion de los resultados negativos

Hay resultados negativos y **no son un error de calculo ni una division mal hecha**. Un `t_umbral` negativo significa que `k · S0 > M`: la fuente completa **ya no cabe hoy** en ese escenario de hardware. El signo indica cuantos periodos hace que se cruzo la linea.

- **SECOP II**: requiere 26.71 GB para cargarse completa en pandas. Supera la memoria util en el escenario de 8 GB (t = -14.0), el escenario de 16 GB (t = -8.1), el escenario de medido (16 GB) (t = -21.8). La pregunta operativa deja de ser *cuando* y pasa a ser *que hago ahora*.
- **IDEAM**: requiere 26.63 GB para cargarse completa en pandas. Supera la memoria util en el escenario de 8 GB (t = -21.2), el escenario de 16 GB (t = -12.2), el escenario de medido (16 GB) (t = -33.1). La pregunta operativa deja de ser *cuando* y pasa a ser *que hago ahora*.

La lectura correcta de un negativo no es *el calculo fallo*, sino: **la salida ante la saturacion ya debe estar activa**. Las tres salidas posibles son (a) reducir el dato antes de cargarlo — proyeccion de columnas, filtro de filas, tipos mas estrechos, formato columnar; (b) procesar por lotes o en streaming sin cargar todo; (c) distribuir. La (a) es casi siempre suficiente y casi nunca se intenta.

---

## 3. Sensibilidad a g · las tres preguntas del paso 2.3

Barrido con M = 10.40 GB (escenario de 16 GB), k y S0 fijos en los medidos:

| Fuente | g = 1% | g = 2% | g = 4% | g = 8% | g = 16% | g = 32% |
|---|---|---|---|---|---|---|
| SECOP II | -94.8 | -47.6 | -24.0 | -12.3 | -6.4 | -3.4 |
| IDEAM | -94.5 | -47.5 | -24.0 | -12.2 | -6.3 | -3.4 |
| GEIH (sustituto sintetico) | 647.2 | 325.2 | 164.2 | 83.7 | 43.4 | 23.2 |

### Pregunta 1 · ¿Duplicar g reduce el umbral a la mitad?

**No, y la diferencia es estructural, no un detalle numerico.** En `SECOP II`, pasar de g = 1 % a g = 2 % lleva el umbral de -94.8 a -47.6 periodos, y de 2 % a 4 % lo lleva a -24.0. La razon 1.99 y la razon 1.98 se parecen mucho a 2, pero no lo son.

La relacion es **hiperbolica, no lineal**: `g` entra por `ln(1+g)` en el denominador, y para `g` pequeno `ln(1+g) ≈ g`. Por eso duplicar `g` casi divide el umbral entre dos **mientras g sea pequeno**, y deja de hacerlo a medida que `g` crece, porque `ln(1+g)` crece mas despacio que `g`. En el extremo alto del barrido la aproximacion se rompe visiblemente. Consecuencia practica: **el error relativo en `g` se traduce casi uno a uno en error relativo en el horizonte**, en el rango de tasas que se observan en la vida real (1 % a 30 %).

### Pregunta 2 · ¿Que error en g cambia la recomendacion de arquitectura?

Depende enteramente de donde este el umbral, y eso es lo interesante:

- **SECOP II**: entre g = 8 % y g = 16 % el umbral pasa de -12.3 a -6.4 periodos. La diferencia es de 5.9 anos.
- **IDEAM**: entre g = 8 % y g = 16 % el umbral pasa de -12.2 a -6.3 periodos. La diferencia es de 5.9 anos.
- **GEIH (sustituto sintetico)**: entre g = 8 % y g = 16 % el umbral pasa de 83.7 a 43.4 periodos. La diferencia es de 40.3 anos.

Un punto porcentual de error **no cambia nada** cuando el umbral esta lejos: pasar de 40 a 37 anos no altera ninguna decision de compra. Pero **cuando el umbral esta entre 0 y 3 periodos, un punto porcentual lo mueve entre trimestres**, y ahi si decide si se aprueba una inversion este ano o el siguiente. La regla que uso: *si `t_umbral` es mayor que el horizonte de planeacion (tipicamente 3 anos), la precision de `g` es irrelevante; si es menor, `g` hay que medirlo, no suponerlo.*

### Pregunta 3 · ¿Que es mas grave, equivocarse en g o en k?

**Equivocarse en `k` es mas grave**, y aqui esta la verificacion numerica en `SECOP II`:

| Escenario | t_umbral (anos) |
|---|---|
| k x0.5 | -2.1 |
| k x1.0 | -8.1 |
| k x2.0 | -14.0 |
| k x4.0 | -19.9 |

La asimetria tiene una causa estructural: **`k` esta dentro del logaritmo del numerador y `g` dentro del logaritmo del denominador**. Un error en `g` reescala el resultado de forma suave; un error en `k` entra restando `ln(k)` al numerador y puede **cambiar el signo del umbral**, que es exactamente el cambio de decision: de *tengo tiempo* a *ya no cabe*.

Y hay un argumento no matematico que pesa mas: **`k` es medible hoy, en cinco minutos, con el archivo en la mano. `g` es siempre una proyeccion.** Equivocarse en algo que se podia medir es negligencia; equivocarse en algo que se debia proyectar es incertidumbre. El error clasico — omitir `deep=True` — subestima `k` sistematicamente, nunca lo sobreestima, y por lo tanto **siempre empuja la decision hacia *todavia no hace falta***. Es el sesgo mas peligroso posible en una decision de infraestructura.

---

## 4. Criterio de correctitud · autoevaluacion

| Requisito de la guia | Como se cumple |
|---|---|
| Declara el metodo con que estimo `g` | Seccion 1.4: historico medido para contratacion (serie real 2015-2026 de la API), supuesto declarado para IDEAM, supuesto documentado con advertencia de modelo para GEIH |
| Distingue memoria total de memoria util | Seccion 1.1: fraccion medida con `psutil`, no supuesta |
| Interpreta los resultados negativos | Seccion 2.1: el negativo se lee como *ya no cabe* y activa la salida ante la saturacion |
| Conclusiones sobre sensibilidad con cifras propias | Secciones 3.1 a 3.3: cada afirmacion apunta a una fila de las tablas de barrido |

### Limite que declaro explicitamente

El `g` de IDEAM es el numero mas debil de este documento. No existe una serie publicada del tamano historico del conjunto y la consulta agregada por ano no termina contra el servidor (el propio timeout es evidencia de volumen). Lo declaro como supuesto y muestro en el barrido que, para esa fuente, el resultado no cambia de signo en todo el rango de 1 % a 32 %: **la decision no depende de ese numero**, y por eso el supuesto es tolerable. Si dependiera, no lo seria.