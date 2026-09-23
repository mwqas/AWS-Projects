"""Offline contract tests: real SDK imports, mocked AWS/MCP/model boundaries."""
import asyncio
import contextlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import main
from strands.models.model import Model


def message(role, text):
    return {"role": role, "content": [{"text": text}]}


def memory_mock():
    client = MagicMock()
    client.get_memory_strategies.return_value = [
        {"type": "SEMANTIC", "namespaces": ["cs_agent/{actorId}/facts"]},
        {"type": "USER_PREFERENCE", "namespaces": ["cs_agent/{actorId}/preferences"]},
    ]
    client.retrieve_memories.return_value = [{"content": {"text": "Jane prefers concise responses"}}]
    client.gmdp_client.list_events.return_value = {"events": []}
    return client


class MemoryTests(unittest.TestCase):
    def test_namespace_templates_and_legacy_namespaces(self):
        client = MagicMock()
        client.get_memory_strategies.return_value = [
            {"memoryStrategyType": "SEMANTIC", "namespaceTemplates": ["facts/{actorId}"]},
            {"type": "USER_PREFERENCE", "namespaces": ["preferences/{actorId}"]},
        ]
        self.assertEqual(main.get_namespaces(client, "mem"),
                         {"SEMANTIC": "facts/{actorId}", "USER_PREFERENCE": "preferences/{actorId}"})
    def test_actual_strands_agent_calls_registered_hooks(self):
        observed = []
        class LocalModel(Model):
            def update_config(self, **kwargs):
                self.config = kwargs
            def get_config(self):
                return {"model_id": "offline-test"}
            async def structured_output(self, *args, **kwargs):
                raise NotImplementedError("Not used in this contract test")
                yield
            async def stream(self, messages, *args, **kwargs):
                observed.append(messages[-1]["content"][0]["text"])
                yield {"messageStart": {"role": "assistant"}}
                yield {"contentBlockStart": {"start": {}, "contentBlockIndex": 0}}
                yield {"contentBlockDelta": {"delta": {"text": "Your name is Jane."}, "contentBlockIndex": 0}}
                yield {"contentBlockStop": {"contentBlockIndex": 0}}
                yield {"messageStop": {"stopReason": "end_turn"}}
                yield {"metadata": {"usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2}, "metrics": {"latencyMs": 1}}}
        client = memory_mock()
        hook = main.MemoryHook("CUST-123", "s1", client, "mem")
        agent = main.Agent(model=LocalModel(), hooks=[hook], callback_handler=None)
        result = asyncio.run(agent.invoke_async("What is my name?"))
        self.assertIn("Jane", str(result))
        self.assertIn("Customer Context:", observed[0])
        self.assertEqual(client.create_event.call_args.kwargs["messages"][0], ("What is my name?", "USER"))

    def test_original_query_saved_without_retrieved_context(self):
        client = memory_mock()
        hook = main.MemoryHook("CUST-123", "session-A", client, "mem")
        agent = SimpleNamespace(messages=[message("user", "What is my name?")])
        event = SimpleNamespace(agent=agent)
        hook.retrieve_customer_context(event)
        self.assertIn("Customer Context:", agent.messages[0]["content"][0]["text"])
        namespaces = [call.kwargs["namespace"] for call in client.retrieve_memories.call_args_list]
        self.assertEqual(namespaces, ["cs_agent/CUST-123/facts", "cs_agent/CUST-123/preferences"])
        agent.messages.extend([
            {"role": "assistant", "content": [{"toolUse": {"name": "get_customer"}}]},
            {"role": "user", "content": [{"toolResult": {"content": [{"text": "profile"}]}}]},
            message("assistant", "Your name is Jane."),
        ])
        hook.save_support_interaction(event)
        self.assertEqual(client.create_event.call_args.kwargs["messages"],
                         [("What is my name?", "USER"), ("Your name is Jane.", "ASSISTANT")])

    def test_tool_results_do_not_trigger_retrieval(self):
        client = memory_mock()
        hook = main.MemoryHook("CUST-123", "s1", client, "mem")
        hook.retrieve_customer_context(SimpleNamespace(agent=SimpleNamespace(messages=[
            {"role": "user", "content": [{"text": "tool data"}, {"toolResult": {}}]},
        ])))
        client.retrieve_memories.assert_not_called()

    def test_second_customer_has_separate_namespaces(self):
        client = memory_mock()
        for actor in ("CUST-123", "CUST-456"):
            hook = main.MemoryHook(actor, "same-session", client, "mem")
            hook.retrieve_customer_context(SimpleNamespace(agent=SimpleNamespace(messages=[message("user", "Hello")])) )
        self.assertEqual(client.retrieve_memories.call_args.kwargs["namespace"], "cs_agent/CUST-456/preferences")

    def test_memory_failure_preserves_response_and_reports_warning(self):
        client = memory_mock()
        client.create_event.side_effect = RuntimeError("AWS unavailable")
        hook = main.MemoryHook("CUST-123", "s1", client, "mem")
        with self.assertLogs("CSAI_Agent", level="ERROR"):
            hook.save_support_interaction(SimpleNamespace(agent=SimpleNamespace(messages=[
                message("user", "Hi"), message("assistant", "Hello"),
            ])))
        self.assertIn("could not be saved", hook.warnings[0])

    def test_history_pagination_order_and_actor_scope(self):
        client = memory_mock()
        def event(n):
            return {"eventTimestamp": n, "eventId": str(n), "payload": [
                {"conversational": {"role": "USER", "content": {"text": str(n)}}},
                {"conversational": {"role": "ASSISTANT", "content": {"text": "ok"}}},
            ]}
        client.gmdp_client.list_events.side_effect = [
            {"events": [event(3), event(1)], "nextToken": "next"}, {"events": [event(2)]},
        ]
        history = main.session_history(client, "CUST-456", "s2")
        self.assertEqual([m["content"][0]["text"] for m in history[::2]], ["1", "2", "3"])
        self.assertEqual(client.gmdp_client.list_events.call_args.kwargs["actorId"], "CUST-456")
        self.assertEqual(client.gmdp_client.list_events.call_args.kwargs["nextToken"], "next")


class KnowledgeTests(unittest.TestCase):
    def test_retrieval_and_sources(self):
        client = MagicMock()
        client.retrieve.return_value = {"retrievalResults": [
            {"content": {"text": "Platinum: 15% discount"}, "location": {"s3Location": {"uri": "s3://catalog/products.txt"}}},
            {"content": {"text": "Priority support"}}, {"content": {}},
        ]}
        with patch.object(main, "KB_ID", "KB123"), patch.object(main, "clients", return_value=(None, None, client)):
            result = main.search_knowledge_base("Platinum")
        client.retrieve.assert_called_once_with(knowledgeBaseId="KB123", retrievalQuery={"text": "Platinum"})
        self.assertIn("\n---\n", result)
        self.assertIn("s3://catalog/products.txt", result)

    def test_missing_empty_and_failed_retrieval(self):
        for missing in (None, "", "  "):
            with patch.object(main, "KB_ID", missing), patch.object(main, "clients") as clients:
                self.assertIn("KB_ID is empty or missing", main.search_knowledge_base("x"))
                clients.assert_not_called()
        client = MagicMock()
        client.retrieve.return_value = {"retrievalResults": []}
        with patch.object(main, "KB_ID", "KB123"), patch.object(main, "clients", return_value=(None, None, client)):
            self.assertIn("No relevant", main.search_knowledge_base("x"))
            client.retrieve.side_effect = RuntimeError("denied")
            with self.assertLogs("CSAI_Agent", level="ERROR"):
                self.assertIn("unavailable", main.search_knowledge_base("x"))


class CalculatorTests(unittest.TestCase):
    def calculate(self, points, tier, total, category="standard"):
        interpreter = MagicMock()
        def run(method, params):
            self.assertEqual(method, "executeCode")
            self.assertEqual(params["language"], "python")
            self.assertTrue(params["clearContext"])
            stdout = io.StringIO()
            # Execute only the application's fixed, trusted calculator program.
            with contextlib.redirect_stdout(stdout):
                exec(params["code"], {})
            return {"stream": iter([{"result": {"isError": False, "content": [{"type": "text", "text": stdout.getvalue()}]}}])}
        interpreter.invoke.side_effect = run
        session = MagicMock()
        session.__enter__.return_value = interpreter
        with patch.object(main, "code_session", return_value=session):
            result = json.loads(main.calculate_loyalty_discount(points, tier, total, category))
        session.__exit__.assert_called_once()
        return result

    def test_course_example(self):
        result = self.calculate(4250, "Gold", 150)
        self.assertEqual(result["points_redeemed"], 4000)
        self.assertEqual(result["tier_discount"], "11.00")
        self.assertEqual(result["tier_discount_pct"], 10)
        self.assertEqual(result["final_total"], "99.00")
        self.assertEqual(result["total_savings"], "51.00")
        self.assertEqual(result["remaining_points"], 250)
        self.assertEqual(result["points_earned"], 99)
        self.assertEqual(result["balance_after_purchase"], 349)

    def test_redemption_cap_and_rounding(self):
        result = self.calculate(100000, "Platinum", 19.99, "device")
        self.assertEqual(result["points_redeemed"], 500)
        self.assertEqual(result["tier_discount"], "2.25")
        self.assertEqual(result["final_total"], "12.74")
        self.assertEqual(result["points_earned"], 25)
        self.assertEqual(self.calculate(499, "Silver", 10)["points_redeemed"], 0)
        self.assertEqual(self.calculate(500, "Gold", 9.99)["points_redeemed"], 0)
        self.assertEqual(self.calculate(500, "Gold", 0)["final_total"], "0.00")
        self.assertEqual(self.calculate(0, "Silver", 10.50, "fresh")["points_earned"], 52)

    def test_validation_before_sandbox(self):
        with patch.object(main, "code_session") as sandbox:
            for args in [(-1, "Gold", 100), (True, "Gold", 100), (1, "Invalid", 100),
                         (1, "Gold", float("nan")), (1, "Gold", -1), (1, "Gold", 1.001),
                         (1, "Gold", 100, "invalid")]:
                with self.subTest(args=args):
                    self.assertIn("error", json.loads(main.calculate_loyalty_discount(*args)))
            sandbox.assert_not_called()

    def test_unavailable_and_error_stream_fallback(self):
        for response in ({"stream": []}, {"stream": [{"result": {"isError": True}}]},
                         {"stream": [{"internalServerException": {}}]}):
            sandbox = MagicMock()
            sandbox.__enter__.return_value.invoke.return_value = response
            with patch.object(main, "code_session", return_value=sandbox), self.assertLogs("CSAI_Agent", level="ERROR"):
                result = json.loads(main.calculate_loyalty_discount(4250, "Gold", 150))
            self.assertTrue(result["partial"])
            self.assertEqual(result["final_total"], "135.00")
            self.assertNotIn("points_earned", result)
            self.assertIsNone(result["points_redeemed"])
            self.assertIsNone(result["remaining_points"])
            self.assertEqual(result["tier_discount_pct"], 10)


class EntryTests(unittest.TestCase):
    def test_gateway_failures_are_safe_and_actionable(self):
        for stage, error, expected in (
            ("enter", TimeoutError("SECRET_TOKEN"), "GATEWAY_TIMEOUT"),
            ("enter", ConnectionError("SECRET_TOKEN"), "GATEWAY_CONNECTION_FAILED"),
            ("list", RuntimeError("SECRET_TOKEN"), "GATEWAY_TOOL_LOADING_FAILED"),
        ):
            with self.subTest(stage=stage, error=type(error).__name__):
                mcp = MagicMock()
                if stage == "enter":
                    mcp.__enter__.side_effect = error
                else:
                    mcp.__enter__.return_value.list_tools_sync.side_effect = error
                with patch.multiple(main, GATEWAY_URL="https://dummy.invalid/mcp", KB_ID="kb", MEMORY_ID="mem"), \
                     patch.object(main, "clients", return_value=("model", memory_mock(), None)), \
                     patch.object(main, "MCPClient", return_value=mcp), \
                     patch.object(main, "Agent") as agent, self.assertLogs("CSAI_Agent", level="ERROR") as logs:
                    result = asyncio.run(main.invoke({"prompt": "Track ORD-001"}))
                self.assertEqual(result["error_code"], expected)
                self.assertIn("No order lookup or refund action was attempted", result["response"])
                self.assertIn("reference ID", result["response"])
                self.assertIn("endpoint", result["next_step"])
                self.assertNotIn("SECRET_TOKEN", json.dumps(result) + "".join(logs.output))
                agent.assert_not_called()
                if stage == "list":
                    mcp.__exit__.assert_called_once()

    def test_gateway_empty_discovery_is_not_silent_success(self):
        mcp = MagicMock()
        class Empty(list):
            pagination_token = None
        mcp.__enter__.return_value.list_tools_sync.return_value = Empty()
        with patch.object(main, "MCPClient", return_value=mcp), \
             self.assertLogs("CSAI_Agent", level="ERROR"), self.assertRaises(main.GatewayUnavailable):
            with main.gateway_connection():
                self.fail("Empty Gateway must not invoke the model")
        mcp.__exit__.assert_called_once()

    def test_gateway_audit_handles_api_and_lambda_envelopes_without_secret_fields(self):
        audit = main.ToolAuditHook("test-session")
        for name, payload in (
            ("order-tracker___get_order", {"order_id": "ORD-001", "status": "SHIPPED", "token": "SECRET"}),
            ("refund-processor___check_refund_status", {"statusCode": 200, "body": json.dumps({"refund_id": "REF-TEST", "status": "PROCESSING", "eta": "2-3 business days", "token": "SECRET"})}),
        ):
            audit.record(SimpleNamespace(tool_use={"name": name}, result={"status": "success", "content": [{"text": json.dumps(payload)}]}))
        self.assertEqual(audit.calls[0]["result"]["status"], "SHIPPED")
        self.assertEqual(audit.calls[1]["result"]["statusCode"], 200)
        self.assertEqual(audit.calls[1]["result"]["status"], "PROCESSING")
        self.assertNotIn("SECRET", json.dumps(audit.calls))

    def test_browser_stops_remote_session_after_connection_failure(self):
        client = MagicMock()
        client.generate_ws_headers.return_value = ("wss://example.com", {})
        playwright = MagicMock()
        playwright.chromium.connect_over_cdp = AsyncMock(side_effect=RuntimeError("blocked"))
        playwright.stop = AsyncMock()
        with patch.object(main, "BrowserClient", return_value=client):
            with main.managed_browser() as browser:
                browser._playwright = playwright
                with self.assertRaises(RuntimeError):
                    browser._execute_async(browser.create_browser_session())
        client.stop.assert_called_once()
        self.assertTrue(browser._loop.is_closed())

    def test_actual_agentcore_browser_owns_continuous_loop_and_registered_tool(self):
        client = MagicMock()
        client.generate_ws_headers.return_value = ("wss://example.com", {})
        playwright = MagicMock()
        playwright.chromium.connect_over_cdp = AsyncMock(return_value="remote-browser")
        playwright.stop = AsyncMock()
        with patch.object(main, "BrowserClient", return_value=client):
            with main.managed_browser() as browser:
                self.assertIsInstance(browser, main.AgentCoreBrowser)
                self.assertEqual(browser.region, main.REGION)
                self.assertTrue(browser._loop.is_running())
                browser._playwright = playwright
                self.assertEqual(browser._execute_async(browser.create_browser_session()), "remote-browser")
        client.stop.assert_called_once()
        self.assertTrue(browser._loop.is_closed())

    def test_input_and_missing_configuration(self):
        for payload in ([], {}, {"prompt": ""}, {"prompt": "Hi", "customer_id": "../other"}):
            self.assertIn("error", asyncio.run(main.invoke(payload)))
        with patch.object(main, "GATEWAY_URL", ""):
            result = asyncio.run(main.invoke({"prompt": "Hi"}))
            self.assertIn("Missing configuration", result["error"])

    def test_gateway_tools_hooks_response_and_cleanup(self):
        memory = memory_mock()
        gateway = MagicMock()
        class Page(list):
            def __init__(self, items, token):
                super().__init__(items)
                self.pagination_token = token
        gateway.list_tools_sync.side_effect = [Page(["order-tool"], "next"), Page(["refund-tool"], None)]
        mcp = MagicMock()
        mcp.__enter__.return_value = gateway
        captured = {}
        class FakeAgent:
            def __init__(self, **kwargs):
                captured.update(kwargs)
                self.messages = kwargs["messages"]
            async def invoke_async(self, prompt):
                hook = captured["hooks"][0]
                self.messages.append(message("user", prompt))
                hook.retrieve_customer_context(SimpleNamespace(agent=self))
                self.messages.append(message("assistant", "Order is shipped."))
                hook.save_support_interaction(SimpleNamespace(agent=self))
                return SimpleNamespace(message={"content": [{"text": "Order is shipped."}, {"text": "UPS"}]})
        with patch.multiple(main, GATEWAY_URL="https://example.com/mcp", KB_ID="KB123", MEMORY_ID="mem"), \
             patch.object(main, "clients", return_value=("model", memory, None)), \
             patch.object(main, "MCPClient", return_value=mcp), \
             patch.object(main, "Agent", FakeAgent):
            result = asyncio.run(main.invoke({"prompt": "Track ORD-001", "customer_id": "CUST-123", "session_id": "s1"}))
        self.assertEqual(result["response"], "Order is shipped.\nUPS")
        self.assertIn("order-tool", captured["tools"])
        self.assertIn("refund-tool", captured["tools"])
        self.assertIn("browser", [getattr(t, "tool_name", None) for t in captured["tools"]])
        self.assertEqual(gateway.list_tools_sync.call_args.kwargs["pagination_token"], "next")
        mcp.__exit__.assert_called_once()


class LambdaTests(unittest.TestCase):
    def load(self, name):
        spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / "lambda" / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_order_fixture_and_missing_order(self):
        handler = self.load("order_tracker").lambda_handler
        with contextlib.redirect_stdout(io.StringIO()):
            response = handler({"resource": "/orders/{order_id}", "httpMethod": "GET", "pathParameters": {"order_id": "ORD-001"}}, None)
            missing = handler({"resource": "/orders/{order_id}", "pathParameters": {"order_id": "MISSING"}}, None)
        body = json.loads(response["body"])
        self.assertEqual(body["tracking_number"], "TRK987654321")
        self.assertEqual(body["carrier"], "UPS")
        self.assertEqual(missing["statusCode"], 404)

    def test_refund_gateway_routing(self):
        handler = self.load("refund_processor").lambda_handler
        context = SimpleNamespace(client_context=SimpleNamespace(custom={"bedrockAgentCoreToolName": "refund-processor___initiate_refund"}))
        with contextlib.redirect_stdout(io.StringIO()):
            result = handler({"order_id": "ORD-002", "reason": "Changed my mind", "amount": 139.99}, context)
        body = json.loads(result["body"])
        self.assertEqual(body["status"], "APPROVED")
        self.assertEqual(body["amount"], 139.99)
        self.assertTrue(body["refund_id"].startswith("REF-"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
