# Prices observed at experiment setup

Source: GET <https://openrouter.ai/api/v1/models>, the four used-model records are retained in [used-model-prices.json](used-model-prices.json). USD per million tokens, standard context tier. Cache write/read are separate prices.

| OpenRouter ID | Role | Input | Output | Cache read | Cache write (5m) |
|---|---|---:|---:|---:|---:|
| anthropic/claude-haiku-5.5 | executor | $0.1 | $0.5 | $0.01 | $0.125 |
| anthropic/claude-opus-4.8 | paper-default-editor comparison | $5 | $25 | $0.5 | $6.25 |
| anthropic/claude-sonnet-4.6 | first editor/composer | $3 | $15 | $0.3 | $3.75 |
| anthropic/claude-haiku-4.5 | incidental OpenCode session titles | $1 | $5 | $0.1 | $1.25 |

Haiku 5.5 has a higher tier at >=100,000 prompt tokens: see [used-model-prices.json](used-model-prices.json). The actual billed total comes from the key meter in [cost.md](cost.md); step-finish estimates omit title calls.
