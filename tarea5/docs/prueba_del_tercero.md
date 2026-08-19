# La prueba del tercero

**Tarea T5 · Sesión 5 · IFPN0025 Big Data e Ingeniería de Datos · Universidad Ean**

> Este archivo se rellena **a mano**, y es lo único de la entrega que se rellena a mano. Todo lo demás lo generan los scripts. Aquí lo que se registra es una observación, no una medición.

---

## Por qué existe esta prueba

El enunciado de la tarea lo dice así:

> *Si una persona ajena al equipo, dada una fuente y una fecha, puede escribir la ruta del objeto sin consultar a nadie, la convención cumple. Si tiene que preguntar, no cumple.*

Es el criterio de aceptación 4, y es el único que **no se puede comprobar con código**. `verificar_lago.py` puede confirmar que todas las claves cumplen la convención, pero no puede confirmar que la convención se *entienda*. Eso solo lo dice una persona que no la escribió.

De ahí el nombre: el tercero es quien no participó en el diseño.

## Cómo se hace

**Quién.** Un integrante que **no** haya escrito la convención ni los scripts. Si los tres participaron en todo, sirve alguien de fuera del equipo: un compañero de otro grupo, alguien que estudie otra cosa. Cuanto menos sepa del proyecto, más vale la prueba.

**Con qué puede contar.** Solo con esto:

- La consola de MinIO en <http://localhost:9001> (`minioadmin` / `minioadmin`)
- El archivo `_LEEME.txt` que hay en la raíz de cada cubo

**Con qué NO puede contar.** Ni el repositorio, ni `docs/T5_lago.md`, ni preguntarle a nadie del equipo. Si abre el informe, la prueba no vale: el informe es justo lo que se está poniendo a prueba.

**La regla de oro.** Si en algún momento pregunta algo, **eso que preguntó es exactamente lo que falta escribir** en el `_LEEME.txt`. Anótenlo aunque dé vergüenza: una prueba que sale perfecta a la primera normalmente significa que el tercero ya sabía la respuesta.

---

## Las cuatro preguntas

### 1. ¿Dónde está el dato de SECOP II que entró el 2 de febrero de 2027?

Escriba la ruta completa del objeto.

```
[[COMPLETAR: la respuesta del tercero, tal cual la escribió]]
```

- [ ] Acertó sin preguntar
- [ ] Acertó, pero preguntó algo: `[[COMPLETAR: qué preguntó]]`
- [ ] No acertó. Escribió: `[[COMPLETAR]]`

---

### 2. Encuentra un objeto y no sabe de dónde salió. ¿Dónde lo averigua?

```
[[COMPLETAR: la respuesta del tercero]]
```

- [ ] Acertó sin preguntar
- [ ] Acertó, pero preguntó algo: `[[COMPLETAR: qué preguntó]]`
- [ ] No acertó. Escribió: `[[COMPLETAR]]`

---

### 3. El archivo del 19 de agosto tiene una columna mal. ¿Dónde se corrige?

```
[[COMPLETAR: la respuesta del tercero]]
```

- [ ] Acertó sin preguntar
- [ ] Acertó, pero preguntó algo: `[[COMPLETAR: qué preguntó]]`
- [ ] No acertó. Escribió: `[[COMPLETAR]]`

> Esta es la que más se falla, y es la que más importa. Quien responda «en la capa cruda, editando el CSV» ha entendido dónde está el dato pero no la regla que lo protege.

---

### 4. Ese mismo día entra un segundo archivo de la misma fuente. ¿Cómo se llama?

```
[[COMPLETAR: la respuesta del tercero]]
```

- [ ] Acertó sin preguntar
- [ ] Acertó, pero preguntó algo: `[[COMPLETAR: qué preguntó]]`
- [ ] No acertó. Escribió: `[[COMPLETAR]]`

---

## Resultado

| | |
|---|---|
| Quién hizo la prueba | [[COMPLETAR: nombre]] |
| ¿Participó en el diseño de la convención? | [[COMPLETAR: no / sí, en qué parte]] |
| Fecha | [[COMPLETAR]] |
| Aciertos sin preguntar | [[COMPLETAR: n]] de 4 |
| ¿Tuvo que preguntar algo? | [[COMPLETAR: sí / no]] |

**Qué se corrigió a raíz de la prueba.**

```
[[COMPLETAR: si el tercero preguntó algo o falló alguna, escriban qué se
cambió en el _LEEME.txt, en la convención o en el informe para que la próxima
persona no tropiece igual. Si no se cambió nada, díganlo y expliquen por qué
no hizo falta.]]
```

**Veredicto sobre el criterio 4.**

```
[[COMPLETAR: ¿la convención se puede predecir sin preguntar, sí o no?]]
```

---

## Cómo verificar las respuestas

Las respuestas correctas están en la sección 2.5 de [`T5_lago.md`](T5_lago.md).

**No la abran hasta haber anotado lo que dijo el tercero.** Si se lee antes, se contamina el resultado: es muy fácil convencerse de que una respuesta a medias «en realidad era correcta».

## Cómo se entrega esto

Quien haga la prueba rellena este archivo y **lo commitea desde su propia cuenta**:

```bash
git add tarea5/docs/prueba_del_tercero.md
git commit -m "docs(T5): prueba del tercero sobre la convencion de rutas"
git push
```

Después, copien el veredicto en la sección 2.5 de `T5_lago.md`, donde está marcado `[[COMPLETAR: Resultado de la prueba]]`.
