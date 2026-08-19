# Evidencia del lago - verificacion automatica

<!-- GENERADO por src/ingesta/verificar_lago.py. No editar a mano.
     Se regenera en cada corrida. -->

Generado: `2026-08-19T17:28:01.574222+00:00` (UTC)
Capa cruda: `lago-cruda`
Veredicto global: **PASA**

## Los seis criterios de aceptacion

| # | Criterio | Comprobaciones | Resultado |
|---|---|---|---|
| 1 | El dato crudo esta en la capa cruda bajo `<fuente>/anio=YYYY/mes=MM/dia=DD/` | C1, C3, C5 | **PASA** |
| 2 | La carga es un script reproducible con boto3, reejecutable sin duplicar ni romper | C9 | **PASA** |
| 3 | El versionado esta activo en la capa cruda y se evidencia | C2, C7 | **PASA** |
| 4 | La convencion esta documentada de modo que otra persona prediga donde esta cualquier objeto | C3, C4, C6 | **PASA** |
| 5 | La capa cruda se declara inmutable y nadie la ha editado | C8 | **PASA** |
| 6 | Es reproducible: otra persona clona en limpio, ejecuta y obtiene el mismo lago | C1, C3, C4, C5, C6 | **PASA** |

## Las nueve comprobaciones

| # | Comprobacion | Resultado |
|---|---|---|
| C1 | Las tres capas del lago existen | PASA |
| C2 | El versionado esta donde la configuracion lo declara | PASA |
| C3 | Toda clave de datos cumple la convencion de rutas | PASA |
| C4 | Cada objeto de datos tiene su manifiesto hermano | PASA |
| C5 | El contenido del lago coincide con su sha256 declarado | PASA |
| C6 | Cada cubo trae su _LEEME.txt con la convencion | PASA |
| C7 | Hay evidencia de que una version anterior se recupera | PASA |
| C8 | Ningun objeto de datos ha sido sobrescrito | PASA |
| C9 | Reejecutar no ha duplicado el dato | PASA |

## Que fallo

Ninguna. Las nueve comprobaciones pasan.


## Inventario completo del lago

Todo lo que hay dentro, en el momento de generar este archivo. Las claves que
empiezan por guion bajo son metadato del lago, no dato del proyecto.

| Cubo | Clave | Tamano | Ultima modificacion |
|---|---|---|---|
| `lago-cruda` | `_LEEME.txt` | 2.3 KiB | 2026-08-19T17:26:49.274000+00:00 |
| `lago-cruda` | `_evidencia/prueba-de-versionado.txt` | 436.0 B | 2026-08-19T17:28:00.583000+00:00 |
| `lago-cruda` | `secop2_procesos/anio=2026/mes=08/dia=19/secop2_procesos_20260819.csv` | 54.7 MiB | 2026-08-19T17:27:59.609000+00:00 |
| `lago-cruda` | `secop2_procesos/anio=2026/mes=08/dia=19/secop2_procesos_20260819.csv.manifiesto.json` | 3.6 KiB | 2026-08-19T17:27:59.617000+00:00 |
| `lago-refinada` | `_LEEME.txt` | 1.1 KiB | 2026-08-19T17:26:49.295000+00:00 |
| `lago-curada` | `_LEEME.txt` | 919.0 B | 2026-08-19T17:26:49.319000+00:00 |

## Como reproducir esta verificacion

```bash
docker compose up -d
python3 -m pip install -r requisitos.txt
python3 src/ingesta/cargar_cruda.py
python3 src/ingesta/demostrar_versionado.py
python3 src/ingesta/verificar_lago.py
```

El codigo de salida es 0 si todo pasa y 1 si algo falla.
