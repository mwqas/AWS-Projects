"""Run the actual Python AgentCore CLI with safely separated arguments.
Run from your configured agent directory. Cloud invocation can incur charges.
"""
import argparse,json,subprocess,uuid,sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("--cli",required=True,help="Path to Python toolkit agentcore executable")
p.add_argument("--customer",required=True)
p.add_argument("--session",default=None)
p.add_argument("--prompt",required=True)
p.add_argument("--output",default="invoke-output.txt")
a=p.parse_args()
session=a.session or str(uuid.uuid4())
payload=json.dumps({"prompt":a.prompt,"customer_id":a.customer,"session_id":session})
command=[str(Path(a.cli).resolve()),"invoke",payload,"--session-id",session]
display="agentcore invoke '"+payload+"' --session-id "+session
print(display,flush=True)
result=subprocess.run(command,text=True,encoding="utf-8",errors="replace",stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
print(result.stdout)
Path(a.output).write_text(display+"\n\n"+result.stdout+f"\nCLI exit code: {result.returncode}\n",encoding="utf-8")
print("Inspect application and tool results; exit code alone is insufficient proof.")
sys.exit(result.returncode)
