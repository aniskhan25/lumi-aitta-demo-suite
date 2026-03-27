# lumi-aitta-demo-suite

An Aitta-first demo and benchmark suite built around an OpenAI-compatible chat completions interface.

## What this repo includes

- `demos/smoke_test.py`: validate credentials, endpoint routing, model selection, and basic latency.
- `demos/rag_demo.py`: local grounded document Q&A with simple lexical retrieval and token-budget reporting.
- `demos/extraction_demo.py`: structured JSON extraction from free text samples.
- `demos/multiturn_demo.py`: client-managed conversational memory with recent turns plus an older-turn summary.
- `demos/reasoning_candidates_demo.py`: multi-candidate reasoning with `n` completions and simple selection strategies.
- `demos/batch_summarization_demo.py`: folder-to-JSONL or CSV summarization.
- `benchmarks/benchmark_openai.py`: whole-response latency and concurrency benchmark for OpenAI-compatible endpoints.
- `benchmarks/benchmark_reasoning.py`: compare `n=1/3/5` reasoning workflows.
- `reports/generate_summary.py`: generate a Markdown capability report from benchmark JSON and demo artifacts.

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   The transport layer uses the standard library for HTTP, so no `openai` SDK is required.

2. Copy `config/aitta.env.example` to `config/aitta.env` or export equivalent environment variables.

3. Edit `config/models.yaml` if you want to add more model aliases or per-model API-key variables.

## Quick start

Run the smoke test in discovery mode:

```bash
python demos/smoke_test.py --model-key poro_70b_instruct
```

Run direct mode explicitly:

```bash
python demos/smoke_test.py --mode direct --base-url https://example/v1 --api-key "$AITTA_API_KEY"
```

Run the demo suite wrapper:

```bash
bash run_demo_suite.sh
```

Run the benchmark suite wrapper:

```bash
bash run_benchmark_suite.sh
```

## Design notes

- Aitta discovery is treated as a first-class integration path through `clients/aitta_discovery.py`.
- Streaming is disabled for the Aitta path by design.
- Conversation continuity is handled client-side through the `messages` payload.
- Multi-candidate reasoning uses `n` completions instead of repeated independent requests.

## Limitations

- The discovery adapter is intentionally defensive because `aitta-client` may expose slightly different method names across environments. If your local API differs, update the adapter methods in `clients/aitta_discovery.py`.
- Token estimation in the demos uses a lightweight heuristic for budgeting, not model-specific tokenization.
