# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/);
versiones según [SemVer](https://semver.org/lang/es/).

## [Sin publicar] (los ejemplos ya apuntan a `v0.2.0`)

### Agregado

- `cohorte.yml`: planilla de seguimiento de una cohorte de Classroom con `dredd cohorte`, para un repo privado de los docentes (Ola 25).
- `evaluar.yml`: anotaciones sobre las líneas (`anotaciones: true`), que funcionan sin Code Scanning; un único comentario en el PR, actualizado en cada push; ripley corre una sola vez (`--md` y `--sarif`).

### Seguridad

- `evaluar.yml` separa la ejecución de la publicación: el job que compila y ejecuta la entrega tiene token de solo lectura y checkout sin credenciales; `comentar` y `sarif` no ejecutan código de la entrega. Se rechaza `pull_request_target`.

### Corregido

- `evaluar.yml` fijaba `permissions: contents: read` a nivel del workflow, que en uno reutilizable recorta lo que otorga el llamador: el comentario en el PR no podía tener `pull-requests: write`.
- Con `bloqueante: true` el commit sólo se marcaba en rojo si no compilaba (ripley `--md` salía con 0 ante errores de reglas); se corrige con ripley N-RIPLEY-16.

## [0.1.0] - 2026-09-28

### Agregado

- `evaluar.yml`: devolución de ripley por push (resumen, comentario en PR, SARIF
  opcional, modo bloqueante), con las herramientas instaladas por mother.
- `proctoring.yml`: auditoría forense de exámenes con uatu-audit.
- Ejemplos de uso para consignas y exámenes.
