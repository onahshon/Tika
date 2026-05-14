(function () {

  /* ── SVG icons ─────────────────────────────────────────────────────────── */
  var SVG_SCALE =
    '<svg viewBox="0 0 24 24" fill="currentColor" width="22" height="22">' +
    '<ellipse cx="12" cy="22" rx="5" ry="1.5"/>' +
    '<rect x="11" y="5.5" width="2" height="16" rx="0.5"/>' +
    '<rect x="2" y="3.5" width="20" height="2.5" rx="1.25"/>' +
    '<polygon points="3.5,6 1,14 7,14"/>' +
    '<path d="M1 14 A3 2 0 0 1 7 14 Z"/>' +
    '<polygon points="20.5,6 17,14 23,14"/>' +
    '<path d="M17 14 A3 2 0 0 1 23 14 Z"/>' +
    '</svg>';

  var SVG_PLANE =
    '<svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18" style="transform:rotate(180deg)">' +
    '<path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/>' +
    '</svg>';

  /* ── DOM helpers ────────────────────────────────────────────────────────── */
  function createElement(tagName, className, text) {
    var el = document.createElement(tagName);
    if (className) el.className = className;
    if (text) el.textContent = text;
    return el;
  }

  /* ── Styles ─────────────────────────────────────────────────────────────── */
  function injectStyles() {
    if (document.querySelector("#tika-law-widget-styles")) return;
    var style = createElement("style");
    style.id = "tika-law-widget-styles";
    style.textContent =
      ".tika-law-root{" +
        "--tika-primary:#2563EB;--tika-primary-dark:#1E40AF;--tika-primary-hover:#1D4ED8;" +
        "--tika-bot-bubble:#F1F7FF;--tika-bot-text:#1E293B;" +
        "--tika-user-bubble:#2563EB;--tika-user-text:#FFFFFF;" +
        "--tika-panel-bg:#FFFFFF;--tika-page-bg:#F6F8FB;--tika-border:#D9E2EC;" +
        "--tika-text-primary:#1E293B;--tika-text-secondary:#64748B;--tika-text-muted:#94A3B8;" +
        "--tika-input-border:#BFD3EA;" +
      "}" +

      /* Launcher */
      ".tika-law-launcher{position:fixed;right:24px;bottom:24px;z-index:2147483000;" +
        "width:56px;height:56px;border:0;border-radius:50%;" +
        "background:var(--tika-primary-dark);color:#fff;" +
        "box-shadow:0 4px 18px rgba(30,64,175,.40);" +
        "cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .15s}" +
      ".tika-law-launcher:hover{background:var(--tika-primary)}" +

      /* Panel */
      ".tika-law-panel{position:fixed;right:24px;bottom:92px;z-index:2147483000;" +
        "width:min(400px,calc(100vw - 32px));height:min(640px,calc(100vh - 112px));" +
        "display:none;flex-direction:column;overflow:hidden;" +
        "border-radius:20px;background:var(--tika-panel-bg);" +
        "border:1px solid var(--tika-border);" +
        "box-shadow:0 12px 48px rgba(15,23,42,.13),0 2px 8px rgba(15,23,42,.06);" +
        "font-family:Arial,'Noto Sans Hebrew',sans-serif;color:var(--tika-text-primary);direction:rtl}" +
      ".tika-law-panel.is-open{display:flex}" +

      /* Header */
      ".tika-law-header{display:flex;align-items:center;padding:16px 18px;" +
        "background:var(--tika-panel-bg);border-bottom:1px solid var(--tika-border)}" +
      ".tika-law-header-icon{width:38px;height:38px;border-radius:50%;background:var(--tika-primary-dark);color:#fff;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-inline-end:10px}" +
      ".tika-law-header-info{display:flex;flex-direction:column;gap:2px}" +
      ".tika-law-title{margin:0;font-size:15px;font-weight:700;color:var(--tika-text-primary)}" +
      ".tika-law-subtitle{margin:0;font-size:12px;color:var(--tika-text-secondary);display:flex;align-items:center;gap:5px}" +
      ".tika-law-online{display:inline-block;width:7px;height:7px;border-radius:50%;background:#22C55E;flex-shrink:0}" +
      ".tika-law-close{margin-inline-start:auto;border:0;background:transparent;" +
        "color:var(--tika-text-muted);border-radius:8px;width:32px;height:32px;" +
        "cursor:pointer;font-size:20px;display:flex;align-items:center;justify-content:center;transition:background .12s}" +
      ".tika-law-close:hover{background:var(--tika-page-bg)}" +

      /* Messages area */
      ".tika-law-messages{flex:1;overflow:auto;padding:20px 16px;" +
        "display:flex;flex-direction:column;gap:6px;background:var(--tika-panel-bg)}" +

      /* Rows — no avatars, just bubbles aligned by side */
      ".tika-law-row{display:flex;flex-direction:column;animation:tika-pop .2s ease}" +
      /* RTL: bot sits on the right → tail points left (flat bottom-left corner) */
      ".tika-law-row.is-bot .tika-law-bubble{align-self:flex-end;border-bottom-left-radius:4px}" +
      /* RTL: user sits on the left → tail points right (flat bottom-right corner) */
      ".tika-law-row.is-user .tika-law-bubble{align-self:flex-start;border-bottom-right-radius:4px}" +

      /* Bubbles */
      ".tika-law-bubble{max-width:80%;padding:11px 15px;border-radius:18px;" +
        "line-height:1.55;font-size:14px;white-space:pre-wrap;word-break:break-word}" +
      ".tika-law-row.is-bot .tika-law-bubble{background:var(--tika-bot-bubble);color:var(--tika-bot-text)}" +
      ".tika-law-row.is-user .tika-law-bubble{background:var(--tika-user-bubble);color:var(--tika-user-text)}" +

      /* Pop-in animation */
      "@keyframes tika-pop{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}" +

      /* Typing indicator */
      ".tika-law-typing{display:flex;gap:5px;align-items:center;padding:11px 15px;" +
        "background:var(--tika-bot-bubble);border-radius:18px;border-bottom-right-radius:4px;align-self:flex-end}" +
      ".tika-law-typing span{width:6px;height:6px;border-radius:50%;background:var(--tika-text-muted);" +
        "animation:tika-bounce 1.2s infinite ease-in-out}" +
      ".tika-law-typing span:nth-child(2){animation-delay:.2s}" +
      ".tika-law-typing span:nth-child(3){animation-delay:.4s}" +
      "@keyframes tika-bounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-5px)}}" +

      /* Disclaimer */
      ".tika-law-disclaimer{padding:7px 14px;background:var(--tika-page-bg);" +
        "border-top:1px solid var(--tika-border);color:var(--tika-text-muted);font-size:11px;text-align:center}" +

      /* Composer */
      ".tika-law-composer{display:flex;gap:10px;align-items:flex-end;padding:12px 14px;" +
        "background:var(--tika-page-bg);border-top:1px solid var(--tika-border)}" +
      ".tika-law-input{flex:1;min-width:0;border:1.5px solid var(--tika-input-border);" +
        "border-radius:14px;padding:12px 16px;font:14px Arial,sans-serif;outline:none;" +
        "background:var(--tika-panel-bg);color:var(--tika-text-primary);line-height:1.4}" +
      ".tika-law-input::placeholder{color:var(--tika-text-muted)}" +
      ".tika-law-input:focus{border-color:var(--tika-primary);box-shadow:0 0 0 3px rgba(37,99,235,.10)}" +
      ".tika-law-send{flex-shrink:0;width:44px;height:44px;border:0;border-radius:50%;" +
        "background:var(--tika-primary);color:#fff;cursor:pointer;" +
        "display:flex;align-items:center;justify-content:center;transition:background .15s}" +
      ".tika-law-send:hover:not(:disabled){background:var(--tika-primary-hover)}" +
      ".tika-law-send:disabled{opacity:.5;cursor:wait}" +

      /* Mobile */
      "@media(max-width:520px){" +
        ".tika-law-panel{right:0;bottom:0;width:100vw;height:100dvh;border-radius:0;border:0}" +
        ".tika-law-launcher{right:16px;bottom:16px}" +
      "}";

    document.head.appendChild(style);
  }

  /* ── Theme override ─────────────────────────────────────────────────────── */
  var THEME_MAP = {
    primary:       "--tika-primary",
    primaryDark:   "--tika-primary-dark",
    primaryHover:  "--tika-primary-hover",
    botBubble:     "--tika-bot-bubble",
    botText:       "--tika-bot-text",
    userBubble:    "--tika-user-bubble",
    userText:      "--tika-user-text",
    panelBg:       "--tika-panel-bg",
    pageBg:        "--tika-page-bg",
    border:        "--tika-border",
    textPrimary:   "--tika-text-primary",
    textSecondary: "--tika-text-secondary",
    textMuted:     "--tika-text-muted",
    inputBorder:   "--tika-input-border",
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
    var dots = createElement("div", "tika-law-typing");
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

    /* Launcher */
    var launcher = createElement("button", "tika-law-launcher");
    launcher.type = "button";
    launcher.innerHTML = SVG_SCALE;

    /* Panel */
    var panel = createElement("section", "tika-law-panel");

    /* Header */
    var header = createElement("header", "tika-law-header");
    var headerIcon = createElement("div", "tika-law-header-icon");
    headerIcon.innerHTML = SVG_SCALE;
    var headerInfo = createElement("div", "tika-law-header-info");
    var title = createElement("h2", "tika-law-title", "Tika Law");
    var subtitle = createElement("p", "tika-law-subtitle");
    var onlineDot = createElement("span", "tika-law-online");
    subtitle.appendChild(onlineDot);
    subtitle.appendChild(document.createTextNode("תיאום ובירור ראשוני"));
    headerInfo.appendChild(title);
    headerInfo.appendChild(subtitle);
    var closeButton = createElement("button", "tika-law-close", "×");
    closeButton.type = "button";
    header.appendChild(headerIcon);
    header.appendChild(headerInfo);
    header.appendChild(closeButton);

    /* Body */
    var messages = createElement("div", "tika-law-messages");
    var disclaimer = createElement("div", "tika-law-disclaimer", "שיחה ראשונית בלבד, לא ייעוץ משפטי.");

    /* Composer */
    var composer = createElement("form", "tika-law-composer");
    var input = createElement("input", "tika-law-input");
    input.type = "text";
    input.placeholder = "כתוב/כתבי כאן...";
    var send = createElement("button", "tika-law-send");
    send.type = "submit";
    send.innerHTML = SVG_PLANE;
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
        .then(function (res) {
          if (!res.ok) return res.json().then(function (b) { throw new Error(b.detail || "שגיאה"); });
          return res.json();
        })
        .then(function (data) {
          hideTyping(typingRow);
          conversationId = data.conversation_id;
          appendMessage(messages, "bot", data.assistant_message);
        })
        .catch(function (err) {
          hideTyping(typingRow);
          appendMessage(messages, "bot", "מצטערת, הייתה תקלה בחיבור. אפשר לנסות שוב בעוד רגע. " + err.message);
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
