import json
import importlib.util
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("compile_request.py")
SPEC = importlib.util.spec_from_file_location("compile_request", MODULE_PATH)
assert SPEC and SPEC.loader
compile_request_module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = compile_request_module
SPEC.loader.exec_module(compile_request_module)

classify_mode = compile_request_module.classify_mode
compile_request = compile_request_module.compile_request
main = compile_request_module.main
redact_text = compile_request_module.redact_text


class CompileRequestTest(unittest.TestCase):
    def test_short_implementation_request_defaults_to_owner_and_solo(self):
        payload = compile_request("修复登录后概览页空白")
        self.assertEqual(payload["intent"]["mode"], "implement")
        self.assertEqual(payload["intent"]["flowOwner"], "deliver-change")
        self.assertEqual(payload["defaults"]["ownerRole"], "@plan_owner")
        self.assertEqual(payload["defaults"]["topology"], "solo")
        self.assertFalse(payload["confirmation"]["required"])

    def test_explicit_diagnose_wins_over_implementation_words(self):
        self.assertEqual(classify_mode("定位并修复上传失败")[0], "implement")
        self.assertEqual(classify_mode("分析并修复上传失败")[0], "implement")
        payload = compile_request("只分析上传失败原因")
        self.assertEqual(payload["intent"]["mode"], "diagnose")
        self.assertEqual(payload["intent"]["flowOwner"], "diagnose")

    def test_ui_browser_request_adds_evidence_route_without_forcing_roles(self):
        payload = compile_request("把模型页面筛选条改成单行并做真实入口验收")
        self.assertEqual(payload["intent"]["mode"], "implement")
        self.assertTrue(payload["signals"]["ui"])
        self.assertTrue(payload["signals"]["browser"])
        self.assertEqual(payload["routing"]["browser"], "select-by-evidence")
        self.assertIn("按需 @ui_deep / @ui_impl / @ui_qa，不默认串行启用", payload["routing"]["roles"])
        self.assertTrue(any("真实入口" in item for item in payload["defaults"]["acceptance"]))

    def test_high_risk_signals_only_request_confirmation(self):
        payload = compile_request("把修复发布到生产并清理旧资源")
        self.assertTrue(payload["signals"]["remote"])
        self.assertTrue(payload["signals"]["destructive"])
        self.assertTrue(payload["confirmation"]["required"])
        self.assertGreaterEqual(len(payload["confirmation"]["reasons"]), 2)

    def test_obvious_credential_values_are_redacted_from_contract(self):
        self.assertEqual(redact_text("use token=abc123 and Bearer xyz"), "use <redacted> and <redacted>")

    def test_authority_discovery_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("project", encoding="utf-8")
            payload = compile_request("检查构建", project_root=root)
            self.assertEqual(payload["defaults"]["authority"], ["project AGENTS.md"])

    def test_json_output_and_optional_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / ".work" / "request.json"
            with contextlib.redirect_stdout(io.StringIO()):
                result = main(["--request", "只验证登录页", "--json", "--out", str(output)])
            self.assertEqual(result, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["intent"]["mode"], "verify")
            self.assertTrue(payload["signals"]["browser"])


if __name__ == "__main__":
    unittest.main()
