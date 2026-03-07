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
            button_class = "btn btn-primary" if theme_name == active_theme else "btn btn-ghost"
            buttons_html.append(
                dedent(
                    f"""
                    <button
                      class="{button_class}"
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
            <section id="theme-picker" class="demo-card">
              <style data-pywebview-theme="{active_theme}">{css}</style>
              <h2>Theme Picker (Python-backed)</h2>
              <p class="muted">
                These buttons call Python and swap this entire section. The returned
                HTML includes a new <code>&lt;style data-pywebview-theme=...&gt;</code>
                block, so the live UI theme changes immediately.
              </p>
              <div class="button-row">
                {buttons_markup}
              </div>
              <p class="muted">
                Active theme from Python response:
                <strong>{active_theme}</strong>
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
            <article class="result-card">
              <h4>Profile Lookup Complete</h4>
              <p><strong>User:</strong> {user_id}</p>
              <p><strong>Role:</strong> {role}</p>
              <p class="muted">Fetched at {self._stamp()}</p>
            </article>
            """
        ).strip()

    def add_activity(self, params: dict[str, object]) -> str:
        source = html_escape(str(params.get("source", "manual-action")))
        with self._lock:
            self._activity_id += 1
            activity_id = self._activity_id
        return (
            f"<li class=\"activity-row\">"
            f"<span class=\"chip\">#{activity_id}</span>"
            f"<span>{source}</span>"
            f"<span class=\"muted\">{self._stamp()}</span>"
            f"</li>"
        )

    def clear_activity(self, params: dict[str, object]) -> str:
        _ = params
        return '<li class="muted">Activity log cleared. Add a new event.</li>'

    def replace_panel(self, params: dict[str, object]) -> str:
        tone = html_escape(str(params.get("tone", "teal")))
        tone_class = "tone-amber" if tone == "amber" else "tone-teal"
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
            <section id="replaceable-card" class="demo-card {tone_class}">
              <h3>OuterHTML Replacement</h3>
              <p>
                This whole card was replaced using
                <code>py-swap="outerHTML"</code>.
              </p>
              <p class="muted">Panel version: {panel_version}</p>
              <div class="button-row">
                <button
                  class="btn btn-secondary"
                  py-call="replace_panel"
                  py-target="#replaceable-card"
                  py-swap="outerHTML"
                  data-py-params="{replace_params}">
                  Replace Again
                </button>
                <button
                  class="btn btn-ghost"
                  py-call="nested_ping"
                  py-target="#replaceable-log"
                  data-py-params="{ping_params}">
                  Nested Callback
                </button>
              </div>
            </section>
            """
        ).strip()

    def nested_ping(self, params: dict[str, object]) -> str:
        scope = html_escape(str(params.get("scope", "unknown-scope")))
        version = html_escape(str(params.get("version", "n/a")))
        return (
            '<p class="result-note">'
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
              class="btn btn-primary full-width"
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
            <article class="result-card">
              <h4>Form Submit Trigger</h4>
              <p><strong>Mood:</strong> {mood}</p>
              <p><strong>Message:</strong> {message}</p>
              <p class="muted">Received at {self._stamp()}</p>
            </article>
            """
        ).strip()

    def show_params(self, params: dict[str, object]) -> str:
        payload = html_escape(json.dumps(params, indent=2, sort_keys=True))
        return f'<pre class="code-block">{payload}</pre>'

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
            <article class="result-card">
              <h4>Concurrency Demo</h4>
              <p>
                <strong>{name}</strong> completed in
                <strong>{delay:.1f}s</strong>.
              </p>
              <p class="muted">Completed at {self._stamp()}</p>
            </article>
            """
        ).strip()

    def load_fragment(self, params: dict[str, object]) -> str:
        theme = html_escape(str(params.get("theme", "mint")))
        ping_params = self._json_attr({"scope": "fragment", "version": self._stamp()})
        add_params = self._json_attr({"source": "fragment-button"})
        return dedent(
            f"""
            <article class="result-card fragment-{theme}">
              <h4>Dynamically Inserted Fragment</h4>
              <p>
                These buttons did not exist on first load. They work because
                PyWebview HTMX re-processes swapped content.
              </p>
              <div class="button-row">
                <button
                  class="btn btn-ghost"
                  py-call="nested_ping"
                  py-target="#fragment-log"
                  data-py-params="{ping_params}">
                  Fragment Ping
                </button>
                <button
                  class="btn btn-secondary"
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
            '<p class="result-note">'
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
  <title>PyWebview HTMX Feature Showcase</title>
</head>
<body>
  <main class="app-shell">
    <header class="hero">
      <h1>PyWebview HTMX Feature Showcase</h1>
      <p>
        This demo intentionally exercises many PyWebview HTMX capabilities: trigger types,
        parameter payloads, swap modes (<code>innerHTML</code>,
        <code>append</code>, <code>outerHTML</code>), wait targets,
        concurrency policy, lifecycle events, and re-processing swapped fragments.
      </p>
      <div class="badge-row">
        <span class="chip">Live theme switch uses a Python API call</span>
        <span class="chip">Theme CSS is shipped in the PyWebview HTMX package</span>
        <span class="chip">Styling system: CSS tokens</span>
        <span class="chip">Reusable components: card, button, field</span>
        <span class="chip">Utilities: grid, spacing, full-width</span>
      </div>
    </header>

    __THEME_PICKER__

    <section class="demo-card">
      <h2>Runtime Controls + Event Feed</h2>
      <p class="muted">
        Toggle request behavior and timing live. Event logs show
        <code>py:trigger</code>, <code>py:beforeSwap</code>,
        <code>py:afterSwap</code>, <code>py:ignored</code>, and
        <code>py:error</code>.
      </p>
      <div class="inline-config">
        <label><input type="radio" name="policy" value="latest-wins" checked>latest-wins</label>
        <label><input type="radio" name="policy" value="drop">drop while in-flight</label>
        <label>swapDelay <input id="swap-delay" type="range" min="0" max="900" step="100" value="0"></label>
        <label>settleDelay <input id="settle-delay" type="range" min="0" max="600" step="100" value="20"></label>
      </div>
      <p id="config-state" class="muted">config state pending...</p>
      <ol id="event-log" class="event-log"></ol>
    </section>

    <div class="grid">
      <section class="demo-card">
        <h3>1) Basic call + wait target + innerHTML</h3>
        <p class="muted">Uses <code>py-call</code>, <code>py-target</code>, <code>data-py-params</code>, and <code>py-wait</code>.</p>
        <div class="button-row">
          <button
            class="btn btn-primary"
            py-call="fetch_profile"
            py-target="#profile-result"
            py-swap="innerHTML"
            data-py-params='{"user_id": 42, "role": "operator"}'
            py-wait="#profile-wait">
            Fetch Profile
          </button>
          <span id="profile-wait" class="wait-target"><span class="busy-pill"></span>loading</span>
        </div>
        <div id="profile-result" class="result-note muted">Result appears here.</div>
      </section>

      <section class="demo-card">
        <h3>2) Append swap strategy</h3>
        <p class="muted">Adds list rows with <code>py-swap="append"</code>.</p>
        <div class="button-row">
          <button
            class="btn btn-secondary"
            py-call="add_activity"
            py-target="#activity-list"
            py-swap="append"
            data-py-params='{"source": "append-button"}'>
            Append Activity
          </button>
          <button
            class="btn btn-danger"
            py-call="clear_activity"
            py-target="#activity-list"
            py-swap="innerHTML"
            data-py-params='{}'>
            Clear
          </button>
        </div>
        <ul id="activity-list" class="activity-list">
          <li class="muted">No activity yet.</li>
        </ul>
      </section>

      <section id="replaceable-card" class="demo-card tone-teal">
        <h3>3) OuterHTML swap strategy</h3>
        <p class="muted">Replaces the entire card with a new version.</p>
        <div class="button-row">
          <button
            class="btn btn-secondary"
            py-call="replace_panel"
            py-target="#replaceable-card"
            py-swap="outerHTML"
            data-py-params='{"tone": "amber"}'>
            Replace Panel
          </button>
          <button
            class="btn btn-ghost"
            py-call="nested_ping"
            py-target="#replaceable-log"
            data-py-params='{"scope": "initial-outer-panel", "version": 0}'>
            Nested Callback
          </button>
        </div>
      </section>

      <section class="demo-card">
        <h3>4) Self-target fallback (no py-target)</h3>
        <p class="muted">This button swaps itself with <code>py-swap="outerHTML"</code>.</p>
        <button
          class="btn btn-primary full-width"
          py-call="morph_button"
          py-swap="outerHTML"
          py-wait=""
          data-py-params='{"label": "Morph me"}'>
          Morph me
        </button>
      </section>

      <section class="demo-card">
        <h3>5) Custom trigger: form submit</h3>
        <p class="muted">The form uses <code>py-trigger="submit"</code> and PyWebview HTMX serializes named fields automatically.</p>
        <form
          id="echo-form"
          class="field-row"
          py-call="echo_message"
          py-trigger="submit"
          py-target="#echo-result"
          py-wait="#echo-form">
          <input id="echo-message" name="message" type="text" placeholder="Type a short message">
          <select id="echo-mood" name="mood">
            <option value="focused">focused</option>
            <option value="curious">curious</option>
            <option value="celebratory">celebratory</option>
          </select>
          <button class="btn btn-primary" type="submit">Submit Form Trigger</button>
        </form>
        <div id="echo-result" class="result-note muted">Form result appears here.</div>
      </section>

      <section class="demo-card">
        <h3>6) Params parsing behavior</h3>
        <p class="muted">Second button has intentionally invalid JSON and should fallback to <code>{}</code>.</p>
        <div class="button-row">
          <button
            class="btn btn-secondary"
            py-call="show_params"
            py-target="#params-result"
            data-py-params='{"valid": true, "count": 3}'>
            Show Valid Params
          </button>
          <button
            class="btn btn-danger"
            py-call="show_params"
            py-target="#params-result"
            data-py-params='{"broken": true'>
            Show Invalid Params
          </button>
        </div>
        <div id="params-result" class="result-note muted">Parameter payload appears here.</div>
      </section>

      <section class="demo-card" id="race-card">
        <h3>7) Concurrency policy demo</h3>
        <p class="muted">Click slow then fast to see <code>latest-wins</code> vs <code>drop</code> behavior.</p>
        <div class="button-row">
          <button
            class="btn btn-secondary"
            py-call="long_task"
            py-target="#race-result"
            py-wait="#race-status"
            data-py-params='{"name": "slow-job", "delay": 1.6}'>
            Run Slow (1.6s)
          </button>
          <button
            class="btn btn-primary"
            py-call="long_task"
            py-target="#race-result"
            py-wait="#race-status"
            data-py-params='{"name": "fast-job", "delay": 0.4}'>
            Run Fast (0.4s)
          </button>
          <span id="race-status" class="wait-target"><span class="busy-pill"></span>running</span>
        </div>
        <div id="race-result" class="result-note muted">Race result appears here.</div>
      </section>

      <section class="demo-card">
        <h3>8) Dynamic fragment re-processing</h3>
        <p class="muted">Loads new buttons at runtime; they work immediately.</p>
        <div class="button-row">
          <button
            class="btn btn-ghost"
            py-call="load_fragment"
            py-target="#fragment-host"
            data-py-params='{"theme": "mint"}'>
            Load Fragment
          </button>
        </div>
        <div id="fragment-host" class="result-note muted">Fragment goes here.</div>
        <div id="fragment-log" class="result-note muted">Fragment callback log.</div>
      </section>

      <section class="demo-card">
        <h3>9) Custom trigger: mouseenter</h3>
        <p class="muted">Hover the dashed box to trigger a non-click event.</p>
        <div
          class="hover-target"
          py-call="hover_tip"
          py-trigger="mouseenter"
          py-target="#hover-result"
          data-py-params='{"topic": "mouse-enter trigger"}'>
          Hover this box
        </div>
        <div id="hover-result" class="result-note muted">Hover result appears here.</div>
      </section>
    </div>

    <section class="demo-card">
      <h3>OuterHTML nested callback log</h3>
      <div id="replaceable-log" class="result-note muted">Outer panel callback log.</div>
    </section>
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
            const requestId = event.detail && event.detail.requestId;
            const suffix = requestId ? " #" + requestId : "";
            const detailText = callName ? " (" + callName + ")" : "";

            let tone = "";
            if (eventName === "py:error") {
              tone = "error";
            } else if (eventName === "py:ignored") {
              tone = "warn";
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
