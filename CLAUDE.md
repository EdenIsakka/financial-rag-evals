# financial-rag-evals: reglas del proyecto

RAG sobre reportes financieros (20-F de SEC + informes de bancos colombianos) con citas y suite de evals.
Stack: Python 3.12 + uv, Postgres/pgvector (Docker, puerto **5433**), Docling, BGE-M3, LLM **local con Ollama (Qwen3 8B)**.
Todo corre local y gratis (RTX 3070 8 GB). Las citas se implementan a mano: chunks con ID, el modelo cita IDs y el código verifica que existan.
Comandos: `uv run pytest`, `uv run ruff check`, `docker compose up -d --wait`.

## Reglas para no desviarse

1. **Un hito a la vez.** No se empieza el siguiente hasta cumplir el "hecho cuando" del actual. Si surge una idea fuera del hito, se anota en "Ideas para después" y se sigue.
2. **El golden set lo revisa el usuario.** Claude puede proponer preguntas y sacar respuestas del XBRL, pero ninguna pregunta entra a `evals/golden_set.jsonl` sin la revisión del usuario.
3. **Toda mejora llega con su número.** Un PR de mejora debe agregar su fila en la tabla de ablación. Sin número, no se mergea.
4. **Sin atribución a Claude.** Ningún commit ni PR lleva `Co-Authored-By`, "Generated with Claude" ni enlaces de sesión. El autor es solo el usuario, con su cuenta **personal** EdenIsakka. El repo vive en `C:\Users\julia\personal\` (ahí aplica `~/.gitconfig-personal`) y además el git local fija EdenIsakka + email noreply. La identidad global es la del trabajo y no se toca.

## Modo aprendizaje

El usuario quiere aprender ingeniería de IA con este proyecto, no solo terminarlo.

- **Antes de cada paso**, explica en 2-4 líneas el concepto y por qué se hace así (y qué hace la industria).
- **El usuario escribe las piezas clave**: la función de métricas, la consulta híbrida y el prompt de generación. Claude da la firma, el test y pistas, no la solución, salvo que el usuario la pida.
- **Al cerrar cada hito**, haz 2-3 preguntas cortas para comprobar que se entendió, y resume lo aprendido.
- No entregues bloques grandes de código sin explicar las partes no obvias.

## Hitos

| # | Hito | Hecho cuando… |
|---|---|---|
| 1 | Esqueleto | `uv run pytest` pasa local y en CI; `docker compose up` levanta Postgres |
| 2 | Ingesta | `finrag-ingest` carga 4 documentos con página/empresa por chunk; test de chunking de tablas |
| 3 | Golden set v1 | 50 preguntas en 6 categorías, revisadas por el usuario |
| 4 | Pipeline base + eval | Primer JSON en `evals/results/` con costo real por corrida |
| 5 | Ablaciones | Tabla con 4 filas reales (pdftotext→Docling, +BM25, +reranker) |
| 6 | Demo + README | README entendible en 60 s; golden set 100+ |

**Hito actual: 2 (Ingesta).**

## Ideas para después

- Despliegue público (Fly.io).
- Comparar contra Claude por API (fila extra en la ablación), si algún día se quiere pagar.
- (Hito 5) La "sección" de muchos chunks es el encabezado repetido de página (p. ej. "Banco Davivienda S. A. y sus Subsidiarias"), no el título real de la tabla. Filtrar encabezados repetidos y medir si mejora el retrieval.
- (Hito 5) Tablas de hasta ~21k caracteres: probar partirlas por filas repitiendo el encabezado de columnas.
- (Hito 4) El 20-F en HTML no trae páginas ni encabezados reconocibles (la SEC usa `<div>` con estilos, no `<h1>`): sus chunks quedan sin página ni sección. Para citarlos, detectar los "Item N." del 20-F como sección.
- Validar al ingerir que el año del documento coincide con el del nombre de archivo (pasó con un 20-F de 2008 guardado como 2024).
