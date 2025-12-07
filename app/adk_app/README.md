# ADK App

This package exposes agent entrypoints for an ADK-style web runner. It includes a stub `root_agent` declared in `config.yaml`.

- Config path: `app/adk_app/config.yaml`
- Entrypoint: `app.adk_app.agent_app:root_agent`

Note: The ADK CLI/tooling is not part of this repository. If you use an external `adk` command, point it to this directory as the agents root.

