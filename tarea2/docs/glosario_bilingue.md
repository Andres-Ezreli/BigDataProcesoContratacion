# Glosario bilingüe acumulativo

**IFPN0025 · Big Data e Ingeniería de Datos · Universidad Ean**
Glosario del repositorio del equipo. Se acumula sesión a sesión: cada tarea con componente en inglés
agrega términos nuevos y **no** borra los anteriores.

---

## Sesión 3 · T3 — Lectura: Kleppmann (2017), cap. 5, «Replication»

| # | Término (EN) | Traducción (ES) | Definición breve |
|---|---|---|---|
| 1 | **Replication lag** | Retraso de replicación | Intervalo de tiempo entre el momento en que una escritura se confirma en el nodo líder y el momento en que aparece en un seguidor. Con replicación asíncrona el retraso es variable y no está acotado: si el seguidor va lento o la red se congestiona, puede pasar de milisegundos a minutos. Es la causa directa de que una lectura devuelva un valor viejo. |
| 2 | **Eventual consistency** | Consistencia eventual | Garantía débil según la cual, si las escrituras se detienen, todas las réplicas terminan convergiendo al mismo valor. No dice *cuándo*: solo promete que el retraso de replicación acaba en cero. Kleppmann subraya que la palabra «eventual» es deliberadamente vaga y que por eso hacen falta garantías más fuertes, como *read-your-writes*, para que la aplicación sea usable. |
| 3 | **Failover** | Conmutación por error | Procedimiento por el cual, cuando el nodo líder cae, uno de los seguidores es promovido a líder y el resto del sistema se reconfigura para escribirle a él. Puede ser manual o automático. El riesgo del automático es el *split brain*: dos nodos se creen líderes a la vez y aceptan escrituras contradictorias. |

### Términos relacionados que aparecen en el documento de proyección

| Término (EN) | Traducción (ES) | Definición breve |
|---|---|---|
| **Replication factor** | Factor de réplica | Número de copias de cada bloque que HDFS mantiene en el clúster. Parámetro `dfs.replication`, por defecto 3. Con factor R el sistema tolera R − 1 nodos caídos sin pérdida de dato. |
| **Under-replicated block** | Bloque sub-replicado | Bloque que existe en menos copias que el factor configurado, típicamente porque cayó un DataNode. HDFS intenta restaurar el factor copiándolo a otro nodo; si no hay nodos disponibles, el bloque permanece sub-replicado. |
| **Block** | Bloque | Unidad de direccionamiento y réplica de HDFS, 128 MiB por defecto. Un archivo se parte en `ceil(tamaño / 128 MiB)` bloques. El último bloque ocupa en disco solo los bytes reales, no el bloque completo. |

---

## Convención del glosario

- Un término entra **una sola vez**. Si reaparece en una lectura posterior, se amplía su definición en su fila original en lugar de duplicarla.
- La definición va en español y debe ser comprensible sin haber leído el texto en inglés.
- Los términos se agrupan por la sesión y la lectura de la que salieron, para poder rastrear su origen.

## Historial

| Sesión | Lectura | Términos agregados | Acumulado |
|---|---|---|---|
| 3 | Kleppmann (2017), cap. 5 | 3 (+3 relacionados) | 6 |
