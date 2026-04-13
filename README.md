# lumi-aitta-demo-suite

An Aitta benchmark repo built around an OpenAI-compatible chat completions interface.

The current recorded evaluations in this repo use `TinyLlama/TinyLlama-1.1B-Chat-v1.0`.

## Setup

1. Install the environment once:

   ```bash
   bash scripts/install_venv.sh
   ```

2. For each new LUMI shell, load the runtime environment and activate the venv:

   ```bash
   module purge
   module use /appl/local/csc/modulefiles
   module load pytorch

   source env/lumi-env.sh
   source "${AITTA_VENV}/bin/activate"
   ```

3. Set the endpoint values either manually:

   ```bash
   export AITTA_API_KEY=replace_me
   export AITTA_BASE_URL=https://api-staging-aitta.2.rahtiapp.fi/openai/v1/
   export AITTA_MODEL="TinyLlama/TinyLlama-1.1B-Chat-v1.0"
   ```

   or through a local config file:

   ```bash
   cp config/aitta.env.example config/aitta.env
   ```

   `config/aitta.env` is loaded automatically by the Python scripts. Do not commit real API keys.
   The validated staging endpoint for this repo is `https://api-staging-aitta.2.rahtiapp.fi/openai/v1/`.

## Quick start

Run a single evaluation:

```bash
python benchmarks/benchmark_openai.py --requests 1 --concurrency 1
```

Run the full matrix:

```bash
python benchmarks/run_matrix.py \
  --requests 20 \
  --baseline-concurrency 1 \
  --concurrency-values 1 2 4 8 \
  --max-token-values 64 128 256 \
  --repeats 2
```

Summarize the matrix:

```bash
python benchmarks/summarize_matrix.py reports/example_outputs/benchmark_matrix.json
```

Recorded TinyLlama matrix result from this run:

- baseline_avg_latency_seconds: `2.604`
- baseline_p95_latency_seconds: `7.723`
- baseline_over_3s_rate: `0.075`
- baseline_over_10s_rate: `0.075`
- baseline_over_30s_rate: `0.05`
- stable_concurrency_at_p95_limit: `1`
- baseline_p95_spread_seconds: `10.72`
- best_token_throughput_tokens_per_second: `108.969`
- best_token_throughput_max_completion_tokens: `256`

Observed interpretation:

- `concurrency=1` looks usable for single-user interactive work in this run.
- The latency cliff still begins at `concurrency=2`, where p95 jumps to about `30.9s`.
- Interactive multi-user use is still not supported by this run.
- `concurrency=1` remains the only reasonable operating assumption for TinyLlama on this path.
