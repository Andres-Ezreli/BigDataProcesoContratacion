# T4 — La agregación del proyecto en clave map y reduce

**Tarea T4 · Sesión 4 · IFPN0025 Big Data e Ingeniería de Datos · Universidad Ean**

> **Antes de entregar.** El enunciado dice que la plantilla `docs/T4_mezcla.md` viene *adjunta a la asignación*. Este archivo no es esa plantilla: es el informe completo con el contenido que la plantilla pide. Abran la plantilla oficial y trasladen cada sección a sus campos. Si la plantilla oficial no trae secciones que aquí sí están, déjenlas como anexo; si trae campos que aquí no están, quedan marcados abajo como faltantes.

| | |
|---|---|
| Equipo | [[COMPLETAR: integrante 1, integrante 2, integrante 3]] |
| Repositorio | [[COMPLETAR: URL]] |
| Commit de entrega | [[COMPLETAR: hash corto]] |
| Fuente del proyecto | [[COMPLETAR: la misma fuente consolidada de T1–T3]] |
| Fecha | [[COMPLETAR]] |

---

## Paso 1 · La agregación reescrita en map y reduce

**La pregunta que responde.** [[COMPLETAR: una frase. Por ejemplo: *¿cuál es el valor promedio de contrato por departamento?* La pregunta importa porque de ella sale la clave, y de la clave sale todo el análisis de la mezcla.]]

**La agregación.** Promedio de `[[columna_valor]]` agrupado por `[[columna_clave]]`.

**Cómo queda repartida entre map y reduce.**

| Función | Qué hace | Qué emite |
|---|---|---|
| `mapper.py` | Parte cada línea, normaliza la clave, convierte el valor a número y descarta lo que no es un registro válido | `clave \t valor \t 1` |
| `combiner.py` | Agrega localmente en el nodo del map lo que ya tiene ordenado | `clave \t suma_parcial \t conteo_parcial` |
| `reducer.py` | Acumula todas las parcialidades de una clave y divide **una sola vez** | `clave \t promedio \t suma \t conteo` |

**Dos decisiones de diseño que conviene defender en la sustentación.**

*El map emite la pareja (suma, conteo) y no el valor suelto.* Podría emitir solo el valor y dejar que el reducer contara. Emitir ya `valor \t 1` hace que el combinador y el reductor consuman **el mismo formato**, y por tanto que el trabajo dé exactamente el mismo resultado con combinador o sin él. Sin esa simetría habría que mantener dos formatos intermedios y la comparación del paso 3 dejaría de ser limpia.

*El promedio se calcula solo en la reducción final.* Es el error que el propio enunciado marca como silencioso. El promedio de promedios solo coincide con el promedio cuando todos los grupos tienen el mismo tamaño, y en esta fuente no lo tienen ni de lejos: la clave mayor concentra el [[X]] % de los registros. Suma y conteo, en cambio, son asociativas y conmutativas, que es la condición real para que el framework pueda llamar al combinador cero, una o varias veces sin cambiar nada.

*Nota de reproducibilidad.* La suma en coma flotante no es asociativa: sumar en otro orden mueve los últimos bits. Con combinador y sin combinador el orden cambia, y con otro número de splits también. Por eso el reductor redondea la salida a `decimales_salida` (`esquema.json`). Con ese redondeo las dos ejecuciones dan un archivo **idéntico byte a byte**, que es lo que exige el criterio 6.

---

## Paso 2 · Estimación del volumen de la mezcla

La estimación no se hizo a ojo: `src/mezcla/perfilar.py` recorre la fuente una vez y mide lo que hace falta —número de registros, claves distintas, bytes reales de cada clave y de cada valor serializado—, y `src/mezcla/estimar.py` aplica el modelo sobre esas mediciones. Todos los números de esta sección salen de ejecutar:

```bash
python3 src/mezcla/perfilar.py
python3 src/mezcla/estimar.py
```

### El modelo, en tres líneas

**Sin combinador.** El map emite un par por registro válido. No hay nada que estimar en el número de pares: son exactamente `N`. Lo único estimado es el tamaño medio del par.

```
bytes_mezcla ≈ N × (bytes_clave + bytes_valor + sobrecarga_por_par)
```

**Con combinador.** Cada mapper emite un par por cada clave distinta *que le tocó ver*. La versión gruesa del enunciado supone que todos ven todas:

```
bytes_mezcla ≲ K × M × bytes_par_agregado          (cota superior)
```

Esa cota se puede afinar. Si los registros se reparten al azar entre los `M` mappers, un mapper cualquiera **no** ve una clave que aparece `n` veces con probabilidad `(1 − 1/M)^n`, así que el número esperado de mappers que sí la ven es:

```
pares(n, M) = M × [1 − (1 − 1/M)^n]
```

y los pares totales son la suma de eso sobre todas las claves. La diferencia entre la cota y la esperanza es justo el peso de las claves raras: las que aparecen pocas veces no alcanzan a estar en todos los nodos.

> **Cuándo la cota es ajustada.** Cuando `N/M ≫ K` —muchos registros por mapper y pocas claves— toda clave aparece en todo mapper y la esperanza colapsa contra la cota. En nuestra fuente eso [[COMPLETAR: sí ocurre / no ocurre, y por eso las dos cifras de la tabla salen [[iguales / distintas]] ]].

**Supuesto declarado.** El reparto aleatorio es un supuesto conservador. Si la fuente viene ordenada por la clave, los splits son contiguos, cada mapper ve muchas menos claves distintas y el combinador rinde *más* de lo estimado. Si el resultado real queda por debajo de la estimación, esta es la primera explicación a revisar.

### Cifras

<!-- Pegar aquí el contenido de docs/tabla_mezcla.md, o enlazarlo. -->

Ver **[`docs/tabla_mezcla.md`](tabla_mezcla.md)**, generado por el script.

### Verificación a mano

[[COMPLETAR con sus cifras reales. Rehagan esta aritmética a mano, es lo que el curso pide en cada tarea. El esquema es este, con los números de demostración de la muestra sintética:]]

Sin combinador, con `N = 20.000`, clave de 10,0 B en promedio, valor de 12,9 B y 2 B de sobrecarga:

```
par medio      = 10,0 + 12,9 + 2 = 24,9 B
bytes_mezcla   = 20.000 × 24,9 B = 498.000 B ≈ 486 KB
```

Con combinador y `M = 6`, `K = 20`: como cada mapper recibe unos 3.333 registros y solo hay 20 claves, la clave más rara del conjunto (62 registros en total) aparece en un mapper dado con probabilidad `1 − (1 − 1/6)^62 ≈ 1,0`. Es decir, todas las claves aparecen en todos los mappers y los pares son `20 × 6 = 120`. Con un par agregado de unos 30 B:

```
bytes_mezcla   = 120 × 30 B ≈ 3,5 KB
ahorro         = 1 − 3,5 / 486 ≈ 99,3 %
```

El orden de magnitud es lo que importa: de cientos de kilobytes a unos pocos. Ese factor es el reto de negocio de la sesión, agregar antes de mover.

---

## Paso 3 · Contraste con el contador real

**Qué se contrasta.** El contador `Reduce shuffle bytes` del framework, en dos ejecuciones del mismo trabajo sobre el mismo dato: una sin `-combiner` y otra con él. Los comandos exactos están en [`docs/T4_ejecucion.md`](T4_ejecucion.md).

**Cómo se incorporan.** Los contadores se pegan en `src/mezcla/medicion.json` y se vuelve a ejecutar `estimar.py`. La columna de error de la tabla se llena sola. Ningún número del informe se escribe a mano.

**Lectura del contraste.** [[COMPLETAR después de ejecutar. Guía de interpretación:]]

| Si la estimación queda… | La explicación más probable |
|---|---|
| Por **encima** del real, sin combinador | Compresión de la salida del map activa (`mapreduce.map.output.compress`). Texto repetitivo comprime muchísimo. Verifiquen el valor en `medicion.json`. |
| Por **debajo** del real | La sobrecarga por par está subestimada. El formato IFile guarda prefijos de longitud por clave y por valor; suban `overhead_por_registro_bytes` y vuelvan a correr. |
| Por **encima** del real, con combinador | La fuente llega parcialmente ordenada por la clave, así que cada mapper vio menos claves distintas de las que supone el modelo aleatorio. |
| Muy por **debajo** del real, con combinador | El combinador no llegó a ejecutarse. Con entradas pequeñas Hadoop puede no derramar a disco y saltárselo. Comparen `combine_input_records` con `combine_output_records`: si son iguales, o si están en cero, no corrió. |

**Un aviso que vale la aceptación de la tarea.** Si la entrada cabe en un solo bloque, hay un solo mapper, el combinador agrega todo de una pasada y el ahorro sale artificialmente perfecto. No demuestra nada sobre el comportamiento distribuido. La sección 4 de `T4_ejecucion.md` explica cómo forzar varios splits.

---

## Paso 4 · Justificación de la clave

### Por qué esta clave responde la pregunta

[[COMPLETAR: el argumento debe unir tres cosas — la pregunta de negocio, el grano de la agregación y la columna elegida. Un ejemplo de la forma que debe tener:]]

> La pregunta es *[[pregunta]]*. Eso fija el grano en *[[una fila de salida por cada …]]*, y la única columna de la fuente que expresa ese grano sin transformaciones adicionales es `[[columna]]`. Agrupar por `[[alternativa descartada]]` respondería una pregunta distinta —[[cuál]]— y agrupar por `[[otra alternativa]]` produciría un grano demasiado [[fino/grueso]]: [[K alternativo]] claves para [[N]] registros, es decir [[n]] registros por clave, con lo que la agregación deja de agregar.

### Por qué minimiza la mezcla

La clave gobierna el volumen de la mezcla por dos vías, y hay que argumentar las dos.

**Por el número de claves distintas.** Con combinador, la mezcla es proporcional a `K × M`, no a `N`. Una clave de baja cardinalidad —`[[K]]` valores distintos sobre `[[N]]` registros— hace que el combinador colapse casi todo antes de mover nada. Una clave de alta cardinalidad, como un identificador, daría `K ≈ N` y el combinador no ahorraría nada: cada clave aparecería una sola vez y no habría qué agregar localmente. Ese es el criterio operativo: **una clave sirve para agregar en la medida en que se repite.**

**Por el tamaño del par.** La clave viaja en cada par. Con `[[bytes]]` bytes de promedio sobre un par de `[[bytes]]`, la clave pesa el [[X]] % de la mezcla. Si se usara `[[alternativa larga]]` en vez del código, el mismo trabajo movería aproximadamente [[Y]] veces más bytes sin cambiar el resultado. Por eso la clave se normaliza en el mapper —recorte, mayúsculas, colapso de espacios— antes de emitirla: además de evitar que `"Bogotá D.C. "` y `"BOGOTA D.C."` cuenten como dos grupos, mantiene el par corto.

### Nota sobre el sesgo

[[COMPLETAR con sus cifras. El análisis está en `docs/tabla_mezcla.md`, sección *Sesgo de la clave*. Los tres hechos que hay que exponer:]]

1. **Cuánto sesgo hay.** La clave `[[clave mayor]]` concentra el [[X]] % de los registros, [[Y]] veces el promedio por clave.
2. **Qué consecuencia tiene.** Con `R` reductores y el particionador por defecto —`(hashCode & MAX_INT) % R`— el reductor más cargado recibe [[Z]] registros frente a los [[N/R]] del reparto ideal, un desbalance de [[W]]x. El trabajo no termina cuando termina el promedio de los reductores: termina cuando termina el último. Ese reductor es el trabajo.
3. **Qué se puede hacer.** El rediseño simulado en la tabla parte cada clave en `S` cubos —`clave#b` con `b` aleatorio— y vuelve a agregar por el prefijo en un segundo trabajo.

**El compromiso, dicho sin adornos.** La clave compuesta baja el desbalance de [[W]]x a [[V]]x, pero multiplica los pares de la mezcla por aproximadamente `S` y añade una segunda etapa con su propia lectura, escritura y mezcla. Solo compensa cuando el costo del reductor rezagado supera al de mover ese dato extra, es decir cuando el sesgo es severo y el dato por clave es grande. Con `[[K]]` claves y este nivel de desbalance, la recomendación del equipo es **[[COMPLETAR: mantener la clave simple / aplicar el rediseño]]**, porque [[razón]].

---

## Criterio de aceptación · verificación

| # | Condición | Estado |
|---|---|---|
| 1 | El trabajo produce la agregación correcta sobre la fuente del proyecto | [[ ]] |
| 2 | Está escrito como map y reduce en Python y se ejecuta con Hadoop Streaming | [[ ]] |
| 3 | Incluye la estimación teórica del volumen de mezcla, con y sin combinador | [[ ]] |
| 4 | Contrasta la estimación con el contador real `Reduce shuffle bytes` | [[ ]] |
| 5 | Justifica la clave elegida por su efecto en el volumen de la mezcla | [[ ]] |
| 6 | Es reproducible: otra persona obtiene el mismo resultado y las mismas cifras | [[ ]] |

**Prueba del tercero.** Antes de entregar, un integrante que no haya tocado el código clona el repositorio en limpio, sigue `docs/T4_ejecucion.md` sin preguntar nada y compara su salida con la del informe. Si tiene que preguntar algo, eso que preguntó es lo que falta escribir.

---

## Referencias

Dean, J., y Ghemawat, S. (2008). MapReduce: Simplified data processing on large clusters. *Communications of the ACM, 51*(1), 107–113. https://doi.org/10.1145/1327452.1327492

White, T. (2015). *Hadoop: The definitive guide* (4.ª ed.). O'Reilly Media.
