# Agents - urban-dictionary-mcp

MCP Server exposing the Urban Dictionary via the Model Context Protocol.

- MCP SDK: https://github.com/modelcontextprotocol/python-sdk
- HTTPX: https://github.com/projectdiscovery/httpx
- Hishel: https://github.com/karpetrosyan/hishel

## Commands

This project uses `toml-run` — run any `[tool.scripts]` entry by name:

| Command      | What it does                                 |
| ------------ | -------------------------------------------- |
| `run build`  | hatch build                                  |
| `run cli`    | python -m urban_dictionary_mcp               |
| `run dev`    | uvicorn w/ --reload                          |
| `run server` | uvicorn w/ --host 0.0.0.0                    |
| `run format` | Full format: should always be used to format |
| `run lint`   | Full lint: should always be used to lint     |

## Important

- `app_lifespan` does not run on server startup, it runs on every client connection...
