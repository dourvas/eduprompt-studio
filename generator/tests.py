import json
from unittest import mock

from django.conf import settings
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase, override_settings

from generator.middleware import FrameAncestorsMiddleware
from generator.models import (
    ImprovementSuggestion,
    PageView,
    PromptGeneration,
    TemplateUsage,
    UserSession,
)
from generator.notices import NOTICES, get_notice

EXPECTED_CSP = (
    "frame-ancestors 'self' https://proodoseduai.com "
    "https://www.proodoseduai.com"
)
EXPECTED_EN_NOTICE = (
    "This tool is a separate application used inside PROODOS. "
    "Do not enter personal data of students or colleagues. "
    "What you type is sent to Google Gemini to generate the prompt. "
    "This tool does not store what you type."
)

STORAGE_MODELS = (
    PromptGeneration,
    ImprovementSuggestion,
    UserSession,
    PageView,
    TemplateUsage,
)


def gemini_reply(text):
    """A fake requests.Response for a successful Gemini call."""
    reply = mock.Mock()
    reply.status_code = 200
    payload = {"candidates": [{"content": {"parts": [{"text": text}]}}]}
    reply.json.return_value = payload
    reply.text = json.dumps(payload)
    return reply


def assert_nothing_stored(testcase):
    for model in STORAGE_MODELS:
        testcase.assertEqual(
            model.objects.count(), 0,
            "%s has rows, but the Studio must store nothing" % model.__name__,
        )


FORM_FIELDS = {
    "prompt": "Write a lesson plan on fractions for a class of ten year olds.",
    "template": "lesson_plan",
    "enhancement": "enhanced",
    "theory_enhancement": "blooms",
    "role": "Teacher",
    "subject": "Mathematics",
    "task": "lesson plan",
    "context": "primary school",
    "methodology": "inquiry",
    "tone": "friendly",
}


class IndexPageTests(TestCase):
    def test_index_returns_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_index_stores_nothing(self):
        self.client.get("/")
        assert_nothing_stored(self)

    def test_notice_is_present_in_the_index_page(self):
        response = self.client.get("/")
        self.assertContains(response, get_notice(settings.UI_LANGUAGE))

    def test_english_notice_text_is_exact(self):
        self.assertEqual(NOTICES["en"], EXPECTED_EN_NOTICE)

    def test_notice_falls_back_to_english_when_greek_is_missing(self):
        self.assertIsNone(NOTICES["el"])
        self.assertEqual(get_notice("el"), EXPECTED_EN_NOTICE)
        self.assertEqual(get_notice("unknown"), EXPECTED_EN_NOTICE)

    def test_help_page_returns_200(self):
        self.assertEqual(self.client.get("/help/").status_code, 200)

    def test_get_sets_no_cookie_at_all(self):
        response = self.client.get("/")
        self.assertEqual(len(response.cookies), 0)
        self.assertNotIn("Set-Cookie", response.headers)


@mock.patch("generator.views.requests.post")
class GenerateTests(TestCase):
    def post(self, body):
        return self.client.post(
            "/generate/", data=json.dumps(body), content_type="application/json"
        )

    def test_generate_succeeds_and_stores_nothing(self, post):
        post.return_value = gemini_reply("A generated prompt")
        response = self.post(FORM_FIELDS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"response": "A generated prompt"})
        assert_nothing_stored(self)

    def test_improve_flow_works_and_stores_nothing(self, post):
        post.return_value = gemini_reply('{"prompt_improvements": "1. Add timing."}')
        response = self.post({
            "prompt": "You are a prompt engineering expert. Improve this: text"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("prompt_improvements", json.loads(response.json()["response"]))
        assert_nothing_stored(self)

    def test_theory_suggestion_works_and_stores_nothing(self, post):
        post.return_value = gemini_reply(
            '{"theory_explanation": "why", "teaching_tip": "tip"}'
        )
        response = self.post({
            "prompt": "You are an educational theory expert. Explain this."
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("theory_explanation", json.loads(response.json()["response"]))
        assert_nothing_stored(self)

    def test_gemini_key_is_sent_in_header_not_in_url(self, post):
        post.return_value = gemini_reply("ok")
        with override_settings(GEMINI_API_KEY="test-key-123"):
            self.post(FORM_FIELDS)
        args, kwargs = post.call_args
        url = args[0] if args else kwargs["url"]
        self.assertNotIn("key=", url)
        self.assertNotIn("test-key-123", url)
        self.assertEqual(kwargs["headers"]["x-goog-api-key"], "test-key-123")
        self.assertIn("gemini-2.5-flash", url)

    def test_gemini_error_is_reported_and_stores_nothing(self, post):
        failed = mock.Mock()
        failed.status_code = 500
        failed.text = "upstream failure"
        post.return_value = failed
        response = self.post(FORM_FIELDS)
        self.assertEqual(response.status_code, 500)
        assert_nothing_stored(self)

    def test_generate_does_not_log_the_teacher_text(self, post):
        post.return_value = gemini_reply("SECRET-GENERATED-OUTPUT")
        body = dict(FORM_FIELDS, task="SECRET-TEACHER-INPUT")
        with self.assertNoLogs("generator.views", level="DEBUG"):
            self.post(body)

    def test_post_works_with_csrf_checks_enforced_and_no_token(self, post):
        post.return_value = gemini_reply("ok")
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            "/generate/", data=json.dumps(FORM_FIELDS),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

    def test_post_sets_no_cookie_at_all(self, post):
        post.return_value = gemini_reply("ok")
        response = self.post(FORM_FIELDS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.cookies), 0)
        self.assertNotIn("Set-Cookie", response.headers)

    def test_foreign_origin_gets_403(self, post):
        for origin in ("https://evil.example", "http://evil.example",
                       "https://testserver.evil.example", "null"):
            response = self.client.post(
                "/generate/", data=json.dumps(FORM_FIELDS),
                content_type="application/json", HTTP_ORIGIN=origin,
            )
            self.assertEqual(response.status_code, 403, origin)
            self.assertIn("error", response.json())
            self.assertEqual(len(response.cookies), 0)
        post.assert_not_called()
        assert_nothing_stored(self)

    def test_same_origin_gets_through_over_http_and_https(self, post):
        post.return_value = gemini_reply("ok")
        for origin in ("http://testserver", "https://testserver",
                       "HTTPS://TESTSERVER"):
            response = self.client.post(
                "/generate/", data=json.dumps(FORM_FIELDS),
                content_type="application/json", HTTP_ORIGIN=origin,
            )
            self.assertEqual(response.status_code, 200, origin)

    def test_same_origin_behind_a_tls_terminating_proxy(self, post):
        post.return_value = gemini_reply("ok")
        response = self.client.post(
            "/generate/", data=json.dumps(FORM_FIELDS),
            content_type="application/json", HTTP_HOST="localhost:8000",
            HTTP_ORIGIN="https://localhost:8000",
            HTTP_X_FORWARDED_PROTO="https",
        )
        self.assertEqual(response.status_code, 200)

    def test_missing_origin_gets_through(self, post):
        post.return_value = gemini_reply("ok")
        self.assertEqual(self.post(FORM_FIELDS).status_code, 200)

    def test_get_is_rejected(self, post):
        self.assertEqual(self.client.get("/generate/").status_code, 400)
        post.assert_not_called()


class FramingTests(TestCase):
    def test_csp_frame_ancestors_on_index(self):
        response = self.client.get("/")
        self.assertEqual(response["Content-Security-Policy"], EXPECTED_CSP)

    def test_csp_frame_ancestors_on_every_kind_of_response(self):
        for path in ("/help/", "/does-not-exist/", "/generate/"):
            response = self.client.get(path)
            self.assertEqual(response["Content-Security-Policy"], EXPECTED_CSP, path)

    def test_no_x_frame_options_header(self):
        for path in ("/", "/help/", "/does-not-exist/"):
            response = self.client.get(path)
            self.assertNotIn("X-Frame-Options", response, path)
            self.assertNotEqual(response.headers.get("X-Frame-Options"), "ALLOWALL")

    def test_settings_do_not_allow_all(self):
        self.assertNotEqual(getattr(settings, "X_FRAME_OPTIONS", None), "ALLOWALL")

    def test_middleware_removes_an_existing_x_frame_options(self):
        def view(request):
            response = HttpResponse("x")
            response["X-Frame-Options"] = "ALLOWALL"
            return response
        response = FrameAncestorsMiddleware(view)(RequestFactory().get("/"))
        self.assertNotIn("X-Frame-Options", response)

    @override_settings(FRAME_ANCESTORS=["https://example.org", "https://bad;origin"])
    def test_frame_ancestors_are_configurable_and_sanitised(self):
        middleware = FrameAncestorsMiddleware(lambda request: HttpResponse("x"))
        response = middleware(RequestFactory().get("/"))
        self.assertEqual(
            response["Content-Security-Policy"],
            "frame-ancestors 'self' https://example.org",
        )


class RemovedRoutesTests(TestCase):
    def test_study_era_routes_are_gone(self):
        for path in (
            "/admin/",
            "/admin/login/",
            "/onboarding/",
            "/onboarding/stats/",
            "/training-needs/",
            "/training-needs/stats/",
            "/track-copy/",
        ):
            self.assertEqual(self.client.get(path).status_code, 404, path)
            self.assertEqual(self.client.post(path).status_code, 404, path)
        assert_nothing_stored(self)

    def test_index_has_no_survey_or_onboarding_code(self):
        html = self.client.get("/").content.decode()
        for needle in ("onboarding", "trainingNeeds", "SURVEYS_ENABLED",
                       "track-copy", "follow_up_email", "contact_email",
                       "csrf", "CSRF", "document.cookie"):
            self.assertNotIn(needle, html)
