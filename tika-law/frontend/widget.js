(function () {
  var scriptSrc = document.currentScript && document.currentScript.src;
  var assetBaseUrl = scriptSrc ? scriptSrc.replace(/\/widget\.js(?:\?.*)?$/, "") : "";

  function createElement(tagName, className, text) {
    var element = document.createElement(tagName);
    if (className) element.className = className;
    if (text) element.textContent = text;
    return element;
  }

  function injectStyles() {
    if (document.querySelector("#tika-law-widget-styles")) return;

    var style = createElement("style");
    style.id = "tika-law-widget-styles";
    style.textContent =
      /* CSS custom property defaults scoped to widget root */
      ".tika-law-root{" +
        "--tika-primary:#0077E6;--tika-primary-hover:#0068CC;" +
        "--tika-widget-bg:#FFFFFF;--tika-page-bg:#F5F7FA;--tika-border:#E1E7F0;" +
        "--tika-text-primary:#0F172A;--tika-text-secondary:#64748B;--tika-text-muted:#94A3B8;" +
        "--tika-bot-bubble-bg:#EAF3FF;--tika-bot-bubble-text:#1E293B;" +
        "--tika-user-bubble-bg:#0077E6;--tika-user-bubble-text:#FFFFFF;" +
        "--tika-input-border:#DCE4EE;" +
      "}" +

      ".tika-law-launcher{position:fixed;right:24px;bottom:24px;z-index:2147483000;width:60px;height:60px;border:0;border-radius:50%;background:var(--tika-primary);color:#fff;box-shadow:0 4px 20px rgba(0,119,230,.28);font:700 18px Arial,sans-serif;cursor:pointer;transition:background .15s}" +
      ".tika-law-launcher:hover{background:var(--tika-primary-hover)}" +

      ".tika-law-panel{position:fixed;right:24px;bottom:96px;z-index:2147483000;width:min(380px,calc(100vw - 32px));height:min(620px,calc(100vh - 120px));display:none;flex-direction:column;overflow:hidden;border-radius:16px;background:var(--tika-widget-bg);border:1px solid var(--tika-border);box-shadow:0 8px 36px rgba(15,23,42,.10);font-family:Arial,'Noto Sans Hebrew',sans-serif;color:var(--tika-text-primary);direction:rtl}" +
      ".tika-law-panel.is-open{display:flex}" +

      ".tika-law-header{display:flex;align-items:center;gap:10px;padding:14px 16px;background:var(--tika-widget-bg);border-bottom:1px solid var(--tika-border)}" +
      ".tika-law-header img{width:36px;height:36px;border-radius:50%}" +
      ".tika-law-title{margin:0;font-size:15px;font-weight:600;color:var(--tika-text-primary)}" +
      ".tika-law-subtitle{margin:2px 0 0;font-size:12px;color:var(--tika-text-secondary)}" +
      ".tika-law-close{margin-inline-start:auto;border:0;background:transparent;color:var(--tika-text-muted);border-radius:50%;width:30px;height:30px;cursor:pointer;font-size:20px;line-height:1;display:flex;align-items:center;justify-content:center;transition:background .12s}" +
      ".tika-law-close:hover{background:var(--tika-page-bg)}" +

      ".tika-law-messages{flex:1;overflow:auto;padding:16px;display:flex;flex-direction:column;gap:12px;background:var(--tika-page-bg)}" +

      ".tika-law-row{display:flex;gap:8px;align-items:flex-end}" +
      ".tika-law-row.is-user{flex-direction:row-reverse}" +
      ".tika-law-avatar{width:32px;height:32px;border-radius:50%;flex:0 0 auto}" +
      ".tika-law-bubble{max-width:78%;padding:10px 14px;border-radius:16px;line-height:1.5;font-size:14px;white-space:pre-wrap;word-break:break-word}" +
      ".tika-law-row.is-bot .tika-law-bubble{background:var(--tika-bot-bubble-bg);color:var(--tika-bot-bubble-text);border-bottom-right-radius:4px}" +
      ".tika-law-row.is-user .tika-law-bubble{background:var(--tika-user-bubble-bg);color:var(--tika-user-bubble-text);border-bottom-left-radius:4px}" +

      ".tika-law-composer{display:flex;gap:8px;align-items:center;padding:10px 12px;background:var(--tika-widget-bg);border-top:1px solid var(--tika-border)}" +
      ".tika-law-input{flex:1;min-width:0;border:1px solid var(--tika-input-border);border-radius:999px;padding:10px 14px;font:14px Arial,sans-serif;outline:none;background:var(--tika-widget-bg);color:var(--tika-text-primary)}" +
      ".tika-law-input::placeholder{color:var(--tika-text-muted)}" +
      ".tika-law-input:focus{border-color:var(--tika-primary);box-shadow:0 0 0 3px rgba(0,119,230,.10)}" +
      ".tika-law-send{flex-shrink:0;width:40px;height:40px;border:0;border-radius:50%;background:var(--tika-primary);color:#fff;font-size:17px;cursor:pointer;transition:background .15s}" +
      ".tika-law-send:hover:not(:disabled){background:var(--tika-primary-hover)}" +
      ".tika-law-send:disabled{opacity:.5;cursor:wait}" +

      ".tika-law-disclaimer{padding:6px 14px;background:var(--tika-widget-bg);border-top:1px solid var(--tika-border);color:var(--tika-text-muted);font-size:11px;text-align:center}" +

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

  /* Theme variable map: config.theme key → CSS custom property */
  var THEME_MAP = {
    primary:         "--tika-primary",
    primaryHover:    "--tika-primary-hover",
    widgetBg:        "--tika-widget-bg",
    pageBg:          "--tika-page-bg",
    border:          "--tika-border",
    textPrimary:     "--tika-text-primary",
    textSecondary:   "--tika-text-secondary",
    textMuted:       "--tika-text-muted",
    botBubbleBg:     "--tika-bot-bubble-bg",
    botBubbleText:   "--tika-bot-bubble-text",
    userBubbleBg:    "--tika-user-bubble-bg",
    userBubbleText:  "--tika-user-bubble-text",
    inputBorder:     "--tika-input-border",
  };

  function applyTheme(root, theme) {
    if (!theme) return;
    Object.keys(theme).forEach(function (key) {
      var prop = THEME_MAP[key];
      if (prop) root.style.setProperty(prop, theme[key]);
    });
  }

  function showTyping(messages) {
    var row = createElement("div", "tika-law-row is-bot tika-law-typing-row");
    var avatar = document.createElement("img");
    avatar.className = "tika-law-avatar";
    avatar.alt = "Tika Law";
    avatar.src = assetBaseUrl + "/assets/bot-avatar.svg";
    var dots = createElement("div", "tika-law-bubble tika-law-typing");
    dots.innerHTML = "<span></span><span></span><span></span>";
    row.appendChild(avatar);
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
    var avatar = document.createElement("img");
    avatar.className = "tika-law-avatar";
    avatar.alt = role === "user" ? "User" : "Tika Law";
    avatar.src = assetBaseUrl + "/assets/" + (role === "user" ? "user-avatar.svg" : "bot-avatar.svg");
    var bubble = createElement("div", "tika-law-bubble", text);
    row.appendChild(avatar);
    row.appendChild(bubble);
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;
  }

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

    var launcher = createElement("button", "tika-law-launcher", "TL");
    var panel = createElement("section", "tika-law-panel");
    var header = createElement("header", "tika-law-header");
    var headerAvatar = document.createElement("img");
    var headerText = createElement("div");
    var title = createElement("h2", "tika-law-title", "Tika Law");
    var subtitle = createElement("p", "tika-law-subtitle", "תיאום ובירור ראשוני");
    var closeButton = createElement("button", "tika-law-close", "×");
    var messages = createElement("div", "tika-law-messages");
    var disclaimer = createElement("div", "tika-law-disclaimer", "שיחה ראשונית בלבד, לא ייעוץ משפטי.");
    var composer = createElement("form", "tika-law-composer");
    var input = createElement("input", "tika-law-input");
    var send = createElement("button", "tika-law-send", "↑");

    launcher.type = "button";
    closeButton.type = "button";
    input.type = "text";
    input.placeholder = "כתוב/כתבי כאן...";
    send.type = "submit";
    headerAvatar.alt = "Tika Law";
    headerAvatar.src = assetBaseUrl + "/assets/bot-avatar.svg";

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
