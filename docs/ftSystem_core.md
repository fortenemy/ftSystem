---
description: ftSystem Core Instructions
alwaysApply: true
---

> **Goal**  
ftSystem is an open‑source Python CLI that coordinates a *team* of AI agents—managed by a single Master agent—to deliver accurate, format‑controlled answers for users.

## 1. Agent Architecture
* **Mediator pattern**: one **Master** + five specialized **Helper Agents** (e.g., Researcher, Coder, Analyst, Critic, Summarizer).  
* Helpers share a *public forum*; the Master delegates tasks, enforces turn‑taking, monitors quality, and synthesizes the final answer.

## 2. High‑Level Workflow
1. **Plan** – Master receives the user prompt and posts task assignments.  
2. **Parallel Work** – Helpers process sub‑tasks concurrently and post findings.  
3. **Debate & Refine** – Helpers critique and improve each other’s outputs.  
4. **Synthesis** – Master compiles a coherent, format‑specific reply to the user.  
5. **Memory** – Master writes a concise session summary to long‑term storage.

## 3. CLI (Typer) Commands, Examples
| Command | Purpose |
|---------|---------|
| `agent create` / `agent list` / `agent select` | Manage helper profiles |
| `run "<query>" [--format json]` | One‑shot request |
| `interactive` | Multi‑turn chat session |
| `history show` | View past summaries |
| `config set` | Adjust API keys & defaults |

## 4. Core Frameworks
* **Typer** – user‑friendly CLI definitions  
* **asyncio** – non‑blocking agent concurrency  
* **LangChain / LangGraph** – prompt & tool orchestration  
* **Pydantic** – typed models & validation  
* Extras: `logging`, **Rich** for colored console output

## 5. Memory Strategy
* **Short‑term**: summarized dialogue context per session.  
* **Long‑term**: JSONL summaries (`history_YYYY‑MM‑DD.jsonl`) for future recall.

## 6. Prompt Engineering Rules
* Clear **role prompts** for each agent.  
* **Collaboration protocol**: be concise, cite reasoning, politely flag errors.  
* **Output control**: Master must respect requested format & language (English by default).  
* **Safety & Privacy**: hide chain‑of‑thought from user; block disallowed content.  
* **Error recovery**: agents report issues; Master may re‑assign tasks.

## 7. API & Tool Integration
* Per‑agent model mapping (OpenAI GPT‑4, Claude v2, Gemini, local LLaMA).  
* Async calls via wrapper clients; graceful back‑off on rate limits.  
* Optional MCP tools: code‑interpreter, shell, browser—gated by Master.

## 8. Sample Code Skeleton (outline)
* `Agent` → async `process(task, forum)`  
* `MasterAgent` → `handle_query`, `_synthesize_answer`, `_save_session_summary`  
* CLI entry in `main.py` with Typer; model clients in `model_clients.py`.

## 9. Development Guidelines
1. **Modularity** – separate agents, model clients, CLI, memory.  
2. **Concurrency** – launch helper tasks with `asyncio.gather`.  
3. **Testing** – unit & e2e tests; simulate multi‑agent dialogues.  
4. **Documentation** – keep prompts & configs under version control.

## 10. Dependencies
* The following Python packages are declared in `requirements.txt`:
  - `typer`
  - `pydantic`
  - `langchain`
* To install or update dependencies, run:
  ```bash
  pip install -r requirements.txt
  ```
---
*Last updated: 2025‑07‑29*