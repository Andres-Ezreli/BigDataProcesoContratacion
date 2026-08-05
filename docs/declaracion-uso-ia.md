# Declaración de uso de asistentes de inteligencia artificial

**Tarea T3 · Sesión 3 · Equipo [[COMPLETAR]]**

El enunciado permite el uso de asistentes de IA para apoyar el cálculo y la redacción, con dos condiciones: declararlo y verificar cada cifra a mano. Esta es la declaración.

## Qué se usó y para qué

| Uso | Herramienta | Verificación realizada |
|---|---|---|
| Estructura del documento de proyección | Claude (Anthropic) | Revisión completa del equipo frente al enunciado y la rúbrica |
| Implementación del script `src/proyeccion.py` | Claude (Anthropic) | Cada fórmula contrastada con la sección 3 del enunciado; resultados recalculados a mano (ver `docs/proyeccion.md`, sección 2) |
| Borrador del párrafo en inglés | Claude (Anthropic) | Reescrito por el equipo; ver nota en `docs/replication-summary-en.md` |
| Definiciones del glosario | Claude (Anthropic) | Contrastadas contra el capítulo 5 de Kleppmann (2017) |

## Qué no se delegó

- La elección de la fuente consolidada del equipo y su justificación técnica.
- Los datos de entrada salen de la ficha T1, no del asistente. Con una precisión sobre su procedencia, porque los cuatro no tienen el mismo estatus:
  - *Formato* (CSV UTF-8, 59 columnas): **medido** por el equipo en S01.
  - *Volumen* (9,28 GB): **deducido** por el equipo a partir de dos mediciones propias —el tamaño en disco de la muestra de 200.000 filas y el `count(*)` de la API verificado el 2026-07-24—. No estaba escrito como tal en la ficha.
  - *Tasa de crecimiento* (0,9786 % mensual): **deducida** del CAGR 2023→2025 de la serie anual de filas publicada por el portal. Tampoco estaba escrita como tal.
  - *Licencia*: **declarada, no verificada** contra el portal. Es el único de los cuatro sin evidencia medida y queda señalado como tal en la sección 1 del documento de proyección.
- La recomendación de factor de réplica y su argumentación.
- La verificación aritmética, hecha a mano y documentada paso a paso.

## Verificación aritmética

Todas las cifras de la tabla de proyección se recalcularon manualmente. El procedimiento de verificación está en `docs/proyeccion.md`, sección 2, subsección *Verificación a mano*.

Firman: [[COMPLETAR: los tres integrantes]]
