"""Offline request validation exercise and reference solution."""
def validate_request(payload):
    if not isinstance(payload, dict):
        return {"valid": False, "error": "Expected a JSON object."}
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        return {"valid": False, "error": "Prompt must be text."}
    return {"valid": True}

def format_order(order):
    tracking = order.get("tracking_number")
    suffix = f"Tracking: {tracking}." if tracking else "Tracking information is unavailable."
    return f"Order {order['order_id']} is {order['status']}. {suffix}"

if __name__ == "__main__":
    print(validate_request({"prompt": "Track ORD-001"}))
    print(validate_request({"prompt": "   "}))
