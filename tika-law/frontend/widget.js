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
      ".tika-law-launcher{position:fixed;right:24px;bottom:24px;z-index:2147483000;width:62px;height:62px;border:0;border-radius:50%;background:#2f6fed;color:#fff;box-shadow:0 16px 40px rgba(20,31,56,.25);font:700 18px Arial,sans-serif;cursor:pointer}" +
      ".tika-law-panel{position:fixed;right:24px;bottom:98px;z-index:2147483000;width:min(380px,calc(100vw - 32px));height:min(620px,calc(100vh - 128px));display:none;flex-direction:column;overflow:hidden;border-radius:22px;background:#f2f4ef;box-shadow:0 22px 70px rgba(20,31,56,.28);font-family:Arial,'Noto Sans Hebrew',sans-serif;color:#1f2937;direction:rtl}" +
      ".tika-law-panel.is-open{display:flex}" +
      ".tika-law-header{display:flex;align-items:center;gap:10px;padding:16px 18px;background:#fff;border-bottom:1px solid #dde3ea}" +
      ".tika-law-header img{width:38px;height:38px;border-radius:50%}.tika-law-title{margin:0;font-size:16px}.tika-law-subtitle{margin:2px 0 0;color:#64748b;font-size:12px}.tika-law-close{margin-inline-start:auto;border:0;background:#edf1f5;border-radius:50%;width:32px;height:32px;cursor:pointer;font-size:18px}" +
      ".tika-law-messages{flex:1;overflow:auto;padding:18px 16px;display:flex;flex-direction:column;gap:14px;background:linear-gradient(180deg,#f7f8f3,#eef2ec)}" +
      ".tika-law-row{display:flex;gap:9px;align-items:flex-end}.tika-law-row.is-user{flex-direction:row-reverse}.tika-law-avatar{width:34px;height:34px;border-radius:50%;flex:0 0 auto}.tika-law-bubble{max-width:76%;padding:12px 14px;border-radius:16px;line-height:1.45;font-size:14px;white-space:pre-wrap}.tika-law-row.is-bot .tika-law-bubble{background:#36383d;color:#fff;border-bottom-right-radius:5px}.tika-law-row.is-user .tika-law-bubble{background:#fff;color:#1f2937;border:1px solid #dbe2ea;border-bottom-left-radius:5px}" +
      ".tika-law-meta{font-size:11px;color:#718096;margin-top:4px}.tika-law-composer{display:flex;gap:8px;align-items:center;padding:12px;background:#fff;border-top:1px solid #dde3ea}.tika-law-input{flex:1;min-width:0;border:1px solid #d7dee8;border-radius:999px;padding:11px 14px;font:14px Arial,sans-serif;outline:none}.tika-law-input:focus{border-color:#2f6fed}.tika-law-send{width:42px;height:42px;border:0;border-radius:50%;background:#2f6fed;color:#fff;font-size:18px;cursor:pointer}.tika-law-send:disabled{opacity:.55;cursor:wait}.tika-law-disclaimer{padding:8px 14px;background:#fff;color:#64748b;font-size:11px;text-align:center}" +
      ".tika-law-typing{display:flex;gap:5px;align-items:center;padding:10px 14px}.tika-law-typing span{width:7px;height:7px;border-radius:50%;background:#adb5bd;animation:tika-bounce 1.2s infinite ease-in-out}.tika-law-typing span:nth-child(2){animation-delay:.2s}.tika-law-typing span:nth-child(3){animation-delay:.4s}@keyframes tika-bounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-6px)}}" +
      "@media (max-width:520px){.tika-law-panel{right:12px;bottom:88px;width:calc(100vw - 24px);height:calc(100vh - 112px)}.tika-law-launcher{right:18px;bottom:18px}}";
    document.head.appendChild(style);
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
