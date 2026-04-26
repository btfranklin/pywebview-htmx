(function () {
  "use strict";

  const config = {
    defaultSwapStyle: "innerHTML",
    swapDelay: 0,
    settleDelay: 20,
    requestPolicy: "latest-wins",
  };
  const requestState = new WeakMap();
  const waitState = new WeakMap();

  function $(selector, root = document) {
    if (!selector) return null;
    try {
      return root.querySelector(selector);
    } catch (error) {
      console.warn("PyWebview HTMX: invalid selector", selector, error);
      return null;
    }
  }

  function triggerEvent(target, eventName, detail = {}) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      cancelable: true,
      detail,
    });
    target.dispatchEvent(event);
    return event;
  }

  function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function pySwap(target, content, swapStyle = config.defaultSwapStyle) {
    switch (swapStyle) {
      case "innerHTML":
        target.innerHTML = content;
        return target;
      case "outerHTML": {
        const parent = target.parentElement || document.body;
        target.outerHTML = content;
        return parent;
      }
      case "append":
        target.insertAdjacentHTML("beforeend", content);
        return target;
      default:
        target.innerHTML = content;
        return target;
    }
  }

  function parseParams(element) {
    const raw = element.getAttribute("data-py-params");
    if (!raw) return {};
    try {
      return JSON.parse(raw);
    } catch (error) {
      console.error("PyWebview HTMX: invalid JSON in data-py-params", error);
      return {};
    }
  }

  function mergeParamValue(target, key, value) {
    if (Object.prototype.hasOwnProperty.call(target, key)) {
      const existing = target[key];
      if (Array.isArray(existing)) {
        existing.push(value);
      } else {
        target[key] = [existing, value];
      }
      return;
    }
    target[key] = value;
  }

  function serializeForm(form, event) {
    const params = {};
    const formData = new FormData(form);

    for (const [key, value] of formData.entries()) {
      if (typeof File !== "undefined" && value instanceof File) {
        console.warn("PyWebview HTMX: file inputs are not supported in data-py-params", key);
        continue;
      }
      mergeParamValue(params, key, value);
    }

    const submitter = event && "submitter" in event ? event.submitter : null;
    if (submitter && submitter.name) {
      mergeParamValue(params, submitter.name, submitter.value || "");
    }

    return params;
  }

  function buildRequestParams(element, eventName, event) {
    const params = parseParams(element);
    if (element.tagName !== "FORM" || eventName !== "submit") {
      return params;
    }
    return { ...params, ...serializeForm(element, event) };
  }

  function getWaitTarget(element) {
    if (!element.hasAttribute("py-wait")) {
      return element;
    }

    const waitSelector = element.getAttribute("py-wait");
    if (!waitSelector) {
      return element;
    }

    return $(waitSelector) || element;
  }

  async function invokePython(functionName, params) {
    const bridge = window.pywebview && window.pywebview.api;
    if (!bridge) {
      throw new Error("window.pywebview.api is not available");
    }

    const func = bridge[functionName];
    if (typeof func !== "function") {
      throw new Error(`Python API method '${functionName}' was not found`);
    }

    return await func(params);
  }

  function getRequestState(key) {
    let state = requestState.get(key);
    if (!state) {
      state = { lastIssued: 0, inFlightCount: 0 };
      requestState.set(key, state);
    }
    return state;
  }

  function getRequestStateKey(element, targetSelector) {
    if (!targetSelector) {
      return element;
    }
    return $(targetSelector) || element;
  }

  function addWaiting(waitTarget) {
    const count = (waitState.get(waitTarget) || 0) + 1;
    waitState.set(waitTarget, count);
    waitTarget.classList.add("py-waiting");
  }

  function removeWaiting(waitTarget) {
    const count = Math.max(0, (waitState.get(waitTarget) || 0) - 1);
    if (count === 0) {
      waitState.delete(waitTarget);
      waitTarget.classList.remove("py-waiting");
      return;
    }
    waitState.set(waitTarget, count);
  }

  function shouldPreventDefault(eventName) {
    return eventName === "submit";
  }

  function getRequestPolicy(element) {
    const policy = element.getAttribute("py-policy") || config.requestPolicy;
    if (policy === "drop" || policy === "latest-wins") {
      return policy;
    }
    return config.requestPolicy;
  }

  function processPyWebviewHtmxNodes(root = document) {
    if (!root || typeof root.querySelectorAll !== "function") {
      return;
    }

    const elements = [];
    if (root.matches && root.matches("[py-call]")) {
      elements.push(root);
    }
    elements.push(...root.querySelectorAll("[py-call]"));

    elements.forEach((element) => {
      if (element.getAttribute("data-pywebview-bound") === "true") {
        return;
      }
      element.setAttribute("data-pywebview-bound", "true");

      const functionName = element.getAttribute("py-call");
      const eventName = element.getAttribute("py-trigger") || "click";
      const targetSelector = element.getAttribute("py-target");
      const swapStyle = element.getAttribute("py-swap") || config.defaultSwapStyle;
      const waitTarget = getWaitTarget(element);

      if (!functionName) {
        console.warn("PyWebview HTMX: py-call is empty", element);
        return;
      }

      element.addEventListener(eventName, async (event) => {
        if (shouldPreventDefault(eventName) && event.cancelable) {
          event.preventDefault();
        }

        const params = buildRequestParams(element, eventName, event);
        const state = getRequestState(getRequestStateKey(element, targetSelector));
        const requestPolicy = getRequestPolicy(element);
        if (requestPolicy === "drop" && state.inFlightCount > 0) {
          triggerEvent(element, "py:ignored", { reason: "in-flight" });
          return;
        }

        const requestId = state.lastIssued + 1;
        state.lastIssued = requestId;
        state.inFlightCount += 1;

        triggerEvent(element, "py:trigger", {
          func: functionName,
          params,
          requestId,
        });

        addWaiting(waitTarget);

        try {
          const response = await invokePython(functionName, params);
          if (requestId !== state.lastIssued) {
            return;
          }
          if (typeof response !== "string") {
            throw new Error("PyWebview HTMX: Python API methods must return an HTML string");
          }

          const target = targetSelector ? $(targetSelector) : element;
          if (!target) {
            console.warn("PyWebview HTMX: target element not found", targetSelector);
            return;
          }

          triggerEvent(target, "py:beforeSwap", { response, requestId });
          if (config.swapDelay > 0) {
            await delay(config.swapDelay);
          }
          if (requestId !== state.lastIssued) {
            return;
          }

          const processRoot = pySwap(target, response, swapStyle);
          const afterSwapTarget =
            swapStyle === "outerHTML"
              ? (targetSelector ? $(targetSelector) || processRoot : processRoot)
              : target;
          triggerEvent(afterSwapTarget, "py:afterSwap", { response, requestId });
          processPyWebviewHtmxNodes(processRoot);

          if (config.settleDelay > 0) {
            await delay(config.settleDelay);
          }
        } catch (error) {
          console.error("PyWebview HTMX: error calling Python function", error);
          triggerEvent(element, "py:error", { error, requestId });
        } finally {
          state.inFlightCount = Math.max(0, state.inFlightCount - 1);
          removeWaiting(waitTarget);
        }
      });
    });
  }

  window.pywebviewHtmx = {
    config,
    process: processPyWebviewHtmxNodes,
    swap: pySwap,
    trigger: triggerEvent,
  };

  document.addEventListener("DOMContentLoaded", () => {
    processPyWebviewHtmxNodes(document.body);
  });
})();
