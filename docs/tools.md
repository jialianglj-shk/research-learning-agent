# Tool Use Design (work in progress)

## Tool contract
- Input: `query`, `top_k`
- Output normalized to `{title, url, snippet}`
- Errors normalized to `ToolHTTPError` -> `ToolResult.error`

## Implemented tools
- Serper web search
- DDG IA fallback for web
- YouTube search
- docs_search users Serper + site queries

## Tool failure handling
- timeout + retries
- what is considered retryable
- how failure is represented

## Current Tool Use Capability
- The web/video/doc search results are only used as the agent answer (e.g. search web site -> angent answer says "this web site can help with your query")
- Future goal is to allow agent use the tool results to generate answer (e.g. search web site -> website conent feed to LLM as context/external knowledge -> agent generate answer)