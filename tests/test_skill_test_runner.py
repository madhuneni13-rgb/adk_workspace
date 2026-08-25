"""Tests for Markdown-driven OWASP skill execution planning."""

import json
import unittest

from api_pentest_agent.skill_test_runner import (
    build_skill_test_plan,
    parse_skill_tests,
)
from api_pentest_agent.tools import (
    _apply_bearer_token,
    _extract_bearer_token,
    _prepare_registration_credentials,
    _store_bearer_token_from_result,
    load_owasp_skill,
)


class SkillTestParsingTests(unittest.TestCase):
    def test_extracts_only_test_mutation_bullets(self) -> None:
        markdown = """# Skill
## Methodology
- Not executable
## Test Mutations
- Remove `Authorization`
- Change `limit=10`
## Remediation
- Not a test
"""
        tests = parse_skill_tests("API2", markdown)
        self.assertEqual(["API2-T01", "API2-T02"], [test.id for test in tests])
        self.assertEqual(2, len(tests))

    def test_all_current_skill_bullets_are_accounted_for(self) -> None:
        requests = [
            {
                "index": 0,
                "name": "Update profile",
                "method": "PATCH",
                "url": "http://localhost:3000/api/users/1",
                "headers": {"Authorization": "Bearer {{bearer_token}}"},
                "body": json.dumps(
                    {
                        "username": "user",
                        "url": "https://example.test/image",
                        "amount": 10,
                    }
                ),
                "query_params": {"limit": "10", "q": "profile"},
            }
        ]
        skills = {
            f"API{number}": load_owasp_skill(f"API{number}")
            for number in range(1, 11)
        }
        plan, coverage = build_skill_test_plan(requests, skills)
        expected = sum(
            len(parse_skill_tests(category, skill["content"]))
            for category, skill in skills.items()
        )
        self.assertEqual(46, expected)
        self.assertEqual(expected, len(coverage))
        self.assertGreater(sum(len(items) for items in plan.values()), 0)
        self.assertTrue(
            all(item["status"] in {"planned", "skipped"} for item in coverage)
        )


class AuthenticationBootstrapTests(unittest.TestCase):
    def test_extracts_login_cookie_header_and_saves_both_variable_aliases(self) -> None:
        token = "header.payload.signature"
        result = {
            "success": True,
            "status_code": 200,
            "response_headers": {
                "Set-Cookie": f"auth={token}; Path=/; HttpOnly",
            },
            "response_cookies": {},
            "response_body": "{}",
        }
        variables: dict[str, str] = {}

        self.assertEqual(
            token,
            _extract_bearer_token(response_headers=result["response_headers"]),
        )
        self.assertEqual(token, _store_bearer_token_from_result(result, variables))
        self.assertEqual(token, variables["bearer_token"])
        self.assertEqual(token, variables["Bearer_token"])

    def test_uppercase_bearer_token_placeholder_is_applied_to_protected_call(
        self,
    ) -> None:
        token = "header.payload.signature"
        headers, body, url, params = _apply_bearer_token(
            headers={"X-Token": "{{Bearer_token}}"},
            body='{"token":"{{Bearer_token}}"}',
            url="https://example.test/profile",
            query_params={"token": "{{Bearer_token}}"},
            bearer_token=token,
        )
        self.assertEqual(f"Bearer {token}", headers["Authorization"])
        self.assertEqual(token, headers["X-Token"])
        self.assertIn(token, body or "")
        self.assertEqual(token, params["token"])
        self.assertEqual("https://example.test/profile", url)

    def test_registration_identity_is_copied_to_login_and_later_requests(self) -> None:
        requests = [
            {
                "index": 0,
                "name": "Register",
                "method": "POST",
                "url": "http://localhost/api/register",
                "headers": {},
                "body": '{"username":"user","password":"pass"}',
                "query_params": {},
            },
            {
                "index": 1,
                "name": "Login",
                "method": "POST",
                "url": "http://localhost/api/login",
                "headers": {},
                "body": '{"username":"user","password":"pass"}',
                "query_params": {},
            },
            {
                "index": 2,
                "name": "Get user",
                "method": "GET",
                "url": "http://localhost/api/user",
                "headers": {},
                "body": None,
                "query_params": {"username": "user"},
            },
        ]
        context = _prepare_registration_credentials(requests)
        register_body = json.loads(requests[0]["body"])
        login_body = json.loads(requests[1]["body"])

        self.assertNotEqual("user", register_body["username"])
        self.assertEqual(register_body, login_body)
        self.assertEqual(register_body["username"], requests[2]["query_params"]["username"])
        self.assertEqual("username", next(iter(register_body)))
        self.assertEqual(requests[0], context["register_request"])
        self.assertEqual(requests[1], context["login_request"])


if __name__ == "__main__":
    unittest.main()
