# Nivel 1 · Paso 1.3 · Clasificacion por V dominante

**IFPN0025 · Big Data e Ingenieria de Datos · Universidad Ean · Andres**  
Generado el 2026-07-24 18:54. Complemento de `resultados/mediciones.csv`.

> Regla de la guia: **una frase** que asigne la V dominante y **un numero** que la sostenga. Sin el numero, la frase no cuenta.

| Fuente | V dominante | Evidencia numerica |
|---|---|---|
| SECOP II | **Volumen** | 8,878,158 filas x 59 columnas → S₀ = 8.64 GB, k = 3.09 → **26.7 GB** |
| IDEAM | **Velocidad** | **21,710 registros en 24 h** medidos en el servidor ≈ 905 estaciones-sensor por hora |
| GEIH (sustituto sintetico) | **Variedad** | 28 columnas leidas, 0 de ellas con >50 % de nulos; sin API y con diccionario separado |

**Las tres frases, una por fuente:**

- **SECOP II** — La fuente completa exige 26.7 GB de RAM antes de poder filtrar una sola fila, y eso ocurre con un esquema plano y un solo `read_csv`: el problema es cuanto hay, no que tan raro es.
- **IDEAM** — Registra cada hora y publica cada dia; la restriccion no es el tamano de cada registro (12 columnas) sino la latencia con la que llega.
- **GEIH (sustituto sintetico)** — El costo no es de memoria (0.02 GB, trivial) sino de interpretacion: sin el diccionario del periodo, las 28 columnas no significan nada.

---

## Verificacion de la 'Salida esperada' del Nivel 1

| Criterio de la guia | Resultado |
|---|---|
| Hay exactamente 3 fuentes medidas | PASA |
| Todos los k son mayores que 1 | PASA |
| Los tres k son distintos | PASA |
| No hay tamanos de disco en cero | PASA |
| mediciones.csv tiene 9 columnas y 3 filas | PASA |
| La fuente con mas texto tiene el k mas alto | **FALLA** |

## Un criterio de la guia que NO se cumple, y por que

La linea 311 de la guia dice que la fuente con mayor `proporcion_texto` tendra *casi con certeza* el `k` mas alto. **En mi medicion no ocurre**, y la causa es medible:

| Fuente | Prop. de columnas de texto | Largo medio del texto | **k** |
|---|---|---|---|
| SECOP II | 0.75 | 25 caracteres | **3.09** |
| IDEAM | 0.58 | 15 caracteres | **3.28** |
| GEIH (sustituto sintetico) | 0.00 | n/a | **1.93** |

`SECOP II` tiene la mayor proporcion de columnas de texto (0.75) pero **`IDEAM` tiene el `k` mas alto (3.28 contra 3.09)**.

**La explicacion esta en como CPython guarda una cadena.** Cada objeto `str` arrastra una cabecera fija de unos 49 a 57 bytes — tipo, contador de referencias, longitud, hash — *antes* de guardar un solo caracter. En una columna `object` de pandas, ademas, cada celda cuesta un puntero de 8 bytes en el arreglo.

Eso significa que **la expansion depende del largo de las cadenas, no de cuantas columnas son de texto**:

- Una celda de **3 caracteres** ocupa 3 bytes en disco y ~57 en memoria: **expande ~19x**.
- Una celda de **300 caracteres** ocupa ~300 bytes en disco y ~357 en memoria: **expande ~1,2x**.

La cabecera es constante, asi que **se amortiza sobre el texto largo y domina sobre el texto corto**. Una fuente de esquema estrecho, llena de codigos y banderas de dos o tres caracteres, expande mas que una fuente de texto libre extenso, aunque esta ultima tenga mas columnas de tipo `object`.

**Por que la guia esperaba lo contrario.** `proporcion_texto` responde *¿cuantas columnas son de texto?*. `k` responde *¿cuanto pesa ese texto en RAM frente al disco?*. Son preguntas distintas. La correlacion que la guia supone existe cuando las fuentes tienen textos de largo comparable; se invierte cuando no. La propia guia habilita este desenlace en la linea 100: *"Si su medicion contradice esta tabla y usted puede sostenerlo con numeros, su respuesta es correcta y la tabla esta equivocada."*

**Consecuencia practica, que es lo que importa.** Para bajar el consumo de memoria de una fuente de codigos cortos, convertir a `category` es dramaticamente mas efectivo que comprimir: `category` guarda cada valor distinto **una sola vez** y deja un entero por fila. Ahi esta la primera de las tres salidas ante la saturacion — reducir el dato antes de cargarlo — y en esta fuente concreta puede valer mas que todo lo demas junto.

*El detalle de S₀ proyectado y RAM necesaria por fuente esta en `resultados/proyeccion_umbral.csv`; `mediciones.csv` se deja con las nueve columnas exactas que pide la guia.*