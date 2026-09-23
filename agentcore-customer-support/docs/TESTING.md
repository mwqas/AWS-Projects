# Tests and submission evidence

## Levels of confidence

Offline exercise tests validate Python logic. Reference boundary tests mock external services. Neither proves that a deployed AWS integration works. A live scenario must show the command, nonempty response, and appropriate tool execution evidence.

From the repository root run:

```powershell
python -m unittest discover -s agentcore-customer-support/companion/offline -p "test_*.py" -v
python scripts/check_resources.py
```

Run the 22 reference tests using the locked environment described in SETUP.md. GitHub Actions intentionally runs only the standard-library exercises and resource checks.

## Capture actual CLI invocation

From `companion/reference`, after configuring and deploying your own runtime:

```powershell
python ../cloud/invoke_cli.py --cli .venv/Scripts/agentcore.exe --customer learner-001 --session 11111111-1111-4111-8111-111111111111 --prompt "Hello. What can you help me with?" --output invoke-output-runtime.txt
```

The helper prints the `agentcore invoke` command and captures its actual output. Read the entire result: a successful CLI exit does not by itself prove application or tool success. For evidence, capture the visible command and output with Windows Snipping Tool. Remove private identifiers and secrets before sharing while retaining enough context to assess the result.

## Six scenarios

| Scenario | Action | Required proof |
| --- | --- | --- |
| Order | Ask for an order from your fixture | Gateway tool name and structured order/tracking result |
| Refund | Request an eligible mock refund from a fixture | Distinct successful Gateway tool and structured refund result |
| RAG | Ask a catalog/policy question | Retrieve tool execution, nonempty chunks, grounded answer |
| Memory | Give name/preferences in session A; ask for them in session B | Same customer ID, different session IDs, correctly recalled details |
| Calculation | Ask for 4,250 Gold points against $150 | Sandbox execution and `points_redeemed`, `tier_discount_pct`, `final_total`, `remaining_points` |
| Browser | Ask for a changing token on a public page you control | AgentCore Browser tool execution, URL, current token/content |

The teaching calculator produces 4,000 redeemed points, a 10% tier discount, $99 final total, and 250 unspent points for the standard-category example. Confirm the catalog/business rules before using this policy elsewhere. A tier-only fallback is failure-path evidence, not proof of a working sandbox.

**Additional Gateway criterion:** order and refund are both Lambda fixtures. Also invoke an API-based target and capture its successful response. Two Lambda tools do not demonstrate one API target plus one Lambda target.

Memory extraction is asynchronous. Wait for records to become available before the recall test; inspect Memory records when troubleshooting. Do not keep the same runtime session and claim cross-session recall.

## Failure-path checks

- Missing or whitespace KB_ID produces a descriptive configuration message.
- Invalid Gateway endpoint produces safe logs and a meaningful failure response.
- Unavailable Code Interpreter triggers the documented tier-only fallback.
- Invalid payloads and loyalty inputs fail clearly.

## CloudWatch screenshot

Capture the alarm details showing its name, namespace/metric, dimensions, statistic, period, threshold, evaluation periods, missing-data setting, and configured actions. An `OK` badge alone is not configuration evidence. A metric alarm is also distinct from a billing budget alert.

## Submission checklist

- [ ] Complete main.py and reproducible dependency versions.
- [ ] Visible successful `agentcore invoke` command and output.
- [ ] Six scenario screenshots or raw logs; memory includes both sessions.
- [ ] Successful API-based and Lambda-based Gateway targets.
- [ ] Calculation uses Code Interpreter rather than only fallback.
- [ ] Browser evidence comes from AgentCore Browser.
- [ ] Alarm configuration screenshot.
- [ ] 200–400-word reflection: design decision, challenge/solution, specific production extension.

No live account evidence is included in this public resource package. Generate evidence from your own deployment and never present expected examples as executed results.
