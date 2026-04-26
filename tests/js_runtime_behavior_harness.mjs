import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

class DomEvent {
  constructor(type, options = {}) {
    this.type = type;
    this.bubbles = Boolean(options.bubbles);
    this.cancelable = Boolean(options.cancelable);
    this.detail = options.detail || {};
    this.defaultPrevented = false;
    this.target = null;
    this.currentTarget = null;
  }

  preventDefault() {
    if (this.cancelable) {
      this.defaultPrevented = true;
    }
  }
}

class DomCustomEvent extends DomEvent {}

class ClassList {
  constructor() {
    this.tokens = new Set();
  }

  add(...tokens) {
    tokens.forEach((token) => this.tokens.add(token));
  }

  remove(...tokens) {
    tokens.forEach((token) => this.tokens.delete(token));
  }

  contains(token) {
    return this.tokens.has(token);
  }
}

class Element {
  constructor(tagName, ownerDocument) {
    this.tagName = tagName.toUpperCase();
    this.ownerDocument = ownerDocument;
    this.parentElement = null;
    this.children = [];
    this.attributes = new Map();
    this.classList = new ClassList();
    this.listeners = new Map();
    this._innerHTML = "";
    this.id = "";
  }

  append(...children) {
    children.forEach((child) => {
      child.parentElement = this;
      child.ownerDocument = this.ownerDocument;
      this.children.push(child);
    });
  }

  setAttribute(name, value) {
    const stringValue = String(value);
    this.attributes.set(name, stringValue);
    if (name === "id") {
      this.id = stringValue;
    }
  }

  getAttribute(name) {
    return this.attributes.has(name) ? this.attributes.get(name) : null;
  }

  hasAttribute(name) {
    return this.attributes.has(name);
  }

  matches(selector) {
    return this.ownerDocument.matchesSelector(this, selector);
  }

  querySelector(selector) {
    return this.ownerDocument.querySelectorFrom(selector, this);
  }

  querySelectorAll(selector) {
    return this.ownerDocument.querySelectorAllFrom(selector, this);
  }

  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) || [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }

  dispatchEvent(event) {
    if (!event.target) {
      event.target = this;
    }
    event.currentTarget = this;

    for (const listener of this.listeners.get(event.type) || []) {
      listener.call(this, event);
    }

    if (event.bubbles && this.parentElement) {
      this.parentElement.dispatchEvent(event);
    }
    return !event.defaultPrevented;
  }

  set innerHTML(value) {
    this._innerHTML = String(value);
    this.children = [];
  }

  get innerHTML() {
    return this._innerHTML;
  }

  set outerHTML(value) {
    if (!this.parentElement) {
      this.innerHTML = value;
      return;
    }

    const replacement = this.ownerDocument.createElement("div");
    replacement.innerHTML = value;
    const index = this.parentElement.children.indexOf(this);
    this.parentElement.children.splice(index, 1, replacement);
    replacement.parentElement = this.parentElement;
  }

  insertAdjacentHTML(position, value) {
    assert.equal(position, "beforeend");
    this._innerHTML += String(value);
  }
}

class Document {
  constructor() {
    this.listeners = new Map();
    this.body = new Element("body", this);
  }

  createElement(tagName) {
    return new Element(tagName, this);
  }

  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) || [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }

  querySelector(selector) {
    return this.querySelectorFrom(selector, this.body);
  }

  querySelectorAll(selector) {
    return this.querySelectorAllFrom(selector, this.body);
  }

  querySelectorFrom(selector, root) {
    return this.querySelectorAllFrom(selector, root)[0] || null;
  }

  querySelectorAllFrom(selector, root) {
    this.validateSelector(selector);
    const matches = [];

    const visit = (node) => {
      for (const child of node.children) {
        if (this.matchesSelector(child, selector)) {
          matches.push(child);
        }
        visit(child);
      }
    };

    visit(root);
    return matches;
  }

  matchesSelector(element, selector) {
    this.validateSelector(selector);
    if (selector === "[py-call]") {
      return element.hasAttribute("py-call");
    }
    if (selector.startsWith("#")) {
      return element.id === selector.slice(1);
    }
    throw new SyntaxError(`Unsupported selector in test harness: ${selector}`);
  }

  validateSelector(selector) {
    if (!selector || selector === "[" || selector.includes("###")) {
      throw new SyntaxError(`Invalid selector: ${selector}`);
    }
  }
}

function makeElement(document, tagName, attributes = {}) {
  const element = document.createElement(tagName);
  for (const [name, value] of Object.entries(attributes)) {
    element.setAttribute(name, value);
  }
  return element;
}

function createHarness(runtimeSource) {
  const document = new Document();
  const warnings = [];
  const context = {
    clearTimeout,
    console: {
      ...console,
      warn: (...args) => warnings.push(args.map(String).join(" ")),
    },
    CustomEvent: DomCustomEvent,
    document,
    Promise,
    setTimeout,
  };
  context.window = context;
  context.globalThis = context;

  vm.createContext(context);
  vm.runInContext(runtimeSource, context);

  context.pywebviewHtmx.config.settleDelay = 0;
  context.pywebviewHtmx.config.swapDelay = 0;

  return { document, warnings, window: context };
}

async function flushAsyncWork() {
  await Promise.resolve();
  await new Promise((resolve) => setTimeout(resolve, 0));
  await Promise.resolve();
}

function click(element) {
  element.dispatchEvent(new DomEvent("click", { bubbles: true, cancelable: true }));
}

async function testInvalidWaitSelectorFallsBackAndDoesNotAbort(runtimeSource) {
  const { document, warnings, window } = createHarness(runtimeSource);
  const result = makeElement(document, "div", { id: "result" });
  const badWait = makeElement(document, "button", {
    "py-call": "load",
    "py-target": "#result",
    "py-wait": "[",
  });
  const laterButton = makeElement(document, "button", { "py-call": "later" });
  document.body.append(badWait, result, laterButton);

  let resolveLoad;
  window.pywebview = {
    api: {
      load: () => new Promise((resolve) => {
        resolveLoad = resolve;
      }),
      later: () => "<p>later</p>",
    },
  };

  window.pywebviewHtmx.process(document.body);
  assert.equal(badWait.getAttribute("data-pywebview-bound"), "true");
  assert.equal(laterButton.getAttribute("data-pywebview-bound"), "true");
  assert.ok(warnings.some((warning) => warning.includes("invalid selector")));

  click(badWait);
  assert.equal(badWait.classList.contains("py-waiting"), true);

  resolveLoad("<p>loaded</p>");
  await flushAsyncWork();

  assert.equal(result.innerHTML, "<p>loaded</p>");
  assert.equal(badWait.classList.contains("py-waiting"), false);
}

async function testLatestWinsIsSharedByTarget(runtimeSource) {
  const { document, window } = createHarness(runtimeSource);
  const result = makeElement(document, "div", { id: "race-result" });
  const wait = makeElement(document, "span", { id: "race-status" });
  const slow = makeElement(document, "button", {
    "py-call": "long_task",
    "py-target": "#race-result",
    "py-wait": "#race-status",
  });
  const fast = makeElement(document, "button", {
    "py-call": "long_task",
    "py-target": "#race-result",
    "py-wait": "#race-status",
  });
  document.body.append(slow, fast, wait, result);

  const requests = [];
  window.pywebview = {
    api: {
      long_task: () => new Promise((resolve) => {
        requests.push(resolve);
      }),
    },
  };

  window.pywebviewHtmx.process(document.body);
  click(slow);
  click(fast);

  assert.equal(requests.length, 2);
  assert.equal(wait.classList.contains("py-waiting"), true);

  requests[1]("<p>fast</p>");
  await flushAsyncWork();

  assert.equal(result.innerHTML, "<p>fast</p>");
  assert.equal(wait.classList.contains("py-waiting"), true);

  requests[0]("<p>slow</p>");
  await flushAsyncWork();

  assert.equal(result.innerHTML, "<p>fast</p>");
  assert.equal(wait.classList.contains("py-waiting"), false);
}

async function testDropPolicyIsSharedByTarget(runtimeSource) {
  const { document, window } = createHarness(runtimeSource);
  const result = makeElement(document, "div", { id: "drop-result" });
  const first = makeElement(document, "button", {
    "py-call": "long_task",
    "py-policy": "drop",
    "py-target": "#drop-result",
  });
  const second = makeElement(document, "button", {
    "py-call": "long_task",
    "py-policy": "drop",
    "py-target": "#drop-result",
  });
  document.body.append(first, second, result);

  const requests = [];
  window.pywebview = {
    api: {
      long_task: () => new Promise((resolve) => {
        requests.push(resolve);
      }),
    },
  };

  window.pywebviewHtmx.process(document.body);
  click(first);
  click(second);

  assert.equal(requests.length, 1);
  requests[0]("<p>first</p>");
  await flushAsyncWork();
  assert.equal(result.innerHTML, "<p>first</p>");
}

const runtimePath = process.argv[2];
const runtimeSource = fs.readFileSync(runtimePath, "utf8");

await testInvalidWaitSelectorFallsBackAndDoesNotAbort(runtimeSource);
await testLatestWinsIsSharedByTarget(runtimeSource);
await testDropPolicyIsSharedByTarget(runtimeSource);
