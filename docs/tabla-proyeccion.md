<!-- GENERADO POR src/proyeccion.py — NO EDITAR A MANO -->

### Datos de entrada (ficha T1)

| Parametro | Valor |
|---|---|
| Fuente | SECOP II - Procesos de Contratacion (datos.gov.co / p6dx-8zbt) |
| Licencia | Datos Abiertos de Colombia - Ley 1712 de 2014, uso libre con atribucion |
| Formato | CSV UTF-8 delimitado por comas, esquema plano, 59 columnas |
| Volumen actual (V0) | 9.28 GB |
| Crecimiento mensual (g) | 0.98% |
| Horizonte (n) | 12 meses |
| Archivo tipico | 96 MB |
| Tamano de bloque HDFS | 128 MB |
| Costo de almacenamiento | 0.023 USD por GB-mes |

### Volumen logico proyectado

V12 = 9.28 x (1 + 0.009786) ^ 12 = **10.43 GB** (factor de crecimiento: 1.1240x)

### Almacenamiento fisico por factor de replica (a 12 meses)

| R | Almacenamiento fisico | Sobrecosto vs R=1 | Nodos que puede perder | Costo mensual (USD) | Bloques fisicos por archivo |
|---|---|---|---|---|---|
| 1 | 10.43 GB | +0.00 GB | 0 | 0.24 | 1 |
| 2 | 20.86 GB | +10.43 GB | 1 | 0.48 | 2 |
| 3 | 31.29 GB | +20.86 GB | 2 | 0.72 | 3 |

### Bloques HDFS

ceil(96.41 MB / 128 MB) = **1 bloque** por archivo. El archivo cabe en **un solo bloque**, que queda con 96.41 MB ocupados de 128 MB. HDFS no reserva el bloque completo en disco: el remanente no se desperdicia.

