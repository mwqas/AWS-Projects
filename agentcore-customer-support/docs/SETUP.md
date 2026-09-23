# Windows setup and cloud progression

## Offline foundation

Install Python 3.13, Git, and a code editor. Verify `python --version` and `git --version`. The offline exercises need no packages.

## Reference dependencies

Install uv using its official instructions linked in RESOURCES.md. From the repository root:

```powershell
cd agentcore-customer-support/companion/reference
uv sync --locked --python 3.13
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\agentcore.exe --help
```

Use the lockfile for the classroom version. It includes the Python AgentCore starter toolkit. Avoid installing both Python and npm AgentCore CLIs.

## AWS account

Install AWS CLI v2 and configure your own AWS-supported sign-in method/profile. Prefer temporary credentials. Check the active account locally using `aws sts get-caller-identity --profile YOUR_PROFILE`. Do not commit the output or your `.aws` directory.

Create a budget alert and review the current pricing for the services you choose. Promotional credit is not a spending cap; alerts do not automatically stop resources. Cloud experiments should use fictional data and mock refunds.

## Provision in order

1. Choose a supported AWS region and accessible Bedrock model.
2. Create IAM roles with only the required permissions.
3. Deploy the order/refund Lambda fixtures and configure Gateway tool schemas.
4. Add and independently test an API-based Gateway target as required by the reviewer rubric. The Lambda fixtures alone do not satisfy this criterion.
5. Create a Knowledge Base, upload the sample catalog, ingest it, and confirm Retrieve returns chunks.
6. Create Memory strategies and confirm their actor-scoped namespace templates.
7. Configure Browser and Code Interpreter access for the runtime role.
8. Configure and deploy the reference agent with the Python toolkit, then invoke it.

The book contains the detailed labs. Use current AWS documentation for account- and region-specific console choices.

## Configuration

`.env.example` lists names; `main.py` does not automatically load a `.env` file. Set process variables for local runs, and pass the same values through the toolkit's runtime deployment configuration for cloud runs. A variable set only in local PowerShell does not automatically configure a deployed runtime.

```powershell
$env:AWS_PROFILE = 'YOUR_PROFILE'
$env:AWS_REGION = 'us-east-1'
$env:MODEL_ID = 'YOUR_SUPPORTED_MODEL_ID'
$env:GATEWAY_URL = 'https://YOUR_GATEWAY_HOST/mcp'
$env:KB_ID = 'YOUR_KNOWLEDGE_BASE_ID'
$env:MEMORY_ID = 'YOUR_MEMORY_ID'
.\.venv\Scripts\agentcore.exe configure --help
.\.venv\Scripts\agentcore.exe deploy --help
```

Use the book's deployment chapter and your installed CLI help for exact configuration flags. Keep generated deployment configuration private. After the lab, use the toolkit's destroy workflow and separately inventory and remove unused Gateway, Lambda, Knowledge Base/vector storage, Memory, S3, logs, and other resources; runtime destruction alone is not a complete cleanup.
