import pytest
from playwright.sync_api import Page, expect

def test_chat_interface_visible(page: Page):
    page.goto("http://localhost:8000")
    chat_area = page.locator("#chat-messages")
    expect(chat_area).to_be_visible()
    expect(chat_area).to_contain_text("Welcome!")

def test_message_input(page: Page):
    page.goto("http://localhost:8000")
    message_input = page.locator("#message-input")
    expect(message_input).to_be_visible()
    expect(message_input).to_be_empty()

def test_send_message(page: Page):
    page.goto("http://localhost:8000")
    test_message = "Test message"

    # Type and send message
    page.fill("#message-input", test_message)
    page.click("#send-btn")

    # Check message appears in chat
    expect(page.locator("#chat-messages")).to_contain_text(test_message)
    expect(page.locator("#message-input")).to_be_empty()

@pytest.mark.parametrize("key", ["Enter", "Escape"])
def test_keyboard_shortcuts(page: Page, key: str):
    page.goto("http://localhost:8000")
    test_message = "Test keyboard shortcuts"

    # Type message
    page.fill("#message-input", test_message)

    if key == "Enter":
        page.keyboard.press("Enter")
        expect(page.locator("#chat-messages")).to_contain_text(test_message)
        expect(page.locator("#message-input")).to_be_empty()
    elif key == "Escape":
        page.keyboard.press("Escape")
        expect(page.locator("#message-input")).to_be_empty()