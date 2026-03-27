# Aitta Capability Report

## Supported Behaviors

- OpenAI-compatible chat completions transport.
- Discovery-first or direct URL backend selection.
- Client-managed conversation history through `messages`.
- Multi-candidate completions through `n`.
- Non-streaming request path for Aitta demos and benchmarks.

## Benchmarks

## Demo Artifacts

- No demo artifact files were supplied.

## Caveats

- Streaming is intentionally disabled in the Aitta path.
- Memory continuity is handled client-side by rebuilding `messages` on each turn.
- Token budgeting in the demos uses heuristics and should be validated against the target model.
