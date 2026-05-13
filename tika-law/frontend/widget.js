(function () {
  function createElement(tagName, className, text) {
    var element = document.createElement(tagName);
    if (className) element.className = className;
    if (text) element.textContent = text;
    return element;
  }

  function init(options) {
    var config = options || {};
    var mount =
      typeof config.mount === "string"
        ? document.querySelector(config.mount)
        : config.mount;

    if (!mount) {
      throw new Error("Tika Law widget mount element was not found.");
    }

    if (!config.apiBaseUrl) {
      throw new Error("Tika Law widget requires apiBaseUrl.");
    }

    if (!config.attorneyId) {
      throw new Error("Tika Law widget requires attorneyId.");
    }

    mount.innerHTML = "";

    var root = createElement("section", "tika-law-widget");
    root.setAttribute("dir", "rtl");

    var title = createElement("h2", "tika-law-widget__title", "בדיקת התאמה ראשונית");
    var description = createElement(
      "p",
      "tika-law-widget__description",
      "השירות אוסף פרטים ראשוניים עבור עורך הדין ואינו מספק ייעוץ משפטי."
    );
    var status = createElement("p", "tika-law-widget__status", "מוכן לבדיקה");
    var button = createElement("button", "tika-law-widget__button", "בדיקת חיבור");

    button.type = "button";
    button.addEventListener("click", function () {
      status.textContent = "בודק חיבור...";

      fetch(config.apiBaseUrl.replace(/\/$/, "") + "/health", {
        headers: {
          "X-Attorney-Id": config.attorneyId,
        },
      })
        .then(function (response) {
          if (!response.ok) {
            throw new Error("Health check failed with status " + response.status);
          }

          return response.json();
        })
        .then(function (data) {
          status.textContent = "החיבור תקין: " + data.service;
        })
        .catch(function (error) {
          status.textContent = "שגיאת חיבור: " + error.message;
        });
    });

    root.appendChild(title);
    root.appendChild(description);
    root.appendChild(button);
    root.appendChild(status);
    mount.appendChild(root);
  }

  window.TikaLaw = window.TikaLaw || {};
  window.TikaLaw.init = init;
})();
