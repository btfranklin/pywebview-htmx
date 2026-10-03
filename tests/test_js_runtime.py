from __future__ import annotations

import json
from dataclasses import dataclass, field

import pytest
from playwright.sync_api import Page

from pywebview_htmx import get_theme_css


@dataclass
class RuntimeBrowser:
    page: Page
    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    expected_console_errors: list[str] = field(default_factory=list)

    def load(self, html: str, js_source: str) -> None:
        self.page.set_content(html)
        self.page.add_script_tag(content=js_source)
        self.page.evaluate(
            """
            () => {
              window.pywebviewHtmx.config.settleDelay = 0;
              window.pywebviewHtmx.config.swapDelay = 0;
            }
            """
        )

    def process(self) -> None:
        self.page.evaluate("window.pywebviewHtmx.process(document.body)")

    def expect_console_error(self, substring: str) -> None:
        self.expected_console_errors.append(substring)

    def assert_logs(self) -> None:
        assert not self.page_errors, self.page_errors
        unmatched = list(self.console_errors)
        for expected in self.expected_console_errors:
            match = next((item for item in unmatched if expected in item), None)
            assert match is not None, (
                f"Expected console error containing {expected!r}; got {unmatched!r}"
            )
            unmatched.remove(match)
        assert not unmatched, f"Unexpected browser console errors: {unmatched!r}"


@pytest.fixture
def runtime_browser(page: Page) -> RuntimeBrowser:
    browser = RuntimeBrowser(page)
    page.on(
        "console",
        lambda message: (
            browser.console_errors.append(message.text)
            if message.type == "error"
            else None
        ),
    )
    page.on("pageerror", lambda error: browser.page_errors.append(str(error)))
    yield browser
    browser.assert_logs()


def install_pending_bridge(page: Page, method: str = "load") -> None:
    page.evaluate(
        """
        method => {
          window.bridgeCalls = [];
          window.pendingRequests = [];
          window.pywebview = {api: {}};
          window.pywebview.api[method] = params => {
            window.bridgeCalls.push(params);
            return new Promise((resolve, reject) => {
              window.pendingRequests.push({resolve, reject});
            });
          };
        }
        """,
        method,
    )


def resolve_request(page: Page, index: int, response: str) -> None:
    page.evaluate(
        "([index, response]) => window.pendingRequests[index].resolve(response)",
        [index, response],
    )


def reject_request(page: Page, index: int, message: str) -> None:
    page.evaluate(
        "([index, message]) => "
        "window.pendingRequests[index].reject(new Error(message))",
        [index, message],
    )


def test_latest_request_wins_for_stable_selector_scope(
    runtime_browser: RuntimeBrowser,
    js_source: str,
) -> None:
    runtime_browser.load(
        """
        <button id="slow" py-call="load" py-target="#result">Slow</button>
        <button id="fast" py-call="load" py-target="#result">Fast</button>
        <div id="result">initial</div>
        """,
        js_source,
    )
    page = runtime_browser.page
    install_pending_bridge(page)
    runtime_browser.process()

    page.locator("#slow").click()
    page.locator("#fast").click()
    assert page.evaluate("window.pendingRequests.length") == 2

    resolve_request(page, 1, "<p>fast</p>")
    page.locator("#result").get_by_text("fast").wait_for()
    resolve_request(page, 0, "<p>slow</p>")

    page.wait_for_timeout(20)
    assert page.locator("#result").inner_text() == "fast"


def test_latest_request_wins_after_ancestor_replaces_target(
    runtime_browser: RuntimeBrowser,
    js_source: str,
) -> None:
    runtime_browser.load(
        """
        <button id="slow" py-call="load" py-target="#result">Slow</button>
        <button id="replace" py-call="replace" py-target="#host"
                py-swap="outerHTML">Replace host</button>
        <section id="host"><div id="result">initial</div></section>
        """,
        js_source,
    )
    page = runtime_browser.page
    install_pending_bridge(page)
    page.evaluate(
        """
        () => {
          window.pywebview.api.replace = () => `
            <section id="host">
              <button id="fast" py-call="load" py-target="#result">Fast</button>
              <div id="result">replacement</div>
            </section>`;
        }
        """
    )
    runtime_browser.process()

    page.locator("#slow").click()
    page.locator("#replace").click()
    page.locator("#fast").wait_for()
    page.locator("#fast").click()
    assert page.evaluate("window.pendingRequests.length") == 2

    resolve_request(page, 1, "<p>fast</p>")
    page.locator("#result").get_by_text("fast").wait_for()
    resolve_request(page, 0, "<p>slow</p>")

    page.wait_for_timeout(20)
    assert page.locator("#result").inner_text() == "fast"


def test_drop_policy_spans_controls_and_target_replacement(
    runtime_browser: RuntimeBrowser,
    js_source: str,
) -> None:
    runtime_browser.load(
        """
        <button id="first" py-call="load" py-policy="drop"
                py-target="#result" py-swap="outerHTML">First</button>
        <button id="second" py-call="load" py-policy="drop"
                py-target="#result" py-swap="outerHTML">Second</button>
        <div id="result">initial</div>
        """,
        js_source,
    )
    page = runtime_browser.page
    install_pending_bridge(page)
    page.evaluate(
        """
        () => {
          window.ignoredEvents = [];
          document.addEventListener('py:ignored', event => {
            event.preventDefault();
            window.ignoredEvents.push({
              cancelable: event.cancelable,
              defaultPrevented: event.defaultPrevented,
              reason: event.detail.reason,
            });
          });
        }
        """
    )
    runtime_browser.process()
    page.evaluate("window.pywebviewHtmx.config.settleDelay = 100")

    page.locator("#first").click()
    page.locator("#second").click()
    assert page.evaluate("window.pendingRequests.length") == 1
    assert page.evaluate("window.ignoredEvents") == [
        {
            "cancelable": False,
            "defaultPrevented": False,
            "reason": "in-flight",
        }
    ]

    resolve_request(page, 0, '<div id="result">first</div>')
    page.locator("#result").get_by_text("first").wait_for()
    page.locator("#second").click()
    assert page.evaluate("window.pendingRequests.length") == 1
    assert len(page.evaluate("window.ignoredEvents")) == 2

    page.wait_for_timeout(120)
    page.locator("#second").click()
    assert page.evaluate("window.pendingRequests.length") == 2
    resolve_request(page, 1, '<div id="result">second</div>')
    page.locator("#result").get_by_text("second").wait_for()


@pytest.mark.parametrize("replace_wait", [False, True], ids=["shared", "replaced"])
def test_wait_targets_resolve_per_request_and_balance_counts(
    runtime_browser: RuntimeBrowser,
    js_source: str,
    replace_wait: bool,
) -> None:
    runtime_browser.load(
        """
        <button id="load" py-call="load" py-target="#result"
                py-wait="#status">Load</button>
        <span id="status">old</span>
        <div id="result"></div>
        """,
        js_source,
    )
    page = runtime_browser.page
    install_pending_bridge(page)
    runtime_browser.process()

    page.locator("#load").click()
    old_status = page.locator("#status").element_handle()
    assert old_status is not None
    assert old_status.evaluate("node => node.classList.contains('py-waiting')")

    if replace_wait:
        page.evaluate(
            """
            () => {
              const replacement = document.createElement('span');
              replacement.id = 'status';
              replacement.textContent = 'new';
              document.querySelector('#status').replaceWith(replacement);
            }
            """
        )
    page.locator("#load").click()
    assert page.locator("#status").evaluate(
        "node => node.classList.contains('py-waiting')"
    )

    resolve_request(page, 1, "<p>newest</p>")
    page.locator("#result").get_by_text("newest").wait_for()
    assert page.locator("#status").evaluate(
        "node => node.classList.contains('py-waiting')"
    ) is (not replace_wait)
    assert old_status.evaluate(
        "node => node.classList.contains('py-waiting')"
    )

    resolve_request(page, 0, "<p>stale</p>")
    page.wait_for_timeout(20)
    assert not old_status.evaluate("node => node.classList.contains('py-waiting')")
    assert page.locator("#result").inner_text() == "newest"


def test_default_swap_style_is_read_for_each_request(
    runtime_browser: RuntimeBrowser,
    js_source: str,
) -> None:
    runtime_browser.load(
        """
        <button id="load" py-call="load" py-target="#result">Load</button>
        <div id="result"><span>original</span></div>
        """,
        js_source,
    )
    page = runtime_browser.page
    page.evaluate(
        """
        () => {
          let call = 0;
          window.pywebview = {api: {load: () => `<i>${++call}</i>`}};
        }
        """
    )
    runtime_browser.process()

    page.locator("#load").click()
    page.locator("#result i").get_by_text("1").wait_for()
    assert page.locator("#result").inner_text() == "1"

    page.evaluate("window.pywebviewHtmx.config.defaultSwapStyle = 'append'")
    page.locator("#load").click()
    page.locator("#result i").get_by_text("2").wait_for()
    assert page.locator("#result").inner_text() == "12"


def test_native_destructive_defaults_are_prevented_selectively(
    runtime_browser: RuntimeBrowser,
    js_source: str,
) -> None:
    runtime_browser.load(
        """
        <a id="link" href="#navigated" py-call="act">Link</a>
        <form id="form" action="#submitted">
          <input id="text" name="text" value="keep">
          <button id="submit" py-call="act">Submit</button>
          <button id="reset" type="reset" py-call="act">Reset</button>
        </form>
        <button id="ordinary" type="button" py-call="act">Ordinary</button>
        <input id="check" type="checkbox" py-call="act">
        <input id="radio" name="choice" type="radio" py-call="act">
        <input id="label-check" type="checkbox">
        <label id="label" for="label-check" py-call="act">Label</label>
        """,
        js_source,
    )
    page = runtime_browser.page
    page.evaluate(
        """
        () => {
          window.calls = 0;
          window.pywebview = {api: {act: () => {
            window.calls += 1;
            return '';
          }}};
        }
        """
    )
    runtime_browser.process()

    page.locator("#link").click()
    page.locator("#submit").click()
    page.locator("#text").fill("changed")
    page.locator("#reset").click()
    page.locator("#ordinary").click()
    page.locator("#check").click()
    page.locator("#radio").click()
    page.locator("#label").click()

    assert page.evaluate("location.hash") == ""
    assert page.locator("#text").input_value() == "changed"
    assert page.locator("#check").is_checked()
    assert page.locator("#radio").is_checked()
    assert page.locator("#label-check").is_checked()
    assert page.evaluate("window.calls") == 7


@pytest.mark.parametrize("control_type", ["checkbox", "radio"])
def test_label_text_click_does_not_repeat_for_forwarded_control_click(
    runtime_browser: RuntimeBrowser,
    js_source: str,
    control_type: str,
) -> None:
    other_radio = (
        '<input id="other" type="radio" name="choice">'
        if control_type == "radio"
        else ""
    )
    runtime_browser.load(
        f'<label id="label" py-call="act" py-target="#result">'
        f'<input id="check" type="{control_type}" name="choice">'
        '<span id="label-text">Toggle</span></label>'
        f'{other_radio}'
        '<div id="result"></div>',
        js_source,
    )
    page = runtime_browser.page
    page.evaluate(
        """
        () => {
          window.calls = 0;
          window.pywebview = {api: {act: () => { calls += 1; return ''; }}};
        }
        """
    )
    runtime_browser.process()

    page.locator("#label-text").click()
    assert page.locator("#check").is_checked()
    assert page.evaluate("window.calls") == 1

    page.locator("#check").click()
    assert page.locator("#check").is_checked() is (control_type == "radio")
    assert page.evaluate("window.calls") == 2

    if control_type == "radio":
        page.locator("#other").click()
        assert not page.locator("#check").is_checked()

    page.locator("#check").focus()
    page.keyboard.press("Space")
    assert page.locator("#check").is_checked()
    assert page.evaluate("window.calls") == 3


def test_external_label_and_control_clear_forwarding_marker_in_same_task(
    runtime_browser: RuntimeBrowser,
    js_source: str,
) -> None:
    runtime_browser.load(
        '<label id="label" for="check" py-call="labelAction" '
        'py-target="#result">Toggle</label>'
        '<input id="check" type="checkbox" py-call="controlAction" '
        'py-target="#result"><div id="result"></div>',
        js_source,
    )
    page = runtime_browser.page
    page.evaluate(
        """
        () => {
          window.calls = [];
          window.pywebview = {api: {
            labelAction: () => { calls.push('label'); return ''; },
            controlAction: () => { calls.push('control'); return ''; },
          }};
        }
        """
    )
    runtime_browser.process()

    page.evaluate(
        """() => {
          document.querySelector('#label').click();
          document.querySelector('#check').click();
        }"""
    )
    assert not page.locator("#check").is_checked()
    assert page.evaluate("window.calls") == ["label", "control"]


def test_nested_checkbox_py_call_runs_once_per_activation(
    runtime_browser: RuntimeBrowser,
    js_source: str,
) -> None:
    runtime_browser.load(
        '<label id="label" py-call="labelAction" py-target="#result">'
        '<input id="check" type="checkbox" py-call="checkboxAction" '
        'py-target="#result"><span id="label-text">Toggle</span>'
        '</label><div id="result"></div>',
        js_source,
    )
    page = runtime_browser.page
    page.evaluate(
        """
        () => {
          window.calls = [];
          window.pywebview = {api: {
            labelAction: () => { calls.push('label'); return ''; },
            checkboxAction: () => { calls.push('checkbox'); return ''; },
          }};
        }
        """
    )
    runtime_browser.process()

    page.locator("#label-text").click()
    assert page.locator("#check").is_checked()
    assert page.evaluate("window.calls") == ["label"]

    page.locator("#check").click()
    assert not page.locator("#check").is_checked()
    assert page.evaluate("window.calls") == ["label", "checkbox"]

    page.locator("#check").focus()
    page.keyboard.press("Space")
    assert page.locator("#check").is_checked()
    assert page.evaluate("window.calls") == ["label", "checkbox", "checkbox"]


def test_form_serialization_repeats_submitter_and_skips_files(
    runtime_browser: RuntimeBrowser,
    js_source: str,
) -> None:
    runtime_browser.load(
        """
        <form id="form" py-call="save" py-trigger="submit"
              data-py-params='{"fixed":"yes"}'>
          <input name="tag" value="one">
          <input name="tag" value="two">
          <input name="title" value="Example">
          <input name="attachment" type="file">
          <button id="save" name="action" value="save">Save</button>
        </form>
        """,
        js_source,
    )
    page = runtime_browser.page
    page.evaluate(
        """
        () => {
          window.receivedParams = null;
          window.pywebview = {api: {save: params => {
            window.receivedParams = params;
            return '';
          }}};
        }
        """
    )
    runtime_browser.process()
    page.locator("#save").click()

    page.wait_for_function("window.receivedParams !== null")
    assert page.evaluate("window.receivedParams") == {
        "fixed": "yes",
        "tag": ["one", "two"],
        "title": "Example",
        "action": "save",
    }


def test_form_serialization_preserves_reserved_object_property_names(
    runtime_browser: RuntimeBrowser,
    js_source: str,
) -> None:
    runtime_browser.load(
        """
        <form id="form" py-call="save" py-trigger="submit"
              data-py-params='{"fixed":"static","static":"yes"}'>
          <input name="__proto__" value="one">
          <input name="__proto__" value="two">
          <input name="constructor" value="ctor">
          <input name="toString" value="string">
          <input name="fixed" value="form">
          <button id="save">Save</button>
        </form>
        """,
        js_source,
    )
    page = runtime_browser.page
    page.evaluate(
        """
        () => {
          window.receivedParams = null;
          window.pywebview = {api: {save: params => {
            window.receivedParams = params;
            return '';
          }}};
        }
        """
    )
    runtime_browser.process()
    page.locator("#save").click()
    page.wait_for_function("window.receivedParams !== null")

    assert json.loads(page.evaluate("JSON.stringify(window.receivedParams)")) == {
        "__proto__": ["one", "two"],
        "constructor": "ctor",
        "toString": "string",
        "fixed": "form",
        "static": "yes",
    }


@pytest.mark.parametrize(
    ("policy", "expected_calls", "expected_ignored"),
    [("latest-wins", 2, 0), ("drop", 1, 1)],
)
def test_waiting_theme_keeps_controls_clickable_for_request_policy(
    runtime_browser: RuntimeBrowser,
    js_source: str,
    policy: str,
    expected_calls: int,
    expected_ignored: int,
) -> None:
    runtime_browser.load(
        f'<button id="load" py-call="load" py-policy="{policy}" '
        'py-target="#result">Load</button><div id="result"></div>',
        js_source,
    )
    page = runtime_browser.page
    page.add_style_tag(content=get_theme_css())
    install_pending_bridge(page)
    page.evaluate(
        """
        () => {
          window.ignoredCalls = 0;
          document.addEventListener('py:ignored', () => ignoredCalls++);
        }
        """
    )
    runtime_browser.process()

    page.locator("#load").click()
    assert page.locator("#load").evaluate(
        "node => node.classList.contains('py-waiting')"
    )
    assert page.locator("#load").evaluate(
        "node => getComputedStyle(node).pointerEvents"
    ) == "auto"

    page.locator("#load").click()
    assert page.evaluate("window.bridgeCalls.length") == expected_calls
    assert page.evaluate("window.ignoredCalls") == expected_ignored

    if policy == "latest-wins":
        resolve_request(page, 1, "newest")
        page.wait_for_function(
            "document.querySelector('#result').textContent === 'newest'"
        )
        resolve_request(page, 0, "stale")
    else:
        resolve_request(page, 0, "accepted")
    page.wait_for_function(
        "!document.querySelector('#load').classList.contains('py-waiting')"
    )
    assert page.locator("#result").inner_text() == (
        "newest" if policy == "latest-wins" else "accepted"
    )


@pytest.mark.parametrize("swap_style", ["innerHTML", "outerHTML", "append"])
def test_real_swaps_parse_html_and_bind_inserted_controls(
    runtime_browser: RuntimeBrowser,
    js_source: str,
    swap_style: str,
) -> None:
    runtime_browser.load(
        f"""
        <button id="load" py-call="load" py-target="#result"
                py-swap="{swap_style}">Load</button>
        <div id="result"><span id="original">original</span></div>
        """,
        js_source,
    )
    page = runtime_browser.page
    replacement = (
        '<div id="result"><button id="inserted" py-call="inserted">New</button></div>'
        if swap_style == "outerHTML"
        else '<button id="inserted" py-call="inserted">New</button>'
    )
    page.evaluate(
        """
        replacement => {
          window.insertedCalls = 0;
          window.pywebview = {api: {
            load: () => replacement,
            inserted: () => {
              window.insertedCalls += 1;
              return '<strong id="done">done</strong>';
            },
          }};
        }
        """,
        replacement,
    )
    runtime_browser.process()

    page.locator("#load").click()
    page.locator("#inserted").wait_for()
    if swap_style == "append":
        assert page.locator("#original").count() == 1
    else:
        assert page.locator("#original").count() == 0

    page.locator("#inserted").click()
    page.locator("#done").wait_for()
    assert page.evaluate("window.insertedCalls") == 1


def test_lifecycle_events_are_observational_and_errors_report_staleness(
    runtime_browser: RuntimeBrowser,
    js_source: str,
) -> None:
    runtime_browser.load(
        """
        <button id="load" py-call="load" py-target="#result">Load</button>
        <div id="result"></div>
        """,
        js_source,
    )
    page = runtime_browser.page
    install_pending_bridge(page)
    page.evaluate(
        """
        () => {
          window.events = [];
          for (const name of ['py:trigger', 'py:beforeSwap', 'py:afterSwap',
                              'py:error', 'py:ignored']) {
            document.addEventListener(name, event => {
              event.preventDefault();
              window.events.push({
                name,
                cancelable: event.cancelable,
                defaultPrevented: event.defaultPrevented,
                stale: event.detail.stale,
              });
            });
          }
        }
        """
    )
    runtime_browser.process()

    page.locator("#load").click()
    page.locator("#load").click()
    reject_request(page, 0, "older failure")
    reject_request(page, 1, "newer failure")
    runtime_browser.expect_console_error("older failure")
    runtime_browser.expect_console_error("newer failure")
    page.wait_for_function(
        "window.events.filter(event => event.name === 'py:error').length === 2"
    )

    events = page.evaluate("window.events")
    assert all(not event["cancelable"] for event in events)
    assert all(not event["defaultPrevented"] for event in events)
    errors = [event for event in events if event["name"] == "py:error"]
    assert [event["stale"] for event in errors] == [True, False]


def test_successful_swap_events_are_observational(
    runtime_browser: RuntimeBrowser,
    js_source: str,
) -> None:
    runtime_browser.load(
        """
        <button id="load" py-call="load" py-target="#result">Load</button>
        <div id="result"></div>
        """,
        js_source,
    )
    page = runtime_browser.page
    page.evaluate(
        """
        () => {
          window.events = [];
          for (const name of ['py:trigger', 'py:beforeSwap', 'py:afterSwap']) {
            document.addEventListener(name, event => {
              event.preventDefault();
              window.events.push({
                name,
                cancelable: event.cancelable,
                defaultPrevented: event.defaultPrevented,
              });
            });
          }
          window.pywebview = {api: {load: () => '<p>done</p>'}};
        }
        """
    )
    runtime_browser.process()
    page.locator("#load").click()
    page.locator("#result").get_by_text("done").wait_for()

    events = page.evaluate("window.events")
    assert [event["name"] for event in events] == [
        "py:trigger",
        "py:beforeSwap",
        "py:afterSwap",
    ]
    assert all(not event["cancelable"] for event in events)
    assert all(not event["defaultPrevented"] for event in events)


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        ("delete window.pywebview", "window.pywebview.api is not available"),
        (
            "window.pywebview = {api: {}}",
            "Python API method 'load' was not found",
        ),
        (
            "window.pywebview = {api: {load: () => ({html: 'wrong'})}}",
            "PyWebview HTMX: Python API methods must return an HTML string",
        ),
    ],
    ids=["missing-bridge", "missing-method", "non-string-response"],
)
def test_bridge_failures_emit_errors(
    runtime_browser: RuntimeBrowser,
    js_source: str,
    setup: str,
    expected: str,
) -> None:
    runtime_browser.load(
        '<button id="load" py-call="load">Load</button>',
        js_source,
    )
    page = runtime_browser.page
    page.evaluate(setup)
    page.evaluate(
        """
        () => {
          window.errors = [];
          document.addEventListener('py:error', event => {
            window.errors.push({
              message: event.detail.error.message,
              stale: event.detail.stale,
            });
          });
        }
        """
    )
    runtime_browser.process()
    runtime_browser.expect_console_error(expected)
    page.locator("#load").click()
    page.wait_for_function("window.errors.length === 1")

    assert page.evaluate("window.errors") == [{"message": expected, "stale": False}]


def test_invalid_params_and_selectors_degrade_safely(
    runtime_browser: RuntimeBrowser,
    js_source: str,
) -> None:
    runtime_browser.load(
        """
        <button id="invalid-json" py-call="load" data-py-params="{">JSON</button>
        <button id="invalid-target" py-call="load" py-target="[">Target</button>
        <button id="invalid-wait" py-call="pending" py-wait="[">Wait</button>
        """,
        js_source,
    )
    page = runtime_browser.page
    page.evaluate(
        """
        () => {
          window.calls = [];
          window.finishPending = null;
          window.pywebview = {api: {
            load: params => {
              window.calls.push(params);
              return '<p>loaded</p>';
            },
            pending: () => new Promise(resolve => {
              window.finishPending = resolve;
            }),
          }};
        }
        """
    )
    runtime_browser.process()
    runtime_browser.expect_console_error("invalid JSON in data-py-params")

    page.locator("#invalid-json").click()
    page.wait_for_function("window.calls.length === 1")
    assert page.evaluate("window.calls[0]") == {}

    page.locator("#invalid-target").click()
    page.wait_for_timeout(20)
    page.locator("#invalid-wait").click()
    assert page.locator("#invalid-wait").evaluate(
        "node => node.classList.contains('py-waiting')"
    )
    page.evaluate("window.finishPending('<p>done</p>')")
    page.locator("#invalid-wait p").get_by_text("done").wait_for()
    assert not page.locator("#invalid-wait").evaluate(
        "node => node.classList.contains('py-waiting')"
    )


@pytest.mark.parametrize("remove_target", [False, True], ids=["replace", "remove"])
def test_target_is_resolved_again_after_swap_delay(
    runtime_browser: RuntimeBrowser, js_source: str, remove_target: bool,
) -> None:
    runtime_browser.load(
        '<button id="load" py-call="load" py-target="#result">Load</button>'
        '<div id="result">original</div>',
        js_source,
    )
    page = runtime_browser.page
    install_pending_bridge(page)
    runtime_browser.process()
    page.evaluate(
        """() => {
          const originalTimeout = window.setTimeout;
          window.setTimeout = (callback, ms, ...args) => {
            if (ms === 1234) {
              window.finishSwapDelay = callback;
              return 0;
            }
            return originalTimeout(callback, ms, ...args);
          };
          pywebviewHtmx.config.swapDelay = 1234;
          window.oldTarget = document.querySelector('#result');
          window.afterSwaps = 0;
          document.body.addEventListener('py:afterSwap', () => afterSwaps++);
        }"""
    )
    page.locator("#load").click()
    resolve_request(page, 0, "response")
    page.wait_for_function("typeof window.finishSwapDelay === 'function'")
    page.evaluate(
        """remove => {
          if (remove) oldTarget.remove();
          else oldTarget.outerHTML = '<div id="result">replacement</div>';
          finishSwapDelay();
        }""",
        remove_target,
    )
    page.wait_for_function(
        "!document.querySelector('#load').classList.contains('py-waiting')"
    )
    assert page.evaluate("oldTarget.textContent") == "original"
    assert page.evaluate("afterSwaps") == (0 if remove_target else 1)
    if not remove_target:
        assert page.locator("#result").inner_text() == "response"


def test_detached_control_error_reaches_body_listener(
    runtime_browser: RuntimeBrowser, js_source: str,
) -> None:
    runtime_browser.load(
        '<section id="host"><button id="load" py-call="load" '
        'py-target="#host" py-swap="outerHTML">Load</button></section>',
        js_source,
    )
    page = runtime_browser.page
    install_pending_bridge(page)
    runtime_browser.process()
    page.evaluate(
        """() => {
          window.originalControl = document.querySelector('#load');
          window.errors = [];
          document.body.addEventListener('py:error', event => errors.push({
            stale: event.detail.stale,
            original: event.detail.element === originalControl,
            message: event.detail.error.message,
          }));
        }"""
    )
    page.locator("#load").click()
    page.locator("#load").click()
    resolve_request(page, 1, '<section id="host">replaced</section>')
    page.locator("#host").get_by_text("replaced").wait_for()
    runtime_browser.expect_console_error("older failure")
    reject_request(page, 0, "older failure")
    page.wait_for_function("errors.length === 1")
    assert page.evaluate("errors") == [
        {"stale": True, "original": True, "message": "older failure"}
    ]
    assert page.evaluate("originalControl.classList.contains('py-waiting')") is False


def test_cloned_controls_bind_once_when_processed_repeatedly(
    runtime_browser: RuntimeBrowser, js_source: str,
) -> None:
    runtime_browser.load(
        '<button id="load" py-call="load" py-target="#result">Load</button>'
        '<div id="result"></div>',
        js_source,
    )
    page = runtime_browser.page
    install_pending_bridge(page)
    runtime_browser.process()
    page.evaluate(
        """() => {
          const clone = document.querySelector('#load').cloneNode(true);
          clone.id = 'clone';
          document.body.append(clone);
          pywebviewHtmx.process(clone);
          pywebviewHtmx.process(document.body);
          pywebviewHtmx.process(document.body);
        }"""
    )
    page.locator("#clone").click()
    assert page.evaluate("bridgeCalls.length") == 1
    resolve_request(page, 0, "cloned")
    page.locator("#result").get_by_text("cloned").wait_for()
    page.locator("#load").click()
    assert page.evaluate("bridgeCalls.length") == 2
    resolve_request(page, 1, "original")
    page.locator("#result").get_by_text("original").wait_for()


def test_injected_runtime_binds_controls_on_document_load(
    runtime_browser: RuntimeBrowser,
) -> None:
    from pywebview_htmx import inject_runtime

    page = runtime_browser.page
    page.set_content(inject_runtime(
        '<!doctype html><html><body>'
        '<button id="load" py-call="load" py-target="#result">Load</button>'
        '<div id="result"></div></body></html>'
    ))
    install_pending_bridge(page)
    page.locator("#load").click()
    assert page.evaluate("bridgeCalls") == [{}]
    resolve_request(page, 0, "ready")
    page.locator("#result").get_by_text("ready").wait_for()
