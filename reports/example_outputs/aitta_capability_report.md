# Aitta Capability Report

## Supported Behaviors

- OpenAI-compatible chat completions transport.
- Direct URL backend selection by default, with optional discovery.
- Client-managed conversation history through `messages`.
- Multi-candidate completions through `n`.
- Direct smoke-test streaming support.

## Benchmarks

## Demo Artifacts

- No demo artifact files were supplied.

## Caveats

- Benchmark scripts currently measure whole-response latency rather than token-stream cadence.
- Memory continuity is handled client-side by rebuilding `messages` on each turn.
- Token budgeting in the demos uses heuristics and should be validated against the target model.
