# ruff: noqa: E501

from __future__ import annotations

import json
import time
from datetime import datetime
from html import escape as html_escape
from textwrap import dedent
from threading import Lock

from pywebview_htmx import (
    DEFAULT_THEME,
    create_window,
    encode_params_attr,
    get_theme_css,
    list_themes,
)


class API:
    def __init__(self) -> None:
        self._lock = Lock()
        self._activity_id = 0
        self._panel_version = 0
        self._morph_count = 0
        self._available_themes = list_themes()
        self._current_theme = DEFAULT_THEME

    @staticmethod
    def _stamp() -> str:
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _json_attr(payload: dict[str, object]) -> str:
        return encode_params_attr(payload)

    def _normalize_theme(self, requested: object) -> str:
        candidate = str(requested).strip().lower()
        if candidate in self._available_themes:
            return candidate
        return self._current_theme

    def _theme_picker_markup(self, active_theme: str) -> str:
        buttons_html = []
        for theme_name in self._available_themes:
            theme_payload = self._json_attr({"theme": theme_name})
            button_class = (
                "pyh-btn pyh-btn-primary"
                if theme_name == active_theme
                else "pyh-btn pyh-btn-ghost"
            )
            buttons_html.append(
                dedent(
                    f"""
                    <button
                      id="theme-{theme_name}"
                      class="{button_class}"
                      aria-pressed="{'true' if theme_name == active_theme else 'false'}"
                      py-call="switch_theme"
                      py-target="#theme-picker"
                      py-swap="outerHTML"
                      data-py-params="{theme_payload}">
                      {theme_name.title()}
                    </button>
                    """,
                ).strip(),
            )

        css = get_theme_css(active_theme)
        buttons_markup = "\n".join(buttons_html)
        return dedent(
            f"""
            <section id="theme-picker" class="pyh-card">
              <style data-pywebview-theme="{active_theme}">{css}</style>
              <h2>Theme</h2>
              <div class="pyh-row">
                {buttons_markup}
              </div>
              <p class="pyh-muted" data-demo-status role="status" aria-live="polite">
                Current theme: <strong>{active_theme}</strong>
              </p>
            </section>
            """,
        ).strip()

    def switch_theme(self, params: dict[str, object]) -> str:
        requested = params.get("theme", self._current_theme)
        with self._lock:
            self._current_theme = self._normalize_theme(requested)
            active_theme = self._current_theme
        return self._theme_picker_markup(active_theme)

    def fetch_profile(self, params: dict[str, object]) -> str:
        user_id = html_escape(str(params.get("user_id", "unknown")))
        role = html_escape(str(params.get("role", "guest")))
        return dedent(
            f"""
            <article class="pyh-result">
              <h4>Profile Lookup Complete</h4>
              <p><strong>User:</strong> {user_id}</p>
              <p><strong>Role:</strong> {role}</p>
              <p class="pyh-muted">Fetched at {self._stamp()}</p>
            </article>
            """
        ).strip()

    def add_activity(self, params: dict[str, object]) -> str:
        source = html_escape(str(params.get("source", "manual-action")))
        with self._lock:
            self._activity_id += 1
            activity_id = self._activity_id
        return (
            f"<li class=\"pyh-activity-row\">"
            f"<span class=\"pyh-chip\">#{activity_id}</span>"
            f"<span>{source}</span>"
            f"<span class=\"pyh-muted\">{self._stamp()}</span>"
            f"</li>"
        )

    def clear_activity(self, params: dict[str, object]) -> str:
        _ = params
        return '<li class="pyh-muted">Activity log cleared. Add a new event.</li>'

    def replace_panel(self, params: dict[str, object]) -> str:
        tone = html_escape(str(params.get("tone", "teal")))
        tone_class = "pyh-tone-amber" if tone == "amber" else "pyh-tone-teal"
        next_tone = "teal" if tone == "amber" else "amber"

        with self._lock:
            self._panel_version += 1
            panel_version = self._panel_version

        replace_params = self._json_attr({"tone": next_tone})
        ping_params = self._json_attr(
            {"scope": "outer-panel", "version": panel_version},
        )

        return dedent(
            f"""
            <section id="replaceable-card" class="pyh-card {tone_class} demo-example" data-demo-example>
              <h3>Replace a card</h3>
              <p>
                This card was replaced. Its action is ready again.
              </p>
              <p class="pyh-muted">Panel version: {panel_version}</p>
              <div class="pyh-row">
                <button
                  id="replace-panel-button"
                  class="pyh-btn pyh-btn-secondary"
                  py-call="replace_panel"
                  py-target="#replaceable-card"
                  py-swap="outerHTML"
                  data-py-params="{replace_params}">
                  Replace Again
                </button>
                <button
                  class="pyh-btn pyh-btn-ghost"
                  py-call="nested_ping"
                  py-target="#replaceable-log"
                  data-py-params="{ping_params}">
                  Nested Callback
                </button>
              </div>
              <p class="pyh-muted demo-status" data-demo-status role="status" aria-live="polite">Request complete.</p>
              <details><summary>Implementation</summary><p>The response keeps the button ID for focus restoration.</p></details>
            </section>
            """
        ).strip()

    def nested_ping(self, params: dict[str, object]) -> str:
        scope = html_escape(str(params.get("scope", "unknown-scope")))
        version = html_escape(str(params.get("version", "n/a")))
        return (
            '<p class="pyh-note">'
            f"Nested callback from <strong>{scope}</strong> "
            f"(v{version}) at {self._stamp()}"
            "</p>"
        )

    def morph_button(self, params: dict[str, object]) -> str:
        current_label = html_escape(str(params.get("label", "Morph Button")))
        with self._lock:
            self._morph_count += 1
            morph_count = self._morph_count

        next_payload = self._json_attr(
            {"label": f"Morph again (step {morph_count + 1})"},
        )

        return dedent(
            f"""
            <button
              id="morph-button"
              class="pyh-btn pyh-btn-primary pyh-full-width"
              py-call="morph_button"
              py-swap="outerHTML"
              py-wait=""
              data-py-params="{next_payload}">
              {current_label} (swap #{morph_count})
            </button>
            """
        ).strip()

    def echo_message(self, params: dict[str, object]) -> str:
        message = html_escape(str(params.get("message", ""))).strip() or "(empty message)"
        mood = html_escape(str(params.get("mood", "neutral")))
        return dedent(
            f"""
            <article class="pyh-result">
              <h4>Form Submit Trigger</h4>
              <p><strong>Mood:</strong> {mood}</p>
              <p><strong>Message:</strong> {message}</p>
              <p class="pyh-muted">Received at {self._stamp()}</p>
            </article>
            """
        ).strip()

    def show_params(self, params: dict[str, object]) -> str:
        payload = html_escape(json.dumps(params, indent=2, sort_keys=True))
        return f'<pre class="pyh-code">{payload}</pre>'

    def long_task(self, params: dict[str, object]) -> str:
        name = html_escape(str(params.get("name", "task")))
        delay_raw = params.get("delay", 1)
        try:
            delay = float(delay_raw)
        except (TypeError, ValueError):
            delay = 1.0
        delay = max(0.0, min(delay, 3.0))
        time.sleep(delay)
        return dedent(
            f"""
            <article class="pyh-result">
              <h4>Concurrency Demo</h4>
              <p>
                <strong>{name}</strong> completed in
                <strong>{delay:.1f}s</strong>.
              </p>
              <p class="pyh-muted">Completed at {self._stamp()}</p>
            </article>
            """
        ).strip()

    def load_fragment(self, params: dict[str, object]) -> str:
        theme = html_escape(str(params.get("theme", "mint")))
        ping_params = self._json_attr({"scope": "fragment", "version": self._stamp()})
        add_params = self._json_attr({"source": "fragment-button"})
        return dedent(
            f"""
            <article class="pyh-result fragment-{theme}">
              <h4>Dynamically Inserted Fragment</h4>
              <p>
                These buttons did not exist on first load. They work because
                PyWebview HTMX re-processes swapped content.
              </p>
              <div class="pyh-row">
                <button
                  class="pyh-btn pyh-btn-ghost"
                  py-call="nested_ping"
                  py-target="#fragment-log"
                  data-py-params="{ping_params}">
                  Fragment Ping
                </button>
                <button
                  class="pyh-btn pyh-btn-secondary"
                  py-call="add_activity"
                  py-target="#activity-list"
                  py-swap="append"
                  data-py-params="{add_params}">
                  Append Activity
                </button>
              </div>
            </article>
            """
        ).strip()

    def hover_tip(self, params: dict[str, object]) -> str:
        topic = html_escape(str(params.get("topic", "hover")))
        return (
            '<p class="pyh-note">'
            f"Triggered by <strong>{topic}</strong> at {self._stamp()}"
            "</p>"
        )


api = API()
DEMO_THEME = DEFAULT_THEME
assert DEMO_THEME in list_themes()

html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PyWebview HTMX Demo</title>
</head>
<body>
  <main class="pyh-shell">
    <header class="pyh-hero">
      <h1>PyWebview HTMX</h1>
      <p>
        Small examples show Python calls, HTML swaps, forms, and request behavior.
      </p>
    </header>

    __THEME_PICKER__

    <div class="pyh-grid">
      <section class="pyh-card demo-example" data-demo-example>
        <h3>1) Basic call</h3>
        <p class="pyh-muted">Call Python and show its response here.</p>
        <div class="pyh-row">
          <button
            id="fetch-profile-button"
            class="pyh-btn pyh-btn-primary"
            py-call="fetch_profile"
            py-target="#profile-result"
            py-swap="innerHTML"
            data-py-params='{"user_id": 42, "role": "operator"}'
            py-wait="#profile-wait">
            Fetch Profile
          </button>
          <span id="profile-wait" class="pyh-wait-target"><span class="pyh-busy-pill"></span>loading</span>
        </div>
        <p class="pyh-muted demo-status" data-demo-status role="status" aria-live="polite">Ready.</p>
        <div id="profile-result" class="pyh-note pyh-muted" role="status" aria-live="polite">Result appears here.</div>
        <details><summary>Implementation</summary><p>Uses <code>py-call</code>, <code>py-target</code>, <code>data-py-params</code>, and <code>py-wait</code>.</p></details>
      </section>

      <section class="pyh-card demo-example" data-demo-example>
        <h3>2) Append activity</h3>
        <p class="pyh-muted">Add an item to the list or clear it.</p>
        <div class="pyh-row">
          <button
            id="append-activity-button"
            class="pyh-btn pyh-btn-secondary"
            py-call="add_activity"
            py-target="#activity-list"
            py-swap="append"
            data-py-params='{"source": "append-button"}'>
            Append Activity
          </button>
          <button
            id="clear-activity-button"
            class="pyh-btn pyh-btn-danger"
            py-call="clear_activity"
            py-target="#activity-list"
            py-swap="innerHTML"
            data-py-params='{}'>
            Clear
          </button>
        </div>
        <p class="pyh-muted demo-status" data-demo-status role="status" aria-live="polite">Ready.</p>
        <ul id="activity-list" class="pyh-activity-list">
          <li class="pyh-muted">No activity yet.</li>
        </ul>
        <details><summary>Implementation</summary><p>The first call uses <code>py-swap="append"</code>. The second replaces the list contents.</p></details>
      </section>

      <section id="replaceable-card" class="pyh-card pyh-tone-teal demo-example" data-demo-example>
        <h3>3) Replace a card</h3>
        <p class="pyh-muted">Replace this card and keep its action available.</p>
        <div class="pyh-row">
          <button
            id="replace-panel-button"
            class="pyh-btn pyh-btn-secondary"
            py-call="replace_panel"
            py-target="#replaceable-card"
            py-swap="outerHTML"
            data-py-params='{"tone": "amber"}'>
            Replace Panel
          </button>
          <button
            id="nested-callback-button"
            class="pyh-btn pyh-btn-ghost"
            py-call="nested_ping"
            py-target="#replaceable-log"
            data-py-params='{"scope": "initial-outer-panel", "version": 0}'>
            Nested Callback
          </button>
        </div>
        <p class="pyh-muted demo-status" data-demo-status role="status" aria-live="polite">Ready.</p>
        <details><summary>Implementation</summary><p>The first call uses <code>py-swap="outerHTML"</code>. Its response keeps the button ID for focus restoration.</p></details>
      </section>

      <section class="pyh-card demo-example" data-demo-example>
        <h3>4) Replace this button</h3>
        <p class="pyh-muted">The response replaces the button that started the call.</p>
        <button
          id="morph-button"
          class="pyh-btn pyh-btn-primary pyh-full-width"
          py-call="morph_button"
          py-swap="outerHTML"
          py-wait=""
          data-py-params='{"label": "Morph me"}'>
          Morph me
        </button>
        <p class="pyh-muted demo-status" data-demo-status role="status" aria-live="polite">Ready.</p>
        <details><summary>Implementation</summary><p>With no <code>py-target</code>, the button is the target. Its response keeps the button ID for focus restoration.</p></details>
      </section>

      <section class="pyh-card demo-example" data-demo-example>
        <h3>5) Submit a form</h3>
        <p class="pyh-muted">Send the named fields to Python.</p>
        <form
          id="echo-form"
          class="pyh-fields"
          py-call="echo_message"
          py-trigger="submit"
          py-target="#echo-result"
          py-wait="#echo-form">
          <label for="echo-message">Message</label>
          <input id="echo-message" name="message" type="text" placeholder="Type a short message">
          <label for="echo-mood">Mood</label>
          <select id="echo-mood" name="mood">
            <option value="focused">focused</option>
            <option value="curious">curious</option>
            <option value="celebratory">celebratory</option>
          </select>
          <button id="echo-submit-button" class="pyh-btn pyh-btn-primary" type="submit">Submit</button>
        </form>
        <p class="pyh-muted demo-status" data-demo-status role="status" aria-live="polite">Ready.</p>
        <div id="echo-result" class="pyh-note pyh-muted" role="status" aria-live="polite">Form result appears here.</div>
        <details><summary>Implementation</summary><p>The form uses <code>py-trigger="submit"</code>. The runtime sends named fields to Python.</p></details>
      </section>

      <section class="pyh-card demo-example" data-demo-example>
        <h3>6) Validate request parameters</h3>
        <p class="pyh-muted">The second button has invalid JSON and will show an error here.</p>
        <div class="pyh-row">
          <button
            id="show-valid-params-button"
            class="pyh-btn pyh-btn-secondary"
            py-call="show_params"
            py-target="#params-result"
            data-py-params='{"valid": true, "count": 3}'>
            Show Valid Params
          </button>
          <button
            id="show-invalid-params-button"
            class="pyh-btn pyh-btn-danger"
            py-call="show_params"
            py-target="#params-result"
            data-py-params='{"broken": true'>
            Show Invalid Params
          </button>
        </div>
        <p id="params-status" class="pyh-muted demo-status" data-demo-status role="status" aria-live="polite">Ready.</p>
        <div id="params-result" class="pyh-note pyh-muted" role="status" aria-live="polite">Parameter payload appears here.</div>
        <details><summary>Implementation</summary><p>Invalid parameters raise <code>py:error</code> with phase <code>params</code>. Python is not called.</p></details>
      </section>

      <section class="pyh-card demo-example" id="race-card" data-demo-example>
        <h3>7) Request timing</h3>
        <p class="pyh-muted">Compare slow and fast calls. A timeout does not stop Python work.</p>
        <div class="pyh-row">
          <button
            id="run-slow-button"
            class="pyh-btn pyh-btn-secondary"
            py-call="long_task"
            py-target="#race-result"
            py-wait="#race-status"
            data-py-params='{"name": "slow-job", "delay": 1.6}'>
            Run Slow (1.6s)
          </button>
          <button
            id="run-fast-button"
            class="pyh-btn pyh-btn-primary"
            py-call="long_task"
            py-target="#race-result"
            py-wait="#race-status"
            data-py-params='{"name": "fast-job", "delay": 0.4}'>
            Run Fast (0.4s)
          </button>
          <button
            id="run-timeout-button"
            class="pyh-btn pyh-btn-danger"
            py-call="long_task"
            py-target="#race-result"
            py-wait="#race-status"
            py-policy="drop"
            py-timeout="250"
            data-py-params='{"name": "long-job", "delay": 1.2}'>
            Run with 250 ms timeout
          </button>
          <span id="race-status" class="pyh-wait-target"><span class="pyh-busy-pill"></span>running</span>
        </div>
        <p id="race-demo-status" class="pyh-muted demo-status" data-demo-status role="status" aria-live="polite">Ready.</p>
        <div id="race-result" class="pyh-note pyh-muted" role="status" aria-live="polite">Result appears here.</div>
        <details><summary>Implementation</summary><p>The first two calls use the selected request policy. The last uses <code>py-policy="drop"</code> and <code>py-timeout="250"</code>. A timeout reports an error. It does not cancel Python work or retry the call.</p></details>
      </section>

      <section class="pyh-card demo-example" data-demo-example>
        <h3>8) Load a fragment</h3>
        <p class="pyh-muted">Add new buttons, then use them.</p>
        <div class="pyh-row">
          <button
            id="load-fragment-button"
            class="pyh-btn pyh-btn-ghost"
            py-call="load_fragment"
            py-target="#fragment-host"
            data-py-params='{"theme": "mint"}'>
            Load Fragment
          </button>
        </div>
        <p class="pyh-muted demo-status" data-demo-status role="status" aria-live="polite">Ready.</p>
        <div id="fragment-host" class="pyh-note pyh-muted" role="status" aria-live="polite">Fragment goes here.</div>
        <div id="fragment-log" class="pyh-note pyh-muted">Fragment callback log.</div>
        <details><summary>Implementation</summary><p>Swapped fragments are processed so their new buttons can call Python.</p></details>
      </section>

      <section class="pyh-card demo-example" data-demo-example>
        <h3>9) Use a hover trigger</h3>
        <p class="pyh-muted">Move the pointer over the box to call Python.</p>
        <div
          class="pyh-hover-target"
          py-call="hover_tip"
          py-trigger="mouseenter"
          py-target="#hover-result"
          data-py-params='{"topic": "mouse-enter trigger"}'>
          Hover this box
        </div>
        <p class="pyh-muted demo-status" data-demo-status role="status" aria-live="polite">Ready.</p>
        <div id="hover-result" class="pyh-note pyh-muted" role="status" aria-live="polite">Hover result appears here.</div>
        <details><summary>Implementation</summary><p>The box uses <code>py-trigger="mouseenter"</code> instead of a click.</p></details>
      </section>
    </div>

    <details class="pyh-card" id="runtime-diagnostics">
      <summary>Runtime diagnostics</summary>
      <p class="pyh-muted">Change request behavior and inspect lifecycle events.</p>
      <div class="pyh-inline-config">
        <label><input type="radio" name="policy" value="latest-wins" checked>latest-wins</label>
        <label><input type="radio" name="policy" value="drop">drop while in-flight</label>
        <label for="swap-delay">Swap delay</label>
        <input id="swap-delay" type="range" min="0" max="900" step="100" value="0">
        <label for="settle-delay">Settle delay</label>
        <input id="settle-delay" type="range" min="0" max="600" step="100" value="20">
      </div>
      <p id="config-state" class="pyh-muted">Request settings are ready.</p>
      <ol id="event-log" class="pyh-event-log" aria-label="Runtime events"></ol>
      <h3>Outer card callback</h3>
      <div id="replaceable-log" class="pyh-note pyh-muted">Callback log.</div>
    </details>
  </main>

  <script>
    document.addEventListener("DOMContentLoaded", () => {
      const eventLog = document.querySelector("#event-log");
      const configState = document.querySelector("#config-state");
      const swapDelay = document.querySelector("#swap-delay");
      const settleDelay = document.querySelector("#settle-delay");
      const policyInputs = Array.from(document.querySelectorAll("input[name='policy']"));

      const pushEvent = (text, tone = "") => {
        const item = document.createElement("li");
        item.textContent = text;
        if (tone) {
          item.classList.add(tone);
        }
        eventLog.prepend(item);
        while (eventLog.children.length > 24) {
          eventLog.removeChild(eventLog.lastElementChild);
        }
      };

      const statusFor = (element) => {
        const example = element && element.closest("[data-demo-example]");
        return example && example.querySelector("[data-demo-status]");
      };

      const applyConfig = () => {
        const selected = document.querySelector("input[name='policy']:checked");
        if (!window.pywebviewHtmx || !selected) {
          return;
        }

        window.pywebviewHtmx.config.requestPolicy = selected.value;
        window.pywebviewHtmx.config.swapDelay = Number(swapDelay.value);
        window.pywebviewHtmx.config.settleDelay = Number(settleDelay.value);

        configState.textContent =
          "requestPolicy=" + window.pywebviewHtmx.config.requestPolicy +
          " | swapDelay=" + window.pywebviewHtmx.config.swapDelay + "ms" +
          " | settleDelay=" + window.pywebviewHtmx.config.settleDelay + "ms";
      };

      policyInputs.forEach((input) => input.addEventListener("change", applyConfig));
      swapDelay.addEventListener("input", applyConfig);
      settleDelay.addEventListener("input", applyConfig);
      applyConfig();

      const eventNames = [
        "py:trigger",
        "py:beforeSwap",
        "py:afterSwap",
        "py:ignored",
        "py:error",
      ];

      eventNames.forEach((eventName) => {
        document.body.addEventListener(
          eventName,
          (event) => {
            const callName = event.target.getAttribute && event.target.getAttribute("py-call");
            const detail = event.detail || {};
            const requestId = detail.requestId;
            const suffix = requestId ? " #" + requestId : "";
            const detailText = callName ? " (" + callName + ")" : "";

            let tone = "";
            if (eventName === "py:error") {
              tone = "pyh-error";
              const source = detail.element;
              const error = detail.error || {};
              const status = statusFor(source);
              const timedOut = detail.phase === "timeout" || error.name === "TimeoutError";
              if (status && source && source.isConnected && !detail.stale) {
                status.textContent = timedOut
                  ? "Request timed out. Python may still be working; no retry was sent."
                  : "Request failed: " + (error.message || "Unknown error");
              }
            } else if (eventName === "py:ignored") {
              tone = "pyh-warn";
            } else if (eventName === "py:trigger") {
              const status = statusFor(event.target);
              if (status) {
                status.textContent = "Request started: " + (callName || "Python call") + ".";
              }
            } else if (eventName === "py:afterSwap") {
              const status = statusFor(event.target);
              if (status) {
                status.textContent = "Request complete.";
              }
            }

            pushEvent(
              "[" + new Date().toLocaleTimeString() + "] " + eventName + detailText + suffix,
              tone,
            );
          },
          true,
        );
      });

      pushEvent("Demo ready. Interact with any card to inspect behavior.");
    });
  </script>
</body>
</html>
"""

html_content = html_content.replace(
    "__THEME_PICKER__",
    api.switch_theme({"theme": DEMO_THEME}),
)

if __name__ == "__main__":
    create_window(
        "PyWebview HTMX Feature Showcase",
        html_content,
        js_api=api,
        theme=None,
    )
