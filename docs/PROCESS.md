# Cómo se construyó este proyecto

Este documento lo redactó Claude Code a partir de la conversación de desarrollo. Solo
incluye lo que ocurrió en esa conversación.

## Quién hizo qué

- **Guido Pallas:** definió el alcance, revisó cada fase, decidió los cambios e hizo todos
  los commits.
- **Claude Code (modelo Opus 5.5):** propuso el diseño y escribió el código, los tests y
  la documentación.

## Forma de trabajo

1. Plan en `docs/PLAN.md`, discutido antes de escribir código.
2. Por fase: tests en rojo, revisión de Guido, implementación mínima, nueva revisión.
3. Sin avanzar de fase ni commitear sin aprobación.

Guido separó los commits de tests y de implementación. En la Fase 2 pidió deshacer
temporalmente la implementación para commitear primero los tests.

La regla tuvo excepciones: el test de `Spring` contra `Springboot` documentó un
comportamiento ya implementado, y el test de la ruta con `ñ` se escribió junto con su
implementación. Ninguno de los dos se vio en rojo.

## Cómo cambió el alcance

- El agente propuso primero un agente de performance y después un agente de cualificación
  de leads. Guido descartó el segundo por grande y por ser parecido al producto de la
  empresa a la que se postula.
- Se eligió un chequeo de oferta contra CV, con Python y la API de Anthropic.
- Guido pidió no usar la API, para que alcanzara con su plan. El análisis pasó a una skill
  de Claude Code y un hook que corre el validador.
- Guido pidió sumar Docker Compose. Se eligió usarlo solo para tareas, sin servicio ni base
  de datos, para no agrandar el proyecto.

## Decisiones que corrigió Guido

| Tema | Propuesta del agente | Resultado |
|---|---|---|
| Tests de estructura | 47 tests a mano | Guido propuso pydantic; 11 tests de reglas propias |
| Cita de una palabra | Exigir 2 palabras | Una palabra sirve si no es genérica; con 2 o más la lista no aplica |
| Tildes | Comparar con tilde | Se ignoran |
| Coincidencia de citas | Solo existencia | Guido propuso scoring; se separó existencia (motor) de cobertura (LLM) |
| Palabras genéricas | Archivo editable, con `backend` en duda | En memoria, sin `backend` ni `frontend` |
| Margen de citas | Aclarar el comportamiento | Guido preguntó por un margen del 30%; el reporte ya se escribía siempre, y el aviso quedó como mejora |
| Lista de requisitos vacía | Campo con motivo | Guido lo consideró sobreingeniería; da error |
| Generación de PDFs de prueba | Función `make_pdf` | Guido la rechazó dos veces; se usan dos PDFs chicos como fixtures |
| Nombres | `build_report`, `VALID` | `run_matching`, `FOUND` |
| Estructura | Módulos sueltos | Paquete, `models.py`, `constants.py`, `exceptions.py` |
| Estilo de tests | `assert run(...) == 2` y helpers mezclados | `exit_code` explícito, `conftest.py`, `helpers.py` y docstrings |

Una propuesta de Guido no se aplicó tras discutirla: absorber `parse_analysis` dentro de
`run_matching`. El agente argumentó dejar el parseo en el borde del sistema y Guido lo
aceptó.

## Errores del agente

- Propuso proyectos demasiado grandes para el pedido.
- Mezcló inglés y español en nombres (`check_oferta`, `citas_rechazadas`). Guido indicó que
  ya había ocurrido varias veces.
- Escribió inner functions en los tests. La regla existía en memorias de otros proyectos,
  que no se cargaban en este. Se pasó al `CLAUDE.md` global.
- Eligió `VALID` para una cita que solo existe en el CV. Guido notó que era confuso.

## Problemas encontrados al probar

- **pydantic aceptaba `true` y `false` como score:** lo detectó un test. Se agregó un
  validador.
- **`Java` podía coincidir dentro de `JavaScript`:** se previó con un test antes de
  implementar.
- **Mensajes de Docker mezclados con el error para el agente:** los tests con `Mock` no
  podían verlo; apareció al correr el hook contra Docker real. Se corrigió con
  `--progress quiet`.
- **Ruta con `ñ`:** macOS puede representarla de dos formas, y el hook compara las rutas
  normalizadas.

## Un límite que surgió de una pregunta

Guido preguntó cómo podía afirmarse cobertura con una cita real pero sin relación con el
requisito, como Kubernetes contra Python. El validador no lo detecta. Se decidió agregar
una regla a la skill y documentar el límite. La segunda pasada con un subagente quedó como
mejora.

## Qué se verificó

- 76 tests automáticos, ejecutados en Docker.
- `convert` y `validate` corridos por Compose, con datos temporales.
- El hook ejecutado en el host contra Docker real, pasándole el evento a mano: rechazos,
  análisis limpio, JSON inválido y otro archivo.
- Una corrida de `/check-offer` hecha por Guido con datos ficticios. Los 6 requisitos dieron
  lo esperado y no hubo citas rechazadas.

## Qué no se hizo o no se verificó

- Pruebas manuales pendientes: oferta maliciosa, reintento con Claude Code real, extensión
  no soportada y Docker detenido. Están en `docs/SKILL_CHECKLIST.md`.
- Mini eval con datos reales: se decidió no hacerla. Tampoco se midió con cuánta frecuencia
  el agente inventa una relación.
- Revisión final de código y de seguridad, prevista en la Fase 6.
- Solo se probó en una Mac. En Windows, por ejemplo, el comando `python3` puede no existir.
- El proyecto no usa LLMs dentro de un producto, ni tiene function calling ni medición de
  costo por token, y no se probó con una API.
