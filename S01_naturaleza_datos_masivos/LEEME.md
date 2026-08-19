# Sesión 1 · Naturaleza de los datos masivos — LEEME PRIMERO

**IFPN0025 · Big Data e Ingeniería de Datos · Universidad Ean**
Estado: **resuelta y ejecutable**. Falta un paso tuyo de ~10 minutos (opcional pero recomendado).

---

## Los 3 minutos que necesitas

**Qué se resolvió:** los cuatro entregables obligatorios (Nivel 1, Nivel 2, Nivel 3 y reto de negocio),
más el notebook ejecutado con salidas visibles.

**Cómo:** ningún número está escrito a mano. Todos salen de código que mide archivos reales y se
inyectan en los documentos desde `resultados/_resultados.json`. Eso es justo lo que la rúbrica premia
y lo que la competencia TECH IA MAKER exige verificar.

**Lo que falta (opcional):** esta corrida se hizo en **modo contingencia** — el entorno donde se ejecutó
no tenía acceso a `datos.gov.co`, así que se usó el generador sintético de la sección 2.4 de la guía,
declarado en todos los documentos. Tu equipo **sí** tiene internet.

---

## Para dejarlo con datos reales (10 min)

Doble clic en **`sesion01/EJECUTAR.bat`**.

Descarga SECOP II e IDEAM del portal, mide todo en **tu** máquina, y reescribe los cuatro entregables
con **tus** cifras. No tienes que tocar nada más.

Si quieres incluir también la GEIH real: bájala de `dane.gov.co` → Microdatos → Gran Encuesta Integrada
de Hogares, descomprime el paquete de un mes en `sesion01/data/raw/geih/` y vuelve a ejecutar el `.bat`.

---

## Dónde está cada cosa

| Quiero... | Abrir |
|---|---|
| Entender todo y poder defenderlo en clase | `sesion01/docs/EXPLICACION_PASO_A_PASO.md` |
| Saber exactamente qué comprimir y entregar | `sesion01/docs/COMO_ENTREGAR.md` |
| Ver el Nivel 1 | `sesion01/resultados/mediciones.csv` |
| Ver el Nivel 2 | `sesion01/resultados/nivel2_sensibilidad.md` |
| Ver el Nivel 3 | `sesion01/resultados/nivel3_matriz.md` |
| Ver el reto de negocio | `sesion01/resultados/reto_negocio.md` |
| Ver el notebook ejecutado | `sesion01/notebooks/s01_perfilamiento.ipynb` |

---

## Antes de entregar

- [ ] Corriste `EJECUTAR.bat` (para tener cifras de tu propia máquina)
- [ ] Reemplazaste "Andrés" por tu nombre completo en los tres `.md`
- [ ] Completaste la tabla del Paso 1.3 con una frase por fuente (la evidencia numérica ya está)
- [ ] Comprimiste como `S01_apellido_nombre.zip`, excluyendo `data/`
