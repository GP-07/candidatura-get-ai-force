# Plan: chequeo de una oferta contra un CV

## Objetivo

Una skill de Claude Code (`/check-offer`) que compara una oferta con un CV y
devuelve, por cada requisito, un nivel de cobertura y la cita del CV que lo
respalda. Claude Code hace el análisis; el código propio verifica ese análisis.
No se llama a ninguna API de LLM: alcanza con un plan de Claude Code.

El proyecto es deliberadamente chico. Lo que se quiere mostrar es cómo se trabaja
con agentes para programar, testear y revisar.

## Reglas funcionales

### Dos preguntas, dos responsables

| Pregunta | Responde | Cómo |
|---|---|---|
| ¿La cita existe en el CV? | `check_offer/quotes.py` | Sin LLM; ignora mayúsculas, tildes, espacios y saltos de línea |
| ¿La cita cubre el requisito? | LLM | Nivel de la rúbrica y justificación |

### Rúbrica

| Score | Significado |
|---|---|
| `1.0` | Cobertura directa |
| `0.7` | Equivalente, escrito de otra forma |
| `0.4` | Parcial |
| `0` | Sin evidencia |

### Citas

- La skill siempre intenta citar al menos 2 palabras.
- La skill copia el término completo tal como aparece en el CV ("Springboot", no
  "Spring"). El motor exige palabras completas; si ese término cubre el requisito lo
  decide el LLM con la rúbrica.
- Una cita de 1 palabra es válida solo si no está en las listas de palabras genéricas,
  en memoria por ahora (por ejemplo, "Python" sí; "desarrollo" no).
- Con 2 palabras o más, la lista de genéricas no aplica.
- Un score mayor a 0 sin cita válida baja a 0.

- La cita debe nombrar la tecnología o un equivalente directo; si no, score 0 y cita
  `null`. El motor no detecta una cita real sin relación con el requisito: ver "Qué
  garantiza el validador" en el README.

### Citas rechazadas

1. El primer rechazo bloquea y le explica el error al agente.
2. Hay un único reintento. Si la cita sigue siendo inválida, baja a 0 y el proceso
   termina.
3. Toda cita rechazada se imprime en la salida y se agrega a
   `private/rejected_quotes.jsonl`.
4. Los casos útiles se incorporan a mano: como test de regresión con datos ficticios
   y como regla o ejemplo en la skill. El modelo no aprende solo de estos registros.

### Entradas y datos

- CV y oferta: `.md`, `.txt` o `.pdf`. El PDF se convierte con `pdftotext` y las
  citas se validan contra el texto convertido.
- `examples/` contiene un CV y una oferta ficticios, para probarlo al clonar.
- `private/` guarda datos reales y está ignorada por git.

### Docker

Compose corre tareas (`convert`, `validate`, `tests`). Claude Code se ejecuta en el
host, para no meter el login del plan en un contenedor.

## Forma de trabajo

En cada fase de código: tests en rojo, revisión, implementación mínima hasta el
verde, revisión. Nada se commitea sin aprobación explícita.

## Fases

### Fase 0: base

`docs/PLAN.md`, `CLAUDE.md`, `.gitignore`, `Dockerfile`, `compose.yaml` y servicio
`tests`. Listo cuando `docker compose run --rm tests` pasa el test de humo.

### Fase 1: contrato del JSON

pydantic valida la estructura y por eso no se testean sus casos genéricos. Los tests
cubren lo propio: la rúbrica, el rechazo de un análisis sin requisitos y que todo error
llegue como `ContractError`, indicando el ítem inválido, sin resultado parcial.

### Fase 2: verificación de citas

Cita literal, inventada, con saltos de línea distintos, mayúsculas, acentos y
ligaturas de PDF, vacía, de 1 palabra válida, de 1 palabra genérica y de 2 palabras
que incluyen una genérica.

### Fase 3: coherencia y CLI

Score mayor a 0 sin cita válida baja a 0; score 0 con cita se conserva; resumen;
registro de rechazos; códigos de salida (`0` procesó, `2` contrato inválido).

### Fase 4: conversión de entradas

`.md` y `.txt` pasan tal cual; PDF con texto se convierte; PDF sin texto y extensión
no soportada dan error claro. Servicios `convert` y `validate`.

### Fase 5: hook y skill

Hook con tests: lee el evento de Claude Code por stdin, se activa solo con el archivo
de salida, devuelve `2` para informar el error al agente, cuenta los intentos por
análisis y avisa si Docker no está corriendo.

La skill no admite TDD porque su salida no es determinística: se valida con una
checklist manual y ejemplos, incluida una oferta con una instrucción maliciosa.

### Fase 6: prueba real y cierre

Corrida con la oferta y el CV reales, mini eval manual de 5 requisitos, revisión de
código y de seguridad, `README.md` y `PROCESS.md` con lo que haya ocurrido.

La mini eval incluye requisitos que no están en el CV, para medir si el agente inventa
una relación. Con ese resultado se decide si implementar la segunda pasada con un
subagente. Si no se implementa, queda como mejora en el README.
