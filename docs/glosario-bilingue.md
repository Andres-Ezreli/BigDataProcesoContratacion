# Glosario bilingüe acumulativo

Glosario del repositorio de equipo. Cada sesión agrega términos; no se borran los anteriores.

---

## Sesión 3 — Kleppmann (2017), cap. 5: Replication

| Término (EN) | Término (ES) | Definición breve |
|---|---|---|
| **Leader-based replication** | Replicación basada en líder | Un nodo se designa líder y es el único que acepta escrituras; los seguidores reciben el flujo de cambios y lo aplican en el mismo orden. Las lecturas pueden atenderse desde cualquiera de los dos. Es el modelo por defecto en PostgreSQL, MySQL y Kafka. |
| **Replication lag** | Retardo de réplica | El intervalo durante el cual un seguidor todavía no ha aplicado una escritura que el líder ya confirmó. Mientras dura, una lectura contra ese seguidor devuelve un valor desactualizado. Es el costo directo de replicar de forma asíncrona. |
| **Eventual consistency** | Consistencia eventual | Garantía según la cual, si las escrituras cesan, todas las réplicas convergen al mismo valor. No dice *cuándo*: es una promesa sobre el estado final, no sobre ninguna lectura intermedia. |

**Nota de lectura para el reactivo del cuestionario.** Kleppmann distingue tres razones para replicar —tolerancia a fallos, cercanía geográfica al lector y escalar el volumen de lecturas— y sostiene que la dificultad no está en copiar el dato sino en manejar los cambios sobre las copias. Es la distinción que suele evaluarse.

---

## Sesión 1–2

<!-- [[COMPLETAR: si el equipo ya tenía glosario de T1/T2, péguenlo aquí para no perder el acumulado]] -->
