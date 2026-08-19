# T3 · Proyección de almacenamiento y factor de réplica

**IFPN0025 · Big Data e Ingeniería de Datos · Universidad Ean · Sesión 3 · Módulo 1**
**Equipo:** Andrés Linero · `[INTEGRANTE 2]` · `[INTEGRANTE 3]`
**Fuente única del equipo:** SECOP II — Procesos de Contratación (`datos.gov.co / p6dx-8zbt`)

---

## Resultado en una línea

A doce meses la fuente pasa de **8,6435 GiB a 9,7150 GiB**. Con R = 3 son **29,1450 GiB** de disco y
**USD 8,64 al año**. Recomendamos **R = 3 en la zona cruda y R = 2 en la derivada**, porque el snapshot
del portal **no es regenerable** y la tercera réplica cuesta USD 2,88 al año.

| R | Físico a 12 m | Bloques de 128 MiB | Tolera | USD/año |
|---|---|---|---|---|
| 1 | 9,7150 GiB | 78 | 0 nodos | 2,88 |
| 2 | 19,4300 GiB | 156 | 1 nodo | 5,76 |
| 3 | **29,1450 GiB** | 234 | **2 nodos** | 8,64 |

Y el hallazgo que más ahorra: **comprimir vence a des-replicar**. Parquet+Snappy a R = 3 ocupa
5,8290 GiB — 70 % menos que CSV plano a R = 2 — y encima tolera un nodo más.

---

## Dónde está cada cosa

| Quiero… | Abrir |
|---|---|
| **La entrega completa** | [`docs/informe_T3_proyeccion_replica.docx`](docs/informe_T3_proyeccion_replica.docx) |
| El glosario bilingüe acumulativo | [`docs/glosario_bilingue.md`](docs/glosario_bilingue.md) |
| Lo que se pega en el cuadro de la tarea | [`docs/ENTREGA.md`](docs/ENTREGA.md) |
| Las tres fichas T1 originales | [`docs/fichas_t1_originales/`](docs/fichas_t1_originales/) |
| El cálculo | [`scripts/proyeccion.py`](scripts/proyeccion.py) |
| El generador del informe | [`scripts/generar_informe_docx.js`](scripts/generar_informe_docx.js) |
| Las cifras en crudo | [`resultados/`](resultados/) |

El informe `.docx` es el documento único de la entrega: consolida en trece secciones la proyección, la
ficha de la fuente del equipo, la justificación de la consolidación, el componente en inglés y la guía
del repositorio. El glosario se mantiene aparte en Markdown porque es **acumulativo** hasta la sesión 30
y se versiona mejor en git.

---

## Reproducir las cifras

```bash
python scripts/proyeccion.py
```

Solo biblioteca estándar de Python 3.8+. Imprime los nueve pasos del cálculo y reescribe todo
`resultados/`. Ninguna cifra de resultado está escrita a mano en el código: todas se derivan del
diccionario `ENTRADAS` al inicio del script.

Para regenerar el informe en Word a partir de esas cifras:

```bash
npm install docx        # solo la primera vez
node scripts/generar_informe_docx.js
```

El `.docx` lee `resultados/proyeccion.json`, así que tampoco contiene cifras escritas a mano.

Para rehacer la proyección con **otra** fuente, cambiar solo el diccionario `ENTRADAS` y reejecutar
los dos comandos en ese orden.

> El índice del `.docx` aparece vacío hasta abrirlo en Word: seleccionarlo y pulsar **F9**. Word calcula
> los números de página al abrir el archivo, no al generarlo.

---

## Cobertura de la rúbrica

| Criterio | Pts | Dónde se responde |
|---|---|---|
| Proyección reproducible | 35 | `scripts/proyeccion.py` + informe §3, §4, §6, §9 |
| Recomendación de factor | 30 | Informe §8 (costo, punto de quiebre, dato crítico vs. regenerable, alternativa) |
| Consolidación del equipo | 15 | Informe §2 (los tres criterios técnicos de la elección) |
| Componente en inglés | 10 | Informe §10 + `docs/glosario_bilingue.md` |
| Trazabilidad del repositorio | 10 | `git shortlog -sne` + informe §11 |

---

## Estructura

```
tarea2/
├── README.md
├── .gitignore
├── docs/
│   ├── informe_T3_proyeccion_replica.docx   ← la entrega
│   ├── glosario_bilingue.md                 ← acumulativo, crece cada sesión
│   ├── ENTREGA.md                           ← texto para el cuadro de la tarea
│   └── fichas_t1_originales/                ← las tres fichas T1, con su autoría
├── scripts/
│   ├── proyeccion.py                        ← produce todas las cifras
│   └── generar_informe_docx.js              ← produce el informe
└── resultados/
    ├── proyeccion.csv
    ├── bloques.csv
    ├── proyeccion.json
    └── tabla.md
```

---

## Pendiente antes de entregar

- [ ] Reemplazar `[INTEGRANTE 2]` y `[INTEGRANTE 3]` en el informe (portada y §11), en `ENTREGA.md`, en `glosario_bilingue.md` y en este README
- [ ] Que los tres integrantes hagan sus propios commits — `git shortlog -sne` debe listar tres
- [ ] Que los integrantes 2 y 3 suban sus fichas T1 a `docs/fichas_t1_originales/`
- [ ] Correr la prueba del tercero con otro equipo: deben llegar a 9,7150 GiB
- [ ] Poner el hash del último commit en `docs/ENTREGA.md`
- [ ] Abrir el `.docx` en Word y actualizar el índice con F9

---

## Declaración de uso de IA

Se usó Claude (Anthropic) para estructurar los documentos, redactar y escribir los dos scripts. Ninguna
cifra proviene del asistente: los datos de entrada vienen de las mediciones de S01 y los resultados se
producen ejecutando código auditable. Las doce operaciones intermedias se rehicieron a mano. Detalle
completo en la sección 12 del informe.
