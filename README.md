# Chequeo de una oferta contra un CV

> **Estado:** en construcción. Este README describe el objetivo del proyecto; por ahora
> solo está lista la base (Docker y test de humo). El avance está en
> [docs/PLAN.md](docs/PLAN.md).

## Qué problema resuelve

Comparar una oferta de trabajo con un CV parece una tarea ideal para un LLM, pero tiene
un riesgo: el modelo puede afirmar que un requisito está cubierto sin que nada en el CV
lo respalde.

Este proyecto hace esa comparación y exige evidencia. Por cada requisito de la oferta
devuelve:

- un nivel de cobertura;
- la cita del CV que lo respalda;
- una justificación.

Si no hay evidencia, el requisito queda como brecha.

## Cómo funciona

El trabajo se reparte entre el modelo y código determinístico:

| Pregunta | Quién responde |
|---|---|
| ¿La cita existe en el CV? | Un validador en Python, sin LLM |
| ¿La cita cubre el requisito? | Claude Code, con una rúbrica |

Niveles de la rúbrica:

| Score | Significado |
|---|---|
| `1.0` | Cobertura directa |
| `0.7` | Equivalente, escrito de otra forma |
| `0.4` | Parcial |
| `0` | Sin evidencia |

Una skill de Claude Code hace el análisis y un hook ejecuta el validador sobre el
resultado, para que el control no dependa de que el agente decida correrlo.

Si una cita no aparece en el CV, el agente recibe el error y tiene un reintento. Si
sigue siendo inválida, el requisito baja a `0`. Las citas rechazadas quedan registradas
para revisarlas a mano y, si aportan algo, convertirlas en tests o en reglas de la
skill.

## Decisiones de diseño

- **Sin llamadas a una API de LLM:** el análisis corre dentro de Claude Code, con un plan
  existente.
- **pydantic para la estructura:** valida el formato del JSON, y los tests se concentran
  en las reglas propias del proyecto.
- **Docker para las tareas:** tests, validación y conversión de PDF corren en
  contenedores. Claude Code se ejecuta en el host, para no meter sus credenciales en una
  imagen.
- **Datos reales fuera del repo:** los tests usan datos ficticios y los datos reales van
  en `private/`, ignorada por git.

## Límites

### Qué garantiza el validador

El validador garantiza que la cita existe en el CV, no que tenga relación con el
requisito. Son dos datos distintos:

| Dato | Pregunta | Quién lo decide |
|---|---|---|
| `quote_status` | ¿Esta cita existe en el CV? | Validador |
| `score` | ¿Esta cita cubre el requisito? | LLM |

Por eso una cita puede estar `found` y tener score `0`: existe, pero no cubre el
requisito. Y una cita solo se rechaza si el agente afirmó cobertura sin sostenerla:

| Score del agente | Cita | Resultado | ¿Rechazada? |
|---|---|---|---|
| `> 0` | Existe | Se mantiene el score | No |
| `> 0` | No existe, vacía o genérica | Baja a `0` | Sí |
| `0` | Cualquiera | Queda en `0`, es una brecha | No |

### Riesgo conocido: cita real sin relación con el requisito

Si el agente puntúa "Kubernetes" con `1.0` y cita "backend con Python", la cita existe
y el validador mantiene el score. Puede ocurrir por un salto de razonamiento (inferir
Kubernetes de "microservicios en AWS"), por el sesgo a encontrar alguna evidencia o por
instrucciones ocultas en la oferta o el CV.

Cómo se aborda por ahora:

- La skill exige que la cita nombre la tecnología o un equivalente directo; si no, el
  score es `0` y la cita, `null`.
- La mini eval incluye requisitos que no están en el CV, para medir si el agente
  inventa una relación.
- El reporte deja juntos el requisito, la cita y la justificación, para la revisión
  humana.

Otro límite: el score del modelo puede variar entre corridas. Los tests cubren las
reglas determinísticas, no el juicio del LLM.

## Mejoras posibles

- **Segunda pasada con un subagente:** si la mini eval muestra citas sin relación con el
  requisito, o si el proyecto creciera o pasara a producción, un subagente juzgaría solo
  el requisito y la cita, sin ver el razonamiento original. Sumaría uso del plan y más
  piezas, y seguiría siendo un LLM.
- **Más de una oferta a la vez:** hoy las rutas de trabajo son fijas y cada análisis pisa
  el anterior. Si el proyecto creciera o pasara a producción, cada análisis necesitaría
  su propio espacio de trabajo.
