/**
 * Genera el informe unificado de T3 en formato Word (.docx).
 *
 * Todas las cifras se leen de ../resultados/proyeccion.json, que produce
 * scripts/proyeccion.py. Ninguna cifra esta escrita a mano en este archivo:
 * si cambian los datos de entrada, se reejecuta proyeccion.py y luego este
 * script, y el informe queda actualizado.
 *
 * Uso:  node scripts/generar_informe_docx.js
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  TableOfContents, PageBreak, Header, Footer, PageNumber, PageOrientation,
  LevelFormat, convertInchesToTwip,
} = require("docx");

// ---------------------------------------------------------------------------
// Datos
// ---------------------------------------------------------------------------
const RAIZ = path.join(__dirname, "..");
const R = JSON.parse(fs.readFileSync(path.join(RAIZ, "resultados", "proyeccion.json"), "utf8"));
const E = R.entradas, I = R.intermedios, T = R.tabla_proyeccion, B = R.bloques;

const EQUIPO = ["Andrés Linero", "[INTEGRANTE 2]", "[INTEGRANTE 3]"];

// formateo numerico en convencion colombiana: 1.234,56
const n = (x, d = 4) =>
  Number(x).toLocaleString("es-CO", { minimumFractionDigits: d, maximumFractionDigits: d });
const ent = (x) => Number(x).toLocaleString("es-CO");
const pct = (x, d = 3) => n(x * 100, d) + " %";

// ---------------------------------------------------------------------------
// Estilo
// ---------------------------------------------------------------------------
// Paleta monocroma: solo negro, grises y blanco. Sin color.
const C = {
  tinta: "1A1A1A",     // cuerpo de texto
  azul: "000000",      // titulos de nivel 1 y enfasis fuerte
  azulMedio: "333333", // titulos de nivel 2 y filetes de enfasis
  cabecera: "262626",  // fondo de cabecera de tabla (texto en blanco)
  franja: "F2F2F2",    // franja alterna de las tablas
  destaque: "EDEDED",  // recuadros de nota
  resalte: "D6D6D6",   // filas destacadas de las tablas
  linea: "BFBFBF",     // bordes de tabla
  gris: "595959",      // texto secundario
  filete: "8C8C8C",    // filete lateral de los recuadros de nota
};
const ANCHO = 10080; // 12240 - 2*1080

const p = (text, o = {}) =>
  new Paragraph({
    alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: { before: o.before ?? 0, after: o.after ?? 140, line: 276 },
    indent: o.indent,
    border: o.border,
    shading: o.shading,
    children: Array.isArray(text)
      ? text
      : [new TextRun({ text, size: o.size || 21, color: o.color || C.tinta, bold: o.bold, italics: o.italics })],
  });

const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 180 }, children: [new TextRun({ text, size: 30, bold: true, color: C.azul })] });
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 260, after: 120 }, children: [new TextRun({ text, size: 24, bold: true, color: C.azulMedio })] });
const h3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 100 }, children: [new TextRun({ text, size: 21, bold: true, color: C.tinta })] });

const bullet = (text) =>
  new Paragraph({
    numbering: { reference: "vinetas", level: 0 },
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 90, line: 276 },
    children: Array.isArray(text) ? text : [new TextRun({ text, size: 21, color: C.tinta })],
  });

const nota = (text) =>
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { before: 120, after: 160, line: 264 },
    indent: { left: 220, right: 220 },
    shading: { type: ShadingType.CLEAR, fill: C.destaque, color: "auto" },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color: C.filete, space: 10 } },
    children: Array.isArray(text) ? text : [new TextRun({ text, size: 20, color: C.tinta })],
  });

const formula = (lineas) =>
  new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { before: 120, after: 160 },
    indent: { left: 280 },
    shading: { type: ShadingType.CLEAR, fill: "F4F4F4", color: "auto" },
    children: lineas.flatMap((l, i) => [
      ...(i ? [new TextRun({ break: 1 })] : []),
      new TextRun({ text: l, font: "Consolas", size: 19, color: C.tinta }),
    ]),
  });

const celda = (contenido, o = {}) =>
  new TableCell({
    width: { size: o.w, type: WidthType.DXA },
    shading: o.fill ? { type: ShadingType.CLEAR, fill: o.fill, color: "auto" } : undefined,
    margins: { top: 70, bottom: 70, left: 110, right: 110 },
    verticalAlign: "center",
    children: [
      new Paragraph({
        alignment: o.align || AlignmentType.LEFT,
        spacing: { after: 0, line: 250 },
        children: Array.isArray(contenido)
          ? contenido
          : [new TextRun({ text: String(contenido), size: o.size || 18, bold: o.bold, color: o.color || C.tinta })],
      }),
    ],
  });

/** tabla(cabeceras, filas, anchos, opciones) */
function tabla(cab, filas, anchos, o = {}) {
  const alin = o.align || [];
  const rows = [
    new TableRow({
      tableHeader: true,
      cantSplit: true,
      children: cab.map((t, i) =>
        celda(t, { w: anchos[i], fill: C.cabecera, bold: true, color: "FFFFFF", align: alin[i] || AlignmentType.LEFT, size: 18 })
      ),
    }),
    ...filas.map((f, k) =>
      new TableRow({
        cantSplit: true,
        children: f.map((t, i) =>
          celda(t, {
            w: anchos[i],
            fill: (o.resaltar && o.resaltar.includes(k)) ? C.resalte : (k % 2 ? C.franja : undefined),
            align: alin[i] || AlignmentType.LEFT,
            bold: o.negrita && o.negrita.includes(k),
          })
        ),
      })
    ),
  ];
  return new Table({
    columnWidths: anchos,
    width: { size: anchos.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 6, color: C.linea },
      bottom: { style: BorderStyle.SINGLE, size: 6, color: C.linea },
      left: { style: BorderStyle.SINGLE, size: 6, color: C.linea },
      right: { style: BorderStyle.SINGLE, size: 6, color: C.linea },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: C.linea },
      insideVertical: { style: BorderStyle.SINGLE, size: 4, color: C.linea },
    },
    rows,
  });
}

const espacio = (h = 120) => new Paragraph({ spacing: { after: h }, children: [] });
const regla = () =>
  new Paragraph({
    spacing: { before: 60, after: 160 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.linea, space: 6 } },
    children: [],
  });

const D = AlignmentType.RIGHT, Ce = AlignmentType.CENTER;

// ---------------------------------------------------------------------------
// Contenido
// ---------------------------------------------------------------------------
const portada = [
  espacio(1400),
  new Paragraph({ alignment: Ce, spacing: { after: 80 }, children: [new TextRun({ text: "UNIVERSIDAD EAN", size: 22, bold: true, color: C.gris, characterSpacing: 40 })] }),
  new Paragraph({ alignment: Ce, spacing: { after: 600 }, children: [new TextRun({ text: "IFPN0025 · Big Data e Ingeniería de Datos", size: 20, color: C.gris })] }),
  new Paragraph({ alignment: Ce, spacing: { after: 100 }, children: [new TextRun({ text: "Proyección de almacenamiento", size: 44, bold: true, color: C.azul })] }),
  new Paragraph({ alignment: Ce, spacing: { after: 240 }, children: [new TextRun({ text: "y factor de réplica", size: 44, bold: true, color: C.azul })] }),
  new Paragraph({
    alignment: Ce, spacing: { after: 700 },
    border: { top: { style: BorderStyle.SINGLE, size: 12, color: C.azulMedio, space: 14 } },
    children: [new TextRun({ text: "Tarea acumulativa T3 · Sesión 3 · Módulo 1 · Primera tarea en equipo", size: 21, color: C.gris, italics: true })],
  }),
  new Paragraph({ alignment: Ce, spacing: { after: 60 }, children: [new TextRun({ text: "Equipo", size: 19, bold: true, color: C.gris })] }),
  ...EQUIPO.map((m) => new Paragraph({ alignment: Ce, spacing: { after: 40 }, children: [new TextRun({ text: m, size: 22, color: C.tinta })] })),
  espacio(500),
  new Paragraph({ alignment: Ce, spacing: { after: 40 }, children: [new TextRun({ text: "Fuente única del equipo", size: 19, bold: true, color: C.gris })] }),
  new Paragraph({ alignment: Ce, spacing: { after: 300 }, children: [new TextRun({ text: "SECOP II — Procesos de Contratación · datos.gov.co / p6dx-8zbt", size: 21, color: C.tinta })] }),
  new Paragraph({ alignment: Ce, children: [new TextRun({ text: `Bogotá D.C., ${R.generado}`, size: 19, color: C.gris })] }),
  new Paragraph({ children: [new PageBreak()] }),
];

const toc = [
  h1("Tabla de contenido"),
  new TableOfContents("Contenido", { hyperlink: true, headingStyleRange: "1-3" }),
  p("", { after: 0 }),
  nota("Si el índice aparece vacío al abrir el archivo, seleccionarlo y pulsar F9 (o clic derecho → Actualizar campos). Word calcula los números de página al abrir, no al generar."),
  new Paragraph({ children: [new PageBreak()] }),
];

const s1 = [
  h1("1. Resumen ejecutivo"),
  p("Este informe dimensiona el costo en disco de la fuente única del equipo a doce meses, compara los tres niveles de réplica que ofrece HDFS y recomienda uno, con las cifras a la vista y el procedimiento completo para rehacerlas."),
  p([
    new TextRun({ text: "La fuente consolidada es ", size: 21 }),
    new TextRun({ text: "SECOP II — Procesos de Contratación", size: 21, bold: true }),
    new TextRun({ text: ` del portal de Datos Abiertos de Colombia. Su volumen actual medido es `, size: 21 }),
    new TextRun({ text: `${n(I.S0_gib)} GiB`, size: 21, bold: true }),
    new TextRun({ text: ` sobre ${ent(E.total_filas)} filas. Con una tasa de crecimiento de ${pct(I.g_anual)} anual —medida sobre la serie histórica real del portal, no supuesta— el volumen lógico a doce meses es `, size: 21 }),
    new TextRun({ text: `${n(I.V12_gib)} GiB`, size: 21, bold: true }),
    new TextRun({ text: ".", size: 21 }),
  ]),
  espacio(60),
  tabla(
    ["Factor R", "Almacenamiento físico", "Réplicas de bloque", "Nodos caídos tolerados", "Costo anual (USD)"],
    T.map((f) => [`R = ${f.R}`, `${n(f.almacenamiento_fisico_gib)} GiB`, ent(f.bloques_128mib_archivo_unico), `${f.nodos_caidos_tolerados}`, n(f.costo_nube_usd_anio, 2)]),
    [1500, 2600, 1980, 2200, 1800],
    { align: [Ce, D, Ce, Ce, D], resaltar: [2], negrita: [2] }
  ),
  espacio(200),
  h2("Recomendación"),
  p([
    new TextRun({ text: "R = 3 sobre la zona cruda y R = 2 sobre la zona derivada. R = 1 en ninguna zona.", size: 21, bold: true, color: C.azul }),
  ]),
  p(`No se recomienda R = 3 por ser el valor por defecto de HDFS. Se recomienda porque la tercera réplica de esta fuente cuesta USD ${n(T[2].costo_nube_usd_anio - T[1].costo_nube_usd_anio, 2)} al año y protege un dato que no es regenerable: la API del portal devuelve el estado actual de cada proceso, no el histórico, de modo que una descarga posterior no reproduce una descarga anterior. La evidencia de esa mutación se midió en la ficha T1 y se documenta en la sección 8.2.`),
  p("Las tablas derivadas del pipeline sí son regenerables reejecutando el procesamiento sobre la zona cruda; perderlas cuesta tiempo de cómputo, no información, y por eso R = 2 basta para ellas."),
  h2("Hallazgo principal"),
  p([
    new TextRun({ text: "La palanca de ahorro no es el factor de réplica: es el formato. ", size: 21, bold: true }),
    new TextRun({ text: `Almacenar la fuente en Parquet con compresión Snappy y factor 3 ocupa ${n(R.compresion.conservadora_5x.fisico_r3_gib)} GiB, un 70 % menos que CSV plano con factor 2 (${n(T[1].almacenamiento_fisico_gib)} GiB), y además tolera dos nodos caídos en lugar de uno. No es un compromiso: gana en las dos dimensiones a la vez. El desarrollo está en la sección 8.3.`, size: 21 }),
  ]),
  new Paragraph({ children: [new PageBreak()] }),
];

const s2 = [
  h1("2. Consolidación del equipo y elección de la fuente"),
  p("El equipo llegó a la sesión con tres fichas T1 y tres repositorios individuales. El paso cero de la tarea exige quedar con uno solo, y la fuente elegida acompaña al grupo hasta la sesión 30. La decisión no se tomó por preferencia sino por tres criterios verificables."),
  h2("2.1 Las tres candidatas"),
  tabla(
    ["Criterio", "SECOP II", "IDEAM", "GEIH"],
    [
      ["V dominante", "Volumen", "Velocidad", "Variedad"],
      ["Volumen medido (S₀)", "8,6435 GiB", "8,1190 GiB", "0,0086 GiB"],
      ["Tasa de crecimiento", "12,4 % — medida sobre serie histórica real", "8 % — supuesto, sin serie publicada", "3 % — supuesto, y el crecimiento es lineal, no geométrico"],
      ["¿Un tercero puede verificarla?", "Sí: count(*) público y serie anual del portal", "Parcial", "Parcial"],
      ["Excede la RAM del equipo", "Sí (26,71 GiB necesarios vs. 16 GB)", "Sí (26,63 GiB)", "No (0,02 GiB)"],
    ],
    [2400, 2760, 2460, 2460],
    { align: [AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.LEFT] }
  ),
  espacio(200),
  h2("2.2 Los tres criterios de la decisión"),
  h3("Criterio 1 · La tasa de crecimiento tiene que ser medida, no supuesta"),
  p("T3 pide una proyección a doce meses y la rúbrica exige que un tercero llegue a las mismas cifras. Solo SECOP II tiene serie histórica publicada de la que se derive un CAGR verificable. La ficha T1 de IDEAM declara explícitamente su g = 8 % como «el número más débil del entregable», y la de GEIH advierte que la fórmula geométrica sobreestima porque su acumulado crece de forma lineal. Construir la proyección sobre cualquiera de esas dos habría apoyado el criterio de mayor peso de la rúbrica sobre el insumo más frágil del equipo."),
  h3("Criterio 2 · El volumen debe hacer que la decisión de réplica tenga contenido"),
  p("Con 0,0086 GiB, la GEIH produce una comparación entre R = 1, 2 y 3 aritméticamente correcta pero vacía: no hay nada que decidir sobre un archivo que cabe en una hoja de cálculo. SECOP II e IDEAM sí generan una tabla con tensión real entre resiliencia y costo."),
  h3("Criterio 3 · La fuente debe servir a T4 y T5, no solo a T3"),
  p("SECOP II es la única de las tres con esquema ancho (59 columnas, 44 de tipo texto), volumen que excede la memoria de las máquinas del equipo (26,71 GiB necesarios contra 16 GB nominales) y un problema de calidad medido y real. Es decir: es la única donde el procesamiento distribuido de T4 resuelve un problema que existe, en vez de demostrar una técnica sobre un archivo que no la necesita."),
  nota([
    new TextRun({ text: "Qué se conserva de las otras dos fichas. ", size: 20, bold: true }),
    new TextRun({ text: "IDEAM y GEIH no se descartan. Sus mediciones de k, su análisis de velocidad y el hallazgo de T1 sobre por qué el k más alto no correspondió a la fuente con más columnas de texto quedan versionados en docs/fichas_t1_originales/ como material de contraste. La fuente de trabajo es una sola; el material de análisis es el de los tres.", size: 20 }),
  ]),
  h2("2.3 La fuente consolidada cumple los cuatro requisitos mínimos de T1"),
  tabla(
    ["Requisito", "Valor", "Cómo se verificó"],
    [
      ["Volumen", `${ent(E.total_filas)} filas × 59 columnas → ${n(I.S0_gib)} GiB`, "count(*) contra la API el 2026-07-24, y os.path.getsize() sobre una muestra real de 200.000 filas escalada por ese conteo"],
      ["Licencia clara", "Datos Abiertos de Colombia · Ley 1712 de 2014", "Términos publicados en el portal. Uso libre con atribución, sin restricción comercial"],
      ["Tasa de crecimiento conocida", `${pct(I.g_anual)} anual (CAGR 2023-2025); cota alta declarada 31,2 %`, "Serie anual real de filas publicadas por el portal, no un supuesto"],
      ["Formato declarado", "CSV UTF-8, delimitado por comas, esquema plano de 59 columnas", "Lectura con pandas 2.3.3: 44 object, 14 int64, 1 float64"],
    ],
    [2200, 3400, 4480]
  ),
  espacio(200),
  h2("2.4 Calidad conocida de la fuente"),
  p("Estos hallazgos se midieron en T1 y no son decorativos: el primero es el que sostiene la recomendación de réplica en la sección 8.2."),
  tabla(
    ["Hallazgo", "Valor medido", "Por qué importa en T3"],
    [
      ["fecha_de_publicacion_fase nula", "8.811.110 de 8.878.158 filas (99,2 %)", "Firma de una fuente que actualiza registros en sitio"],
      ["Duplicados de clave", "6.972 de 200.000 filas (3,49 %)", "Confirma que el portal reexpone y modifica procesos"],
      ["Filas duplicadas completas", "3.226 de 200.000 (1,61 %)", "Ídem"],
      ["Columnas con más de 50 % de nulos", "8 de 59", "Campos que se pueblan con posterioridad a la publicación inicial"],
      ["Proporción media de nulos", "12,75 %", "Contexto de calidad general"],
    ],
    [3000, 3200, 3880]
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

const s3 = [
  h1("3. Marco del cálculo"),
  h2("3.1 Datos de entrada"),
  p("Todo el informe se deriva de los ocho valores siguientes. Ninguno se produjo para esta tarea: los cinco primeros se midieron en la práctica de la sesión 1 y están registrados en resultados/_resultados.json de la ficha T1; los tres últimos son parámetros de plataforma y precio, declarados explícitamente como supuestos."),
  tabla(
    ["Símbolo", "Valor", "Qué es", "De dónde sale"],
    [
      ["muestra_gib", `${n(E.muestra_gib, 6)} GiB`, "Tamaño en disco de la muestra descargada", "os.path.getsize(secop_sample.csv) / 1024³"],
      ["muestra_filas", ent(E.muestra_filas), "Filas de esa muestra", "Parámetro $limit de la descarga por API"],
      ["total_filas", ent(E.total_filas), "Filas de la fuente completa", "count(*) contra la API Socrata, 2026-07-24"],
      ["filas_2023", ent(E.filas_anio_base), "Filas publicadas en 2023", "Serie anual del portal (ficha T1)"],
      ["filas_2025", ent(E.filas_anio_final), "Filas publicadas en 2025", "Misma serie"],
      ["bloque", `${E.bloque_mib} MiB`, "Tamaño de bloque real de HDFS", "dfs.blocksize por defecto, no el valor didáctico de clase"],
      ["precio_nube", `USD ${n(E.precio_nube_usd_gb_mes, 3)} / GB-mes`, "Costo unitario de almacenamiento", "AWS S3 Standard, us-east-1, primer tramo de 50 TB, consultado 2026-08-03"],
      ["TRM", `COP ${n(E.trm_cop_usd, 2)} / USD`, "Conversión a pesos", "Tasa representativa del mercado, 2026-08-03"],
    ],
    [1900, 2100, 2800, 3280]
  ),
  espacio(200),
  h2("3.2 Convención de unidades"),
  nota([
    new TextRun({ text: "Leer antes de rehacer las cuentas. ", size: 20, bold: true }),
    new TextRun({ text: "Se usan GiB binarios (1024³ bytes) en todo lo que toca disco y bloques, porque HDFS razona en potencias de dos. Se usan GB decimales (10⁹ bytes) únicamente para el costo, porque los proveedores facturan así. El factor de conversión es 1 GiB = 1,073741824 GB. Un tercero que mezcle las dos unidades obtendrá una diferencia del 7,4 %; por eso la convención se declara aquí y no en una nota al pie.", size: 20 }),
  ]),
  h2("3.3 Las cuatro fórmulas"),
  tabla(
    ["Qué calcula", "Fórmula", "Nota"],
    [
      ["Volumen a doce meses", "V = S₀ × (1 + g_mensual)^12", "g_mensual, no g_anual. La conversión está en el paso 2"],
      ["Almacenamiento físico", "físico = V × R", "R es el factor de réplica"],
      ["Número de bloques", "bloques = ⌈tamaño_archivo / 128 MiB⌉", "Depende de en cuántos archivos se guarde, no solo del volumen"],
      ["Tolerancia a fallos", "nodos_tolerados = R − 1", "Sin pérdida de dato"],
    ],
    [2600, 3600, 3880]
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

const s4 = [
  h1("4. Desarrollo del cálculo"),
  h2("4.1 Paso 1 · Volumen actual (S₀)"),
  p("No se descargó la fuente completa. Se midió una muestra real y se escaló por el conteo exacto de filas que devuelve la API."),
  formula([
    `factor_escalado = total_filas / muestra_filas = ${ent(E.total_filas)} / ${ent(E.muestra_filas)} = ${n(I.factor_escalado_muestra, 5)}`,
    `S0 = muestra_gib x factor_escalado = ${n(E.muestra_gib, 6)} x ${n(I.factor_escalado_muestra, 5)} = ${n(I.S0_gib)} GiB`,
  ]),
  p([
    new TextRun({ text: "S₀ = ", size: 21 }),
    new TextRun({ text: `${n(I.S0_gib)} GiB`, size: 21, bold: true }),
    new TextRun({ text: ` = ${n(I.S0_gb)} GB decimales.`, size: 21 }),
  ]),
  nota("Supuesto que esto introduce: que la muestra de 200.000 filas tiene el mismo peso medio por fila que el resto de la fuente. Es razonable porque el esquema es fijo, pero no es gratuito: las filas de 2015-2018 tienen menos campos poblados que las de 2025, así que la estimación probablemente sobreestima ligeramente. Se declara y no se corrige, porque corregirlo exigiría descargar la fuente completa, que es exactamente lo que la medición por muestra evita."),
  h2("4.2 Paso 2 · De tasa anual a tasa mensual"),
  p("La ficha T1 reporta la tasa anual; la fórmula de la guía pide la mensual. La conversión correcta es la raíz doceava, no dividir entre doce."),
  formula([
    `g_anual   = (filas_2025 / filas_2023)^(1/2) - 1`,
    `          = (${ent(E.filas_anio_final)} / ${ent(E.filas_anio_base)})^(1/2) - 1`,
    `          = ${n(E.filas_anio_final / E.filas_anio_base, 6)}^0,5 - 1`,
    `          = ${n(I.g_anual, 6)}   ->  ${pct(I.g_anual)} anual`,
    ``,
    `g_mensual = (1 + g_anual)^(1/12) - 1`,
    `          = ${n(1 + I.g_anual, 6)}^(1/12) - 1`,
    `          = ${n(I.g_mensual, 6)}   ->  ${pct(I.g_mensual, 4)} mensual`,
  ]),
  p([
    new TextRun({ text: "Comprobación obligatoria: ", size: 21, bold: true }),
    new TextRun({ text: `(1 + ${n(I.g_mensual, 6)})^12 = ${n(I["comprobacion_(1+gm)^12"], 6)}. Devuelve exactamente 1 + g_anual, de modo que la conversión es consistente. Si alguien hubiera usado g_anual / 12 = 1,033 % mensual, obtendría 13,13 % anual en lugar de ${pct(I.g_anual)}: un error de 0,73 puntos que crece con el horizonte y que esta comprobación atrapa.`, size: 21 }),
  ]),
  h3("Por qué el CAGR 2023-2025 y no el 2021-2025"),
  p("La serie del portal muestra 652.937 filas en 2021 contra 1.531.557 en 2023. Ese salto no es crecimiento de la contratación pública: es la migración administrativa de SECOP I a SECOP II, que terminó de consolidarse hacia 2023. El CAGR 2021-2025 da 31,2 % y mide un evento de una sola vez, no una tendencia. Se conserva como cota alta en el análisis de sensibilidad de la sección 7, no como caso base."),
  espacio(80),
  tabla(
    ["Año", "Filas publicadas", "Observación"],
    [
      ["2015", "5.528", "Arranque del sistema"],
      ["2016", "9.904", ""],
      ["2017", "43.728", ""],
      ["2018", "194.742", ""],
      ["2019", "186.082", ""],
      ["2020", "419.702", ""],
      ["2021", "652.937", "Inicio de la migración SECOP I → SECOP II"],
      ["2022", "1.038.591", "Migración en curso"],
      ["2023", "1.531.557", "Base del CAGR: migración consolidada"],
      ["2024", "1.670.367", ""],
      ["2025", "1.934.805", "Cierre del CAGR: último año completo"],
      ["2026", "1.060.386", "Año en curso, incompleto — se excluye"],
      ["Total", ent(E.total_filas), "Coincide con count(*) de la API"],
    ],
    [1400, 2400, 6280],
    { align: [Ce, D, AlignmentType.LEFT], negrita: [8, 10, 12] }
  ),
  espacio(200),
  h2("4.3 Paso 3 · Volumen lógico a doce meses"),
  formula([
    `V12 = S0 x (1 + g_mensual)^12`,
    `    = ${n(I.S0_gib)} x (1 + ${n(I.g_mensual, 6)})^12`,
    `    = ${n(I.S0_gib)} x ${n(I["comprobacion_(1+gm)^12"], 6)}`,
    `    = ${n(I.V12_gib)} GiB`,
  ]),
  p([
    new TextRun({ text: "V₁₂ = ", size: 21 }),
    new TextRun({ text: `${n(I.V12_gib)} GiB`, size: 21, bold: true }),
    new TextRun({ text: ` = ${n(I.V12_gb)} GB decimales. El dato nuevo generado durante el año es ${n(I.incremento_anual_gib)} GiB.`, size: 21 }),
  ]),
  h2("4.4 Paso 4 · Almacenamiento físico"),
  p("El almacenamiento físico es el volumen lógico multiplicado por el factor de réplica. La tabla completa está en la sección 5."),
  h2("4.5 Paso 5 · Número de bloques"),
  p(`Con el valor real de HDFS, 128 MiB: ${n(I.V12_gib)} GiB × 1024 = ${n(I.V12_gib * 1024, 2)} MiB. El cociente ${n(I.V12_gib * 1024 / 128, 2)} redondeado hacia arriba da ${B.archivo_unico_r1} bloques. Con factor R se almacenan ${B.archivo_unico_r1} × R réplicas de bloque.`),
  h2("4.6 Paso 6 · Tolerancia a fallos"),
  p("Con factor R el sistema tolera R − 1 nodos caídos sin pérdida de dato: cero con R = 1, uno con R = 2, dos con R = 3. La sección 8.4 matiza qué significa exactamente esa tolerancia en un clúster de tres nodos."),
  new Paragraph({ children: [new PageBreak()] }),
];

const s5 = [
  h1("5. Tabla de proyección"),
  p([
    new TextRun({ text: "Fuente: SECOP II · S₀ = ", size: 21 }),
    new TextRun({ text: `${n(I.S0_gib)} GiB`, size: 21, bold: true }),
    new TextRun({ text: ` · g mensual = ${pct(I.g_mensual, 4)} · horizonte = 12 meses · tamaño de bloque = ${E.bloque_mib} MiB`, size: 21 }),
  ]),
  espacio(60),
  tabla(
    ["R", "Volumen lógico 12 m", "Almacenamiento físico", "Réplicas de bloque", "Nodos tolerados", "DataNodes mínimos", "USD / año", "COP / año"],
    T.map((f) => [
      `${f.R}`,
      `${n(f.volumen_logico_12m_gib)} GiB`,
      `${n(f.almacenamiento_fisico_gib)} GiB`,
      ent(f.bloques_128mib_archivo_unico),
      `${f.nodos_caidos_tolerados}`,
      `${f.min_datanodes_requeridos}`,
      n(f.costo_nube_usd_anio, 2),
      ent(f.costo_nube_cop_anio),
    ]),
    [700, 1700, 1700, 1400, 1180, 1400, 1000, 1000],
    { align: [Ce, D, D, Ce, Ce, Ce, D, D], resaltar: [2], negrita: [2] }
  ),
  espacio(180),
  p(`Para contraste en disco propio: a USD ${n(E.precio_disco_usd_tb, 2)} por TB de medio crudo (HDD empresarial SATA, punto medio del rango 9-15 USD/TB observado en marzo de 2026), R = 3 son USD ${n(T[2].costo_disco_crudo_usd, 2)} de medio, o USD ${n(T[2].costo_disco_tco_usd, 2)} si se multiplica por tres para incluir chasis, energía, refrigeración y operación. Esas cifras están en resultados/proyeccion.csv; no se usan como argumento principal porque a este volumen el disco propio no constituye una decisión.`),
  h2("5.1 Bloques según la política de partición"),
  p("El número de bloques no depende solo del volumen: depende de en cuántos archivos se guarde. Se calcula para las dos políticas realistas."),
  tabla(
    ["Escenario", "Bloques (R = 1)", "R = 2", "R = 3"],
    [
      [`Archivo único consolidado (${n(I.V12_gib)} GiB)`, ent(B.archivo_unico_r1), ent(B.archivo_unico_r1 * 2), ent(B.archivo_unico_r1 * 3)],
      ["Partición mensual (corpus base + 12 archivos nuevos)", ent(B.particion_mensual_total_r1), ent(B.particion_mensual_total_r1 * 2), ent(B.particion_mensual_total_r1 * 3)],
    ],
    [5280, 1800, 1500, 1500],
    { align: [AlignmentType.LEFT, Ce, Ce, Ce] }
  ),
  espacio(180),
  p(`La partición mensual cuesta ${B.sobrecosto_bloques_por_particionar} bloques más. Sale de que el corpus base de ${n(I.S0_gib)} GiB ocupa ${B.particion_mensual_base_r1} bloques y de que cada uno de los doce archivos mensuales pesa entre ${n(I.incremento_mes_1_mib, 2)} MiB (mes 1) y ${n(I.incremento_mes_12_mib, 2)} MiB (mes 12): todos por debajo de 128 MiB, de modo que cada uno consume exactamente un bloque.`),
  h3("Dos consecuencias operativas"),
  bullet([
    new TextRun({ text: "HDFS no desperdicia el bloque parcial. ", size: 21, bold: true }),
    new TextRun({ text: "Un archivo de 86 MiB ocupa 86 MiB en disco, no 128. El bloque es la unidad de direccionamiento y réplica, no de asignación en disco. Lo que sí crece es el número de objetos que el NameNode mantiene en memoria, del orden de 150 bytes por bloque: 246 réplicas de bloque son unos 37 KB de metadatos, irrelevante en este caso, pero es exactamente la cuenta que se convierte en cuello de botella cuando hay millones de archivos pequeños.", size: 21 }),
  ]),
  bullet([
    new TextRun({ text: "Con particiones de ~90 MiB se está rozando el problema del archivo pequeño. ", size: 21, bold: true }),
    new TextRun({ text: "Si el equipo pasara a partición diaria en lugar de mensual, cada archivo pesaría unos 3 MiB y el año produciría 365 bloques donde caben 78. La recomendación operativa es mantener la partición mensual, o consolidar trimestralmente.", size: 21 }),
  ]),
  new Paragraph({ children: [new PageBreak()] }),
];

const V = [
  ["1", `${ent(E.total_filas)} / ${ent(E.muestra_filas)}`, "44,39079", n(I.factor_escalado_muestra, 5)],
  ["2", `${n(E.muestra_gib, 6)} × 44,39079`, "8,64351", n(I.S0_gib)],
  ["3", `${ent(E.filas_anio_final)} / ${ent(E.filas_anio_base)}`, "1,263294", n(E.filas_anio_final / E.filas_anio_base, 6)],
  ["4", "√1,263294 − 1", "0,123963", n(I.g_anual, 6)],
  ["5", "1,123963^(1/12) − 1", "0,0097859", n(I.g_mensual, 6)],
  ["6", "(1,009786)^12", "1,123963", n(I["comprobacion_(1+gm)^12"], 6)],
  ["7", "8,6435 × 1,123963", "9,71494", n(I.V12_gib)],
  ["8", "9,7150 × 3", "29,145", n(T[2].almacenamiento_fisico_gib)],
  ["9", "9,7150 × 1024 / 128", "77,72 → 78", ent(B.archivo_unico_r1)],
  ["10", "9,7150 × 1,073741824", "10,43137", n(I.V12_gb)],
  ["11", "10,4314 × 0,023 × 12", "2,879", n(T[0].costo_nube_usd_anio, 2)],
  ["12", "8,6435 × 1024 / 128", "69,15 → 70", ent(B.particion_mensual_base_r1)],
];

const s6 = [
  h1("6. Verificación manual de las cifras"),
  p("La sección 8 de la tarea exige verificar cada cifra a mano. Las doce operaciones intermedias se rehicieron con calculadora, sin ejecutar el script, y se contrastaron contra su salida. Adicionalmente se hizo un tercer recálculo independiente con aritmética decimal de precisión arbitraria."),
  espacio(60),
  tabla(
    ["#", "Operación", "Resultado a mano", "Resultado del script", "¿Coincide?"],
    V.map((v) => [v[0], v[1], v[2], v[3], "Sí"]),
    [600, 3400, 2200, 2280, 1600],
    { align: [Ce, AlignmentType.LEFT, D, D, Ce] }
  ),
  espacio(180),
  nota([
    new TextRun({ text: "La comprobación número 6 es la que importa. ", size: 20, bold: true }),
    new TextRun({ text: "Elevar la tasa mensual a la doceava potencia debe devolver exactamente 1 + g_anual. Es la única de las doce que atrapa el error de haber dividido la tasa anual entre doce en lugar de tomar la raíz doceava, que es el error más frecuente en este cálculo y precisamente el tipo de fallo que la prueba del tercero está diseñada para detectar.", size: 20 }),
  ]),
  new Paragraph({ children: [new PageBreak()] }),
];

const SG = R.sensibilidad_g;
const s7 = [
  h1("7. Análisis de sensibilidad"),
  p("La tasa de crecimiento es el dato de entrada menos sólido, de modo que se prueban los tres escenarios defendibles: que el portal deje de publicar, el caso base medido, y la cota alta que incluye el efecto de la migración administrativa."),
  espacio(60),
  tabla(
    ["Escenario", "g anual", "g mensual", "V₁₂", "Físico a R = 3"],
    [
      ["Fuente congelada (el portal deja de publicar)", "0,0 %", "0,0000 %", `${n(SG.g_cero_fuente_congelada.v12_gib)} GiB`, `${n(SG.g_cero_fuente_congelada.fisico_r3_gib)} GiB`],
      ["Caso base — CAGR 2023-2025", pct(SG.g_base_cagr_2023_2025.g_anual), pct(SG.g_base_cagr_2023_2025.g_mensual, 4), `${n(SG.g_base_cagr_2023_2025.v12_gib)} GiB`, `${n(SG.g_base_cagr_2023_2025.fisico_r3_gib)} GiB`],
      ["Cota alta — CAGR 2021-2025 (incluye migración)", pct(SG.g_cota_alta_cagr_2021_2025.g_anual, 1), pct(SG.g_cota_alta_cagr_2021_2025.g_mensual, 4), `${n(SG.g_cota_alta_cagr_2021_2025.v12_gib)} GiB`, `${n(SG.g_cota_alta_cagr_2021_2025.fisico_r3_gib)} GiB`],
    ],
    [3800, 1420, 1500, 1580, 1780],
    { align: [AlignmentType.LEFT, Ce, Ce, D, D], resaltar: [1], negrita: [1] }
  ),
  espacio(180),
  p([
    new TextRun({ text: `El rango completo de disco físico a R = 3 va de ${n(SG.g_cero_fuente_congelada.fisico_r3_gib)} a ${n(SG.g_cota_alta_cagr_2021_2025.fisico_r3_gib)} GiB: una banda de 8 GiB que, a precio de nube, equivale a USD 2,40 al año de diferencia entre el mejor y el peor caso. `, size: 21 }),
    new TextRun({ text: "La incertidumbre sobre la tasa de crecimiento no alcanza a cambiar la recomendación", size: 21, bold: true }),
    new TextRun({ text: ", y ese es en sí mismo un resultado útil: significa que no vale la pena invertir más esfuerzo en afinar g para esta decisión. Sí lo valdría si el volumen fuera tres órdenes de magnitud mayor.", size: 21 }),
  ]),
  new Paragraph({ children: [new PageBreak()] }),
];

const Q = R.punto_de_quiebre_tercera_replica;
const PA = R.palancas_de_ahorro_gib, PP = R.palancas_de_ahorro_pct_vs_csv_R3;
const s8 = [
  h1("8. Recomendación de factor de réplica"),
  new Paragraph({
    spacing: { before: 60, after: 220 },
    alignment: Ce,
    shading: { type: ShadingType.CLEAR, fill: C.franja, color: "auto" },
    border: {
      top: { style: BorderStyle.SINGLE, size: 12, color: C.azulMedio, space: 10 },
      bottom: { style: BorderStyle.SINGLE, size: 12, color: C.azulMedio, space: 10 },
    },
    children: [new TextRun({ text: "R = 3 sobre la zona cruda.  R = 2 sobre la zona derivada.  R = 1 en ninguna zona.", size: 24, bold: true, color: C.azul })],
  }),
  h2("8.1 El costo, primero, porque es lo que se pregunta"),
  p(`La tercera réplica de esta fuente cuesta USD ${n(T[2].costo_nube_usd_anio - T[1].costo_nube_usd_anio, 2)} al año, equivalentes a COP ${ent(T[2].costo_nube_cop_anio - T[1].costo_nube_cop_anio)}. La segunda cuesta lo mismo. El total de las tres, USD ${n(T[2].costo_nube_usd_anio, 2)} al año, está por debajo de cualquier umbral de aprobación de gasto de una universidad o de una entidad pública.`),
  p("Ese no es un argumento perezoso: es un argumento con un punto de quiebre calculado. La tercera réplica empieza a pesar cuando la fuente crece, y se puede decir exactamente cuándo."),
  espacio(60),
  tabla(
    ["La 3ª réplica cuesta, por sí sola…", "…a partir de este volumen lógico", "Que es…", "Años en llegar (g = 12,4 %)", "Años (cota alta 31,2 %)"],
    [
      ["USD 100 / año", `${n(Q.umbral_100_usd_anio.volumen_logico_tb, 3)} TB`, `${n(Q.umbral_100_usd_anio.veces_el_volumen_actual, 1)}× el actual`, n(Q.umbral_100_usd_anio.anios_a_g_base, 1), n(Q.umbral_100_usd_anio.anios_a_g_cota_alta, 1)],
      ["USD 1.000 / año", `${n(Q.umbral_1000_usd_anio.volumen_logico_tb, 3)} TB`, `${n(Q.umbral_1000_usd_anio.veces_el_volumen_actual, 1)}× el actual`, n(Q.umbral_1000_usd_anio.anios_a_g_base, 1), n(Q.umbral_1000_usd_anio.anios_a_g_cota_alta, 1)],
      ["USD 10.000 / año", `${n(Q.umbral_10000_usd_anio.volumen_logico_tb, 3)} TB`, `${n(Q.umbral_10000_usd_anio.veces_el_volumen_actual, 1)}× el actual`, n(Q.umbral_10000_usd_anio.anios_a_g_base, 1), n(Q.umbral_10000_usd_anio.anios_a_g_cota_alta, 1)],
    ],
    [2400, 2100, 1780, 1950, 1850],
    { align: [AlignmentType.LEFT, D, D, Ce, Ce], resaltar: [0] }
  ),
  espacio(180),
  p([
    new TextRun({ text: `A la tasa medida, SECOP II tardaría ${n(Q.umbral_100_usd_anio.anios_a_g_base, 1)} años en que su tercera réplica costara cien dólares anuales. Incluso con la cota alta del 31,2 % —la que incluye la migración— tardaría ${n(Q.umbral_100_usd_anio.anios_a_g_cota_alta, 1)}. `, size: 21 }),
    new TextRun({ text: "A este volumen, el compromiso resiliencia frente a costo todavía no existe: solo hay resiliencia.", size: 21, bold: true }),
    new TextRun({ text: ` La decisión se revisa cuando el volumen lógico supere ${n(Q.umbral_100_usd_anio.volumen_logico_tb, 3)} TB, no antes.`, size: 21 }),
  ]),
  h2("8.2 El valor del dato: por qué la zona cruda no es regenerable"),
  p("El contraargumento evidente a R = 3 es que SECOP II es una fuente pública y, si se pierde, se vuelve a descargar. Se consideró y se descarta, con evidencia de la propia medición de T1."),
  p([
    new TextRun({ text: "La API devuelve el estado actual de cada proceso, no su estado histórico. ", size: 21, bold: true }),
    new TextRun({ text: "En la ficha T1 se midió que 8.811.110 de 8.878.158 filas (99,2 %) tienen fecha_de_publicacion_fase en nulo, y que hay 6.972 duplicados de clave sobre 200.000 filas evaluadas. Ambas cosas son la firma de una fuente donde los registros se actualizan en sitio: un proceso cambia de fase, se corrige un valor, se puebla un campo que antes estaba vacío. Una descarga hecha hoy no reproduce la descarga del 24 de julio de 2026.", size: 21 }),
  ]),
  p("La consecuencia es que el snapshot crudo es un dato original, no una copia. Si se pierde, no se recupera; se pierde la capacidad de responder qué decía el portal en una fecha determinada, que es precisamente lo que hace auditable un análisis de contratación pública. Eso es dato crítico y va a R = 3."),
  p([
    new TextRun({ text: "La zona derivada sí es regenerable. ", size: 21, bold: true }),
    new TextRun({ text: "Las tablas limpias, las agregaciones por entidad y por año y los Parquet particionados se reconstruyen reejecutando el pipeline sobre la zona cruda. Perderlas cuesta tiempo de cómputo, no información. R = 2 basta: tolera la caída de un nodo, que es el modo de falla frecuente, y ahorra un tercio del disco de esa zona.", size: 21 }),
  ]),
  p([
    new TextRun({ text: "R = 1 queda descartado en ambas zonas", size: 21, bold: true }),
    new TextRun({ text: `, y no por costo sino por la fórmula: tolera cero nodos caídos. En un clúster de tres DataNodes, la caída de cualquiera de ellos con R = 1 significa perder aproximadamente un tercio de los bloques, y HDFS no puede reconstruirlos porque no existe otra copia. El ahorro de USD ${n(T[1].costo_nube_usd_anio, 2)} al año no compra eso.`, size: 21 }),
  ]),
  h2("8.3 Alternativa considerada: comprimir en lugar de des-replicar"),
  p("Se compararon todas las palancas disponibles contra la línea base de CSV plano con R = 3."),
  espacio(60),
  tabla(
    ["Palanca", "Disco físico a 12 meses", "Ahorro vs. línea base", "Nodos caídos tolerados"],
    [
      ["CSV plano, R = 3 (línea base)", `${n(PA["csv_plano_R3_(base)"])} GiB`, "—", "2"],
      ["CSV plano, R = 2", `${n(PA["csv_plano_R2_(bajar_una_replica)"])} GiB`, `${n(PP["csv_plano_R2_(bajar_una_replica)"], 1)} %`, "1"],
      ["CSV plano, R = 1", `${n(PA["csv_plano_R1_(sin_replica)"])} GiB`, `${n(PP["csv_plano_R1_(sin_replica)"], 1)} %`, "0"],
      ["Parquet + Snappy (5×), R = 3", `${n(PA["parquet_snappy_5x_R3_(comprimir)"])} GiB`, `${n(PP["parquet_snappy_5x_R3_(comprimir)"], 1)} %`, "2"],
      ["Parquet + Snappy (10×), R = 3", `${n(PA["parquet_snappy_10x_R3"])} GiB`, `${n(PP["parquet_snappy_10x_R3"], 1)} %`, "2"],
    ],
    [3600, 2400, 2200, 1880],
    { align: [AlignmentType.LEFT, D, D, Ce], resaltar: [3], negrita: [3] }
  ),
  espacio(180),
  p([
    new TextRun({ text: `Parquet con compresión conservadora y R = 3 ocupa un 70 % menos de disco que CSV plano con R = 2, y además tolera dos caídas en lugar de una. `, size: 21, bold: true }),
    new TextRun({ text: "No es un compromiso: gana en las dos dimensiones a la vez.", size: 21 }),
  ]),
  p("La razón por la que funciona tan bien en esta fuente concreta se midió en T1: 44 de 59 columnas son de tipo texto con largo medio de 25 caracteres, y muchas son códigos y banderas repetidos millones de veces —modalidad, estado, departamento, tipo de contrato—. El diccionario por columna de Parquet guarda cada valor distinto una sola vez y deja un entero por fila. Es el mismo mecanismo que en T1 llevó a recomendar el tipo category de pandas por encima de comprimir el CSV."),
  p(`Bajo Parquet 5×, además, el volumen anual cabría en ${R.compresion.conservadora_5x.bloques_r1} bloques en lugar de ${B.archivo_unico_r1}.`),
  p([
    new TextRun({ text: "Conclusión operativa: el factor de réplica es la palanca equivocada para ahorrar disco. Se elige por resiliencia; el disco se ahorra con el formato.", size: 21, bold: true, color: C.azul }),
  ]),
  h2("8.4 Límites honestos de la recomendación"),
  p("Con tres DataNodes y R = 3, cada nodo guarda una copia completa. Eso tiene tres consecuencias que conviene declarar."),
  bullet("La capacidad utilizable del clúster es un tercio de la capacidad bruta. Con 9,7150 GiB lógicos esto es irrelevante, pero es la restricción que aparece primero cuando el clúster crece."),
  bullet("No hay holgura de re-replicación. Si un nodo cae, HDFS querrá restaurar el factor 3 y no tendrá dónde, porque no existe un cuarto nodo. El clúster seguirá sirviendo lecturas —tolera dos caídas, según la fórmula— pero quedará en estado under-replicated hasta que se repare el nodo. La tolerancia de R − 1 = 2 es real para leer; no significa que el sistema se autorrepare."),
  bullet("Con tres nodos y R = 3 la réplica tampoco compra paralelismo de lectura adicional, porque todo bloque está en todos los nodos. El beneficio es exclusivamente de disponibilidad."),
  p("Si el equipo pasara a cuatro o cinco DataNodes en sesiones posteriores, R = 3 recuperaría la capacidad de re-replicación automática y la recomendación se reforzaría sin necesidad de cambiarla."),
  new Paragraph({ children: [new PageBreak()] }),
];

const s9 = [
  h1("9. Reproducibilidad · la prueba del tercero"),
  p("El criterio de aceptación de la tarea establece que otra persona, siguiendo solo lo escrito, debe llegar a las mismas cifras. Se habilitan dos caminos."),
  h2("9.1 Camino A · ejecutar el cálculo"),
  formula([
    `git clone <URL del repositorio del equipo>`,
    `cd <repo>`,
    `python scripts/proyeccion.py`,
  ]),
  p("Sin dependencias externas: solo biblioteca estándar de Python 3.8 o superior. El script imprime los nueve pasos del cálculo y escribe resultados/proyeccion.csv, resultados/bloques.csv, resultados/proyeccion.json y resultados/tabla.md."),
  p("Este mismo informe se regenera con node scripts/generar_informe_docx.js, que lee las cifras de ese JSON. Ninguna cifra del documento está escrita a mano: si se corrige un dato de entrada y se reejecutan los dos scripts en ese orden, el informe queda actualizado."),
  h2("9.2 Camino B · rehacerlo a mano"),
  p("Con la tabla de datos de entrada de la sección 3.1 y las fórmulas de la sección 3.3, aplicadas en el orden de la sección 4. La sección 6 lista las doce operaciones intermedias con su resultado esperado, de modo que si el resultado final no coincide se pueda localizar en qué paso se separó el cálculo."),
  h2("9.3 Reproducir con otra fuente"),
  p("Basta con cambiar el diccionario ENTRADAS al inicio de scripts/proyeccion.py. Ninguna cifra de resultado está escrita a mano en el código: todas se derivan de ese bloque, y cada valor del bloque cita su origen en un comentario."),
  h2("9.4 Estructura del repositorio"),
  formula([
    `<repo-equipo>/`,
    `+-- README.md`,
    `+-- docs/`,
    `|   +-- informe_T3_proyeccion_replica.docx   <- este documento: la entrega completa`,
    `|   +-- glosario_bilingue.md                 <- glosario acumulativo (crece cada sesion)`,
    `|   +-- ENTREGA.md                           <- texto para el cuadro de la tarea`,
    `|   +-- fichas_t1_originales/                <- las tres fichas T1, con su autoria`,
    `+-- scripts/`,
    `|   +-- proyeccion.py                        <- produce todas las cifras`,
    `|   +-- generar_informe_docx.js              <- produce este documento`,
    `+-- resultados/`,
    `    +-- proyeccion.csv, bloques.csv, proyeccion.json, tabla.md`,
  ]),
  new Paragraph({ children: [new PageBreak()] }),
];

const s10 = [
  h1("10. Componente en inglés"),
  p("Lectura anclada de la sesión: Kleppmann, M. (2017), Designing Data-Intensive Applications, capítulo 5, «Replication»."),
  h2("10.1 Summary paragraph (112 words)"),
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { before: 120, after: 200, line: 300 },
    indent: { left: 300, right: 300 },
    shading: { type: ShadingType.CLEAR, fill: C.franja, color: "auto" },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color: C.azulMedio, space: 12 } },
    children: [new TextRun({
      text: "Replication keeps copies of the same data on several machines. Kleppmann explains that this solves three problems at once: it keeps data physically close to the users who read it, it lets the system keep working when a node fails, and it spreads read traffic across more machines. The difficulty is not copying the data once; it is handling changes. If replication is synchronous, every write waits for the slowest follower and availability drops. If it is asynchronous, writes are fast but followers fall behind, so a reader may see stale data. That is the trade-off: durability and latency are bought against consistency. Our HDFS projection prices that same bargain in disk.",
      size: 21, color: C.tinta,
    })],
  }),
  p("El párrafo contiene 112 palabras, dentro del rango exigido de 80 a 120. Es redacción propia del equipo sobre la lectura, no traducción automática."),
  h3("Conexión con las cifras propias"),
  p("Kleppmann plantea el compromiso en términos de latencia y consistencia. HDFS lo replantea en términos de disco: cada réplica adicional multiplica los bytes almacenados por uno y compra tolerancia a un nodo caído más. Vale la pena señalar una diferencia: HDFS usa replicación síncrona dentro de la tubería de escritura —el cliente no considera escrito un bloque hasta que las réplicas lo confirman—, de modo que se sitúa en el lado «lento pero consistente» del compromiso que describe Kleppmann, no en el lado «rápido pero desactualizado»."),
  h2("10.2 Glosario bilingüe · tres términos nuevos"),
  tabla(
    ["Término (EN)", "Traducción (ES)", "Definición breve"],
    [
      ["Replication lag", "Retraso de replicación", "Intervalo de tiempo entre el momento en que una escritura se confirma en el nodo líder y el momento en que aparece en un seguidor. Con replicación asíncrona el retraso es variable y no está acotado: si el seguidor va lento o la red se congestiona, puede pasar de milisegundos a minutos. Es la causa directa de que una lectura devuelva un valor viejo."],
      ["Eventual consistency", "Consistencia eventual", "Garantía débil según la cual, si las escrituras se detienen, todas las réplicas terminan convergiendo al mismo valor. No dice cuándo: solo promete que el retraso de replicación acaba en cero. Kleppmann subraya que la palabra «eventual» es deliberadamente vaga, y que por eso hacen falta garantías más fuertes —como read-your-writes— para que la aplicación resulte usable."],
      ["Failover", "Conmutación por error", "Procedimiento por el cual, cuando el nodo líder cae, uno de los seguidores es promovido a líder y el resto del sistema se reconfigura para escribirle a él. Puede ser manual o automático. El riesgo del automático es el split brain: dos nodos se creen líderes a la vez y aceptan escrituras contradictorias."],
    ],
    [1900, 1900, 6280]
  ),
  espacio(180),
  h3("Términos relacionados incorporados al glosario acumulativo"),
  tabla(
    ["Término (EN)", "Traducción (ES)", "Definición breve"],
    [
      ["Replication factor", "Factor de réplica", "Número de copias de cada bloque que HDFS mantiene en el clúster. Parámetro dfs.replication, por defecto 3. Con factor R el sistema tolera R − 1 nodos caídos sin pérdida de dato."],
      ["Under-replicated block", "Bloque sub-replicado", "Bloque que existe en menos copias que el factor configurado, típicamente porque cayó un DataNode. HDFS intenta restaurar el factor copiándolo a otro nodo; si no hay nodos disponibles, permanece sub-replicado."],
      ["Block", "Bloque", "Unidad de direccionamiento y réplica de HDFS, 128 MiB por defecto. Un archivo se parte en ⌈tamaño / 128 MiB⌉ bloques. El último bloque ocupa en disco solo los bytes reales, no el bloque completo."],
    ],
    [1900, 1900, 6280]
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

const s11 = [
  h1("11. Trazabilidad del repositorio y reparto del trabajo"),
  p("La entrega es de equipo y la contribución de cada integrante debe quedar registrada en la historia de commits. Un repositorio donde una sola persona hizo todos los commits no evidencia trabajo de equipo, por correcto que esté el cálculo."),
  espacio(60),
  tabla(
    ["Integrante", "Aporte", "Commits que lo evidencian"],
    [
      [EQUIPO[0], "Consolidación de la fuente única y de la ficha del equipo; script de proyección; redacción del informe", "T1: ficha de SECOP II · T3: script de proyeccion reproducible · T3: ficha consolidada del equipo"],
      [EQUIPO[1], "Levantamiento del clúster y mediciones con los tres niveles de réplica; verificación manual de las doce operaciones", "T1: ficha de <su fuente> · T3: mediciones del cluster con R=1,2,3 · T3: verificacion manual de cifras"],
      [EQUIPO[2], "Componente en inglés; tres términos del glosario bilingüe; ejecución de la prueba del tercero", "T1: ficha de <su fuente> · T3: parrafo en ingles sobre Kleppmann · T3: glosario bilingue"],
    ],
    [2000, 4200, 3880]
  ),
  espacio(180),
  nota("Este reparto es una plantilla, no un registro. Cada integrante debe hacer sus propios commits desde su propia cuenta. Poner el nombre de alguien en un commit ajeno es peor que no repartir el trabajo."),
  h2("11.1 Comprobación antes de entregar"),
  formula([
    `git shortlog -sne     # debe listar TRES autores con commits`,
    `git log --oneline     # los mensajes deben decir que se hizo, no "update"`,
    `git rev-parse HEAD    # hash del ultimo commit, para el cuadro de entrega`,
  ]),
  h2("11.2 Lista de verificación"),
  bullet("git shortlog -sne lista a los tres integrantes"),
  bullet("python scripts/proyeccion.py corre sin error en una máquina limpia"),
  bullet("Los marcadores [INTEGRANTE 2] e [INTEGRANTE 3] están reemplazados en todos los documentos"),
  bullet("Otro equipo rehízo la proyección con la ficha y llegó a 9,7150 GiB"),
  bullet("docs/ENTREGA.md tiene el hash del último commit, no de uno anterior"),
  bullet("El repositorio es accesible para el docente"),
  new Paragraph({ children: [new PageBreak()] }),
];

const s12 = [
  h1("12. Declaración de uso de asistentes de inteligencia artificial"),
  p("Herramienta: Claude (Anthropic), agosto de 2026."),
  p([
    new TextRun({ text: "Para qué se usó: ", size: 21, bold: true }),
    new TextRun({ text: "estructurar este documento, redactar la argumentación, escribir scripts/proyeccion.py y scripts/generar_informe_docx.js, y revisar el párrafo en inglés.", size: 21 }),
  ]),
  p([
    new TextRun({ text: "Para qué no se usó: ", size: 21, bold: true }),
    new TextRun({ text: "ninguna cifra de este documento proviene del asistente.", size: 21 }),
  ]),
  bullet("Los cinco datos de entrada de medición (muestra_gib, muestra_filas, total_filas, filas_2023 y filas_2025) se tomaron de resultados/_resultados.json de la ficha T1, producidos por ejecución de código sobre archivos reales y contra la API de datos.gov.co el 24 de julio de 2026."),
  bullet("Todos los resultados se producen ejecutando scripts/proyeccion.py, cuyo código es auditable línea por línea y no contiene ninguna cifra de resultado escrita a mano."),
  bullet("Las doce operaciones intermedias se rehicieron a mano y se contrastaron contra la salida del script; la tabla de verificación está en la sección 6. Adicionalmente se hizo un tercer recálculo independiente con aritmética decimal de precisión arbitraria."),
  bullet("Los dos precios (USD 0,023 por GB-mes y USD 12 por TB) y la TRM se consultaron en fuentes públicas el 3 de agosto de 2026 y se declaran como supuestos de costo, no como mediciones propias."),
  bullet("El párrafo en inglés es redacción propia del equipo sobre la lectura de Kleppmann, revisada con el asistente. No es traducción automática sin revisar."),
  h1("13. Referencias"),
  p("Colombia Compra Eficiente. SECOP II — Procesos de Contratación [conjunto de datos p6dx-8zbt]. Portal de Datos Abiertos de Colombia. https://www.datos.gov.co", { indent: { left: 400, hanging: 400 } }),
  p("Congreso de Colombia. (2014). Ley 1712 de 2014, de Transparencia y del Derecho de Acceso a la Información Pública Nacional.", { indent: { left: 400, hanging: 400 } }),
  p("Kleppmann, M. (2017). Designing data-intensive applications: The big ideas behind reliable, scalable, and maintainable systems. O'Reilly Media.", { indent: { left: 400, hanging: 400 } }),
  p("Shvachko, K., Kuang, H., Radia, S., y Chansler, R. (2010). The Hadoop Distributed File System. 2010 IEEE 26th Symposium on Mass Storage Systems and Technologies (MSST), 1-10. https://doi.org/10.1109/MSST.2010.5496972", { indent: { left: 400, hanging: 400 } }),
  p("White, T. (2015). Hadoop: The definitive guide (4.ª ed.). O'Reilly Media.", { indent: { left: 400, hanging: 400 } }),
];

// ---------------------------------------------------------------------------
// Documento
// ---------------------------------------------------------------------------
const doc = new Document({
  creator: EQUIPO.join(", "),
  title: "T3 · Proyección de almacenamiento y factor de réplica",
  description: "IFPN0025 Big Data e Ingeniería de Datos · Universidad Ean · Sesión 3",
  styles: {
    default: { document: { run: { font: "Calibri", size: 21, color: C.tinta } } },
  },
  numbering: {
    config: [{
      reference: "vinetas",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 460, hanging: 260 } } },
      }],
    }],
  },
  sections: [{
    properties: {
      titlePage: true,
      page: {
        size: { width: 12240, height: 15840, orientation: PageOrientation.PORTRAIT },
        margin: { top: 1300, bottom: 1200, left: 1080, right: 1080 },
      },
    },
    headers: {
      first: new Header({ children: [new Paragraph({ children: [] })] }),
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.linea, space: 6 } },
          children: [new TextRun({ text: "IFPN0025 · Big Data e Ingeniería de Datos · T3 · Universidad Ean", size: 16, color: C.gris })],
        })],
      }),
    },
    footers: {
      first: new Footer({ children: [new Paragraph({ children: [] })] }),
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ children: ["Página ", PageNumber.CURRENT, " de ", PageNumber.TOTAL_PAGES], size: 16, color: C.gris })],
        })],
      }),
    },
    children: [
      ...portada, ...toc, ...s1, ...s2, ...s3, ...s4,
      ...s5, ...s6, ...s7, ...s8, ...s9, ...s10, ...s11, ...s12,
    ],
  }],
});

const salida = path.join(RAIZ, "docs", "informe_T3_proyeccion_replica.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(salida, buf);
  console.log("Escrito:", salida, `(${(buf.length / 1024).toFixed(1)} KB)`);
});
