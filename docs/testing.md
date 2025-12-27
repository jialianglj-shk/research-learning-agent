# Testing 

## How to run test
`uv run pytest -q`

## Unit testing design
- No network calls in unit tests
- Mock `request_json`
- Separate tests for http retry logic vs tool parsing vs fallback behavior