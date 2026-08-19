# Texto para el cuadro de la tarea

> Copiar y pegar tal cual en el cuadro de entrega, reemplazando los campos entre corchetes.

---

**Enlace al repositorio consolidado del equipo:**
`https://github.com/[ORG-O-USUARIO]/[REPO-EQUIPO]`

**Ruta al documento de proyección:**
`docs/informe_T3_proyeccion_replica.docx`

**Identificador del último commit:**
`[HASH]` — obtener con `git rev-parse HEAD`

**Fuente única del equipo:**
SECOP II — Procesos de Contratación (`datos.gov.co`, conjunto `p6dx-8zbt`). Justificación técnica de la
elección en la sección 2 del informe.

**Cifra principal:**
Volumen lógico a 12 meses = **9,7150 GiB**. Almacenamiento físico con R = 3 = **29,1450 GiB** (78 bloques
de 128 MiB, 234 réplicas de bloque). Factor recomendado: **R = 3 en zona cruda, R = 2 en zona derivada**.

---

## Integrantes y aporte

| Integrante | Aporte |
|---|---|
| **Andrés Linero** | Consolidación de la fuente única y de la ficha del equipo; script `scripts/proyeccion.py` que produce todas las cifras; redacción del documento de proyección. |
| **`[INTEGRANTE 2]`** | Levantamiento del clúster y mediciones con los tres niveles de réplica; verificación manual de las doce operaciones intermedias (sección 4 del documento). |
| **`[INTEGRANTE 3]`** | Componente en inglés sobre Kleppmann cap. 5; tres términos nuevos del glosario bilingüe; ejecución de la prueba del tercero con otro equipo. |

*(Ajustar a lo que realmente hizo cada quien. La historia de commits debe coincidir: `git shortlog -sne`.)*

---

## Comandos para llenar los campos

```bash
git rev-parse HEAD          # hash completo del último commit
git rev-parse --short HEAD  # versión corta
git remote get-url origin   # URL del repositorio
git shortlog -sne           # comprobar que aparecen los tres autores
```
