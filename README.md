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

1. On LUMI, create the virtual environment through the container-backed installer:

   ```bash
   bash scripts/install_venv.sh
   ```

2. Load the repo env file and activate the venv:

   ```bash
   source env/lumi-env.sh
   export AITTA_API_KEY="replace_me"
   export AITTA_BASE_URL="https://api-staging-aitta.2.rahtiapp.fi/model/LumiOpen~Poro-34B-chat/openai/v1/"
   export AITTA_MODEL="LumiOpen/Poro-34B-chat"
   source "${AITTA_VENV}/bin/activate"
   ```

   Do not commit real API keys into the repository. Keep them in your shell environment or in a separate local-only secrets file that is not tracked by git.

3. Optionally copy `config/aitta.env.example` to `config/aitta.env` if you want a local config file instead of exporting the variables in your shell.

Only three settings matter for the normal path:

- `AITTA_API_KEY`
- `AITTA_BASE_URL`
- `AITTA_MODEL` (optional if you keep the default)

The venv installer follows the same mechanism as the Anemoi LUMI repo: source `env/lumi-env.sh`, load `lumi-aif-singularity-bindings`, and create the venv inside the configured container with `--system-site-packages`.

## Quick start

Run the smoke test against the OpenAI-compatible endpoint:

```bash
python demos/smoke_test.py
```

Run the same smoke test with streaming:

```bash
python demos/smoke_test.py --stream
```

Run the demo suite wrapper:

```bash
bash run_demo_suite.sh
```

Run the benchmark suite wrapper:

```bash
bash run_benchmark_suite.sh
```

Run the benchmark matrix for throughput, delay, and concurrency:

```bash
python benchmarks/run_matrix.py
```

Summarize the matrix into a compact capacity report:

```bash
python benchmarks/summarize_matrix.py reports/example_outputs/benchmark_matrix.json
```

Recommended TinyLlama benchmark plan:

- Latency baseline: `requests=20`, `concurrency=1`
- Concurrency sweep: `1 2 4 8`
- Token sweep: `64 128 256`
- Keep `n=1`
- Use `--repeats 2` or `--repeats 3` when you want noise detection

Example:

```bash
python benchmarks/run_matrix.py \
  --requests 20 \
  --baseline-concurrency 1 \
  --concurrency-values 1 2 4 8 \
  --max-token-values 64 128 256 \
  --repeats 2
```

Validated LUMI sequence for running the matrix:

```bash
module purge
module use /appl/local/csc/modulefiles
module load pytorch

source env/lumi-env.sh
source "${AITTA_VENV}/bin/activate"

python benchmarks/run_matrix.py \
  --requests 20 \
  --baseline-concurrency 1 \
  --concurrency-values 1 2 4 8 \
  --max-token-values 64 128 256 \
  --repeats 2
```

Notes:

- `config/aitta.env` is loaded automatically by the Python scripts.
- Keep `AITTA_API_KEY` in `config/aitta.env` without surrounding quotes.

## Design notes

- The repo uses the OpenAI-compatible endpoint directly.
- Direct smoke tests can stream tokens.
- Streaming support depends on the model endpoint. The smoke test supports it.
- Conversation continuity is handled client-side through the `messages` payload.
- Multi-candidate reasoning uses `n` completions instead of repeated independent requests.

## Limitations

- Token estimation in the demos uses a lightweight heuristic for budgeting, not model-specific tokenization.
