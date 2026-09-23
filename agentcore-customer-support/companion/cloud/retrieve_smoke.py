import os
import boto3

client = boto3.client(
    "bedrock-agent-runtime", region_name=os.environ["AWS_REGION"]
)
result = client.retrieve(
    knowledgeBaseId=os.environ["KB_ID"],
    retrievalQuery={"text": "What are the Platinum benefits?"},
)
for item in result.get("retrievalResults", []):
    print(item.get("content", {}).get("text", ""))
