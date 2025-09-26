import pytest
from playwright.sync_api import Page, expect
from pathlib import Path

def test_file_upload_area_visible(page: Page):
    page.goto("http://localhost:8000")
    drop_zone = page.locator("#drop-zone")
    expect(drop_zone).to_be_visible()
    expect(drop_zone).to_have_text("Drag and drop your file here or")

def test_file_upload_button(page: Page):
    page.goto("http://localhost:8000")
    file_input = page.locator("#file-input")
    expect(file_input).to_be_hidden()
    upload_button = page.get_by_text("Choose File")
    expect(upload_button).to_be_visible()

@pytest.mark.parametrize("file_type", [".txt", ".mp3", ".wav"])
def test_file_upload_accepts_valid_types(page: Page, file_type: str, tmp_path: Path):
    # Create test file
    test_file = tmp_path / f"test{file_type}"
    test_file.write_text("test content" if file_type == ".txt" else "binary content")

    page.goto("http://localhost:8000")

    # Upload file
    page.locator("#file-input").set_input_files(str(test_file))

    # Check file info is displayed
    expect(page.locator("#file-info")).to_be_visible()
    expect(page.locator("#file-name")).to_have_text(f"test{file_type}")