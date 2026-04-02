# arch-analyser — CLAUDE.md

## What this project is
A 5-prompt Plan-and-Execute pipeline that analyses software architecture descriptions.
Implements patterns from "Prompt Engineering" (Sadot, 2024).

## How to run
`arch-analyser "payment processing system, 1M TPS, PostgreSQL, Kafka"`

## Pipeline order
p1_context → p2_decompose → p3_patterns → p4_risks → p5_synthesis
Each prompt module exposes a single function: `run(context: dict) -> dict`

## API key
Set ANTHROPIC_API_KEY in .env — never hardcoded.

## Testing
`pytest tests/` — all tests use fixtures, no live API calls.

## Domain examples
Use airline/PSS inputs to demonstrate domain-calibrated output:
- "departure control system, 500 concurrent check-ins, PostgreSQL, Redis, Kafka, SITA integration"
- "baggage reconciliation system, real-time, 10k bags/hour, event-sourced, Oracle"