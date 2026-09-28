# Instrucciones para el Agente (sulaco)

1. **Commits semánticos en español**: `<tipo>(<alcance>): <descripción>`.
2. Solo workflows reutilizables (`on: workflow_call`): la lógica vive en las
   herramientas (ripley, uatu, mother), no en YAML.
3. Permisos mínimos, acciones fijadas por versión, entradas siempre por `env:`.
4. Herramientas propias siempre desde git (`git+https://github.com/…`).
5. `uvx --with pyyaml pytest -q tests` antes de cada commit.
