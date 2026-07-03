(function () {
  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function listMarkup(items, className) {
    const values = Array.isArray(items) ? items : [];
    if (!values.length) {
      return `<ul class="${className}"><li>Nothing has been recorded here yet.</li></ul>`;
    }
    return `<ul class="${className}">${values
      .map((item) => `<li>${escapeHtml(item)}</li>`)
      .join("")}</ul>`;
  }

  async function loadResearchSurfaceBundle() {
    const candidates = ["proof/research-surfaces.json", "/v1/research/surfaces"];
    for (const url of candidates) {
      try {
        const response = await fetch(url, { cache: "no-store" });
        if (response.ok) {
          return await response.json();
        }
      } catch (_error) {
        // keep trying the next surface
      }
    }
    return null;
  }

  async function loadRepositoryPulse() {
    const candidates = ["proof/repository-pulse.json", "/v1/repository/pulse"];
    for (const url of candidates) {
      try {
        const response = await fetch(url, { cache: "no-store" });
        if (response.ok) {
          return await response.json();
        }
      } catch (_error) {
        // keep trying the next surface
      }
    }
    return null;
  }

  window.AMAIResearch = {
    escapeHtml,
    listMarkup,
    loadResearchSurfaceBundle,
    loadRepositoryPulse,
  };
})();
