# ruff: noqa: E501

from __future__ import annotations

import json
import time
from datetime import datetime
from html import escape as html_escape
from textwrap import dedent
from threading import Lock

from pyhtmx import create_window


class API:
    def __init__(self) -> None:
        self._lock = Lock()
        self._activity_id = 0
        self._panel_version = 0
        self._morph_count = 0

    @staticmethod
    def _stamp() -> str:
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _json_attr(payload: dict[str, object]) -> str:
        return html_escape(json.dumps(payload), quote=True)

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
                pyHTMX re-processes swapped content.
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

html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>pyHTMX Feature Showcase</title>
  <style>
    :root {
      --bg-top: #071423;
      --bg-mid: #0d2235;
      --bg-bottom: #102c40;
      --surface: rgba(255, 255, 255, 0.1);
      --surface-strong: rgba(255, 255, 255, 0.16);
      --border: rgba(255, 255, 255, 0.22);
      --text: #f4f8fb;
      --text-muted: #b8c7d4;
      --accent: #55e1b8;
      --accent-2: #f7ba54;
      --danger: #ef6f6f;
      --radius: 16px;
      --radius-sm: 10px;
      --shadow: 0 16px 36px rgba(0, 0, 0, 0.25);
      --space-1: 8px;
      --space-2: 12px;
      --space-3: 16px;
      --space-4: 24px;
      --space-5: 32px;
      --font-ui: "Avenir Next", "Trebuchet MS", "Segoe UI", sans-serif;
      --font-headline: "Gill Sans", "Trebuchet MS", sans-serif;
      --font-mono: "SFMono-Regular", "Menlo", "Consolas", monospace;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      color: var(--text);
      font-family: var(--font-ui);
      background:
        radial-gradient(1200px 600px at 90% -10%, rgba(85, 225, 184, 0.18), transparent 70%),
        radial-gradient(900px 420px at 0% 110%, rgba(247, 186, 84, 0.18), transparent 70%),
        linear-gradient(160deg, var(--bg-top), var(--bg-mid) 45%, var(--bg-bottom));
      min-height: 100vh;
    }

    .app-shell {
      width: min(1200px, 94vw);
      margin: var(--space-5) auto;
      display: grid;
      gap: var(--space-4);
    }

    .hero,
    .demo-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      backdrop-filter: blur(12px);
    }

    .hero {
      padding: var(--space-5);
      display: grid;
      gap: var(--space-3);
    }

    .hero h1 {
      margin: 0;
      font-family: var(--font-headline);
      font-size: clamp(1.8rem, 4vw, 2.8rem);
      letter-spacing: 0.02em;
    }

    .hero p {
      margin: 0;
      color: var(--text-muted);
      max-width: 78ch;
      line-height: 1.5;
    }

    .badge-row {
      display: flex;
      flex-wrap: wrap;
      gap: var(--space-2);
    }

    .chip {
      display: inline-flex;
      align-items: center;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.14);
      border: 1px solid rgba(255, 255, 255, 0.2);
      font-size: 0.82rem;
      line-height: 1;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: var(--space-3);
    }

    .demo-card {
      padding: var(--space-4);
      display: grid;
      gap: var(--space-3);
      align-content: start;
    }

    .tone-teal {
      border-color: rgba(85, 225, 184, 0.5);
    }

    .tone-amber {
      border-color: rgba(247, 186, 84, 0.5);
    }

    h2,
    h3,
    h4 {
      margin: 0;
      font-family: var(--font-headline);
      letter-spacing: 0.01em;
    }

    p {
      margin: 0;
      line-height: 1.45;
    }

    .muted {
      color: var(--text-muted);
    }

    .button-row {
      display: flex;
      flex-wrap: wrap;
      gap: var(--space-2);
    }

    .btn {
      border: 1px solid transparent;
      border-radius: var(--radius-sm);
      padding: 10px 14px;
      font-weight: 700;
      cursor: pointer;
      transition: transform 120ms ease, filter 120ms ease;
      color: #0a1d2d;
      background: #dce8f1;
      min-height: 40px;
    }

    .btn:hover {
      transform: translateY(-1px);
      filter: brightness(1.06);
    }

    .btn-primary {
      background: linear-gradient(130deg, #79ffd3, #55e1b8);
    }

    .btn-secondary {
      background: linear-gradient(130deg, #ffd899, #f7ba54);
    }

    .btn-ghost {
      background: rgba(255, 255, 255, 0.12);
      color: var(--text);
      border-color: rgba(255, 255, 255, 0.28);
    }

    .btn-danger {
      background: linear-gradient(130deg, #ffb8b8, #ef6f6f);
    }

    .full-width {
      width: 100%;
    }

    .field-row {
      display: grid;
      gap: var(--space-2);
    }

    .field-row input,
    .field-row select {
      width: 100%;
      border-radius: var(--radius-sm);
      border: 1px solid rgba(255, 255, 255, 0.24);
      background: rgba(255, 255, 255, 0.1);
      color: var(--text);
      padding: 10px 12px;
      min-height: 38px;
      font: inherit;
    }

    .field-row input::placeholder {
      color: #d2deea;
      opacity: 0.8;
    }

    .result-card,
    .result-note,
    .code-block,
    .event-log,
    .activity-list,
    .hover-target {
      border-radius: var(--radius-sm);
      border: 1px solid rgba(255, 255, 255, 0.22);
      background: rgba(7, 20, 35, 0.35);
      padding: 12px;
    }

    .result-card {
      display: grid;
      gap: 6px;
    }

    .code-block {
      margin: 0;
      font-family: var(--font-mono);
      font-size: 0.82rem;
      line-height: 1.35;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .activity-list {
      margin: 0;
      padding-left: 0;
      list-style: none;
      display: grid;
      gap: 8px;
    }

    .activity-row {
      display: flex;
      gap: 10px;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      border-bottom: 1px dashed rgba(255, 255, 255, 0.2);
      padding-bottom: 6px;
    }

    .hover-target {
      min-height: 56px;
      display: grid;
      place-items: center;
      text-align: center;
      border-style: dashed;
      cursor: default;
    }

    .wait-target {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--text-muted);
      font-size: 0.88rem;
    }

    .busy-pill {
      width: 14px;
      height: 14px;
      border-radius: 999px;
      border: 2px solid rgba(255, 255, 255, 0.35);
      border-top-color: var(--accent);
      animation: spin 800ms linear infinite;
      visibility: hidden;
    }

    .wait-target.py-waiting .busy-pill {
      visibility: visible;
    }

    .py-waiting {
      opacity: 0.55;
      filter: saturate(0.7);
      pointer-events: none;
    }

    .event-log {
      margin: 0;
      padding-left: 0;
      list-style: none;
      max-height: 260px;
      overflow: auto;
      display: grid;
      gap: 6px;
      font-size: 0.85rem;
      font-family: var(--font-mono);
    }

    .event-log li {
      padding: 6px 8px;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.14);
    }

    .event-log li.warn {
      border-color: rgba(247, 186, 84, 0.55);
    }

    .event-log li.error {
      border-color: rgba(239, 111, 111, 0.65);
      color: #ffe2e2;
    }

    .inline-config {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }

    .inline-config label {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 10px;
      border-radius: 999px;
      border: 1px solid rgba(255, 255, 255, 0.25);
      background: rgba(255, 255, 255, 0.09);
      font-size: 0.88rem;
    }

    code {
      font-family: var(--font-mono);
      font-size: 0.9em;
      background: rgba(255, 255, 255, 0.12);
      border-radius: 6px;
      padding: 2px 5px;
    }

    @keyframes spin {
      to {
        transform: rotate(360deg);
      }
    }

    @media (max-width: 720px) {
      .app-shell {
        margin: var(--space-4) auto;
      }

      .hero,
      .demo-card {
        padding: var(--space-3);
      }
    }
  </style>
</head>
<body>
  <main class="app-shell">
    <header class="hero">
      <h1>pyHTMX Feature Showcase</h1>
      <p>
        This demo intentionally exercises many pyHTMX capabilities: trigger types,
        parameter payloads, swap modes (<code>innerHTML</code>,
        <code>append</code>, <code>outerHTML</code>), wait targets,
        concurrency policy, lifecycle events, and re-processing swapped fragments.
      </p>
      <div class="badge-row">
        <span class="chip">Styling system: CSS tokens</span>
        <span class="chip">Reusable components: card, button, field</span>
        <span class="chip">Utilities: grid, spacing, full-width</span>
      </div>
    </header>

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
        <p class="muted">The form uses <code>py-trigger="submit"</code> and JS keeps payload synced.</p>
        <form
          id="echo-form"
          class="field-row"
          py-call="echo_message"
          py-trigger="submit"
          py-target="#echo-result"
          data-py-params='{}'
          py-wait="#echo-form">
          <input id="echo-message" type="text" placeholder="Type a short message">
          <select id="echo-mood">
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
      const form = document.querySelector("#echo-form");
      const messageInput = document.querySelector("#echo-message");
      const moodInput = document.querySelector("#echo-mood");
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

      const syncFormParams = () => {
        const params = {
          message: messageInput.value,
          mood: moodInput.value,
        };
        form.setAttribute("data-py-params", JSON.stringify(params));
      };

      const applyConfig = () => {
        const selected = document.querySelector("input[name='policy']:checked");
        if (!window.pyhtmx || !selected) {
          return;
        }

        window.pyhtmx.config.requestPolicy = selected.value;
        window.pyhtmx.config.swapDelay = Number(swapDelay.value);
        window.pyhtmx.config.settleDelay = Number(settleDelay.value);

        configState.textContent =
          "requestPolicy=" + window.pyhtmx.config.requestPolicy +
          " | swapDelay=" + window.pyhtmx.config.swapDelay + "ms" +
          " | settleDelay=" + window.pyhtmx.config.settleDelay + "ms";
      };

      syncFormParams();
      messageInput.addEventListener("input", syncFormParams);
      moodInput.addEventListener("change", syncFormParams);
      form.addEventListener("submit", syncFormParams, true);

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

if __name__ == "__main__":
    create_window("pyHTMX Feature Showcase", html_content, js_api=api)
