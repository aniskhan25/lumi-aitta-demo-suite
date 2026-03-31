# lumi-aitta-demo-suite

An Aitta benchmark repo built around an OpenAI-compatible chat completions interface.

## What this repo includes

- `benchmarks/benchmark_openai.py`: whole-response latency and concurrency benchmark for OpenAI-compatible endpoints.
- `benchmarks/benchmark_reasoning.py`: compare `n=1/3/5` reasoning workflows.
- `benchmarks/run_matrix.py`: run a latency, concurrency, and token-budget matrix.
- `benchmarks/summarize_matrix.py`: summarize a matrix run into a compact capacity report.
- `reports/generate_summary.py`: generate a Markdown report from benchmark JSON files.

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

Run a single whole-response benchmark:

```bash
python benchmarks/benchmark_openai.py --requests 1 --concurrency 1
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

Recorded TinyLlama matrix result from this run:

- baseline_avg_latency_seconds: `2.412`
- baseline_p95_latency_seconds: `3.663`
- baseline_over_3s_rate: `0.075`
- baseline_over_10s_rate: `0.05`
- baseline_over_30s_rate: `0.05`
- stable_concurrency_at_p95_limit: `None`
- best_token_throughput_tokens_per_second: `108.6`
- best_token_throughput_max_completion_tokens: `256`

Observed interpretation:

- The endpoint works, but latency is unstable even at `concurrency=1`.
- Interactive multi-user use is not supported by this run.
- `concurrency=1` is the only reasonable operating assumption for TinyLlama on this path.

## Design notes

- The repo uses the OpenAI-compatible endpoint directly.
- Multi-candidate reasoning is benchmarked through `n`.
- The matrix runner is meant for burst-style concurrency sweeps, not paced load testing.

## Limitations

- The current benchmarks measure whole-response latency, not token-stream cadence.
