# Evidencia del versionado de la capa cruda

<!-- GENERADO por src/ingesta/demostrar_versionado.py. No editar a mano.
     Se regenera en cada corrida. -->

Cubo: `lago-cruda` - Generado: `2026-08-19T17:28:00.641372+00:00` (UTC) - Veredicto: **VERSIONADO DEMOSTRADO**

## Que se demuestra

1. `GetBucketVersioning` sobre `lago-cruda` devuelve `Status=Enabled`.
2. Se escribe un objeto, se **sobrescribe** con contenido distinto, y la
   version anterior se recupera **identica byte a byte** pidiendola por su
   `VersionId`.
3. Se **borra** la clave: deja de verse, pero no se pierde. Queda un marcador
   de borrado y el contenido sigue siendo legible por `VersionId`. Al quitar
   el marcador, el objeto vuelve.

## La prueba, con los identificadores reales

| | |
|---|---|
| Objeto sonda | `_evidencia/prueba-de-versionado.txt` |
| `VersionId` de la escritura inicial | `2dd9f646-4801-4899-9a1f-d13f8ecf26ff` |
| `sha256` de la escritura inicial | `b4a1dd302f3f85abe4caad7d4bd413c3f11b491c698af0028ff6b683eaf37291` |
| `VersionId` tras sobrescribir | `9be35f41-0860-43ef-a8f3-0d7fe22ddf76` |
| `sha256` tras sobrescribir | `29ff408ecb484b6fbde71f9ff6e2d488cf360a5c74364698e3bf321d1e916490` |
| La version inicial se recupero intacta | **si, sha256 identico** |

### Historial completo de la sonda

| Tipo | VersionId | Es la actual | Bytes |
|---|---|---|---|
| version | `9be35f41-0860-43ef-a8f3-0d7fe22ddf76` | si | 436 |
| version | `2dd9f646-4801-4899-9a1f-d13f8ecf26ff` | no | 429 |

## Por que la prueba se hace sobre una sonda y no sobre el dato

La capa cruda es inmutable. La demostracion no se hace sobre el dato del proyecto: se hace sobre un objeto de prueba fuera del prefijo de la fuente.

## El dato real sigue intacto

El objeto de datos `secop2_procesos/anio=2026/mes=08/dia=19/secop2_procesos_20260819.csv` tiene **1 version(es)**. Nadie lo ha sobrescrito: la capa cruda sigue siendo inmutable.


## Como reproducir esta evidencia

```bash
docker compose up -d
python3 src/ingesta/cargar_cruda.py
python3 src/ingesta/demostrar_versionado.py
```
