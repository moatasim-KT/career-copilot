import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.core.config import settings
from app.services.template_service import TemplateService


class _DummySession:
	pass


@pytest.fixture
def template_service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TemplateService:
	upload_root = tmp_path / "uploads"
	monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_root), raising=False)
	return TemplateService(db=_DummySession())


def test_sanitize_filename_removes_illegal_sequences(template_service: TemplateService) -> None:
	unsafe_name = "../my::../../resume"
	sanitized = template_service._sanitize_filename(unsafe_name)

	assert ".." not in sanitized
	assert re.match(r"^[A-Za-z0-9_.-]+$", sanitized)


def test_save_generated_file_produces_safe_path(template_service: TemplateService) -> None:
	generated_doc = SimpleNamespace(user_id=1, document_type="../../resume")
	html_content = "<p>Hello</p>"

	saved_path = template_service._save_generated_file(generated_doc, html_content, "html")

	expected_dir = (Path(settings.UPLOAD_DIR) / "generated" / "1").resolve()
	assert saved_path.exists()
	assert saved_path.parent == expected_dir
	assert ".." not in saved_path.name
	assert saved_path.suffix == ".html"
	assert saved_path.read_text(encoding="utf-8") == html_content


def test_render_template_autoescapes_html(template_service: TemplateService) -> None:
	malicious_value = "<script>alert('x')</script>"
	template = SimpleNamespace(template_content="{{ user.name }}", template_styles=None, template_structure={})

	rendered = template_service._render_template(
		template,
		{
			"user_data": {"name": malicious_value},
			"job_data": {},
			"tailored_content": {},
			"customizations": {},
		},
	)

	assert malicious_value not in rendered
	assert "&lt;script&gt;alert(&#39;x&#39;)&lt;/script&gt;" in rendered
