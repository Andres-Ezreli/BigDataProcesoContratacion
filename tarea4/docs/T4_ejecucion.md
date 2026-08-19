# T4 — Ejecución y reproducción

Estos son los comandos exactos. Alguien ajeno al equipo debe poder clonar el repositorio, seguir esta página de arriba abajo y obtener el mismo resultado y las mismas cifras de mezcla sin preguntar nada.

Requisitos: Python 3.8 o superior en los nodos y un clúster con Hadoop y YARN. Sin dependencias externas de Python.

---

## 1. Configurar la fuente

Todo lo editable vive en un solo archivo: `src/mapreduce/esquema.json`.

```bash
# ver el encabezado para ubicar las columnas (0 es la primera)
head -1 datos/fuente.csv | tr ',' '\n' | nl -v0
```

Ajusten en `esquema.json`:

| Campo | Qué es |
|---|---|
| `ruta_local`, `ruta_hdfs` | dónde está la fuente en local y en HDFS |
| `delimitador` | el separador real del archivo |
| `indice_clave`, `indice_valor` | posición de las columnas, **empezando en 0** |
| `separador_miles`, `separador_decimal` | `"."` y `","` para formato colombiano; `""` y `"."` para formato anglosajón |
| `quitar_simbolos` | símbolos a limpiar antes de convertir a número |

> Verifiquen con la prueba local del paso 2 antes de subir nada al clúster. Si `registros_descartados` sale casi igual a `registros_leidos`, los índices o el separador decimal están mal.

---

## 2. Prueba local (antes de tocar el clúster)

El `sort` intermedio simula lo que hace la mezcla del framework. Si el trabajo no funciona aquí, tampoco va a funcionar en el clúster, y depurarlo aquí cuesta segundos en vez de minutos.

```bash
# sin combinador
cat datos/muestra.csv \
  | python3 src/mapreduce/mapper.py \
  | sort -t$'\t' -k1,1 \
  | python3 src/mapreduce/reducer.py \
  > /tmp/local_sin.txt

# con combinador, simulando 3 splits
split -n l/3 datos/muestra.csv /tmp/split_
for f in /tmp/split_*; do
  cat "$f" | python3 src/mapreduce/mapper.py \
    | sort -t$'\t' -k1,1 | python3 src/mapreduce/combiner.py
done | sort -t$'\t' -k1,1 | python3 src/mapreduce/reducer.py \
  > /tmp/local_con.txt

# prueba de que el combinador no altera el resultado
diff /tmp/local_sin.txt /tmp/local_con.txt && echo "IDENTICOS"
```

Ese `diff` vacío es la evidencia de que el combinador está bien escrito. Si sale diferencia, casi siempre es porque alguien promedió antes de tiempo.

---

## 3. Perfilar y estimar

```bash
python3 src/mezcla/perfilar.py     # mide la fuente  -> docs/perfil.json
python3 src/mezcla/estimar.py      # estima la mezcla -> docs/tabla_mezcla.md
```

Análisis de sensibilidad, sin tocar los archivos:

```bash
python3 src/mezcla/estimar.py --mappers 6 --reducers 3
```

---

## 4. Ejecutar en el clúster

```bash
export HADOOP_STREAMING=$(ls $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar | head -1)

hdfs dfs -mkdir -p /t4/entrada
hdfs dfs -put -f datos/muestra.csv /t4/entrada/
hdfs dfs -rm -r -f /t4/salida_sin /t4/salida_con
```

**Sin combinador:**

```bash
hadoop jar $HADOOP_STREAMING \
  -D mapreduce.job.name="T4 sin combinador" \
  -D mapreduce.job.reduces=3 \
  -D mapreduce.map.output.compress=false \
  -files src/mapreduce/mapper.py,src/mapreduce/reducer.py,src/mapreduce/comun.py,src/mapreduce/esquema.json \
  -input /t4/entrada \
  -output /t4/salida_sin \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py"
```

**Con combinador:**

```bash
hadoop jar $HADOOP_STREAMING \
  -D mapreduce.job.name="T4 con combinador" \
  -D mapreduce.job.reduces=3 \
  -D mapreduce.map.output.compress=false \
  -files src/mapreduce/mapper.py,src/mapreduce/combiner.py,src/mapreduce/reducer.py,src/mapreduce/comun.py,src/mapreduce/esquema.json \
  -input /t4/entrada \
  -output /t4/salida_con \
  -mapper "python3 mapper.py" \
  -combiner "python3 combiner.py" \
  -reducer "python3 reducer.py"
```

`mapreduce.map.output.compress=false` es deliberado: con compresión activa, `Reduce shuffle bytes` mide bytes comprimidos y deja de ser comparable con una estimación hecha sobre bytes de texto plano. Si su clúster la trae activa por defecto y quieren dejarla, decláralo en el informe y compárenlo contra `Map output bytes`.

### Forzar varios splits cuando la entrada es pequeña

Si la fuente cabe en un bloque hay un solo mapper, el combinador agrega todo de una pasada y el ahorro sale artificialmente perfecto. Dos formas de evitarlo:

```bash
# a) bajar el tamaño máximo de split (16 MB)
-D mapreduce.input.fileinputformat.split.maxsize=16777216

# b) partir el archivo en varios, uno por mapper
split -n l/6 datos/muestra.csv parte_ && hdfs dfs -put parte_* /t4/entrada/
```

Cualquiera de las dos sirve; anoten en el informe cuál usaron.

---

## 5. Sacar los contadores

El contador aparece en la salida del trabajo, bajo `Map-Reduce Framework`. Para recuperarlo después:

```bash
mapred job -counters <job_id> | grep -Ei "Reduce shuffle bytes|Map output records|Map output bytes|Combine (input|output) records|Reduce input records"
```

Si no tienen el `job_id` a la mano:

```bash
mapred job -list all | tail -20
```

Peguen los valores de **las dos ejecuciones** en `src/mezcla/medicion.json`, incluyendo `mappers_reportados` (aparece en la salida del trabajo como *number of splits*) y `reducers_usados`. Después:

```bash
python3 src/mezcla/estimar.py
```

La tabla de `docs/tabla_mezcla.md` se regenera con la columna de contraste ya llena.

---

## 6. Recuperar el resultado

```bash
hdfs dfs -cat /t4/salida_con/part-* | sort -t$'\t' -k1,1 > resultado.tsv
head resultado.tsv
```

Columnas: `clave`, `promedio`, `suma`, `conteo`.

**Comprobación de equivalencia** entre las dos ejecuciones del clúster:

```bash
hdfs dfs -cat /t4/salida_sin/part-* | sort > /tmp/h_sin.txt
hdfs dfs -cat /t4/salida_con/part-* | sort > /tmp/h_con.txt
diff /tmp/h_sin.txt /tmp/h_con.txt && echo "IDENTICOS"
```

---

## 7. Secuencia completa, de cero

```bash
git clone [[URL_DEL_REPOSITORIO]] && cd [[repo]]
python3 datos/generar_muestra.py      # solo si usan la muestra de demostración
python3 src/mezcla/perfilar.py
python3 src/mezcla/estimar.py
# ... pasos 4 y 5 ...
python3 src/mezcla/estimar.py         # de nuevo, ya con los contadores
```

Nueve comandos. Si alguno falla en un clon limpio, el criterio 6 no se cumple.
