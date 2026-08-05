# Replication: the problem it solves and the trade-off it introduces

> Basado en Kleppmann, M. (2017). *Designing data-intensive applications*, cap. 5 — Replication.

**Borrador de trabajo — reescríbanlo con sus propias palabras antes de entregar.** El enunciado exige que el párrafo sea propio del equipo. Léanlo, entiéndanlo, ciérrenlo y vuelvan a escribirlo. La versión de abajo sirve como referencia de contenido y extensión, no como texto final.

---

Replication means keeping a copy of the same data on several machines. It solves three problems at once: the system stays available when a node fails, data sits closer to the clients that read it, and many machines can serve read traffic in parallel. The hard part is not copying the data once, but keeping every copy correct while the data keeps changing. Each replica must eventually apply the same writes, and until it does, a reader may see a stale value. That is the trade-off replication introduces: it buys availability and read throughput, and it pays with extra storage and weaker consistency guarantees.

*(104 words)*

---

**Cómo reescribirlo sin perder el punto.** El párrafo tiene que responder dos cosas y nada más:

1. **Qué problema resuelve** — disponibilidad ante fallos, cercanía al lector, escalar lecturas.
2. **Qué compromiso introduce** — costo de almacenamiento y consistencia debilitada mientras las copias se ponen al día.

Si su versión responde ambas en 80–120 palabras y ustedes pueden explicarla en voz alta sin leerla, está lista.
