# 🛡️ Intercept 

**Enterprise-Grade LLM Contract Fuzzing & Hallucination Prevention.**

[![GitHub Action](https://img.shields.io/badge/GitHub%20Action-Ready-blue?style=for-the-badge&logo=github)](https://github.com/features/actions)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)

## ⚠️ The Problem: Silent AI Failures
When building applications powered by Large Language Models (LLMs), developers rely on strict JSON schemas (like Pydantic models) to ensure the AI returns data in a predictable format. 

However, under edge-case prompts or ambiguous inputs, LLMs will silently hallucinate data types, ignore constraints (like negative numbers or unsupported currencies), or drop required fields entirely just to make the JSON parse correctly. **This corrupts production databases and breaks downstream APIs.**

## 🎯 The Solution: Intercept
Intercept is a dual-LLM adversarial testing suite. It uses an AI-driven fuzzer to dynamically generate malicious edge-case prompts designed specifically to break your JSON schemas. It then fires those attacks at your application's AI engine, logs the hallucination rate, and permanently stores the telemetry.

If an LLM breaks the contract, Intercept catches it before your users do.

---

## ✨ Core Features

* 🧠 **Dynamic Schema Ingestion:** No hardcoded types. Pass any valid JSON schema, and the fuzzer instantly understands how to attack it.
* 🚦 **CI/CD Security Gate:** A drop-in GitHub Action that runs fuzz tests on every Pull Request. If the hallucination rate spikes, the PR is blocked.
* 📊 **Next.js Telemetry Dashboard:** A beautiful, real-time React dashboard displaying global failure rates, recent fuzzing sessions, and hallucination trends.
* 🧪 **Live Fuzzing Sandbox:** Paste a schema directly into the browser and watch the adversarial engine attack it in real-time.
* 🗄️ **Persistent PostgreSQL Analytics:** All test cases and failures are permanently logged via SQLAlchemy for compliance and auditing.

---

## 🏗️ Architecture

Intercept operates on a decoupled, microservice-ready architecture:

```text
[ Developer / CI/CD Pipeline ]
       │
       ▼ (Sends Target JSON Schema)
[ FastAPI Orchestrator ] 
       │
       ├──► [ Intercept Fuzzer ] (Generates Malicious Prompts)
       │
       └──► [ Validation Engine ] (Executes & Audits Responses)
       │
       ▼ (Logs Metrics)
[ PostgreSQL Database ] ◄── (Reads Analytics) ── [ Next.js Dashboard ]