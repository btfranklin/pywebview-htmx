"""Check the Python bridge in the local desktop renderer."""

from __future__ import annotations

from html import escape
from threading import Event, Lock

import webview

from pywebview_htmx import create_window, encode_params_attr, get_theme_css


class API:
    def __init__(self) -> None:
        self._lock = Lock()
        self._stages: dict[str, Event] = {}
        self._reports: dict[str, dict[str, object]] = {}
        self.greeting_params: dict[str, object] | None = None
        self.form_params: dict[str, object] | None = None
        self.fragment_params: dict[str, object] | None = None
        self.slow_started = Event()
        self.release_slow = Event()
        self.slow_finished = Event()

    def _record(self, stage: str, result: dict[str, object]) -> None:
        with self._lock:
            self._reports[stage] = result
            event = self._stages.setdefault(stage, Event())
            event.set()

    def wait_for(self, stage: str, timeout: float = 15) -> dict[str, object]:
        with self._lock:
            event = self._stages.setdefault(stage, Event())
        if not event.wait(timeout):
            raise TimeoutError(f"Timed out waiting for native stage {stage!r}")
        with self._lock:
            return self._reports[stage]

    def greeting(self, params: dict[str, object]) -> str:
        self.greeting_params = params
        return f'<p>Hello, {escape(str(params["name"]))}!</p>'

    def fail(self, params: dict[str, object]) -> str:
        _ = params
        raise ValueError("Expected native smoke test failure")

    def form_echo(self, params: dict[str, object]) -> str:
        self.form_params = params
        return '<p id="form-response">Form received.</p>'

    def slow(self, params: dict[str, object]) -> str:
        _ = params
        self.slow_started.set()
        if not self.release_slow.wait(15):
            raise TimeoutError("The smoke test did not release the slow request")
        self.slow_finished.set()
        return '<p id="race-response">Slow response.</p>'

    def fast(self, params: dict[str, object]) -> str:
        _ = params
        return '<p id="race-response">Fast response.</p>'

    def load_fragment(self, params: dict[str, object]) -> str:
        _ = params
        callback_params = encode_params_attr({"source": "native-fragment"})
        return (
            '<button id="fragment-button" py-call="fragment_callback" '
            'py-target="#fragment-result" '
            f'data-py-params="{callback_params}">Run fragment callback</button>'
            '<div id="fragment-result"></div>'
        )

    def fragment_callback(self, params: dict[str, object]) -> str:
        self.fragment_params = params
        return '<p id="fragment-response">Fragment callback worked.</p>'

    def change_theme(self, params: dict[str, object]) -> str:
        _ = params
        css = get_theme_css("paper")
        return (
            '<section id="theme-component">'
            f'<style data-pywebview-theme="paper">{css}</style>'
            '<button id="theme-button" py-call="change_theme" '
            'py-target="#theme-component" py-swap="outerHTML">Paper theme</button>'
            '<p id="theme-name">paper</p></section>'
        )

    def report(self, result: dict[str, object]) -> str:
        self._record(str(result["stage"]), result)
        return ""


def _html(name: str) -> str:
    greeting_params = encode_params_attr({"name": name})
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Native bridge check</title></head>
<body>
  <button id="greeting" py-call="greeting" py-target="#greeting-result"
          data-py-params="{greeting_params}">Greet</button>
  <div id="greeting-result"></div>
  <button id="failure" py-call="fail" py-target="#failure-result"
          data-py-params='{{}}'>Fail</button>
  <div id="failure-result"></div>
  <form id="form" py-call="form_echo" py-trigger="submit"
        py-target="#form-result" py-wait="#form-wait">
    <input name="tag" value="first">
    <input name="tag" value="second">
    <button id="submitter" type="submit" name="intent" value="save">Save</button>
  </form>
  <span id="form-wait" aria-busy="false">Waiting</span>
  <div id="form-result"></div>
  <button id="slow" py-call="slow" py-target="#race-result"
          py-wait="#race-wait" data-py-params='{{}}'>Slow request</button>
  <button id="fast" py-call="fast" py-target="#race-result"
          py-wait="#race-wait" data-py-params='{{}}'>Fast request</button>
  <div id="race-wait" aria-busy="false">Loading</div>
  <div id="race-result"></div>
  <button id="load-fragment" py-call="load_fragment"
          py-target="#fragment-host" data-py-params='{{}}'>Load fragment</button>
  <div id="fragment-host"></div>
  <section id="theme-component">
    <style data-pywebview-theme="aurora">{get_theme_css("aurora")}</style>
    <button id="theme-button" py-call="change_theme"
            py-target="#theme-component" py-swap="outerHTML"
            data-py-params='{{}}'>Change theme</button>
    <p id="theme-name">aurora</p>
  </section>
  <script>
    window.nativeReady = false;
    window.raceStarted = false;
    window.raceIdleReported = false;

    window.addEventListener("pywebviewready", () => {{
      window.nativeReady = true;
      window.pywebview.api.report({{stage: "ready"}});
    }});

    document.body.addEventListener("py:afterSwap", event => {{
      const target = event.target;
      window.pywebview.api.report({{
        stage: "after:" + (target.id || "unknown"),
        target: target.id,
        requestId: event.detail.requestId
      }});
    }});

    document.body.addEventListener("py:error", event => {{
      const detail = event.detail;
      window.pywebview.api.report({{
        stage: "error",
        message: detail.error.message,
        name: detail.error.name,
        element: detail.element.id,
        stale: detail.stale,
        phase: detail.phase || ""
      }});
    }});

    document.body.addEventListener("py:trigger", event => {{
      if (event.target.id === "slow") window.raceStarted = true;
    }});

    const raceWait = document.querySelector("#race-wait");
    const reportRaceIdle = () => {{
      if (!window.raceStarted || window.raceIdleReported) return;
      if (raceWait.getAttribute("aria-busy") !== "false") return;
      if (raceWait.classList.contains("py-waiting")) return;
      window.raceIdleReported = true;
      window.pywebview.api.report({{stage: "race-idle"}});
    }};
    new MutationObserver(reportRaceIdle).observe(raceWait, {{
      attributes: true,
      attributeFilter: ["aria-busy", "class"]
    }});
  </script>
</body></html>"""


def _check(window: webview.Window, api: API, name: str) -> None:
    if not window.events.loaded.wait(15):
        raise TimeoutError("The native window did not load")
    api.wait_for("ready")
    if window.evaluate_js("window.nativeReady === true") is not True:
        raise RuntimeError("The native page did not receive pywebviewready")

    window.evaluate_js("document.querySelector('#greeting').click()")
    api.wait_for("after:greeting-result")
    assert api.greeting_params == {"name": name}, api.greeting_params
    greeting_text = window.evaluate_js(
        "document.querySelector('#greeting-result').textContent",
    )
    assert greeting_text == f"Hello, {name}!"

    window.evaluate_js("document.querySelector('#failure').click()")
    error = api.wait_for("error")
    assert error == {
        "stage": "error",
        "message": "Expected native smoke test failure",
        "name": "ValueError",
        "element": "failure",
        "stale": False,
        "phase": "",
    }, error

    window.evaluate_js("document.querySelector('#submitter').click()")
    api.wait_for("after:form-result")
    assert api.form_params == {
        "tag": ["first", "second"],
        "intent": "save",
    }, api.form_params

    window.evaluate_js("document.querySelector('#slow').click()")
    if not api.slow_started.wait(10):
        raise TimeoutError("The slow Python request did not start")
    window.evaluate_js("document.querySelector('#fast').click()")
    api.wait_for("after:race-result")
    assert window.evaluate_js("document.querySelector('#race-result').textContent") == (
        "Fast response."
    )
    assert window.evaluate_js(
        "document.querySelector('#race-wait').getAttribute('aria-busy') === 'true' "
        "&& document.querySelector('#race-wait').classList.contains('py-waiting')",
    ) is True
    api.release_slow.set()
    if not api.slow_finished.wait(10):
        raise TimeoutError("The slow Python request did not finish")
    api.wait_for("race-idle")
    assert window.evaluate_js(
        "document.querySelector('#race-wait').getAttribute('aria-busy') === 'false' "
        "&& !document.querySelector('#race-wait').classList.contains('py-waiting')",
    ) is True
    assert window.evaluate_js("document.querySelector('#race-result').textContent") == (
        "Fast response."
    )

    window.evaluate_js("document.querySelector('#load-fragment').click()")
    api.wait_for("after:fragment-host")
    if window.evaluate_js("!!document.querySelector('#fragment-button')") is not True:
        raise RuntimeError("The fragment button was not inserted")
    window.evaluate_js("document.querySelector('#fragment-button').click()")
    api.wait_for("after:fragment-result")
    assert api.fragment_params == {"source": "native-fragment"}, api.fragment_params
    assert window.evaluate_js(
        "document.querySelector('#fragment-result').textContent",
    ) == "Fragment callback worked."

    window.evaluate_js("document.querySelector('#theme-button').click()")
    api.wait_for("after:theme-component")
    theme_name = window.evaluate_js(
        """document.querySelector(
          '#theme-component [data-pywebview-theme]'
        ).getAttribute('data-pywebview-theme')""",
    )
    assert theme_name == "paper"
    color_scheme = window.evaluate_js(
        "getComputedStyle(document.documentElement).colorScheme",
    )
    assert color_scheme == "light"


def main() -> None:
    name = 'İstanbul <bridge> "test"'
    api = API()
    window = create_window(
        "pywebview-htmx native smoke test",
        _html(name),
        js_api=api,
        start=False,
        hidden=True,
        focus=False,
    )
    failures: list[Exception] = []
    verified = Event()

    def check() -> None:
        try:
            _check(window, api, name)
            verified.set()
        except Exception as error:
            failures.append(error)
        finally:
            api.release_slow.set()
            window.destroy()

    try:
        webview.start(check)
    except Exception:
        api.release_slow.set()
        try:
            window.destroy()
        except Exception:
            pass
        raise
    if failures:
        raise failures[0]
    if not verified.is_set():
        raise RuntimeError("The native smoke test did not complete")
    print(f"Native smoke test passed ({webview.renderer})")


if __name__ == "__main__":
    main()
