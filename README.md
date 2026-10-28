# sulaco — corrección continua sobre GitHub Classroom

_(La nave de Aliens.)_

Workflows reutilizables de GitHub Actions para que la devolución de cada
entrega llegue sola, en cada push, sin servidores propios. Cada repositorio de
entrega o de examen los llama con `uses:`; las herramientas se instalan
**siempre desde git** con [mother](https://github.com/INGCOM-UNRN-P1/mother).

| Workflow | Para qué | Ejemplo de uso |
|:--|:--|:--|
| [`evaluar.yml`](.github/workflows/evaluar.yml) | Instala el perfil estudiante con mother, corre `ripley check` una vez sobre la entrega y publica la devolución (con secciones colapsables y qué estudiar del apunte) en el resumen del job, como anotaciones sobre las líneas y como un único comentario en el pull request, actualizado en cada push. Opcional: SARIF para Code Scanning y modo bloqueante. | [`ejemplos/entrega.yml`](ejemplos/entrega.yml) |
| [`cohorte.yml`](.github/workflows/cohorte.yml) | En un repo privado de los docentes: clona los repos de una consigna de Classroom y arma con `dredd cohorte` la planilla de seguimiento (estado de cada entrega, observaciones frecuentes, tiempos). | [`ejemplos/cohorte.yml`](ejemplos/cohorte.yml) |
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
    uses: INGCOM-UNRN-P1/sulaco/.github/workflows/evaluar.yml@v0.2.0
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
| `comentar` | `true` | Comentar la devolución en los pull requests (un solo comentario, actualizado en cada push; requiere `pull-requests: write`) |
| `anotaciones` | `true` | Marcar las observaciones sobre las líneas del código (funciona en repos privados, sin Code Scanning) |
| `sarif` | `false` | Subir los hallazgos a GitHub Code Scanning (requiere `security-events: write` y, en repos privados, Advanced Security) |
| `bloqueante` | `false` | Marcar el commit en rojo si ripley encuentra errores |

## Planilla de la cohorte

Copiar [`ejemplos/cohorte.yml`](ejemplos/cohorte.yml) en un repositorio **privado** de los
docentes (no en la consigna) y crear el secreto `CLASSROOM_TOKEN`, un token de solo lectura de
los repos de la organización. Cada corrida (a mano o los lunes) deja `cohorte.csv`, `.md` y
`.json` como artefacto y el resumen en la página del job: estado de cada entrega (aprobada, con
errores, no compila, sin entrega), las observaciones más frecuentes con enlace al apunte y los
tiempos (último commit y atraso respecto de `fecha_limite`, orientativo porque la fecha del
commit la fija el alumno). Sólo lo ve quien tiene acceso a ese repositorio; no se publica en
GitHub Pages, que en un repo privado de una organización gratuita es público.

## Seguridad

- **El código de la entrega corre con token de solo lectura.** En `evaluar.yml` sólo el job
  `evaluar` compila y ejecuta: declara `contents: read` (recorta lo que otorgue el llamador) y su
  checkout no guarda credenciales en `.git`. `comentar` y `sarif` publican a partir del artefacto,
  sin ejecutar nada de la entrega. `evaluar.yml` no fija permisos a nivel del workflow: en uno
  reutilizable sólo recortan, y con `contents: read` el comentario se quedaba sin
  `pull-requests: write`.
- **`pull_request_target` se rechaza**: correría código ajeno con los secretos del repositorio.
- En `cohorte.yml` el token de la organización sólo existe en el paso que clona y se quita de
  cada `.git` antes de correr ripley.
- Permisos mínimos; cada uso agrega solo lo que necesita.
- Acciones fijadas por versión; las entradas llegan a los scripts por `env:`,
  nunca interpoladas (sin inyección de comandos).
- Las claves del docente de `proctoring.yml` se pasan como `secrets` y se
  escriben en un archivo temporal con `umask 077`.

`tests/test_workflows.py` controla todo lo anterior (también que ningún job que ejecute código
tenga permisos de escritura ni secretos); el CI además corre
[actionlint](https://github.com/rhysd/actionlint).

## Licencia

GPL-3.0-or-later (ver `LICENSE`).
