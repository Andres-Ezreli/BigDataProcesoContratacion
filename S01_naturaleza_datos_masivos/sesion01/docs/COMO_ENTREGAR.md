# Como entregar · checklist de 5 minutos

## 1. Regenerar con datos reales (recomendado, ~10 min con internet)

Doble clic en **`EJECUTAR.bat`**, o desde la terminal en la carpeta `sesion01`:

```
pip install pandas numpy psutil
python scripts\ejecutar_todo.py
python scripts\generar_entregables.py
python scripts\construir_notebook.py --ejecutar
```

Esto descarga SECOP II e IDEAM del portal y reescribe los cuatro entregables con **sus** cifras,
medidas en **su** equipo. Si no hay internet, activa solo el plan de contingencia y lo declara.

**Para incluir la GEIH real:** descargue el paquete de un mes desde `dane.gov.co` → Microdatos → Gran
Encuesta Integrada de Hogares, descomprima en `data/raw/geih/` y vuelva a ejecutar. El script toma
automaticamente el archivo mas grande de esa carpeta.

## 1.b Si corre en sus dos equipos (recomendado)

Cada corrida se archiva en `resultados/corridas/<equipo>/` **sin pisar a la anterior**. Corra el `.bat`
en las dos maquinas y ponga una etiqueta distinta cuando la pida (`portatil_8GB`, `portatil_16GB`).

Al hacerlo, la seccion **1.1.b** de `nivel2_sensibilidad.md` se llena sola con:

- la `M` realmente medida en cada equipo, y la fraccion que consume el SO en cada uno
- la verificacion de que `k` es identico en ambos (es propiedad del dato, no del equipo)
- el `t_umbral` de cada fuente en cada maquina
- **el punto de quiebre**, si en la de 8 GB el proceso muere al cargar

Ese ultimo caso no es un fallo. La guia lo dice en la linea 336: *"no es un error suyo: es el fenomeno
que estamos estudiando, ocurriendo en su equipo"*. El script lo atrapa, anota con cuantas filas murio y
lo reporta como resultado. **Vale mas que la carga exitosa en la maquina grande.**

Orden sugerido: primero la de **16 GB** (para tener una corrida completa asegurada), despues la de 8 GB.

## 2. Verificar antes de comprimir

- [ ] `resultados/mediciones.csv` tiene **9 columnas y 3 filas** (lo exige la linea 308 de la guia)
- [ ] Los tres `k` son distintos y mayores que 1
- [ ] Si uso la GEIH real: lleno `config_geih.json` con el periodo y las columnas del **diccionario**
      ANTES de cargar el archivo (paso 2.3.4), y el paquete es de **un solo mes**
- [ ] El notebook esta ejecutado y **con salidas visibles** (no celdas vacias)
- [ ] Complete el Paso 1.3 con una frase por fuente (la evidencia numerica ya esta en el notebook)
- [ ] Su nombre real reemplaza "Andres" en los tres `.md` si el profesor pide nombre completo
- [ ] La declaracion de uso de IA esta al final de `reto_negocio.md`

## 3. Que se entrega

| Archivo | Contenido | Formato |
|---|---|---|
| `resultados/mediciones.csv` | Nivel 1 | CSV |
| `notebooks/s01_perfilamiento.ipynb` | Niveles 1 y 2, ejecutado | Notebook |
| `resultados/nivel2_sensibilidad.md` | Nivel 2 | Markdown |
| `resultados/nivel3_matriz.md` | Nivel 3 | Markdown |
| `resultados/reto_negocio.md` | Reto de negocio | Markdown |
| `resultados/nivel1_paso1_3_v_dominante.md` | Paso 1.3 (complementa mediciones.csv) | Markdown |
| `resultados/proyeccion_umbral.csv` | S₀ proyectado y RAM necesaria (soporte del Nivel 2) | CSV |
| `resultados/corridas/` | Una carpeta por equipo: evidencia de las condiciones de medicion | JSON + CSV |

Todo en texto plano. **No se aceptan `.docx` ni `.pdf`.**

## 4. Comprimir

Nombre el zip **`S01_apellido_nombre.zip`** con su apellido y nombre reales.

> Sugerencia: excluya `data/` del zip (pesa y no se califica). Los scripts y `docs/` si vale la pena
> incluirlos: son la evidencia de que las cifras las produjo codigo y no una estimacion.
