"""
Interactive Code Debugger Page Object Model
"""

from playwright.sync_api import Page, expect
from .base_page import BasePage

class DebuggerPage(BasePage):
    """Page Object for Multi-Language Interactive Code Debugger (/debugger/)."""

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)

        # Locators
        self.editor_container = page.locator("#monacoEditor, #codeEditor, .monaco-editor, #editorContainer")
        self.btn_run = page.locator("button#btnStart")
        self.btn_step_next = page.locator("button#btnNext")
        self.btn_auto_play = page.locator("button#btnAutoPlay")
        
        self.lang_python_btn = page.locator("button#langPython")
        self.lang_js_btn = page.locator("button#langJS")
        self.lang_java_btn = page.locator("button#langJava")
        
        self.output_console = page.locator("#stdoutConsole")
        self.call_stack_view = page.locator("#callStackView, .call-stack-panel, #stackTraceContainer")
        self.variable_inspector = page.locator("#variableInspector, .visual-card")

    def open(self):
        """Opens code debugger page."""
        self.navigate("/debugger/")
        self.bypass_entry_if_present()

    def select_language(self, lang: str):
        """Selects language tab."""
        if lang.lower() == "python" and self.lang_python_btn.is_visible():
            self.lang_python_btn.click()
        elif lang.lower() in ["javascript", "js"] and self.lang_js_btn.is_visible():
            self.lang_js_btn.click()
        elif lang.lower() == "java" and self.lang_java_btn.is_visible():
            self.lang_java_btn.click()
        self.page.wait_for_timeout(300)

    def execute_trace(self):
        """Clicks Start Debugging and waits for trace step initialization."""
        if self.btn_run.is_visible():
            self.btn_run.click()
            self.page.wait_for_timeout(1000)

    def get_console_output(self) -> str:
        """Returns stdout output text."""
        return self.output_console.text_content() or ""
