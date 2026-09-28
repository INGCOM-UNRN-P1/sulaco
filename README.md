# sulaco — corrección continua sobre GitHub Classroom

_(La nave de Aliens.)_

Workflows reutilizables de GitHub Actions para que la devolución de cada
entrega llegue sola, en cada push, sin servidores propios. Cada repositorio de
entrega o de examen los llama con `uses:`; las herramientas se instalan
**siempre desde git** con [mother](https://github.com/INGCOM-UNRN-P1/mother).

| Workflow | Para qué | Ejemplo de uso |
|:--|:--|:--|
| [`evaluar.yml`](.github/workflows/evaluar.yml) | Instala el perfil estudiante con mother, corre `ripley check` sobre la entrega y publica la devolución en el resumen del job y como comentario en los pull requests. Opcional: SARIF (anotaciones en el código) y modo bloqueante. | [`ejemplos/entrega.yml`](ejemplos/entrega.yml) |
| [`proctoring.yml`](.github/workflows/proctoring.yml) | Auditoría forense de un examen supervisado con `uatu-audit` (cadena firmada, alertas heurísticas). | [`ejemplos/examen.yml`](ejemplos/examen.yml) |

El CI de integración de punta a punta del ecosistema (N-ECO-03) sigue en
[p1-tools](https://github.com/INGCOM-UNRN-P1/p1-tools), que es donde están los
scripts que ejecuta.

## Uso en una consigna

Copiar [`ejemplos/entrega.yml`](ejemplos/entrega.yml) a
`.github/workflows/devolucion.yml` de la plantilla de la consigna:

```yaml
jobs:
  evaluar:
    uses: INGCOM-UNRN-P1/sulaco/.github/workflows/evaluar.yml@v0.1.0
    permissions:
      contents: read
      pull-requests: write
    with:
      ruta: src
```

Entradas de `evaluar.yml`:

| Entrada | Por defecto | Qué hace |
|:--|:--|:--|
| `ruta` | `.` | Archivo `.c` o carpeta a verificar |
| `perfil_ripley` | `strict` | `strict`, `relaxed` o `exam` |
| `perfil_mother` | `estudiante` | Perfil de herramientas a instalar |
| `mother_ref` | `main` | Tag o commit de mother |
| `comentar` | `true` | Comentar la devolución en los pull requests |
| `sarif` | `false` | Subir los hallazgos como SARIF (requiere `security-events: write`) |
| `bloqueante` | `false` | Marcar el commit en rojo si ripley encuentra errores |

## Seguridad

- Permisos mínimos (`contents: read`); cada uso agrega solo lo que necesita.
- Acciones fijadas por versión; las entradas llegan a los scripts por `env:`,
  nunca interpoladas (sin inyección de comandos).
- Las claves del docente de `proctoring.yml` se pasan como `secrets` y se
  escriben en un archivo temporal con `umask 077`.

`tests/test_workflows.py` controla todo lo anterior; el CI además corre
[actionlint](https://github.com/rhysd/actionlint).

## Licencia

GPL-3.0-or-later (ver `LICENSE`).
