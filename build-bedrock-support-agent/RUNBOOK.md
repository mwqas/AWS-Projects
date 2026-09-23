# Configure, test, and deploy

## 1. Install the locked dependencies

Run these commands from this project directory:

```powershell
uv sync --locked --python 3.13
uv run python -m unittest discover -s tests -v
uv run agentcore --help
```

Use the **Python bedrock-agentcore-starter-toolkit** included in the lockfile. Do not install a second AgentCore CLI that provides the same executable name.

## 2. Prepare your AWS account

Configure AWS CLI v2 with your own profile and temporary credentials. Confirm the account locally before provisioning:

```powershell
$env:AWS_PROFILE = 'YOUR_PROFILE'
$env:AWS_REGION = 'us-east-1'
aws sts get-caller-identity
```

Choose a region and model available to your account. Create a budget alert before paid experiments. Credits and alerts do not impose a hard spending cap.

## 3. Create the dependencies

Follow the resource-creation labs in the [book](../agentcore-customer-support/companion/book.md):

1. Deploy `lambda/order_tracker.py` and `lambda/refund_processor.py` as separate Python Lambda functions. Use each module's `lambda_handler` entrypoint and its required IAM permissions.
2. Create an AgentCore Gateway, attach the Lambda targets using the supplied schema, and verify tool discovery. Add and test an API-based target separately when following the reviewer rubric.
3. Create a Bedrock Knowledge Base, upload `product_catalog.txt` to its source, ingest it, and confirm retrieval returns content.
4. Create AgentCore Memory with semantic and preference strategies and actor-scoped namespaces.
5. Create a runtime execution role with permissions for the selected model and the required Memory, Knowledge Base, Gateway, Browser, Code Interpreter, and logging operations.

This repository supplies application code; it does not automatically provision these resources. Use the linked AWS documentation for current service and region choices.

## 4. Configure the application

The names in `.env.example` are a reference. `main.py` does **not** automatically load `.env` files.

```powershell
$env:MODEL_ID = 'YOUR_SUPPORTED_MODEL_ID'
$env:GATEWAY_URL = 'https://YOUR_GATEWAY_HOST/mcp'
$env:KB_ID = 'YOUR_KNOWLEDGE_BASE_ID'
$env:MEMORY_ID = 'YOUR_MEMORY_ID'
```

These local variables do not automatically propagate to a deployed runtime. Supply the same configuration through your toolkit deployment's environment settings. Do not put AWS access keys in the application or container.

## 5. Configure and deploy Runtime

Inspect the installed toolkit options first:

```powershell
uv run agentcore configure --help
uv run agentcore configure
uv run agentcore deploy --help
```

Select `main.py` as the entrypoint, the intended region, and your runtime execution role. Follow the book's deployment chapter to supply runtime environment variables, then run the configured `agentcore deploy` command. Keep generated `.bedrock_agentcore` files local.

## 6. Capture a real response

After successful deployment, use the capture helper from this directory on Windows:

```powershell
uv run python scripts/invoke_cli.py --cli .venv/Scripts/agentcore.exe --customer learner-001 --session 11111111-1111-4111-8111-111111111111 --prompt "Hello, what can you help me with?" --output invoke-output-runtime.txt
```

On Linux/macOS the CLI path is `.venv/bin/agentcore`. The helper executes the actual Python toolkit CLI and records its command and output. Inspect tool results as well as the CLI exit code.

Follow the [testing guide](../agentcore-customer-support/docs/TESTING.md) for order tracking, refunds, RAG, cross-session memory, calculations, and browsing. For memory, use a different session ID with the same customer ID for recall. For calculations, prove sandbox execution rather than the fallback. Capture the CloudWatch alarm's full configuration as a separate artifact.

## 7. Clean up

Review `uv run agentcore destroy --help` before using the toolkit's destroy workflow on the intended runtime. Separately inventory and remove unused Gateway targets, Gateway, Lambda, Memory, Knowledge Base and vector storage, source buckets, logs, and any other resources created for the lab. Runtime deletion alone does not remove every dependent resource.
