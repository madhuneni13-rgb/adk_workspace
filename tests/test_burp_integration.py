"""Unit tests for ZAP-to-Burp verification handoff helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from api_pentest_agent import burp_report
from api_pentest_agent.zap_mcp import normalize_zap_alerts


class ZapAlertNormalizationTests(unittest.TestCase):
    def test_filters_by_origin_and_postman_path(self) -> None:
        payload = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "alerts": [
                                {
                                    "alertRef": "1001",
                                    "name": "Missing Header",
                                    "risk": "Low",
                                    "confidence": "High",
                                    "uri": "http://localhost:3000/api/profile",
                                },
                                {
                                    "alertRef": "1002",
                                    "name": "Different Path",
                                    "risk": "High",
                                    "uri": "http://localhost:3000/admin/secret",
                                },
                                {
                                    "alertRef": "1003",
                                    "name": "Different Host",
                                    "risk": "High",
                                    "uri": "http://example.test/api/profile",
                                },
                            ]
                        }
                    ),
                }
            ]
        }
        in_scope, excluded = normalize_zap_alerts(
            payload,
            "http://localhost:3000/",
            ["http://localhost:3000/api/profile"],
        )
        self.assertEqual(["1001"], [item["id"] for item in in_scope])
        self.assertEqual(2, len(excluded))


class BurpReportTests(unittest.TestCase):
    def test_report_redacts_authentication_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(burp_report, "REPORTS_ROOT", Path(temp_dir)),
                patch.object(
                    burp_report,
                    "prune_old_reports",
                    lambda *args, **kwargs: [],
                ),
            ):
                result = burp_report.save_burp_verification_report(
                    verification_results=[
                        {
                            "finding": "Missing Header",
                            "zap_risk": "Low",
                            "verified_status": "Confirmed",
                            "url": "http://localhost:3000/api/profile",
                            "evidence": {
                                "Authorization": "Bearer secret.jwt.value",
                                "body": "Bearer abc.def.ghi",
                            },
                            "reproduction": "Replay once",
                            "notes": "Confirmed",
                        }
                    ],
                    authorized_scope=["http://localhost:3000/api/profile"],
                    collection_name="DVAPI",
                )
                report = Path(result["burp_report_json"]).read_text(encoding="utf-8")
                self.assertNotIn("secret.jwt.value", report)
                self.assertNotIn("abc.def.ghi", report)
                self.assertIn("[REDACTED]", report)


if __name__ == "__main__":
    unittest.main()
