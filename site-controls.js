(function () {
  const THEME_KEY = "amai-theme";
  const CONTRAST_KEY = "amai-contrast";
  const LOCALE_KEY = "amai-locale";

  const THEMES = [
    ["ember", "Ember"],
    ["midnight", "Midnight"],
    ["sea", "Sea"],
    ["rosewood", "Rosewood"],
    ["dawn", "Dawn"],
    ["paper", "Paper"],
  ];

  const CONTRASTS = [
    ["standard", "Standard"],
    ["high", "High"],
  ];

  const LOCALES = [
    ["en", "English"],
    ["de", "Deutsch"],
    ["ru", "Russian"],
    ["ja", "Japanese"],
    ["fr", "French"],
    ["es", "Spanish"],
  ];

  function getStored(key, fallback) {
    try {
      return window.localStorage.getItem(key) || fallback;
    } catch (_error) {
      return fallback;
    }
  }

  function setStored(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch (_error) {
      // ignore storage failures in preview environments
    }
  }

  function applyTheme(theme) {
    document.body.dataset.theme = theme === "ember" ? "" : theme;
    setStored(THEME_KEY, theme);
  }

  function applyContrast(contrast) {
    document.body.dataset.contrast = contrast === "standard" ? "" : contrast;
    setStored(CONTRAST_KEY, contrast);
  }

  function updateTranslateLink(locale, node) {
    if (!node) return;
    node.href = `https://translate.google.com/translate?sl=auto&tl=${encodeURIComponent(locale)}&u=${encodeURIComponent(window.location.href)}`;
  }

  function applyLocale(locale) {
    document.documentElement.lang = locale;
    setStored(LOCALE_KEY, locale);

    if (window.AMAI_TRANSLATIONS && window.AMAI_TRANSLATIONS[locale]) {
      const translations = window.AMAI_TRANSLATIONS[locale];
      document.querySelectorAll("[data-translate-key]").forEach((node) => {
        const key = node.getAttribute("data-translate-key");
        if (key && Object.prototype.hasOwnProperty.call(translations, key)) {
          node.innerHTML = translations[key];
        }
      });
    }

    updateTranslateLink(locale, document.getElementById("site-translate-link"));
  }

  function renderOptions(options, selected) {
    return options
      .map(
        ([value, label]) =>
          `<option value="${value}"${value === selected ? " selected" : ""}>${label}</option>`,
      )
      .join("");
  }

  function buildDock() {
    const target =
      document.querySelector(".nav-links") ||
      document.querySelector(".nav") ||
      document.querySelector(".wrap");
    if (!target) return;

    const theme = getStored(THEME_KEY, "ember");
    const contrast = getStored(CONTRAST_KEY, "standard");
    const locale = getStored(LOCALE_KEY, "en");

    const dock = document.createElement("div");
    dock.className = "site-dock";
    dock.innerHTML = `
      <span class="site-dock-label">Display</span>
      <select id="site-theme-select" aria-label="Theme">
        ${renderOptions(THEMES, theme)}
      </select>
      <select id="site-contrast-select" aria-label="Contrast">
        ${renderOptions(CONTRASTS, contrast)}
      </select>
      <select id="site-locale-select" aria-label="Language">
        ${renderOptions(LOCALES, locale)}
      </select>
      <a id="site-translate-link" href="#" target="_blank" rel="noreferrer">Translate page</a>
    `;
    target.appendChild(dock);

    const themeSelect = dock.querySelector("#site-theme-select");
    const contrastSelect = dock.querySelector("#site-contrast-select");
    const localeSelect = dock.querySelector("#site-locale-select");

    themeSelect.addEventListener("change", (event) => {
      applyTheme(event.target.value);
    });
    contrastSelect.addEventListener("change", (event) => {
      applyContrast(event.target.value);
    });
    localeSelect.addEventListener("change", (event) => {
      applyLocale(event.target.value);
    });

    applyTheme(theme);
    applyContrast(contrast);
    applyLocale(locale);
  }

  document.addEventListener("DOMContentLoaded", buildDock);
})();
