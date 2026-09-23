import os
from strands import Agent
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke(payload, context=None):
    prompt = payload.get("prompt") if isinstance(payload, dict) else None
    if not isinstance(prompt, str) or not prompt.strip():
        return {"error": "Provide a non-empty prompt."}
    model = BedrockModel(
        model_id=os.environ["MODEL_ID"],
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )
    agent = Agent(model=model, callback_handler=None)
    result = await agent.invoke_async(prompt)
    text = "\n".join(
        block["text"] for block in result.message.get("content", [])
        if block.get("text")
    )
    return {"response": text}

if __name__ == "__main__":
    app.run()
