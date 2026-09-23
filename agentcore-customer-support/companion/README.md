# AgentCore learning book companion

Start with the PDF. The editable book source is included as book.md.

## Offline practice

From this companion directory run:

    python offline/validation.py
    python offline/loyalty.py
    python -m unittest discover -s offline -p "test_*.py" -v

These exercises do not contact AWS. The calculator explicitly labels its result offline_exercise.

## Full reference implementation

reference/main.py is the complete September 20 classroom agent, with the pinned lockfile, dependency manifest, original fixture Lambda code, catalog and original tests. Preserve the supplied LICENSE.txt. This code includes demo-specific choices: unauthenticated Gateway transport, caller-supplied customer identity, tool consent bypass, a training Gold-policy mismatch and a private-member browser lifecycle adapter. Read the book's production chapter before adapting it.

To reproduce dependencies, install Python 3.13 and uv, enter reference and run uv sync --locked --python 3.13. Offline boundary tests run with .venv/Scripts/python.exe -m unittest discover -s tests -v on Windows. Tests in reference require its dependency environment; they are separate from the book exercises.

You must create resources in your own AWS account, configure an execution role and supply GATEWAY_URL, KB_ID, MEMORY_ID, AWS_REGION and MODEL_ID. No credentials, historical resource manifest, deployment YAML or account-specific provisioning helpers are included. A .env file is not automatically loaded by main.py.

## CLI capture

cloud/invoke_cli.py executes the real Python toolkit CLI. Run it from the directory containing your generated AgentCore configuration. Pass an explicit --cli path and your prompt and customer. Keep the same --session for a follow-up; use a different --session and the same customer for cross-session recall. Cloud tests incur usage and mock-refund tests must never point at a real payment service.

The book is an educational guide, not an automatic account installer or production payment system. Review SDK changes and official documentation before upgrading.
