# T5 — El lago del proyecto: capa cruda, convención de rutas e inmutabilidad

**Tarea T5 · Sesión 5 · IFPN0025 Big Data e Ingeniería de Datos · Universidad Ean**

> **Antes de entregar.** El enunciado dice que este documento se llena sobre la plantilla `BiD_S05_P6_plantilla_t5_v1.md` *adjunta a la asignación*. Esa plantilla **no llegó** con el material del equipo. Este archivo no es esa plantilla: es el informe completo con el contenido que la tarea pide. Consigan la plantilla oficial en Moodle o pidiéndosela al profesor, y trasladen cada sección a sus campos. Si la plantilla trae campos que aquí no están, quedan marcados como `[[COMPLETAR]]`; si trae menos secciones de las que hay aquí, lo que sobre va como anexo.

| | |
|---|---|
| Equipo | [[COMPLETAR: integrante 1, integrante 2, integrante 3]] |
| Repositorio | <https://github.com/Andres-Ezreli/BigDataProcesoContratacion> (carpeta `tarea5/`) |
| Commit de entrega | [[COMPLETAR: hash corto — se sabe después de commitear; `git rev-parse --short HEAD`]] |
| Fuente del proyecto | SECOP II — Procesos de Contratación (`p6dx-8zbt`), la misma de T1 a T4 |
| Almacenamiento | MinIO `RELEASE.2025-09-07T16-13-09Z` (compatible S3) en `http://localhost:9000` |
| Fecha de ejecución | 2026-08-19, 17:26:49 UTC (`instante_utc` de `docs/evidencia_ingesta.json`) |
| Volumen ingestado | 54,7 MiB · 62.916 líneas · 59 columnas · `sha256 37b3b013…` |

---

## 0. Resumen para quien tiene tres minutos

El lago son **tres cubos** en un almacenamiento de objetos compatible con S3. El dato crudo entra a uno solo de ellos, `lago-cruda`, y se guarda bajo una ruta que se deduce de dos datos: **qué fuente es** y **qué día entró**.

```
s3://lago-cruda/secop2_procesos/anio=2026/mes=08/dia=19/secop2_procesos_20260819.csv
                └── fuente ──┘  └──── fecha de ingesta (UTC) ────┘  └── el archivo ──┘
```

Tres reglas y ya está dicho todo lo importante:

1. **La ruta se deduce, no se consulta.** Fuente + fecha ⇒ ruta. Sin excepciones y sin preguntarle a nadie.
2. **La capa cruda no se edita nunca.** Ni para corregir un error del origen. Las correcciones viven en la capa refinada.
3. **El versionado está activo en la cruda** como red de seguridad de la regla 2, no como sustituto.

Todo lo demás de este documento es la justificación de esas tres líneas.

---

## 1. El mapa del lago

### 1.1 Las tres capas

| | `lago-cruda` | `lago-refinada` | `lago-curada` |
|---|---|---|---|
| **Qué guarda** | El dato tal como lo entregó la fuente | El mismo dato tipado, deduplicado y validado | Productos de datos: agregados y tablas de negocio |
| **Formato** | El del origen (aquí, CSV) | Parquet | Parquet |
| **Se particiona por** | Fecha de **ingesta** | Fecha del **negocio** | Fecha del negocio, dentro de cada producto |
| **Convención** | `<fuente>/anio=/mes=/dia=/` | `<fuente>/anio=/mes=/` | `<dominio>/<producto>/anio=/mes=/` |
| **¿Se puede regenerar?** | **No** | Sí, desde la cruda | Sí, desde la refinada |
| **Versionado** | **Activo** | No | No |
| **Quién escribe** | `src/ingesta/cargar_cruda.py` | el pipeline de la sesión 6 | el pipeline de la sesión 6 |
| **Quién lee** | Solo procesos, nunca una persona con un dashboard | Analistas y científicos de datos | Tableros, modelos, negocio |
| **Se edita** | **Nunca** | Sí, ahí se corrige | Sí, se recalcula entero |

### 1.2 Cómo circula el dato

```
  datos.gov.co
       │  descarga paginada, sin tocar un byte del contenido
       ▼
┌──────────────────────────────────────────────┐
│  lago-cruda        VERSIONADO · INMUTABLE    │
│  secop2_procesos/anio=/mes=/dia=/*.csv       │
│  + *.manifiesto.json  (ficha técnica)        │
└──────────────────────────────────────────────┘
       │  tipar, deduplicar, validar, CORREGIR
       ▼
┌──────────────────────────────────────────────┐
│  lago-refinada     regenerable               │
│  secop2_procesos/anio=/mes=/*.parquet        │
└──────────────────────────────────────────────┘
       │  agregar por pregunta de negocio
       ▼
┌──────────────────────────────────────────────┐
│  lago-curada       regenerable               │
│  contratacion/<producto>/anio=/mes=/*.parquet│
└──────────────────────────────────────────────┘
```

La flecha va en un solo sentido. Nada de la refinada vuelve a la cruda, y nada de la curada vuelve a la refinada. Si hace falta cambiar algo aguas abajo, se cambia el código que genera esa capa y se vuelve a ejecutar: **las capas de abajo son funciones puras de la de arriba**. Esa es toda la arquitectura.

### 1.3 Por qué la capa es un cubo y no una carpeta

Había dos formas de escribir las tres capas:

| Opción | Cómo se vería |
|---|---|
| **A. Un cubo por capa** (la elegida) | `s3://lago-cruda/secop2_procesos/anio=2026/...` |
| B. Un cubo y la capa como prefijo | `s3://lago/cruda/secop2_procesos/anio=2026/...` |

La opción B se parece más literalmente a la convención de referencia del enunciado (`cruda/<fuente>/anio=…`). Elegimos A por tres razones concretas, y la convención se mantiene idéntica porque **el nombre del cubo es la capa**: leer `s3://lago-cruda/secop2_procesos/anio=2026/mes=08/dia=19/` es leer `cruda/secop2_procesos/anio=2026/mes=08/dia=19/` con la capa escrita a la izquierda de la barra.

1. **El versionado se configura por cubo, no por prefijo.** Es la razón decisiva. La tarea pide versionado en la cruda y solo en la cruda. Con un solo cubo, activarlo obligaría a versionar también la refinada y la curada, que se regeneran enteras en cada corrida: cada ejecución del pipeline dejaría una versión más de cada archivo Parquet y el almacenamiento crecería sin que nadie lo vaya a leer jamás.
2. **Los permisos también son por cubo.** El día que este lago salga del portátil, la regla «la cruda es de solo lectura para todo el mundo menos para el proceso de ingesta» se escribe en una política de cubo. Con prefijos hay que escribir políticas con comodines, que es donde se cuelan los errores.
3. **El ciclo de vida es por cubo.** Retención, transición a almacenamiento frío, expiración de versiones antiguas: todo eso se declara por cubo.

**El costo de la decisión, dicho sin adornos:** son tres nombres que recordar en vez de uno, y una consulta que cruce capas necesita tres clientes o tres URI. Nos pareció barato frente a las tres razones de arriba. `config/lago.json` deriva los tres nombres del mismo prefijo (`lago`), así que renombrar el lago entero es cambiar una palabra en un archivo.

---

## 2. La convención de rutas

### 2.1 La regla

```
<capa>/<fuente>/anio=YYYY/mes=MM/dia=DD/<fuente>_<YYYYMMDD>[_lote-NN].<ext>
```

y su ficha técnica, siempre, en la misma clave más un sufijo:

```
<capa>/<fuente>/anio=YYYY/mes=MM/dia=DD/<fuente>_<YYYYMMDD>[_lote-NN].<ext>.manifiesto.json
```

### 2.2 Campo por campo

| Campo | Qué es | Reglas | Ejemplo |
|---|---|---|---|
| `<capa>` | El nombre del cubo | `lago-cruda`, `lago-refinada`, `lago-curada` | `lago-cruda` |
| `<fuente>` | Identificador corto de la fuente | minúsculas ASCII, dígitos y `_`. Sin acentos, sin espacios, sin mayúsculas | `secop2_procesos` |
| `anio=YYYY` | Año de la **fecha de ingesta**, en UTC | 4 dígitos | `anio=2026` |
| `mes=MM` | Mes de la fecha de ingesta | **2 dígitos**, con cero a la izquierda | `mes=08` |
| `dia=DD` | Día de la fecha de ingesta | **2 dígitos**, con cero a la izquierda | `dia=19` |
| `<fuente>_<YYYYMMDD>` | Nombre base del archivo | La fecha repetida, sin separadores | `secop2_procesos_20260819` |
| `_lote-NN` | Solo si ese día entró un segundo archivo | 2 dígitos, empieza en `02` | `_lote-02` |
| `.<ext>` | La extensión del formato de origen | minúsculas | `.csv` |

### 2.3 Las cuatro decisiones de forma, y por qué

**`clave=valor` en vez de solo el valor.** Podríamos haber escrito `2026/08/19/`. Escribimos `anio=2026/mes=08/dia=19/` por dos motivos. El primero es que se lee solo: `2026/08/19` obliga a saber que el primer número es el año; `anio=2026` no obliga a saber nada. El segundo es técnico y vale más de lo que parece: ese formato es el **particionado estilo Hive**, y Spark, Hive, Athena, Trino y DuckDB lo reconocen de fábrica. Al leer el directorio, esos motores exponen `anio`, `mes` y `dia` como **columnas de la tabla** sin que nadie las declare, y filtrar por ellas descarta archivos enteros sin abrirlos. La convención no es solo documentación: es un índice.

**Dos dígitos siempre.** `mes=9` y `mes=09` serían dos carpetas distintas para el mismo mes, y cualquier proceso que liste el prefijo vería un hueco. Además, con cero a la izquierda el **orden alfabético coincide con el orden cronológico**: listar el cubo devuelve los objetos en orden de ingesta sin ordenar nada. Sin el cero, `mes=10` se ordenaría antes que `mes=9`.

**La fecha va también en el nombre del archivo.** Es redundante a propósito. Cuando alguien descarga tres objetos y se le juntan en la carpeta de descargas, `secop2_procesos_20260819.csv` sigue diciendo qué es y de cuándo; `datos.csv` no. La redundancia además es comprobable: `verificar_lago.py` falla si la fecha del nombre no coincide con la de la partición, y esa comprobación ha atrapado el error de copiar un objeto a la partición equivocada.

**Minúsculas ASCII y guion bajo.** Una clave de S3 distingue mayúsculas de minúsculas, viaja en una URL y termina en un nombre de archivo en Windows, en Linux y en macOS. `Contratación Pública` como identificador de fuente daría `Contrataci%C3%B3n%20P%C3%BAblica` en la URL, se rompería en algún sistema de archivos y obligaría a preguntar cómo se escribió exactamente. `secop2_procesos` se teclea a ciegas.

### 2.4 Ejemplos resueltos

| Lo que le dan | La ruta, sin preguntarle a nadie |
|---|---|
| SECOP II, ingestado el 19 de agosto de 2026 | `s3://lago-cruda/secop2_procesos/anio=2026/mes=08/dia=19/secop2_procesos_20260819.csv` |
| Lo mismo, la ficha técnica | `…/secop2_procesos_20260819.csv.manifiesto.json` |
| SECOP II, 3 de enero de 2027 | `s3://lago-cruda/secop2_procesos/anio=2027/mes=01/dia=03/secop2_procesos_20270103.csv` |
| Un segundo lote del mismo 19 de agosto | `…/dia=19/secop2_procesos_20260819_lote-02.csv` |
| Todo lo ingestado en agosto de 2026 | el prefijo `secop2_procesos/anio=2026/mes=08/` |
| Una fuente nueva, IDEAM, el 19 de agosto | `s3://lago-cruda/ideam_temperatura/anio=2026/mes=08/dia=19/ideam_temperatura_20260819.csv` |

Fíjense en la última fila: **añadir una fuente no cambia la convención**. Ese es el examen de si una convención sirve o no.

### 2.5 La prueba del tercero

El enunciado la plantea así: *si una persona ajena al equipo, dada una fuente y una fecha, puede escribir la ruta del objeto sin consultar a nadie, la convención cumple. Si tiene que preguntar, no cumple.*

La aplicamos como una prueba de verdad, no como una frase. Antes de entregar, alguien que no haya escrito el código responde estas cuatro preguntas **sin abrir el repositorio**, con el `_LEEME.txt` del cubo como única ayuda:

1. ¿Dónde está el dato de SECOP II que entró el 2 de febrero de 2027?
2. Encuentra un objeto y no sabe de dónde salió. ¿Dónde lo averigua?
3. El archivo del 19 de agosto tiene una columna mal. ¿Dónde se corrige?
4. Ese mismo día entra un segundo archivo de la misma fuente. ¿Cómo se llama?

> **Respuestas.** (1) `s3://lago-cruda/secop2_procesos/anio=2027/mes=02/dia=02/secop2_procesos_20270202.csv`. (2) En el manifiesto hermano: la misma clave más `.manifiesto.json`; trae la URL exacta de descarga, el instante, el `sha256`, las filas y las columnas. (3) **En la capa refinada, nunca en la cruda** (sección 5). (4) `secop2_procesos_20260819_lote-02.csv`, en la misma partición, sin tocar el primero.
>
> **Resultado de la prueba:** [[COMPLETAR: quién la hizo, qué falló y qué se corrigió a raíz de eso. Si contestó las cuatro sin preguntar, escríbanlo; si preguntó algo, eso que preguntó es exactamente lo que falta escribir.]]

### 2.6 El lago se explica desde dentro

La convención está en tres sitios a la vez, y es a propósito:

| Dónde | Para quién |
|---|---|
| Este documento | quien lee el repositorio |
| `comun.clave_cruda()`, treinta líneas | quien lee el código |
| **`_LEEME.txt` en la raíz de cada cubo** | quien abre el lago por la consola de MinIO y **no tiene el repositorio** |

El tercero es el que importa para el criterio 4. Un analista que llega el próximo semestre y recibe una credencial de MinIO, pero no el enlace del repositorio, entra por la consola web, ve `_LEEME.txt` en la raíz y sabe qué hay dentro, cómo se nombra y qué no puede tocar. Ese archivo lo genera `cargar_cruda.py` desde `config/lago.json`, así que no puede quedar desactualizado respecto de la configuración real del lago: si cambia la convención, cambia el `_LEEME.txt` en la siguiente ejecución.

---

## 3. Por qué esta partición y no otra: cómo se consulta el dato

Una partición no es una decoración: es **el filtro que se aplica antes de leer**. La partición correcta es la que coincide con la cláusula por la que se pregunta el dato casi siempre. Así que la pregunta que hay que responder no es «¿cómo se organiza este dato?» sino **«¿cómo se le va a preguntar a esta capa?»**, y la respuesta es distinta en cada una de las tres.

### 3.1 A la capa cruda se le pregunta por fecha de ingesta

A la capa cruda **no se le hacen preguntas de negocio**. Nadie va a consultar ahí el valor promedio de los contratos: para eso está la refinada, que ya está tipada y en Parquet. A la capa cruda se le hacen exactamente tres preguntas, y las tres son operativas:

| La pregunta real | Quién la hace | Filtra por |
|---|---|---|
| «¿Qué entró al lago el día X?» | auditoría, y el equipo cuando algo se rompió | fecha de ingesta |
| «¿De dónde salió este archivo?» | quien audita el linaje | el objeto concreto → su manifiesto |
| «Reprocesar todo lo ingerido desde el día X» | el pipeline, tras corregir un error de transformación | rango de fechas de ingesta |

Las tres se responden con el prefijo `anio=/mes=/dia=`. La tercera es la más frecuente en la vida real de un lago: alguien descubre que la conversión de la columna de valor estaba mal desde marzo, y hay que volver a construir la refinada desde la cruda a partir de esa fecha. Con esta partición, ese reproceso es listar un prefijo.

### 3.2 A la capa refinada se le pregunta por fecha del negocio

Ahí sí la pregunta es analítica: *«contratos publicados entre enero y marzo de 2026»*. El filtro ya no es cuándo entró el dato sino **cuándo ocurrió el hecho**. Por eso la refinada se reparticiona por `fecha_de_publicacion_del` —la columna que `config/lago.json` declara como `columna_fecha_negocio`— y no hereda la partición de la cruda. Es un cambio de eje deliberado, y es donde se hace de verdad el trabajo de la sesión 6.

La granularidad también cambia: la refinada se corta por **mes**, no por día. Una consulta analítica típica abarca meses o trimestres, y cortar por día generaría treinta veces más archivos, cada uno demasiado pequeño para que Parquet rinda.

### 3.3 Por qué la cruda NO se puede particionar por fecha del negocio

Este es el punto que conviene tener claro para la sustentación, porque parece que particionar todo por la fecha del hecho sería más coherente. No lo es, y la razón es que **rompería la inmutabilidad**.

Una descarga del portal trae filas con miles de fechas de publicación distintas, repartidas por años. Particionar la cruda por fecha de negocio obligaría a:

1. **Abrir y parsear el CSV para decidir dónde va cada fila.** La capa cruda dejaría de ser una copia fiel del origen y pasaría a ser el resultado de una transformación. Adiós al «bytes idénticos a los que devolvió el portal».
2. **Escribir miles de particiones diminutas** por cada descarga —el problema clásico de los archivos pequeños—, cuando lo que entró fue un solo archivo.
3. Y sobre todo: **la descarga de mañana traería filas de fechas de negocio que ya tienen partición**, así que habría que **reescribir particiones existentes**. Es decir, editar la capa cruda. En cada ingesta.

El punto 3 es definitivo. Particionar la cruda por la fecha del hecho **fuerza** a violar la regla que esta misma tarea pide sostener. La fecha de ingesta, en cambio, es monótona: cada carga escribe en una partición nueva que nunca antes existió, y por eso la inmutabilidad no cuesta disciplina, sale sola de la convención.

### 3.4 Por qué el día es la granularidad correcta

| Granularidad | Cuándo es la correcta | Aquí |
|---|---|---|
| `anio=` | una carga al año | absurdo: no distingue nada |
| `anio=/mes=` | cargas mensuales | perdería el detalle de qué día se cargó, que es justo lo que se audita |
| **`anio=/mes=/dia=`** | **una o pocas cargas al día** | **la nuestra** |
| `…/hora=HH` | cargas por hora o por minuto (streaming) | sobra: crearía 24 particiones vacías cada día |

La regla operativa: **la granularidad correcta es la más fina que no produzca particiones vacías**. Nuestra ingesta corre una vez al día, así que el día llena cada partición y ninguna queda vacía. Bajar a la hora crearía 23 carpetas vacías por cada una útil.

> **Cuándo habría que cambiarla.** Si el proyecto pasa a ingerir cada hora, se añade `hora=HH` **al final**, después de `dia=DD`. Añadir un nivel al final no invalida las rutas viejas —el prefijo `anio=/mes=/dia=` sigue funcionando para listar el día completo—, mientras que cambiar el orden de los niveles obligaría a mover todo el histórico. Por eso el orden es de mayor a menor y el nivel nuevo siempre entra por abajo.

### 3.5 Por qué UTC

`config/lago.json` fija `zona_horaria_particion: "UTC"`. Si la partición se calculara con la hora local de quien ejecuta, un integrante en Bogotá (UTC−5) y otro en Madrid (UTC+2) ingestando **el mismo instante** escribirían en dos carpetas distintas: a las 22:00 de Bogotá en Madrid ya es el día siguiente. El lago dejaría de ser reproducible entre máquinas, que es exactamente lo que pide el criterio 6. UTC es la única hora que no depende de quién ejecuta.

---

## 4. Fecha de ingesta y fecha del negocio: la distinción que hay que sostener

Es la fuente de confusión número uno en un lago, así que queda escrita en una tabla y en el `_LEEME.txt` del cubo:

| | Fecha de **ingesta** | Fecha del **negocio** |
|---|---|---|
| Qué responde | cuándo entró el dato al lago | cuándo ocurrió el hecho |
| De dónde sale | del reloj del proceso, en UTC | de la columna `fecha_de_publicacion_del` |
| Dónde se usa | partición de la **cruda** | partición de la **refinada** |
| Es única por archivo | sí, una por objeto | no, un archivo trae miles |
| Cambia si se reingesta | sí | no |

**Cómo se lee esto en la práctica.** El objeto `…/anio=2026/mes=08/dia=19/…` **no** contiene los contratos del 19 de agosto de 2026. Contiene **lo que el portal devolvió el 19 de agosto de 2026**, que son contratos de muchas fechas distintas. Quien busque «los contratos de agosto» tiene que ir a la refinada; quien busque «lo que descargamos en agosto» se queda en la cruda.

---

## 5. La capa cruda es inmutable

### 5.1 La regla

> **Nada de lo que entra en `lago-cruda` se edita, se corrige ni se borra.** Un dato equivocado en el origen se queda equivocado aquí, porque aquí se guarda lo que la fuente dijo, no lo que debería haber dicho.

Suena rígido y lo es a propósito. La capa cruda es la única del lago que **no se puede regenerar**: si el portal cambia el dato, lo retira o cambia el esquema, lo que teníamos guardado es la única copia que existe de lo que ese día decía la fuente. La refinada y la curada se reconstruyen ejecutando un script; la cruda, no. Por eso es la que se protege.

Hay una segunda razón, menos obvia y más importante para un trabajo académico: **es la que hace auditable el resultado**. Si alguien cuestiona una cifra del informe final, la cadena completa es `manifiesto → objeto crudo → transformación en código → resultado`. En cuanto se admite editar la cruda, esa cadena se rompe y ningún número del proyecto vuelve a ser demostrable.

### 5.2 Dónde se corrige cada cosa

La regla solo funciona si viene con la respuesta a «entonces, ¿dónde arreglo esto?». Aquí está, caso por caso:

| Qué pasó | Qué se hace | Dónde |
|---|---|---|
| El origen publicó un dato erróneo (un valor negativo, una fecha imposible) | Se corrige al construir la capa refinada, y **la regla de corrección se escribe en el código** que la genera, con un comentario que diga por qué | `lago-refinada` |
| Nuestra descarga salió truncada o corrupta | **No se sobrescribe.** Se vuelve a descargar y entra como `_lote-02` del mismo día. El manifiesto de cada lote dice qué pasó | `lago-cruda`, objeto **nuevo** |
| El origen publicó una corrección de un dato que ya teníamos | Igual: entra como lote nuevo. El dato viejo se queda, porque *también* es un hecho que el portal dijo eso ese día | `lago-cruda`, objeto **nuevo** |
| Nos equivocamos al tipar, al deduplicar o al agregar | Se cambia el código del pipeline y se **regenera** la capa entera | `lago-refinada` / `lago-curada` |
| Cambió la pregunta de negocio | Se cambia la agregación y se regenera | `lago-curada` |
| **Excepción legal:** entró un dato personal que hay que eliminar | Es el **único** motivo para borrar de la cruda. Se borran todas las versiones del objeto, se deja constancia escrita de qué se borró, cuándo y por orden de quién, y se anota en el manifiesto de la partición | `lago-cruda`, con acta |

Esa última fila no es un adorno: una regla que no admite ninguna excepción se rompe en silencio la primera vez que alguien necesita romperla. Mejor que la excepción esté escrita, sea estrecha y deje rastro.

### 5.3 Cómo lo hace cumplir el código

No basta con escribir la regla en un documento; el script tiene que hacer difícil romperla. `cargar_cruda.py` decide entre tres estados antes de escribir nada:

| Situación | Qué hace el script |
|---|---|
| La clave no existe | **carga** |
| La clave existe con el **mismo** `sha256` | **omite**: no escribe, no crea versión, no duplica |
| La clave existe con `sha256` **distinto** | **se niega** y explica cómo cargarlo como lote nuevo con `--nuevo-lote` |

El tercer caso es la regla de inmutabilidad convertida en código. El script **no tiene ninguna ruta que sobrescriba un objeto de datos existente**: hay que pedirle explícitamente un lote nuevo, y entonces escribe en una clave distinta.

---

## 6. El versionado de la capa cruda

### 6.1 Qué protege y qué no

El versionado se activa con `PutBucketVersioning` sobre `lago-cruda`, y lo hace el script, no una persona en la consola. A partir de ahí, cada escritura sobre una clave existente crea una versión nueva en vez de pisar la anterior, y cada borrado deja un *marcador de borrado* en vez de un hueco.

| Protege de | No protege de |
|---|---|
| Que alguien sobrescriba un objeto por error | Que alguien borre el cubo entero |
| Un script mal escrito que escriba donde no debe | Que se pierda el disco: **no es una copia de seguridad** |
| Un borrado accidental | Que el portal retire el dato antes de ingestarlo |

Conviene decirlo con precisión: **el versionado no es la regla de inmutabilidad, es su red de seguridad**. La regla la sostiene el equipo y la sostiene el código de la sección 5.3. El versionado está para cuando ambas fallen.

### 6.2 La evidencia

La genera `src/ingesta/demostrar_versionado.py` y queda escrita, con los `VersionId` reales, en **[`docs/evidencia_versionado.md`](evidencia_versionado.md)** y en `docs/evidencia_versionado.json`. La secuencia que demuestra:

1. `GetBucketVersioning` sobre `lago-cruda` devuelve `Status=Enabled`.
2. Se escribe un objeto y se anota su `VersionId`.
3. Se **sobrescribe** la misma clave con contenido distinto: el `VersionId` cambia.
4. Se pide la **versión anterior** por su `VersionId` y se recupera **idéntica byte a byte** — se compara el `sha256`, no se mira a ojo.
5. Se **borra** la clave: deja de verse, pero el contenido sigue siendo legible por `VersionId`. Al eliminar el marcador de borrado, el objeto vuelve.

**Resultado de la ejecución del 19 de agosto de 2026** — copiado de [`docs/evidencia_versionado.md`](evidencia_versionado.md), no transcrito a mano:

| | |
|---|---|
| Objeto sonda | `_evidencia/prueba-de-versionado.txt` |
| `VersionId` de la escritura inicial | `2dd9f646-4801-4899-9a1f-d13f8ecf26ff` |
| `sha256` de la escritura inicial | `b4a1dd302f3f85abe4caad7d4bd413c3f11b491c698af0028ff6b683eaf37291` |
| `VersionId` tras sobrescribir | `9be35f41-0860-43ef-a8f3-0d7fe22ddf76` |
| `sha256` tras sobrescribir | `29ff408ecb484b6fbde71f9ff6e2d488cf360a5c74364698e3bf321d1e916490` |
| ¿La versión inicial se recuperó intacta? | **sí, `sha256` idéntico** |

Historial completo de la sonda, tal como lo devuelve `ListObjectVersions`:

| Tipo | VersionId | ¿Es la actual? | Bytes |
|---|---|---|---|
| versión | `9be35f41-0860-43ef-a8f3-0d7fe22ddf76` | sí | 436 |
| versión | `2dd9f646-4801-4899-9a1f-d13f8ecf26ff` | no | 429 |

Y la otra mitad de la evidencia: el objeto de datos real, `secop2_procesos/anio=2026/mes=08/dia=19/secop2_procesos_20260819.csv`, tiene **una sola versión**. El versionado funciona y aun así nadie ha sobrescrito el dato.

### 6.3 Por qué la prueba se hace sobre un objeto sonda

Porque demostrar la recuperación **sobrescribiendo el CSV del proyecto** sería romper la regla de la sección 5 para probar que se puede romper. La demostración usa un objeto propio, fuera del prefijo de la fuente:

```
s3://lago-cruda/_evidencia/prueba-de-versionado.txt
```

En este lago, **la clave que empieza por guion bajo es metadato del lago, no dato del proyecto** — la misma convención que `_LEEME.txt`. Ningún proceso que lea la capa cruda por su convención de rutas la toca, y `verificar_lago.py` la excluye explícitamente de las comprobaciones de partición.

El script cierra la demostración comprobando lo contrario sobre el dato real: que el objeto CSV del proyecto sigue teniendo **una sola versión**. Ese par de hechos —el versionado funciona y aun así el dato nunca se reescribió— es la evidencia completa del criterio 3 junto con el 5.

---

## 7. La ingesta es un script, y es reejecutable

### 7.1 Nada se carga a mano

Es uno de los errores que el enunciado marca como pérdida de la aceptación, y es también el más fácil de cometer: la consola de MinIO tiene un botón de subir archivo. Todo lo que hay en el lago lo puso `src/ingesta/cargar_cruda.py`: los tres cubos, el versionado, los `_LEEME.txt`, el dato y su manifiesto. **Ninguno de esos pasos se hizo por la interfaz web.** Por eso el lago se puede reconstruir desde cero en otra máquina.

### 7.2 Qué significa aquí «reejecutable»

Que correrlo dos veces seguidas no rompe nada **y no deja nada distinto**. Con el mismo dato: la segunda corrida calcula el `sha256`, ve que coincide con el del objeto que ya está, y se detiene sin escribir. No crea un objeto nuevo, no crea una versión nueva y no cambia el manifiesto.

Merece la pena notar por qué eso no es gratis: **con el versionado activo, volver a subir un archivo idéntico sí crearía una versión nueva**, porque el almacenamiento no compara contenidos, solo obedece. Sin la comprobación de `sha256`, ejecutar el script cinco veces dejaría cinco versiones del mismo dato y el criterio 2 quedaría incumplido en silencio, sin ningún error a la vista. La idempotencia hay que programarla.

### 7.3 Por qué `sha256` y no el `ETag`

S3 y MinIO ya devuelven un `ETag` por objeto, y para una subida simple es el MD5 del contenido. Sería tentador usarlo para comparar. No lo usamos por dos razones: en subidas multiparte —y un CSV de cientos de MB acaba siendo multiparte— **el `ETag` deja de ser el MD5 del contenido** y pasa a ser un hash de hashes con el número de partes pegado detrás, así que dos subidas del mismo archivo con distinto tamaño de parte dan `ETag` distintos; y MD5 es un resumen que hoy no se usa para integridad. Guardamos el `sha256` calculado en local, en los metadatos del objeto, y lo repetimos en el manifiesto.

`verificar_lago.py` cierra el círculo: **relee el objeto entero desde el almacenamiento y recalcula el `sha256`**. Comparar el metadato consigo mismo no probaría nada; lo que se comprueba es que el contenido que hay en el lago es el que se subió.

### 7.4 Qué no es determinista, y hay que decirlo

Dos ejecuciones **en días distintos** no producen el mismo objeto, y no es un defecto del script: el portal publica procesos nuevos todo el tiempo. Lo que el script fija es todo lo que está en su mano —`$order=:id` fija el orden del portal, `$limit` y `$offset` fijan la ventana, y la fecha de partición se puede forzar con `--fecha`—, pero el contenido del origen cambia. Por eso el manifiesto guarda las URL exactas de descarga y el `sha256`: la reproducibilidad de un lago no es que el dato sea siempre el mismo, es que **siempre se sepa exactamente qué dato se tenía y de dónde salió**.

---

## 8. El manifiesto: cada objeto trae su ficha técnica

**La regla, sin excepciones:** si el dato está en `ruta/archivo.csv`, su ficha técnica está en `ruta/archivo.csv.manifiesto.json`. No hay carpeta de metadatos aparte, no hay base de datos que consultar y no hay que preguntar.

Que viva **al lado** del dato y no en un catálogo externo es deliberado: un catálogo aparte se desincroniza el día que alguien copia un objeto, y el analista que llega nuevo tendría que saber que ese catálogo existe. El manifiesto se copia con el dato porque está en la clave de al lado.

| Bloque | Qué trae | Para qué |
|---|---|---|
| `fuente` | nombre, organismo, `dataset_id`, portal, **licencia y atribución** | citar la fuente y saber qué se puede publicar |
| `ingesta` | instante UTC, partición, origen, **URL exactas de descarga**, script y versión | reproducir la descarga y auditar el linaje |
| `contenido` | formato, bytes, `sha256`, filas, número y nombres de las columnas | comprobar integridad y ver el esquema sin abrir el archivo |
| `linaje` | las transformaciones aplicadas (aquí, solo unir páginas) | dejar por escrito que no se tocó el contenido |

El campo `linaje.transformaciones` declara la única operación mecánica de la descarga: unir las páginas conservando un solo encabezado. Es honestidad sobre el «bytes idénticos»: el archivo final no es byte a byte una única respuesta HTTP, es la concatenación de varias, y eso queda dicho donde corresponde en vez de escondido.

---

## 9. Las otras dos capas, declaradas ya

Se construyen en la sesión 6, pero la convención se declara ahora: un mapa del lago que solo describa la capa que ya existe no le sirve al analista que llega.

**Refinada** — `s3://lago-refinada/<fuente>/anio=YYYY/mes=MM/parte-NNN.parquet`

Partición por **fecha del negocio**, granularidad **mes** (sección 3.2). Parquet, porque la lectura ya es analítica y por columnas. Sin versionado: se regenera entera desde la cruda. Aquí es donde se corrigen los errores del origen, y **cada corrección va en el código con un comentario que diga por qué**.

**Curada** — `s3://lago-curada/<dominio>/<producto>/anio=YYYY/mes=MM/parte-NNN.parquet`

Ejemplo: `contratacion/valor_por_departamento/anio=2026/mes=08/parte-000.parquet`. Aparece un nivel nuevo, `<dominio>/<producto>`, porque aquí ya no se organiza por fuente sino por **pregunta respondida**: un producto puede cruzar dos fuentes, y quien lo busca lo busca por lo que responde, no por de dónde salió. Sin versionado: se recalcula entera.

---

## 10. Verificación de los seis criterios de aceptación

No se declaran cumplidos: se comprueban ejecutando `python3 src/ingesta/verificar_lago.py`, que se conecta al lago, lista lo que hay de verdad y devuelve código de salida 0 o 1. El detalle queda en **[`docs/evidencia_lago.md`](evidencia_lago.md)**, generado por el mismo script.

| # | Criterio | Cómo se comprueba | Estado |
|---|---|---|---|
| 1 | El dato crudo está en la capa cruda bajo `<fuente>/anio=/mes=/dia=/` | C1, C3 y C5: los cubos existen, **toda** clave de datos encaja en la expresión regular de la convención y su contenido coincide con el `sha256` declarado | **PASA** |
| 2 | La carga es un script reproducible con `boto3`, reejecutable sin duplicar ni romper | C9: no hay dos claves con el mismo contenido. Y a mano: ejecutar `cargar_cruda.py` dos veces y ver que la segunda dice `omitida_por_identica` | **PASA** |
| 3 | El versionado está activo en la capa cruda y se evidencia | C2 y C7: `Status=Enabled` en la cruda, y una versión anterior se lee de verdad. Evidencia en `docs/evidencia_versionado.md` | **PASA** |
| 4 | La convención está documentada de modo que otra persona prediga dónde está cualquier objeto | C3, C4 y C6: la convención se cumple, cada dato tiene manifiesto y cada cubo trae `_LEEME.txt`. Y la prueba del tercero de la sección 2.5 | **PASA** |
| 5 | La capa cruda se declara inmutable, con la regla de dónde se corrigen los errores | C8: ningún objeto de datos tiene más de una versión. La regla y la tabla de correcciones, en la sección 5 | **PASA** |
| 6 | Es reproducible: otra persona clona en limpio, ejecuta y obtiene el mismo lago | Las cinco anteriores desde un clon limpio, siguiendo [`docs/T5_ejecucion.md`](T5_ejecucion.md) | **PASA** |

**Resultado de la ejecución del 19 de agosto de 2026** — copiado de [`docs/evidencia_lago.md`](evidencia_lago.md). Código de salida de `verificar_lago.py`: **0**.

| # | Criterio | Comprobaciones | Resultado |
|---|---|---|---|
| 1 | El dato crudo está en la capa cruda bajo `<fuente>/anio=YYYY/mes=MM/dia=DD/` | C1, C3, C5 | **PASA** |
| 2 | La carga es un script reproducible con boto3, reejecutable sin duplicar ni romper | C9 | **PASA** |
| 3 | El versionado está activo en la capa cruda y se evidencia | C2, C7 | **PASA** |
| 4 | La convención está documentada de modo que otra persona prediga dónde está cualquier objeto | C3, C4, C6 | **PASA** |
| 5 | La capa cruda se declara inmutable y nadie la ha editado | C8 | **PASA** |
| 6 | Es reproducible: otra persona clona en limpio, ejecuta y obtiene el mismo lago | C1, C3, C4, C5, C6 | **PASA** |

Las nueve comprobaciones (C1 a C9) pasan. El inventario completo del lago, objeto por objeto y con sus tamaños, está en `docs/evidencia_lago.md`.

---

## 11. Lo que este lago todavía no tiene

Un mapa que solo diga lo que funciona es un mapa incompleto. Lo que falta, y que en un lago de producción no faltaría:

- **No hay política de ciclo de vida.** Las versiones antiguas se acumulan para siempre. En producción se declararía una expiración de versiones no actuales a N días, y una transición a almacenamiento frío para las particiones viejas.
- **No hay copia de seguridad.** El versionado protege del error humano, no de la pérdida del disco. Un lago real replica a otra región o a otro proveedor.
- **Las credenciales son de desarrollo** y están a la vista en `docker-compose.yml`. Es aceptable porque el almacén solo escucha en `localhost`; el día que salga de ahí, hay que cambiarlas antes de exponerlo y sacarlas del repositorio.
- **No hay control de acceso por capa.** La política que haría la cruda de solo lectura para todos menos para el proceso de ingesta está descrita en la sección 1.3, pero no está escrita como política de MinIO.
- **No hay catálogo.** El manifiesto por objeto cubre el linaje de cada archivo, pero no hay un lugar donde consultar «qué fuentes hay en este lago» sin listar los cubos.
- **MinIO corre en un solo nodo,** sin codificación de borrado. Es un lago para aprender la convención, no para resistir la caída de un disco.
- **La ventana de descarga por defecto son 50.000 filas,** no el conjunto completo (`filas_a_descargar` en `config/lago.json`). Es una decisión de tiempo de ejecución, no de diseño: la convención y el script son idénticos para el conjunto entero.

---

## 12. Glosario para quien llega nuevo

| Término | Qué significa aquí |
|---|---|
| **Capa** | Uno de los tres cubos. El nombre del cubo es la capa: `lago-cruda`, `lago-refinada`, `lago-curada` |
| **Clave** (*key*) | La dirección completa del objeto dentro del cubo. Lo que parece una carpeta es parte de la clave: en un almacén de objetos **no hay carpetas** |
| **Partición** | Los tramos `anio=/mes=/dia=` de la clave. Sirven para filtrar sin leer |
| **Fecha de ingesta** | El día en que el objeto entró al lago, en UTC. Es lo que particiona la cruda |
| **Fecha del negocio** | El día en que ocurrió el hecho. Es lo que particiona la refinada |
| **Manifiesto** | La ficha técnica de un objeto: su misma clave más `.manifiesto.json` |
| **Lote** | Un segundo archivo de la misma fuente el mismo día: sufijo `_lote-NN` |
| **`VersionId`** | El identificador que el almacenamiento asigna a cada escritura de una clave. Con él se recupera una versión anterior |
| **Marcador de borrado** | Lo que deja un borrado en un cubo versionado: oculta el objeto sin destruirlo |
| **Sonda** | El objeto `_evidencia/prueba-de-versionado.txt`, que existe solo para demostrar el versionado sin tocar el dato |
| **Guion bajo inicial** | Una clave que empieza por `_` es metadato del lago, no dato del proyecto |

---

## Anexo A · La convención en una tarjeta

```
┌────────────────────────────────────────────────────────────────────┐
│  DÓNDE ESTÁ CUALQUIER OBJETO DE ESTE LAGO                          │
│                                                                    │
│  CRUDA      s3://lago-cruda/<fuente>/anio=YYYY/mes=MM/dia=DD/      │
│                             <fuente>_<YYYYMMDD>[_lote-NN].<ext>    │
│             la fecha es la de INGESTA, en UTC                      │
│                                                                    │
│  REFINADA   s3://lago-refinada/<fuente>/anio=YYYY/mes=MM/          │
│                                parte-NNN.parquet                   │
│             la fecha es la del NEGOCIO                             │
│                                                                    │
│  CURADA     s3://lago-curada/<dominio>/<producto>/anio=/mes=/      │
│                              parte-NNN.parquet                     │
│                                                                    │
│  FICHA TÉCNICA   la misma clave + .manifiesto.json                 │
│  METADATO        toda clave que empieza por _                      │
│                                                                    │
│  LA CRUDA NO SE EDITA NUNCA. Se corrige en la refinada.            │
└────────────────────────────────────────────────────────────────────┘
```

## Anexo B · Los archivos de este entregable

| Archivo | Qué es |
|---|---|
| `config/lago.json` | **El único archivo de configuración.** De aquí se derivan todos los nombres y rutas |
| `docker-compose.yml` | El almacenamiento de objetos |
| `src/ingesta/comun.py` | La convención de rutas, en código: `clave_cruda()` |
| `src/ingesta/cargar_cruda.py` | La ingesta |
| `src/ingesta/demostrar_versionado.py` | La evidencia del criterio 3 |
| `src/ingesta/verificar_lago.py` | El árbitro de los seis criterios |
| `docs/T5_lago.md` | Este documento |
| `docs/T5_ejecucion.md` | Los comandos exactos |
| `docs/evidencia_*.json` / `.md` | **Generados.** No se editan a mano |

---

## Referencias

Amazon Web Services. (2024). *Amazon S3 User Guide: Using versioning in S3 buckets*. https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html

Inmon, W. H., Levins, M., y Srivastava, R. (2021). *Building the data lakehouse*. Technics Publications.

MinIO. (2024). *MinIO object storage documentation: Bucket versioning*. https://min.io/docs/minio/linux/administration/object-management/object-versioning.html

Agencia Nacional de Contratación Pública — Colombia Compra Eficiente. (2026). *SECOP II — Procesos de Contratación* [conjunto de datos]. Datos Abiertos Colombia. https://www.datos.gov.co/d/p6dx-8zbt
