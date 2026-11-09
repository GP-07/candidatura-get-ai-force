# Chequeo de una oferta contra un CV

> **Estado:** implementado, con 76 tests automáticos. El flujo normal se probó una vez con
> datos ficticios. Quedan pruebas manuales pendientes, listadas en
> [docs/SKILL_CHECKLIST.md](docs/SKILL_CHECKLIST.md).

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

## Cómo correrlo

Requisitos: Docker, Claude Code y `python3`. Solo se probó en una Mac; en Windows, por
ejemplo, el comando `python3` puede no existir.

La imagen se construye sola la primera vez. Para correr los tests:

```bash
docker compose run --rm tests
```

Para analizar una oferta, abrí esta carpeta en Claude Code. Al abrirla, puede pedirte
confirmar que confiás en sus hooks y permitir los comandos de Docker. Después ejecutá
la skill con la oferta y el CV, en ese orden:

```
/check-offer examples/offer.md examples/cv.md
```

Se aceptan archivos `.md`, `.txt` y `.pdf`. Para usar datos propios, dejalos en
`private/`, que git ignora. Docker tiene que estar abierto.

El resultado queda en `private/report.json`. Cada análisis pisa el anterior.

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
- El reporte deja juntos el requisito, la cita y la justificación, para la revisión
  humana.

Otro límite: el score del modelo puede variar entre corridas. Los tests cubren las
reglas determinísticas, no el juicio del LLM.

## Mejoras posibles

- **Mini eval con datos reales:** medir con un CV y una oferta reales, incluyendo
  requisitos ausentes del CV, si el agente inventa una relación y cuántas citas se
  rechazan. No se hizo; hasta ahora solo hubo una corrida con datos ficticios.
- **Segunda pasada con un subagente:** si esa medición muestra citas sin relación con el
  requisito, o si el proyecto creciera o pasara a producción, un subagente juzgaría solo
  el requisito y la cita, sin ver el razonamiento original. Sumaría uso del plan y más
  piezas, y seguiría siendo un LLM.
- **Aviso por muchas citas rechazadas:** el reporte se escribe siempre que el análisis
  tenga un formato válido. Si la medición muestra porcentajes altos de rechazo, la skill
  podría advertir que conviene revisar el análisis, por ejemplo por encima del 30%.
- **Más de una oferta a la vez:** hoy las rutas de trabajo son fijas y cada análisis pisa
  el anterior. Si el proyecto creciera o pasara a producción, cada análisis necesitaría
  su propio espacio de trabajo.

## Cómo se desarrolló

Lo construyeron Guido Pallas y Claude Code (modelo Opus 5.5) en sesiones de trabajo con
revisión humana paso a paso. Claude Code escribió el código, los tests y la documentación,
incluido este texto. Guido definió el alcance, revisó cada fase, pidió cambios e hizo los
commits.

Se avanzó por fases con TDD: tests en rojo, revisión, implementación mínima y revisión.
La skill es la excepción, porque su salida no es determinística: se valida con una
checklist manual.

El detalle, con los errores del agente, las correcciones y lo que no se hizo, está en
[docs/PROCESS.md](docs/PROCESS.md).
