# T5 — La fuente del proyecto en la capa cruda del lago

IFPN0025 · Big Data e Ingeniería de Datos · Universidad Ean
Equipo: Gabriela Garay Beltrán · Juan Andrés Linero Bonnet · Kevin Enrique Darghan Chajín

Ingesta de la fuente cruda del proyecto a un lago de datos sobre almacenamiento de objetos (MinIO, compatible S3), particionada por fecha de ingesta, con versionado en la capa cruda y una convención de rutas que se puede predecir sin preguntarle a nadie.

```
s3://lago-cruda/secop2_procesos/anio=2026/mes=08/dia=19/secop2_procesos_20260819.csv
                └── fuente ──┘  └──── fecha de ingesta (UTC) ────┘
```

## Reproducir en cuatro comandos

```bash
docker compose up -d                            # levanta el almacenamiento
python3 -m pip install -r requisitos.txt        # una sola dependencia: boto3
python3 src/ingesta/cargar_cruda.py             # ingesta a la capa cruda
python3 src/ingesta/verificar_lago.py           # comprueba los 6 criterios
```

El detalle está en [`docs/T5_ejecucion.md`](docs/T5_ejecucion.md). El informe, en [`docs/T5_lago.md`](docs/T5_lago.md).

## Estructura

```
tarea5/
├── README.md
├── docker-compose.yml          ← MinIO, con el tag fijado (no 'latest')
├── requisitos.txt              ← boto3 y nada más
├── config/
│   └── lago.json               ← ÚNICO archivo de configuración
├── src/ingesta/
│   ├── comun.py                ← LA CONVENCIÓN DE RUTAS vive en clave_cruda()
│   ├── cargar_cruda.py         ← la ingesta          → docs/evidencia_ingesta.json
│   ├── demostrar_versionado.py ← evidencia del versionado
│   ├── verificar_lago.py       ← árbitro de los 6 criterios, sale 0 o 1
│   └── historial_lago.py       ← historial de versiones del lago
└── docs/
    ├── T5_lago.md              ← EL INFORME
    ├── T5_ejecucion.md         ← comandos exactos
    ├── prueba_del_tercero.md   ← se rellena A MANO: lo único que no genera un script
    ├── declaracion-uso-ia.md
    ├── evidencia_ingesta.json      ← generados, no editar
    ├── evidencia_versionado.md     ←
    ├── evidencia_versionado.json   ←
    ├── evidencia_lago.md           ←
    ├── evidencia_lago.json         ←
    ├── historial_lago.md           ←
    └── historial_lago.json         ←
```

Ningún nombre de cubo y ninguna ruta están escritos a mano dentro del código: todo se deriva de `config/lago.json`. Cambiar `prefijo_cubos` renombra el lago entero.

Ninguna cifra del informe se escribe a mano: sale de los cinco archivos de evidencia, que generan los scripts.

## Las tres reglas del lago

1. **La ruta se deduce, no se consulta.** Fuente + fecha ⇒ ruta.
2. **La capa cruda no se edita nunca.** Las correcciones van en la refinada.
3. **El versionado está activo en la cruda** como red de seguridad de la regla 2.

## Antes de entregar

- [ ] **Conseguir la plantilla oficial `BiD_S05_P6_plantilla_t5_v1.md`** (no llegó con el material) y trasladar `docs/T5_lago.md` a sus campos
- [ ] Ejecutar la secuencia completa contra MinIO de verdad, no solo leerla
- [ ] Correr `cargar_cruda.py` **dos veces**: la segunda debe decir `omitida_por_identica` y `Versiones de la clave: 1`
- [ ] Ejecutar `verificar_lago.py` **sin** `--sin-integridad` al menos una vez, y que el código de salida sea 0
- [ ] Pegar en el informe la tabla de `docs/evidencia_versionado.md` con los `VersionId` reales
- [ ] Pegar en el informe la tabla de `docs/evidencia_lago.md` con los seis criterios
- [ ] Captura de pantalla de la consola de MinIO: el objeto en su ruta particionada y el historial de versiones. Los `VersionId` de la captura deben coincidir con los de `docs/historial_lago.md`
- [ ] Rellenar [`docs/prueba_del_tercero.md`](docs/prueba_del_tercero.md) y volcar el veredicto en la sección 2.5 del informe, incluso si el tercero falló
- [ ] Borrar el lago con `docker compose down -v` y reconstruirlo de cero: es la prueba real del criterio 6
- [ ] Buscar todos los pendientes: `grep -rn "COMPLETAR" .`
- [ ] Comprobar que los cinco archivos de evidencia están commiteados y **no** ignorados por `.gitignore`
- [ ] Confirmar que los tres integrantes tienen commits con mensaje descriptivo
- [ ] Entregar la **URL del repositorio**, no un zip

## Reparto de commits

| Integrante | Commits |
|---|---|
| Juan Andrés Linero Bonnet | `docker-compose.yml`, `config/lago.json`, `requisitos.txt`, la ingesta contra MinIO real y la prueba de reejecución |
| Gabriela Garay Beltrán | `demostrar_versionado.py`, `historial_lago.py`, la captura de la consola y las respuestas de la prueba del tercero |
| Kevin Enrique Darghan Chajín | `verificar_lago.py`, el informe `T5_lago.md`, las respuestas de la prueba del tercero y la declaración de uso de IA |

**La prueba del tercero es de los dos que no diseñaron la convención.** Cada uno responde las cuatro preguntas de [`docs/prueba_del_tercero.md`](docs/prueba_del_tercero.md) sin abrir el informe, y commitea sus respuestas desde su propia cuenta. Ese commit es su aporte visible a la entrega.

Cada quien empuja lo suyo desde su cuenta. `feat: ingesta particionada por fecha de ingesta`, no `update`.

> **Nota sobre el reparto.** Los tres archivos de `src/ingesta/` dependen de `comun.py`. Quien lo toque, que avise: es donde vive la convención de rutas, y cambiarla sin cambiar la expresión regular de `verificar_lago.py` hace fallar la comprobación C3 a propósito.
