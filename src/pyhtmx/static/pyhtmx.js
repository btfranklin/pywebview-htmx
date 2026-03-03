(function () {
  "use strict";

  const config = {
    defaultSwapStyle: "innerHTML",
    swapDelay: 0,
    settleDelay: 20,
    requestPolicy: "latest-wins",
  };
  const requestState = new WeakMap();

  function $(selector, root = document) {
    if (!selector) return null;
    return root.querySelector(selector);
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
      console.error("pyHTMX: invalid JSON in data-py-params", error);
      return {};
    }
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

  function getRequestState(element) {
    let state = requestState.get(element);
    if (!state) {
      state = { lastIssued: 0, inFlightCount: 0 };
      requestState.set(element, state);
    }
    return state;
  }

  function processPyHTMXNodes(root = document) {
    if (!root || typeof root.querySelectorAll !== "function") {
      return;
    }

    const elements = root.querySelectorAll("[py-call]");

    elements.forEach((element) => {
      if (element.getAttribute("data-pyhtmx-bound") === "true") {
        return;
      }
      element.setAttribute("data-pyhtmx-bound", "true");

      const functionName = element.getAttribute("py-call");
      const eventName = element.getAttribute("py-trigger") || "click";
      const targetSelector = element.getAttribute("py-target");
      const swapStyle = element.getAttribute("py-swap") || config.defaultSwapStyle;
      const waitTarget = getWaitTarget(element);

      if (!functionName) {
        console.warn("pyHTMX: py-call is empty", element);
        return;
      }

      element.addEventListener(eventName, async (event) => {
        if (event.cancelable) {
          event.preventDefault();
        }

        const params = parseParams(element);
        const state = getRequestState(element);
        if (config.requestPolicy === "drop" && state.inFlightCount > 0) {
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

        waitTarget.classList.add("py-waiting");

        try {
          const response = await invokePython(functionName, params);
          if (requestId !== state.lastIssued) {
            return;
          }

          const target = targetSelector ? $(targetSelector) : element;
          if (!target) {
            console.warn("pyHTMX: target element not found", targetSelector);
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
          triggerEvent(target, "py:afterSwap", { response, requestId });
          processPyHTMXNodes(processRoot);

          if (config.settleDelay > 0) {
            await delay(config.settleDelay);
          }
        } catch (error) {
          console.error("pyHTMX: error calling Python function", error);
          triggerEvent(element, "py:error", { error, requestId });
        } finally {
          state.inFlightCount = Math.max(0, state.inFlightCount - 1);
          if (state.inFlightCount === 0) {
            waitTarget.classList.remove("py-waiting");
          }
        }
      });
    });
  }

  window.pyhtmx = {
    config,
    process: processPyHTMXNodes,
    swap: pySwap,
    trigger: triggerEvent,
  };

  document.addEventListener("DOMContentLoaded", () => {
    processPyHTMXNodes(document.body);
  });
})();
