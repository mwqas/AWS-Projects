# Six-week learning path

| Week | Focus | Estimated time | Milestone and understanding check |
| --- | --- | --- | --- |
| 1 | Python, JSON, functions, exceptions, Decimal, Git | 8–10 hours | Pass offline tests; explain why money should not use binary floats. |
| 2 | AWS identity, regions, Bedrock models, Strands, Runtime | 8–10 hours | Deploy a minimal agent; explain runtime role versus local login. |
| 3 | Lambda tools, API targets, Gateway, MCP | 9–12 hours | Demonstrate both target types; explain discovery versus execution failures. |
| 4 | RAG and Memory | 9–12 hours | Retrieve source text and recall preferences across two sessions; explain why these solve different problems. |
| 5 | Code Interpreter and Browser | 8–10 hours | Prove sandbox execution and live page reading; identify fallback behavior. |
| 6 | Monitoring, failure handling, evidence, production design | 8–11 hours | Capture all tests and alarm configuration; explain one security boundary and one cost control. |

For each module: predict, run, inspect, explain, and change one input. Use the book's chapter exercises and answer guide. Intermediate learners can focus on weeks 2–6; advanced learners should prioritize failure boundaries, actor isolation, policy consistency, and upgrade testing.

## Mini-projects

1. Add a malformed-order response test.
2. Explain the loyalty calculation for 4,250 Gold points and a $150 subtotal.
3. Make Gateway unavailable and inspect the safe error response.
4. Ask a policy question with no relevant retrieved chunk; ensure the answer admits missing evidence.
5. Store a preference in session A; retrieve it in session B with the same customer, then verify another customer cannot access it.
6. Read a changing token on a public page you control through Browser.
7. Draft a production design that authenticates customers, checks ownership at the backend, and makes refunds idempotent.

## Feynman final assessment

Without reading the code, teach a new learner how one user message reaches Runtime, selects a tool, receives a result, and saves useful memory. Explain where authorization belongs, what happens when a dependency fails, and which logs prove each claim. Then trace the explanation through actual code and correct any gaps.
