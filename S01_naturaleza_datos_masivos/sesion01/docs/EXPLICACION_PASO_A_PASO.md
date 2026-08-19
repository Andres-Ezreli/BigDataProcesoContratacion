# Explicacion completa · que se hizo, por que, y como defenderlo

**Sesion 1 · IFPN0025 Big Data e Ingenieria de Datos · Universidad Ean**
Lea esto antes de entregar. Son 10 minutos y le permite sostener cualquier pregunta del profesor.

---

## 0. La pregunta del curso, en una frase

> **¿En que momento un problema de datos deja de resolverse comprando un computador mas grande?**

Toda la practica existe para que usted pueda responder eso con **un numero suyo**, no con una opinion.
El numero es `t_umbral`: cuantos periodos faltan para que su fuente ya no quepa en memoria.

---

## 1. Las tres cantidades. Es todo lo que hay que entender

| Simbolo | Que es | Como se obtiene | Trampa |
|---|---|---|---|
| **S₀** | Lo que pesa el archivo **en disco** | `os.path.getsize(ruta) / 1024**3` | Medir la muestra en vez de la fuente completa |
| **k** | Cuantas veces **crece** al abrirlo en memoria | `df.memory_usage(deep=True).sum() / bytes_en_disco` | Olvidar `deep=True` |
| **M** | Memoria **realmente disponible** | `psutil.virtual_memory().available` | Usar la RAM de la etiqueta |

### Por que `deep=True` no es un detalle

Un CSV guarda texto. Al leerlo, pandas crea columnas de tipo `object`, y una columna `object` es **una
lista de punteros**: 8 bytes por celda que apuntan a la cadena real, que vive en otra parte de la memoria.

- `df.memory_usage()` sin argumento cuenta **solo los punteros**.
- `df.memory_usage(deep=True)` sigue cada puntero y **cuenta la cadena**.

En una fuente con mucho texto la diferencia es de un orden de magnitud, y **siempre subestimando**. Un
`k` medido sin `deep=True` es un `k` inventado. Peor: el error empuja la conclusion siempre hacia el
mismo lado — *todavia no hace falta invertir* — que es el sesgo mas caro posible en una decision de
infraestructura.

**Sintoma de que le paso:** los tres `k` le salen casi iguales y bajos.

### Por que M no es la RAM de la etiqueta

Un equipo de 16 GB no le da 16 GB a Python. El sistema operativo, el navegador, Teams y el IDE ya se
comieron una parte antes de que usted escriba `import pandas`. En este trabajo la fraccion consumida no
se supuso: se **midio** con `psutil` y se aplico a los dos escenarios que pide el paso 2.2.

---

## 2. La formula, explicada sin algebra

$$t_{umbral} = \frac{\ln\left(\dfrac{M}{k \cdot S_0}\right)}{\ln(1+g)}$$

Leala asi, de adentro hacia afuera:

1. **`k · S₀`** = cuanta RAM necesita hoy la fuente completa. Si esto ya es mayor que `M`, ya no cabe.
2. **`M / (k · S₀)`** = cuantas veces mas grande puede volverse la fuente antes de reventar. Si da 4,
   tiene margen para que se cuadruplique.
3. **`ln(...)` arriba y `ln(1+g)` abajo** = convierte "cuantas veces puede crecer" en "cuantos periodos
   tardara en crecer eso", dado que crece a tasa `g` por periodo.

**Resultado negativo = ya se paso el umbral.** No es un error de calculo. Es el diagnostico.

### El detalle que casi nadie hace bien: S₀ es de la fuente completa

Usted descarga 200.000 filas. Esas 200.000 filas **siempre caben**. Si calcula el umbral con el S₀ de la
muestra, le va a dar un horizonte de decadas y la conclusion sera falsa.

Lo correcto es proyectar:

```
S₀_completa = S₀_muestra × (filas_totales_de_la_fuente / filas_de_la_muestra)
```

`k` **si** se puede medir en la muestra, porque es un cociente y se estabiliza rapido. `S₀` no.

En este trabajo el numero de filas totales de SECOP II no se supuso: se consulto
`SELECT count(*)` contra la API del portal y devolvio **8.878.158 filas**.

---

## 3. Las 5 V, y por que descartar es el trabajo real

| V | Que restringe | Como se **mide** (no se opina) |
|---|---|---|
| **Volumen** | Cuanto cabe | `k · S₀` contra `M` |
| **Velocidad** | Si llega a tiempo | frecuencia declarada vs. observada en las marcas de tiempo; latencia hasta hoy |
| **Variedad** | Cuanto cuesta interpretarlo | numero de tipos, columnas de texto, largo medio del texto, dependencia de un diccionario externo |
| **Veracidad** | Si se puede confiar | proporcion de nulos por columna, duplicados de clave, valores fuera de rango |
| **Valor** | Si vale la pena | no esta en el archivo: ¿que decision se cae si la fuente desaparece manana? |

**Afirmar que SECOP II es un problema de volumen no cuesta nada.** Lo que se califica es demostrar que
**no es antes** un problema de veracidad — y eso exige haber mirado el dato.

### Los tres hallazgos que hacen que el Nivel 3 no sea una opinion

1. **SECOP II · veracidad.** El **99 %** de las filas tienen vacia la columna `fecha_de_publicacion`
   (8.811.110 de 8.878.158). Es una columna que en la practica no existe. Si el caso de uso fuera series
   temporales, la veracidad **desplazaria** al volumen y la tabla de la guia estaria equivocada para ese
   caso. Conclusion transferible: **la V dominante no es propiedad de la fuente, sino de la pareja
   fuente-uso.**
2. **IDEAM · velocidad.** 21.710 registros en 24 horas ≈ 905 estaciones-sensor reportando cada hora. Pero
   lo que restringe **no es la frecuencia de registro sino la brecha** entre registro (horario) y
   publicacion (diaria). Medir solo lo primero daria una respuesta correcta por la razon equivocada.
3. **GEIH · variedad.** Es la unica fuente donde **hay que leer un documento que no son los datos antes
   de poder leer los datos**. Sin API, multiples archivos por descarga, diccionario separado, codigos que
   cambian entre rediseños. El costo no es de RAM, es de interpretacion.

---

## 4. Las tres respuestas del Nivel 2, en corto

**1. ¿Duplicar `g` reduce el umbral a la mitad?**
Casi, pero no. `g` entra por `ln(1+g)`, y para `g` pequeno `ln(1+g) ≈ g`, asi que en el rango realista
(1 %–30 %) duplicar `g` casi divide el plazo entre dos. La aproximacion se rompe cuando `g` crece. La
relacion es **hiperbolica, no lineal**.

**2. ¿Que error en `g` cambia la recomendacion?**
Depende de donde este el umbral. Si `t_umbral` > horizonte de planeacion (~3 anos), la precision de `g`
es irrelevante: pasar de 40 a 37 anos no cambia ninguna compra. Si `t_umbral` esta entre 0 y 3, **un
punto porcentual mueve trimestres** y ahi si decide si se aprueba este ano o el siguiente.

**3. ¿Que es mas grave, `g` o `k`?**
**`k`.** Dos razones:

- *Estructural*: `k` esta en el logaritmo del **numerador** y `g` en el del **denominador**. Un error en
  `g` reescala suavemente; un error en `k` puede **cambiar el signo** del umbral, o sea, cambiar la
  decision de *tengo tiempo* a *ya no cabe*.
- *Practica*: `k` es medible hoy, en cinco minutos, con el archivo en la mano. `g` es siempre una
  proyeccion. **Equivocarse en algo que se podia medir es negligencia; equivocarse en algo que se debia
  proyectar es incertidumbre.**

---

## 5. Que hace cada archivo del proyecto

```
sesion01/
├── scripts/
│   ├── bd_s01.py               motor: S0, k, M, umbral, veracidad, velocidad, variedad
│   ├── ejecutar_todo.py        descarga (o contingencia) → mide → escribe mediciones.csv + _resultados.json
│   ├── generar_entregables.py  lee el JSON → escribe los 3 documentos en Markdown
│   └── construir_notebook.py   arma y EJECUTA el notebook con salidas visibles
├── notebooks/
│   └── s01_perfilamiento.ipynb  Niveles 1 y 2, ejecutado
├── data/raw/  data/synthetic/
└── resultados/
    ├── mediciones.csv           ← Nivel 1
    ├── nivel2_sensibilidad.md   ← Nivel 2
    ├── nivel3_matriz.md         ← Nivel 3
    ├── reto_negocio.md          ← Reto de negocio
    └── _resultados.json         trazabilidad: toda cifra citada sale de aqui
```

**La regla de diseno:** ningun numero se escribe a mano en los documentos. Todos se inyectan desde
`_resultados.json`. Si vuelve a correr el pipeline con otros datos, los cuatro entregables se reescriben
solos y siguen siendo coherentes entre si. Eso es exactamente lo que pide la rubrica cuando dice
*"reporta cifras sin codigo que las produzca"* como nivel insuficiente.

---

## 6. Si el profesor pregunta

**«¿Uso inteligencia artificial?»** Si, y esta declarado al final de `reto_negocio.md`, que es lo que
exige la competencia TECH IA MAKER. La condicion 2 tambien se cumple: **ninguna cifra viene del
asistente**, todas salen de codigo ejecutado sobre archivos reales y quedan trazadas en el JSON.

**«¿Por que su `k` es distinto al de su companero?»** Porque `k` depende del contenido concreto de la
muestra descargada y de la version de pandas. Lo que **no** puede diferir es el orden: la fuente con mas
texto libre tiene el `k` mas alto.

**«¿Por que su `t_umbral` es negativo?»** Porque `k · S₀ > M`: la fuente completa ya no cabe hoy en ese
escenario de hardware. El signo indica hace cuanto se cruzo la linea. La pregunta operativa deja de ser
*cuando* y pasa a ser *que hago ahora* — y la respuesta esta en las tres salidas ante la saturacion.

**«¿Cuales son las tres salidas ante la saturacion?»**
(1) **Reducir el dato antes de cargarlo**: proyectar columnas, filtrar filas, usar tipos mas estrechos
(`category`, `int32`), pasar a formato columnar comprimido. (2) **Procesar por lotes o en streaming**,
sin cargar todo a la vez. (3) **Distribuir** entre varias maquinas. La (1) suele bastar y casi nunca se
intenta antes de comprar la (3).

---

## 7. Errores que hunden esta practica

| Sintoma | Causa | Que hacer |
|---|---|---|
| Los tres `k` salen casi iguales | falta `deep=True` | recalcular; es la causa en casi todos los casos |
| `k` menor que 1 | mezclo bytes con GB, o el archivo estaba comprimido | revisar unidades; en CSV sin comprimir es imposible |
| `math domain error` | `M / (k·S₀)` salio ≤ 0 | `M` y `S₀` deben estar **ambas en GB** |
| El umbral da decadas | uso `S₀` de la muestra, no de la fuente completa | proyectar con `filas_totales / filas_muestra` |
| El proceso muere al cargar | **es el fenomeno de la sesion ocurriendo** | bajar `$limit`, anotar en que numero de filas ocurrio y **reportarlo**: ese dato vale mas que la carga exitosa |
