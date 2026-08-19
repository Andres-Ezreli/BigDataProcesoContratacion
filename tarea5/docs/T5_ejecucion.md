# T5 — Ejecución y reproducción

Estos son los comandos exactos. Alguien ajeno al equipo debe poder clonar el repositorio, seguir esta página de arriba abajo y obtener **el mismo lago**, sin preguntar nada. Eso es el criterio de aceptación 6.

**Requisitos:** Docker con Compose v2, y Python 3.8 o superior. Una sola dependencia de Python: `boto3`.

> **En Windows.** Todo funciona igual, con dos cambios: el intérprete se llama `python`, no `python3`, y las rutas van con `\` si usan PowerShell (con Git Bash quedan igual que aquí). Donde diga `python3`, escriban `python`.

---

## 1. Levantar el almacenamiento de objetos

```bash
docker compose up -d
docker compose ps          # debe decir 'running' y, tras unos segundos, 'healthy'
```

Eso levanta MinIO, que habla el mismo protocolo que S3. Quedan dos puertos abiertos:

| Puerto | Qué es |
|---|---|
| `9000` | la API de S3 — a este apunta `config/lago.json` |
| `9001` | la consola web — <http://localhost:9001>, usuario y clave `minioadmin` |

MinIO tarda unos segundos en aceptar conexiones tras arrancar. No hay que esperar mirando: los scripts esperan solos hasta 60 segundos.

## 2. Instalar la dependencia

```bash
python3 -m pip install -r requisitos.txt
```

Si prefieren no tocar el Python del sistema:

```bash
python3 -m venv .venv
source .venv/bin/activate        # en Windows:  .venv\Scripts\activate
python3 -m pip install -r requisitos.txt
```

## 3. Ingestar la fuente a la capa cruda

```bash
python3 src/ingesta/cargar_cruda.py
```

En una sola pasada hace las cinco cosas: crea los tres cubos, activa el versionado en la cruda, escribe el `_LEEME.txt` de cada cubo, descarga la fuente del portal y la carga bajo `<fuente>/anio=/mes=/dia=/` con su manifiesto.

Variantes útiles:

```bash
# la muestra completa de T1 (~200 MB): tarda, pero es la cifra del proyecto
python3 src/ingesta/cargar_cruda.py --filas 200000

# sin salida a internet, o con una copia que ya tengan
python3 src/ingesta/cargar_cruda.py --archivo /ruta/a/fuente.csv

# reponer una partición de un día concreto
python3 src/ingesta/cargar_cruda.py --fecha 2026-08-19

# solo crear cubos y versionado, sin cargar datos
python3 src/ingesta/cargar_cruda.py --solo-lago
```

**Prueba de reejecución** — es el criterio 2, y se comprueba en diez segundos:

```bash
python3 src/ingesta/cargar_cruda.py --archivo .descargas/secop2_procesos_*.csv
```

La segunda corrida tiene que decir `ese objeto ya esta en el lago con el mismo sha256` y `Versiones de la clave: 1`. Si dice que cargó algo, o si el número de versiones sube, la idempotencia está rota y el criterio 2 no se cumple.

## 4. Demostrar el versionado

```bash
python3 src/ingesta/demostrar_versionado.py
```

Escribe un objeto sonda, lo sobrescribe, recupera la versión anterior por su `VersionId` y comprueba que es idéntica byte a byte; después lo borra, comprueba que sigue siendo legible, y lo restaura. Deja la prueba en `docs/evidencia_versionado.md` y `docs/evidencia_versionado.json`.

**De ahí salen los `VersionId` que van en el informe.** No los transcriban a mano: copien el bloque del archivo generado.

> La sonda vive en `_evidencia/prueba-de-versionado.txt`, fuera del prefijo de la fuente, porque la capa cruda es inmutable y la demostración no se hace sobre el dato del proyecto. El razonamiento está en la sección 6.3 de [`T5_lago.md`](T5_lago.md).

## 5. Verificar los seis criterios

```bash
python3 src/ingesta/verificar_lago.py
```

Se conecta al lago, lista lo que hay de verdad, corre nueve comprobaciones y las mapea contra los seis criterios de aceptación. Devuelve **0 si todo pasa y 1 si algo falla**, así que sirve tal cual para integración continua. Deja el resultado en `docs/evidencia_lago.md`.

La comprobación 5 relee cada objeto entero desde el almacenamiento para recalcular su `sha256`. Con la muestra grande eso tarda; para una pasada rápida:

```bash
python3 src/ingesta/verificar_lago.py --sin-integridad
```

**Para la entrega hay que ejecutarlo al menos una vez sin esa opción**, o el criterio 1 se queda sin la parte de integridad.

## 6. Mirar el lago por dentro

**Por la consola web** — <http://localhost:9001>, entrar con `minioadmin` / `minioadmin`. En la raíz de cada cubo está `_LEEME.txt`: ábranlo, porque es lo que verá quien llegue nuevo sin el repositorio. Para ver las versiones de un objeto hay que activar el interruptor *Show deleted objects* / el historial de versiones.

**Desde Python**, sin instalar nada más:

```bash
python3 - <<'PY'
import sys; sys.path.insert(0, "src/ingesta")
import comun, json
cfg = comun.cargar_config()
s3  = comun.cliente_s3(cfg)
cubo = comun.nombre_cubo(cfg, "cruda")
for o in s3.list_objects_v2(Bucket=cubo).get("Contents", []):
    print("%10d  %s" % (o["Size"], o["Key"]))
PY
```

**Leer el manifiesto de un objeto** — la ficha técnica es su misma clave más `.manifiesto.json`:

```bash
python3 - <<'PY'
import sys; sys.path.insert(0, "src/ingesta")
import comun, json
cfg = comun.cargar_config(); s3 = comun.cliente_s3(cfg)
cubo = comun.nombre_cubo(cfg, "cruda")
clave = "secop2_procesos/anio=2026/mes=08/dia=19/secop2_procesos_20260819.csv"
print(comun.leer_objeto(s3, cubo, comun.clave_manifiesto(cfg, clave)).decode())
PY
```

## 7. Qué llevarse al informe

Después de ejecutar los pasos 3, 4 y 5 quedan cuatro archivos generados en `docs/`. **Ninguno se edita a mano**; los cuatro se regeneran en cada corrida:

| Archivo | Qué aporta al informe |
|---|---|
| `evidencia_ingesta.json` | la clave exacta cargada, su `sha256`, bytes, filas y columnas |
| `evidencia_versionado.md` | la tabla de `VersionId` — va en la sección 6.2 de `T5_lago.md` |
| `evidencia_versionado.json` | lo mismo, con el detalle paso a paso |
| `evidencia_lago.md` | la tabla de los seis criterios — va en la sección 10 de `T5_lago.md` |

Además, capturen **una pantalla de la consola de MinIO** que muestre el objeto en su ruta particionada y el historial de versiones de la sonda. Los `VersionId` de la captura tienen que ser los mismos del archivo generado; eso es lo que hace la evidencia verificable en vez de decorativa.

## 8. La secuencia completa, de cero

```bash
git clone https://github.com/Andres-Ezreli/BigDataProcesoContratacion.git
cd BigDataProcesoContratacion/tarea5
docker compose up -d
python3 -m pip install -r requisitos.txt
python3 src/ingesta/cargar_cruda.py
python3 src/ingesta/demostrar_versionado.py
python3 src/ingesta/verificar_lago.py
```

Siete comandos. Si alguno falla en un clon limpio, el criterio 6 no se cumple y hay que arreglarlo antes de entregar, no explicarlo en el informe.

## 9. Si algo falla

| Síntoma | Qué pasa y qué hacer |
|---|---|
| `No hay respuesta del almacenamiento de objetos` | Docker no está corriendo, o el contenedor no arrancó. `docker compose ps` y `docker compose logs almacen` |
| `Error response from daemon` o `cannot connect to the Docker daemon` | Docker Desktop no está abierto. Ábranlo y esperen a que el icono deje de girar |
| Al bajar la imagen: `failed to copy: httpReadSeeker … lookup production.cloudfront.docker.com: no such host` | **DNS.** No es el `docker-compose.yml`. El DNS de la red no resuelve el CDN de Docker Hub desde dentro de la máquina virtual de Docker, aunque Windows sí lo resuelva. Por eso el compose apunta a `quay.io/minio/minio`, que es el registro propio de MinIO y esquiva ese CDN. Si aun así falla, ver la fila siguiente |
| Cualquier `docker pull` falla con `no such host`, pero el navegador sí navega | El servidor DNS de la red está agotando el tiempo de espera. Compruébenlo con `nslookup -type=A production.cloudfront.docker.com`: si sale `DNS request timed out`, es eso. Solución: en `%USERPROFILE%\.docker\daemon.json` añadan `"dns": ["8.8.8.8", "1.1.1.1"]` y reinicien Docker Desktop. Alternativa sin tocar nada: conectarse por cable o a otra red |
| El puerto 9000 está ocupado | Otro servicio lo usa. Cambien `"9000:9000"` por `"9010:9000"` en `docker-compose.yml` **y** `endpoint_url` a `http://localhost:9010` en `config/lago.json`. Los dos sitios, o no arranca |
| `Falta boto3` | Falta el paso 2, o están en otro entorno virtual |
| `HTTP Error 500` al descargar | El portal falla a ratos; el script reintenta cuatro veces solo. Si insiste, usen `--archivo` con una copia local |
| `No se pudo descargar la fuente tras 4 intentos` | Sin salida a internet, o el portal caído. `--archivo` |
| `CONFLICTO. Ya hay un objeto en esa clave con contenido DISTINTO` | **No es un error: es la regla de inmutabilidad funcionando.** Si de verdad es un lote nuevo, `--nuevo-lote`. Si no, revisen por qué el contenido cambió |
| `El encabezado cambio entre paginas` | El esquema del portal se movió a mitad de descarga. Vuelvan a ejecutar |
| `verificar_lago.py` falla en C7 | Falta ejecutar `demostrar_versionado.py` |
| `El almacenamiento devolvio VersionId nulo` | El versionado no estaba activo **antes** de la escritura. El versionado no es retroactivo: lo escrito antes de activarlo queda con versión `null` y no se recupera. Borren el lago (`docker compose down -v`) y empiecen de nuevo |
| El número de filas no cuadra con `--filas` | No es un fallo. El conteo es de **líneas**, y SECOP II trae campos de texto libre con saltos de línea dentro de comillas, que cuentan de más. Está declarado en `_nota_filas` del manifiesto |

## 10. Apagar

```bash
docker compose down          # apaga; el lago se conserva en el volumen
docker compose down -v       # apaga y BORRA el lago entero
```

El primero es el normal. El segundo es el que hay que usar para probar de verdad el criterio 6: borrar todo y reconstruirlo desde cero con la secuencia del paso 8.
