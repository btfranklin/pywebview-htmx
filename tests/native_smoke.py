"""Check a real Python bridge in the local desktop renderer."""

from __future__ import annotations

from html import escape
from threading import Event
from time import monotonic, sleep

import webview

from pywebview_htmx import create_window, encode_params_attr


class API:
    def __init__(self) -> None:
        self._done = Event()
        self._params: dict[str, object] | None = None
        self._result: dict[str, object] | None = None

    def greeting(self, params: dict[str, object]) -> str:
        self._params = params
        return f'<p>Hello, {escape(str(params["name"]))}!</p>'

    def fail(self, params: dict[str, object]) -> str:
        raise ValueError("Expected native smoke test failure")

    def report(self, result: dict[str, object]) -> str:
        self._result = result
        self._done.set()
        return ""


def main() -> None:
    name = 'İstanbul <bridge> "test"'
    params = encode_params_attr({"name": name})
    api = API()
    html = f"""<!doctype html>
    <html><head><title>İstanbul</title></head><body>
      <button id="greeting" py-call="greeting" py-target="#result"
              data-py-params="{params}">İstanbul</button>
      <button id="failure" py-call="fail" py-target="#error-result">Fail</button>
      <div id="result"></div><div id="error-result"></div>
      <script>
        document.addEventListener('DOMContentLoaded', () => {{
          document.body.addEventListener('py:afterSwap', event => {{
            if (event.target.id === 'result') {{
              document.querySelector('#failure').click();
            }}
          }});
          document.body.addEventListener('py:error', event => {{
            pywebview.api.report({{
              text: document.querySelector('#result').textContent,
              error: event.detail.error.message,
              name: event.detail.error.name,
              element: event.detail.element.id,
              stale: event.detail.stale
            }}).then(() => {{ window.nativeReportDone = true; }});
          }});
        }});
      </script>
    </body></html>"""
    window = create_window(
        "pywebview-htmx native smoke test", html, js_api=api,
        start=False, hidden=True, focus=False,
    )
    failures: list[Exception] = []
    verified = Event()

    def check() -> None:
        try:
            if not window.events.loaded.wait(15):
                raise TimeoutError("The native window did not load")
            window.evaluate_js("document.querySelector('#greeting').click()")
            if not api._done.wait(15):
                raise TimeoutError("The native bridge did not finish")
            deadline = monotonic() + 15
            while not window.evaluate_js("window.nativeReportDone === true"):
                if monotonic() >= deadline:
                    raise TimeoutError("The native report did not finish")
                sleep(0.01)
            assert api._params == {"name": name}, api._params
            assert api._result == {
                "text": f"Hello, {name}!",
                "error": "Expected native smoke test failure",
                "name": "ValueError",
                "element": "failure",
                "stale": False,
            }, api._result
            verified.set()
        except Exception as error:
            failures.append(error)
        finally:
            window.destroy()

    webview.start(check)
    if failures:
        raise failures[0]
    if not verified.is_set():
        raise RuntimeError("The native smoke test did not complete")
    print(f"Native smoke test passed ({webview.renderer})")


if __name__ == "__main__":
    main()
