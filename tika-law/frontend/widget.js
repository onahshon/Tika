(function () {
  var scriptSrc = document.currentScript && document.currentScript.src;
  var assetBaseUrl = scriptSrc ? scriptSrc.replace(/\/widget\.js(?:\?.*)?$/, "") : "";

  /* ── SVG icons ─────────────────────────────────────────────────────────── */
  var SVG_SCALE =
    '<svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18" xmlns="http://www.w3.org/2000/svg">' +
    /* base */
    '<ellipse cx="12" cy="22" rx="5" ry="1.5"/>' +
    /* pillar */
    '<rect x="11" y="5.5" width="2" height="16" rx="0.5"/>' +
    /* beam */
    '<rect x="2" y="3.5" width="20" height="2.5" rx="1.25"/>' +
    /* left V-chains */
    '<polygon points="3.5,6 1,14 7,14"/>' +
    /* left pan bowl */
    '<path d="M1 14 A3 2 0 0 1 7 14 Z"/>' +
    /* right V-chains */
    '<polygon points="20.5,6 17,14 23,14"/>' +
    /* right pan bowl */
    '<path d="M17 14 A3 2 0 0 1 23 14 Z"/>' +
    '</svg>';

  var SVG_PLANE =
    '<svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18" style="transform:rotate(180deg)">' +
    '<path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/>' +
    '</svg>';

  var SVG_USER =
    '<svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">' +
    '<path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12z"/>' +
    '<path d="M12 14.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/>' +
    '</svg>';

  /* ── DOM helpers ────────────────────────────────────────────────────────── */
  function createElement(tagName, className, text) {
    var el = document.createElement(tagName);
    if (className) el.className = className;
    if (text) el.textContent = text;
    return el;
  }

  function makeAvatar(role) {
    var el = createElement("div", "tika-law-avatar tika-law-avatar-" + role);
    el.innerHTML = role === "user" ? SVG_USER : SVG_SCALE;
    return el;
  }

  /* ── Styles ─────────────────────────────────────────────────────────────── */
  function injectStyles() {
    if (document.querySelector("#tika-law-widget-styles")) return;

    var style = createElement("style");
    style.id = "tika-law-widget-styles";
    style.textContent =
      ".tika-law-root{" +
        "--tika-primary:#0077E6;--tika-primary-hover:#0068CC;" +
        "--tika-scale-bg:#5b21b6;--tika-scale-bg-hover:#4c1d95;" +
        "--tika-widget-bg:#FFFFFF;--tika-page-bg:#F5F7FA;--tika-border:#E1E7F0;" +
        "--tika-text-primary:#0F172A;--tika-text-secondary:#64748B;--tika-text-muted:#94A3B8;" +
        "--tika-bot-bubble-bg:#EAF3FF;--tika-bot-bubble-text:#1E293B;" +
        "--tika-user-bubble-bg:#0077E6;--tika-user-bubble-text:#FFFFFF;" +
        "--tika-input-border:#DCE4EE;" +
      "}" +

      ".tika-law-launcher{position:fixed;right:24px;bottom:24px;z-index:2147483000;width:60px;height:60px;border:0;border-radius:50%;background:var(--tika-scale-bg);color:#fff;box-shadow:0 4px 20px rgba(91,33,182,.35);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .15s}" +
      ".tika-law-launcher:hover{background:var(--tika-scale-bg-hover)}" +

      ".tika-law-panel{position:fixed;right:24px;bottom:96px;z-index:2147483000;width:min(380px,calc(100vw - 32px));height:min(620px,calc(100vh - 120px));display:none;flex-direction:column;overflow:hidden;border-radius:16px;background:var(--tika-widget-bg);border:1px solid var(--tika-border);box-shadow:0 8px 36px rgba(15,23,42,.10);font-family:Arial,'Noto Sans Hebrew',sans-serif;color:var(--tika-text-primary);direction:rtl}" +
      ".tika-law-panel.is-open{display:flex}" +

      ".tika-law-header{display:flex;align-items:center;gap:10px;padding:14px 16px;background:var(--tika-widget-bg);border-bottom:1px solid var(--tika-border)}" +
      ".tika-law-title{margin:0;font-size:15px;font-weight:600;color:var(--tika-text-primary)}" +
      ".tika-law-subtitle{margin:2px 0 0;font-size:12px;color:var(--tika-text-secondary)}" +
      ".tika-law-close{margin-inline-start:auto;border:0;background:transparent;color:var(--tika-text-muted);border-radius:50%;width:30px;height:30px;cursor:pointer;font-size:20px;display:flex;align-items:center;justify-content:center;transition:background .12s}" +
      ".tika-law-close:hover{background:var(--tika-page-bg)}" +

      /* chat area: white */
      ".tika-law-messages{flex:1;overflow:auto;padding:16px;display:flex;flex-direction:column;gap:12px;background:var(--tika-widget-bg)}" +

      ".tika-law-avatar{width:32px;height:32px;border-radius:50%;flex:0 0 auto;display:flex;align-items:center;justify-content:center}" +
      ".tika-law-avatar-bot{background:var(--tika-scale-bg);color:#fff}" +
      ".tika-law-avatar-user{background:var(--tika-primary);color:#fff}" +

      ".tika-law-row{display:flex;gap:8px;align-items:flex-end}" +
      ".tika-law-row.is-user{flex-direction:row-reverse}" +
      ".tika-law-bubble{max-width:78%;padding:10px 14px;border-radius:16px;line-height:1.5;font-size:14px;white-space:pre-wrap;word-break:break-word}" +
      ".tika-law-row.is-bot .tika-law-bubble{background:var(--tika-bot-bubble-bg);color:var(--tika-bot-bubble-text);border-bottom-right-radius:4px}" +
      ".tika-law-row.is-user .tika-law-bubble{background:var(--tika-user-bubble-bg);color:var(--tika-user-bubble-text);border-bottom-left-radius:4px}" +

      /* message pop-in animation */
      "@keyframes tika-pop{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}" +
      ".tika-law-row{animation:tika-pop .22s ease}" +

      /* composer area: light gray */
      ".tika-law-composer{display:flex;gap:8px;align-items:center;padding:10px 12px;background:var(--tika-page-bg);border-top:1px solid var(--tika-border)}" +
      ".tika-law-input{flex:1;min-width:0;border:1px solid var(--tika-input-border);border-radius:999px;padding:10px 14px;font:14px Arial,sans-serif;outline:none;background:var(--tika-widget-bg);color:var(--tika-text-primary)}" +
      ".tika-law-input::placeholder{color:var(--tika-text-muted)}" +
      ".tika-law-input:focus{border-color:var(--tika-primary);box-shadow:0 0 0 3px rgba(0,119,230,.10)}" +
      ".tika-law-send{flex-shrink:0;width:40px;height:40px;border:0;border-radius:50%;background:var(--tika-primary);color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .15s}" +
      ".tika-law-send:hover:not(:disabled){background:var(--tika-primary-hover)}" +
      ".tika-law-send:disabled{opacity:.5;cursor:wait}" +

      ".tika-law-disclaimer{padding:6px 14px;background:var(--tika-page-bg);border-top:1px solid var(--tika-border);color:var(--tika-text-muted);font-size:11px;text-align:center}" +

      ".tika-law-typing{display:flex;gap:5px;align-items:center;padding:8px 14px}" +
      ".tika-law-typing span{width:6px;height:6px;border-radius:50%;background:var(--tika-text-muted);animation:tika-bounce 1.2s infinite ease-in-out}" +
      ".tika-law-typing span:nth-child(2){animation-delay:.2s}" +
      ".tika-law-typing span:nth-child(3){animation-delay:.4s}" +
      "@keyframes tika-bounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-6px)}}" +

      "@media(max-width:520px){" +
        ".tika-law-panel{right:12px;bottom:84px;width:calc(100vw - 24px);height:calc(100vh - 108px)}" +
        ".tika-law-launcher{right:16px;bottom:16px}" +
      "}";

    document.head.appendChild(style);
  }

  /* ── Theme ──────────────────────────────────────────────────────────────── */
  var THEME_MAP = {
    primary:        "--tika-primary",
    primaryHover:   "--tika-primary-hover",
    widgetBg:       "--tika-widget-bg",
    pageBg:         "--tika-page-bg",
    border:         "--tika-border",
    textPrimary:    "--tika-text-primary",
    textSecondary:  "--tika-text-secondary",
    textMuted:      "--tika-text-muted",
    botBubbleBg:    "--tika-bot-bubble-bg",
    botBubbleText:  "--tika-bot-bubble-text",
    userBubbleBg:   "--tika-user-bubble-bg",
    userBubbleText: "--tika-user-bubble-text",
    inputBorder:    "--tika-input-border",
  };

  function applyTheme(root, theme) {
    if (!theme) return;
    Object.keys(theme).forEach(function (key) {
      var prop = THEME_MAP[key];
      if (prop) root.style.setProperty(prop, theme[key]);
    });
  }

  /* ── Chat helpers ───────────────────────────────────────────────────────── */
  function showTyping(messages) {
    var row = createElement("div", "tika-law-row is-bot tika-law-typing-row");
    row.appendChild(makeAvatar("bot"));
    var dots = createElement("div", "tika-law-bubble tika-law-typing");
    dots.innerHTML = "<span></span><span></span><span></span>";
    row.appendChild(dots);
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;
    return row;
  }

  function hideTyping(row) {
    if (row && row.parentNode) row.parentNode.removeChild(row);
  }

  function appendMessage(messages, role, text) {
    var row = createElement("div", "tika-law-row " + (role === "user" ? "is-user" : "is-bot"));
    row.appendChild(makeAvatar(role));
    row.appendChild(createElement("div", "tika-law-bubble", text));
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;
  }

  /* ── Init ───────────────────────────────────────────────────────────────── */
  function init(options) {
    var config = options || {};
    var mount =
      typeof config.mount === "string"
        ? document.querySelector(config.mount)
        : config.mount || document.body;

    if (!mount) throw new Error("Tika Law widget mount element was not found.");
    if (!config.apiBaseUrl) throw new Error("Tika Law widget requires apiBaseUrl.");
    if (!config.attorneyId) throw new Error("Tika Law widget requires attorneyId.");

    injectStyles();
    if (mount !== document.body) mount.innerHTML = "";

    var conversationId = null;
    var root = createElement("div", "tika-law-root");
    applyTheme(root, config.theme);

    var launcher = createElement("button", "tika-law-launcher");
    launcher.type = "button";
    launcher.innerHTML = SVG_SCALE;

    var panel = createElement("section", "tika-law-panel");
    var header = createElement("header", "tika-law-header");
    var headerAvatar = makeAvatar("bot");
    var headerText = createElement("div");
    var title = createElement("h2", "tika-law-title", "Tika Law");
    var subtitle = createElement("p", "tika-law-subtitle", "תיאום ובירור ראשוני");
    var closeButton = createElement("button", "tika-law-close", "×");
    closeButton.type = "button";
    var messages = createElement("div", "tika-law-messages");
    var disclaimer = createElement("div", "tika-law-disclaimer", "שיחה ראשונית בלבד, לא ייעוץ משפטי.");
    var composer = createElement("form", "tika-law-composer");
    var input = createElement("input", "tika-law-input");
    input.type = "text";
    input.placeholder = "כתוב/כתבי כאן...";
    var send = createElement("button", "tika-law-send");
    send.type = "submit";
    send.innerHTML = SVG_PLANE;

    headerText.appendChild(title);
    headerText.appendChild(subtitle);
    header.appendChild(headerAvatar);
    header.appendChild(headerText);
    header.appendChild(closeButton);
    composer.appendChild(input);
    composer.appendChild(send);
    panel.appendChild(header);
    panel.appendChild(messages);
    panel.appendChild(disclaimer);
    panel.appendChild(composer);
    root.appendChild(panel);
    root.appendChild(launcher);
    mount.appendChild(root);

    appendMessage(
      messages,
      "bot",
      "שלום, אני טיקה, העוזרת הדיגיטלית של המשרד.\nאנא תארו בקצרה את עניין דיני העבודה שברצונכם לברר."
    );

    launcher.addEventListener("click", function () {
      panel.classList.add("is-open");
      input.focus();
    });
    closeButton.addEventListener("click", function () {
      panel.classList.remove("is-open");
    });

    composer.addEventListener("submit", function (event) {
      event.preventDefault();
      var message = input.value.trim();
      if (!message) return;

      input.value = "";
      send.disabled = true;
      appendMessage(messages, "user", message);
      var typingRow = showTyping(messages);

      fetch(config.apiBaseUrl.replace(/\/$/, "") + "/api/v1/chat/message", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Attorney-Id": config.attorneyId,
        },
        body: JSON.stringify({
          attorney_id: config.attorneyId,
          conversation_id: conversationId,
          message: message,
        }),
      })
        .then(function (response) {
          if (!response.ok) {
            return response.json().then(function (errorBody) {
              throw new Error(errorBody.detail || "השליחה נכשלה");
            });
          }
          return response.json();
        })
        .then(function (data) {
          hideTyping(typingRow);
          conversationId = data.conversation_id;
          appendMessage(messages, "bot", data.assistant_message);
        })
        .catch(function (error) {
          hideTyping(typingRow);
          appendMessage(messages, "bot", "מצטערת, הייתה תקלה בחיבור. אפשר לנסות שוב בעוד רגע. " + error.message);
        })
        .finally(function () {
          send.disabled = false;
          input.focus();
        });
    });
  }

  window.TikaLaw = window.TikaLaw || {};
  window.TikaLaw.init = init;
})();
