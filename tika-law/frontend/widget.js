(function () {
  function createElement(tagName, className, text) {
    var element = document.createElement(tagName);
    if (className) element.className = className;
    if (text) element.textContent = text;
    return element;
  }

  function createField(name, label, type, required) {
    var wrapper = createElement("label", "tika-law-widget__field");
    var labelText = createElement("span", null, label);
    var input = type === "textarea" ? document.createElement("textarea") : document.createElement("input");

    input.name = name;
    input.required = Boolean(required);
    if (type !== "textarea") input.type = type || "text";
    if (type === "textarea") input.rows = 5;

    wrapper.appendChild(labelText);
    wrapper.appendChild(input);
    return wrapper;
  }

  function getFormData(form) {
    var data = new FormData(form);
    return {
      attorney_id: form.getAttribute("data-attorney-id"),
      full_name: String(data.get("full_name") || "").trim(),
      phone: String(data.get("phone") || "").trim(),
      email: String(data.get("email") || "").trim() || null,
      employment_status: String(data.get("employment_status") || "").trim(),
      issue_type: String(data.get("issue_type") || "").trim(),
      employer_name: String(data.get("employer_name") || "").trim() || null,
      incident_date: String(data.get("incident_date") || "").trim() || null,
      desired_outcome: String(data.get("desired_outcome") || "").trim() || null,
      description: String(data.get("description") || "").trim(),
    };
  }

  function renderResult(container, result) {
    container.innerHTML = "";

    container.appendChild(createElement("h3", "tika-law-widget__result-title", "סיכום ראשוני"));
    container.appendChild(
      createElement(
        "p",
        "tika-law-widget__badge",
        "דירוג: " + result.classification + " (" + result.score + "/100)"
      )
    );
    container.appendChild(createElement("p", "tika-law-widget__message", result.next_message));

    if (result.follow_up_questions && result.follow_up_questions.length) {
      var listTitle = createElement("p", "tika-law-widget__questions-title", "שאלות המשך:");
      var list = createElement("ol", "tika-law-widget__questions");
      result.follow_up_questions.forEach(function (question) {
        list.appendChild(createElement("li", null, question));
      });
      container.appendChild(listTitle);
      container.appendChild(list);
    }

    container.appendChild(createElement("p", "tika-law-widget__disclaimer", result.disclaimer));
  }

  function init(options) {
    var config = options || {};
    var mount =
      typeof config.mount === "string"
        ? document.querySelector(config.mount)
        : config.mount;

    if (!mount) throw new Error("Tika Law widget mount element was not found.");
    if (!config.apiBaseUrl) throw new Error("Tika Law widget requires apiBaseUrl.");
    if (!config.attorneyId) throw new Error("Tika Law widget requires attorneyId.");

    mount.innerHTML = "";

    var root = createElement("section", "tika-law-widget");
    root.setAttribute("dir", "rtl");

    var title = createElement("h2", "tika-law-widget__title", "בדיקת התאמה ראשונית");
    var description = createElement(
      "p",
      "tika-law-widget__description",
      "מלאו פרטים ראשוניים לעורך הדין. המערכת אינה מספקת ייעוץ משפטי."
    );
    var form = createElement("form", "tika-law-widget__form");
    var status = createElement("p", "tika-law-widget__status", "");
    var result = createElement("div", "tika-law-widget__result");
    var submit = createElement("button", "tika-law-widget__button", "שליחת פנייה לבדיקה");

    form.setAttribute("data-attorney-id", config.attorneyId);
    submit.type = "submit";

    form.appendChild(createField("full_name", "שם מלא", "text", true));
    form.appendChild(createField("phone", "טלפון", "tel", true));
    form.appendChild(createField("email", "אימייל", "email", false));
    form.appendChild(createField("employment_status", "סטטוס העסקה", "text", true));
    form.appendChild(createField("issue_type", "נושא הפנייה", "text", true));
    form.appendChild(createField("employer_name", "שם המעסיק", "text", false));
    form.appendChild(createField("incident_date", "מועד רלוונטי", "text", false));
    form.appendChild(createField("desired_outcome", "מה תרצו להשיג?", "text", false));
    form.appendChild(createField("description", "מה קרה?", "textarea", true));
    form.appendChild(submit);

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      status.textContent = "שולח לבדיקה...";
      result.innerHTML = "";
      submit.disabled = true;

      fetch(config.apiBaseUrl.replace(/\/$/, "") + "/api/v1/intake/qualify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Attorney-Id": config.attorneyId,
        },
        body: JSON.stringify(getFormData(form)),
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
          status.textContent = "";
          renderResult(result, data);
        })
        .catch(function (error) {
          status.textContent = "שגיאה: " + error.message;
        })
        .finally(function () {
          submit.disabled = false;
        });
    });

    root.appendChild(title);
    root.appendChild(description);
    root.appendChild(form);
    root.appendChild(status);
    root.appendChild(result);
    mount.appendChild(root);
  }

  window.TikaLaw = window.TikaLaw || {};
  window.TikaLaw.init = init;
})();
