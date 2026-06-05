<div align="center">
  
# 🛡️ Intercept

**The CI/CD Security Gate for Agentic AI & LLMs**

[![Release](https://img.shields.io/github/v/release/ShreyashF130/intercept)](https://github.com/ShreyashF130/intercept/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![FastAPI Backend](https://img.shields.io/badge/Gateway-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js Telemetry](https://img.shields.io/badge/Telemetry-Next.js-black?logo=next.js)](https://nextjs.org/)

</div>

## ⚠️ The Problem: Agents Hallucinate, Pipelines Crash

When you build autonomous AI agents using frameworks like LangChain, CrewAI, or AutoGen, you rely on strict data contracts (like **Pydantic**) to route logic. 

But LLMs are probabilistic. Eventually, an LLM will hallucinate a string instead of a float, or inject conversational text into a JSON key. When that hits your production pipeline, Pydantic throws a `ValidationError` and your agent crashes.

## 🚀 The Solution: Shift-Left Adversarial Fuzzing

**Intercept** is a CI/CD GitHub Action that acts as a structural security guard for your Agentic AI contracts. On every Pull Request, Intercept parses your Python schemas and uses an LLM to aggressively fuzz and attack those contracts with edge-case payloads.

If an AI hallucination can break your schema, we catch it *before* you merge.

---

## ✨ Features

* **🧠 Zero-Config AST Parsing:** No manual JSON schemas required. Intercept dynamically extracts your Pydantic models directly from your raw `.py` files.
* **🔑 Bring Your Own Key (BYOK):** Run fuzzing generation using your own `gemini`, `openai`, or `anthropic` keys. Zero compute markup.
* **⚡ Asynchronous execution:** Our API gateway handles complex adversarial generation loops in the background. Your GitHub Action runner will never timeout.
* **📊 Visual Audit Ledger:** Every structural diff, poisoned payload, and parser crash is logged to a persistent PostgreSQL database and viewable on your interactive Web Dashboard.

---

## 📦 Quick Start (GitHub Action)

Add Intercept to your repository in under 60 seconds. Drop this YAML configuration into `.github/workflows/intercept.yml`:

```yaml
name: Intercept AI Contract Guard
on: [pull_request]

jobs:
  security_audit:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Run Adversarial Fuzzer
        uses: your-username/intercept@v1.0.0
        with:
          schema_file: 'src/agents/schemas.py'
          schema_name: 'ToolExecutionModel'
          intercept_api_key: ${{ secrets.INTERCEPT_API_KEY }}
          llm_provider: 'gemini' 
          llm_api_key: ${{ secrets.GEMINI_API_KEY }}

```
## ⚙️ Action Inputs

| Input | Description | Required | Default |
| :--- | :--- | :---: | :--- |
| `schema_file` | Path to the Python file containing your Pydantic models. | **Yes** | - |
| `schema_name` | The exact class name of the Pydantic model to fuzz. | **Yes** | - |
| `intercept_api_key`| Your Intercept Organization API Key. | **Yes** | - |
| `llm_api_key` | Your LLM Provider API Key (Requires billing enabled). | **Yes** | - |
| `llm_provider` | The LLM to use for adversarial generation (`gemini`, `openai`, `anthropic`). | No | `gemini` |

---


## 🖥️ The Telemetry Dashboard

Intercept doesn't just fail your CI build and leave you guessing. Every execution streams metrics directly to the **Intercept Dashboard**.

Expand any failed test run to see a side-by-side split pane of your **Expected Pydantic Structure** against the exact **Poisoned Adversarial Payload** that broke it.

*(Note: Create your account and get your `INTERCEPT_API_KEY` at (https://intercept-landing-iota.vercel.app))*

---

## 🏗️ Architecture

Intercept is built as a highly scalable micro-SaaS:
1. **The Runner (`/action`):** A Composite GitHub action running Python AST extractors.
2. **The Gateway (`/backend`):** A FastAPI server executing asynchronous background workers and connection pooling.
3. **The Ledger (`Supabase`):** Multi-tenant PostgreSQL managing isolated organization telemetry.
4. **The UI (`/frontend`):** A Next.js application utilizing Recharts and real-time state management.

---

## 🤝 Contributing

We welcome contributions from the Agentic AI community. Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
