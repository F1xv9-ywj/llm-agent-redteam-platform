from pathlib import Path


def test_dashboard_does_not_render_api_data_with_html_sinks():
    script = (Path(__file__).parents[1] / "src" / "redsentinel" / "static" / "app.js").read_text(encoding="utf-8")
    assert "innerHTML" not in script
    assert "insertAdjacentHTML" not in script
    assert "document.write" not in script
    assert "textContent" in script
