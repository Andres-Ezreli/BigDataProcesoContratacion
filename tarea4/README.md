# T4 — La agregación del proyecto en clave map y reduce

IFPN0025 · Big Data e Ingeniería de Datos · Universidad Ean
Equipo: [[COMPLETAR: los tres nombres]]

Agregación del proyecto reescrita con el modelo MapReduce, con estimación del volumen de la mezcla, contraste contra el contador real `Reduce shuffle bytes` y justificación de la clave.

## Reproducir en tres comandos

```bash
python3 datos/generar_muestra.py    # solo para la muestra de demostración
python3 src/mezcla/perfilar.py      # mide la fuente
python3 src/mezcla/estimar.py       # estima la mezcla y contrasta
```

Python 3.8+, sin dependencias externas. La ejecución en el clúster está en [`docs/T4_ejecucion.md`](docs/T4_ejecucion.md).

## Estructura

```
tarea4/
├── README.md
├── datos/
│   ├── generar_muestra.py      ← genera la muestra sintética (determinista)
│   └── muestra.csv             ← DEMOSTRACIÓN, reemplazar por la fuente real
├── src/
│   ├── mapreduce/
│   │   ├── esquema.json        ← ÚNICO archivo a editar
│   │   ├── comun.py            ← parseo y agregación compartidos
│   │   ├── mapper.py
│   │   ├── combiner.py
│   │   └── reducer.py
│   └── mezcla/
│       ├── perfilar.py         ← mide la fuente        → docs/perfil.json
│       ├── estimar.py          ← estima y contrasta    → docs/tabla_mezcla.md
│       └── medicion.json       ← contadores reales del trabajo (pegar aquí)
└── docs/
    ├── T4_mezcla.md            ← EL INFORME
    ├── T4_ejecucion.md         ← comandos exactos
    ├── tabla_mezcla.md         ← generado, no editar
    ├── perfil.json             ← generado, no editar
    └── declaracion-uso-ia.md
```

Ningún número está escrito a mano dentro del código. Todo sale de `esquema.json`, de la fuente y de `medicion.json`.

## Antes de entregar

- [ ] Reemplazar `datos/muestra.csv` por la fuente real y ajustar `esquema.json`
- [ ] Verificar que `registros_descartados` sea 1 (el encabezado) y no miles
- [ ] Correr la prueba local del paso 2 de `T4_ejecucion.md`: el `diff` debe salir vacío
- [ ] Ejecutar las **dos** versiones en el clúster, con y sin combinador
- [ ] Pegar los contadores en `src/mezcla/medicion.json` y volver a correr `estimar.py`
- [ ] Buscar todos los pendientes: `grep -rn "COMPLETAR" .`
- [ ] Rehacer a mano la aritmética de la sección *Verificación a mano* con las cifras reales
- [ ] Trasladar el informe a la plantilla oficial adjunta a la asignación
- [ ] Prueba del tercero: un integrante que no tocó el código clona en limpio y reproduce
- [ ] Confirmar que los tres integrantes tienen commits con mensaje descriptivo

## Reparto de commits

| Integrante | Commits |
|---|---|
| 1 | `esquema.json` con la fuente real, `mapper.py`, prueba local |
| 2 | `combiner.py`, `reducer.py`, ejecución en el clúster y captura de contadores |
| 3 | `perfilar.py` / `estimar.py` sobre la fuente real, informe, análisis de sesgo |

Cada quien empuja lo suyo desde su cuenta. `feat: combinador con suma y conteo`, no `update`.
