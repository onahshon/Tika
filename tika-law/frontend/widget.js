(function () {

  /* ── SVG icons ─────────────────────────────────────────────────────────── */
  var SVG_BOT =
    '<svg viewBox="0 0 122 128" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" width="22" height="23">' +
    /* body legs */
    '<path stroke-width="3" d="M37,79C34.3,80.3 31.5,81.4 29,83C21.3,88.1 18.5,91.8 23.9,101.5C29.5,111.5 37.3,118.3 48.2,122.1C51.1,117.6 50,112.3 50.9,107.5C52.6,98.1 53.7,88.5 55,79"/>' +
    '<path stroke-width="3" d="M85,79C89.2,81.4 94,82.8 97.5,86.5C101.1,90.2 101.6,93.1 99.5,98C92.7,114.5 77,125 57.5,124C54.8,123.8 52,123.4 49.5,122"/>' +
    '<path stroke-width="3" d="M67,79C68.8,92 71.1,104.9 72,118C72.1,119 72.7,120 73,121"/>' +
    /* head */
    '<path stroke-width="3" d="M61,25.5C54.9,26.6 48.6,26.2 42.5,25.9C32,25.4 23.3,32 22.2,43.5C21.6,51.1 20.5,59 24,66.5C27.4,73.9 34,78.1 42,78C55.3,77.9 68.7,77.9 82,78C87.6,78.1 95.5,72.6 98,66.5C101,59.2 99.3,51.5 99.4,44C99.5,32.4 89.9,26 80.5,26C74.2,25.9 67.8,26.6 61.5,25.5"/>' +
    /* ears */
    '<path stroke-width="3" d="M22,41C20.2,40.7 19,41.9 18,43C14.1,47.5 15.6,59.3 20.5,63C20.8,63.1 21.5,62.7 22,62.5"/>' +
    '<path stroke-width="3" d="M100,62.5C100.5,62.5 101.1,62.7 101.5,62.5C107.3,59 106.2,53.2 105.9,48C105.7,44.6 104.2,41.4 100,41"/>' +
    /* antenna */
    '<path stroke-width="2" d="M61.5,18C62.4,16.6 65,17 65.1,14.5C65.1,12.1 64.7,9.9 62.5,9.1C60.4,8.3 58,9.2 57.1,11.1C56.4,12.6 56.1,15 58,16.5C58.9,17.1 60,17.5 61,18"/>' +
    '<path stroke-width="3" d="M61,18.5L61,25"/>' +
    /* face screen */
    '<path stroke-width="3" d="M38,38C34.5,39.8 33.8,42.9 34,46.5C34.1,50.5 34,54.5 34,58.5C34.1,63.5 36.5,66 41.5,66C54.5,66 67.5,66 80.5,66C85.5,66 87.9,63.5 88,58.5C88,54.2 88,49.8 88,45.5C87.9,40 85.9,38 80.5,38C66.5,38 52.5,38 38.5,38"/>' +
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
      ".tika-law-messages{flex:1;min-height:0;overflow-y:auto;overflow-x:hidden;padding:20px 16px;" +
        "display:flex;flex-direction:column;gap:6px;background:var(--tika-panel-bg)}" +

      /* Rows — no avatars, just bubbles aligned by side */
      ".tika-law-row{display:flex;flex-direction:column;min-width:0;animation:tika-pop .2s ease}" +
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

      /* Contact form card */
      ".tika-law-contact-card{background:var(--tika-panel-bg);border:1.5px solid var(--tika-border);border-radius:16px;padding:16px 18px;display:flex;flex-direction:column;gap:12px;animation:tika-pop .22s ease}" +
      ".tika-law-contact-heading{margin:0;font-size:13px;font-weight:600;color:var(--tika-text-primary)}" +
      ".tika-law-contact-field{display:flex;flex-direction:column;gap:5px}" +
      ".tika-law-contact-label{font-size:12px;font-weight:500;color:var(--tika-text-secondary)}" +
      ".tika-law-contact-inp{border:1.5px solid var(--tika-input-border);border-radius:10px;padding:9px 13px;font:16px Arial,sans-serif;outline:none;color:var(--tika-text-primary);background:var(--tika-panel-bg);width:100%;box-sizing:border-box;direction:rtl}" +
      ".tika-law-contact-inp:focus{border-color:var(--tika-primary);box-shadow:0 0 0 3px rgba(37,99,235,.10)}" +
      ".tika-law-contact-inp.error{border-color:#EF4444}" +
      ".tika-law-contact-submit{background:var(--tika-primary);color:#fff;border:0;border-radius:10px;padding:11px 16px;font:600 14px Arial,sans-serif;cursor:pointer;transition:background .15s;width:100%}" +
      ".tika-law-contact-submit:hover:not(:disabled){background:var(--tika-primary-hover)}" +
      ".tika-law-contact-submit:disabled{opacity:.55;cursor:wait}" +
      ".tika-law-contact-success{text-align:center;color:var(--tika-text-secondary);font-size:14px;padding:6px 0;line-height:1.5}" +

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
        "border-radius:14px;padding:12px 16px;font:16px Arial,sans-serif;outline:none;" +
        "background:var(--tika-panel-bg);color:var(--tika-text-primary);line-height:1.4}" +
      ".tika-law-input::placeholder{color:var(--tika-text-muted)}" +
      ".tika-law-input:focus{border-color:var(--tika-primary);box-shadow:0 0 0 3px rgba(37,99,235,.10)}" +
      ".tika-law-send{flex-shrink:0;width:44px;height:44px;border:0;border-radius:50%;" +
        "background:var(--tika-primary);color:#fff;cursor:pointer;" +
        "display:flex;align-items:center;justify-content:center;transition:background .15s}" +
      ".tika-law-send:hover:not(:disabled){background:var(--tika-primary-hover)}" +
      ".tika-law-send:disabled{opacity:.5;cursor:wait}" +

      /* Mobile */
      "@media(max-width:640px){" +
        ".tika-law-panel," +
        ".tika-law-panel.is-open{" +
          "position:fixed!important;" +
          "top:0!important;right:0!important;bottom:0!important;left:0!important;" +
          "width:100dvw!important;max-width:100dvw!important;" +
          "height:auto!important;max-height:none!important;min-height:unset!important;" +
          "border-radius:0!important;" +
          "margin:0!important;" +
          "border:none!important;" +
          "box-shadow:none!important;" +
          "overflow-x:hidden!important}" +
        ".tika-law-root{width:100vw;overflow-x:hidden}" +
        ".tika-law-panel.is-open~.tika-law-launcher," +
        ".tika-law-launcher.is-hidden-mobile{display:none!important}" +
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

  /* ── Contact form ───────────────────────────────────────────────────────── */
  function makeField(labelText, inputType, placeholder) {
    var wrapper = createElement("div", "tika-law-contact-field");
    var label = createElement("label", "tika-law-contact-label", labelText);
    var inp = createElement("input", "tika-law-contact-inp");
    inp.type = inputType;
    inp.placeholder = placeholder;
    wrapper.appendChild(label);
    wrapper.appendChild(inp);
    return { wrapper: wrapper, input: inp };
  }

  function appendContactForm(messages, getConversationId, apiBaseUrl, attorneyId) {
    var card = createElement("div", "tika-law-contact-card");
    var heading = createElement("p", "tika-law-contact-heading", "השאירו פרטים ועורך דין יחזור אליכם:");
    var nameF  = makeField("שם מלא *",            "text",  "ישראל ישראלי");
    var phoneF = makeField("טלפון *",              "tel",   "05X-XXXXXXX");
    var emailF = makeField("אימייל (אופציונלי)", "email", "mail@example.com");
    var submit = createElement("button", "tika-law-contact-submit", "שלחו פרטים");
    submit.type = "button";

    card.appendChild(heading);
    card.appendChild(nameF.wrapper);
    card.appendChild(phoneF.wrapper);
    card.appendChild(emailF.wrapper);
    card.appendChild(submit);

    var row = createElement("div", "tika-law-row is-bot");
    row.appendChild(card);
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;

    submit.addEventListener("click", function () {
      var name  = nameF.input.value.trim();
      var phone = phoneF.input.value.trim();
      var email = emailF.input.value.trim();

      nameF.input.classList.toggle("error", !name);
      phoneF.input.classList.toggle("error", !phone);
      if (!name || !phone) return;

      submit.disabled = true;
      submit.textContent = "שולח...";

      fetch(apiBaseUrl.replace(/\/$/, "") + "/api/v1/chat/contact", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Attorney-Id": attorneyId,
        },
        body: JSON.stringify({
          attorney_id: attorneyId,
          conversation_id: getConversationId(),
          name: name,
          phone: phone,
          email: email || null,
        }),
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          card.innerHTML = "";
          var msg = data.success
            ? "✓ פרטיך התקבלו. עורך דין יחזור אליך בהקדם."
            : "הייתה בעיה בשליחה. אפשר לנסות שוב.";
          card.appendChild(createElement("p", "tika-law-contact-success", msg));
          if (!data.success) {
            submit.disabled = false;
            submit.textContent = "שלחו פרטים";
            card.appendChild(submit);
          }
        })
        .catch(function () {
          submit.disabled = false;
          submit.textContent = "שלחו פרטים";
        });
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
    launcher.innerHTML = SVG_BOT;

    /* Panel */
    var panel = createElement("section", "tika-law-panel");

    /* Header */
    var header = createElement("header", "tika-law-header");
    var headerIcon = createElement("div", "tika-law-header-icon");
    headerIcon.innerHTML = SVG_BOT;
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

    if (config.autoOpen) {
      var delay = typeof config.autoOpen === "number" ? config.autoOpen : 2000;
      setTimeout(function () {
        panel.classList.add("is-open");
        input.focus();
      }, delay);
    }

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
          if (data.show_contact_form) {
            appendContactForm(messages, function () { return conversationId; }, config.apiBaseUrl, config.attorneyId);
          }
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
