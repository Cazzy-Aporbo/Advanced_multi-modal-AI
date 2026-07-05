(function () {
  const fallback = {
    taxonomy: {
      category_count: 0,
      language_count: 0,
      deterministic_category_count: 0,
      categories: [],
      language_hints: [],
      family_counts: {},
      severity_counts: {},
      source_references: [],
      design_principles: [],
      boundary_notes: [],
    },
    sample_receipt: {},
    sample_category_summaries: [],
    run_records: [],
  };

  const state = {
    family: "all",
    page: 0,
    pageSize: 9,
    taxonomy: fallback.taxonomy,
  };

  const familyLabels = {
    all: "all traces",
    identity: "identity",
    contact: "contact",
    location: "location",
    temporal: "time",
    financial: "money",
    government: "government",
    healthcare: "health",
    biometric: "biometric",
    workforce: "work",
    education: "education",
    legal: "legal",
    operations: "operations",
    commerce: "commerce",
    network: "network",
    device: "device",
    industrial: "industrial",
    credential: "credentials",
    online: "online",
    sensitive_attribute: "sensitive attributes",
  };

  function text(value) {
    return String(value ?? "");
  }

  function escapeHtml(value) {
    return text(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function shortHash(value) {
    const raw = text(value);
    if (!raw) return "not generated";
    return `${raw.slice(0, 18)}...${raw.slice(-10)}`;
  }

  function severityClass(value) {
    return ["critical", "high", "medium"].includes(value) ? value : "low";
  }

  function setText(id, value) {
    const node = document.getElementById(id);
    if (node) node.textContent = text(value);
  }

  function categoryPool() {
    const categories = state.taxonomy.categories || [];
    if (state.family === "all") return categories;
    return categories.filter((item) => item.family === state.family);
  }

  function renderSummaryCards(items) {
    const target = document.getElementById("summary-cards");
    if (!target) return;
    target.innerHTML = "";
    if (!items.length) {
      target.innerHTML =
        '<article class="card"><h3>No proof rows yet.</h3><p>Run the proof export to populate this surface.</p></article>';
      return;
    }
    items.forEach((item, index) => {
      const width = Math.min(98, 22 + Number(item.count || 0) * 18 + index * 8);
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `
        <span class="chip ${severityClass(item.severity)}">${escapeHtml(item.severity)}</span>
        <h3>${escapeHtml(item.label)}</h3>
        <p>${escapeHtml(item.count)} finding(s) in the fixture. Highest confidence: ${escapeHtml(item.highest_confidence)}.</p>
        <div class="bar" style="--w: ${width}%"><span></span></div>
        <div class="chip-row"><span class="chip">${escapeHtml(item.category_id)}</span></div>
      `;
      target.appendChild(card);
    });
  }

  function renderReceipt(receipt) {
    const target = document.getElementById("receipt-panel");
    if (!target) return;
    const rows = [
      ["source", shortHash(receipt.source_sha256)],
      ["redacted", shortHash(receipt.redacted_sha256)],
      ["finding set", shortHash(receipt.finding_set_sha256)],
      ["detector", receipt.detector_version || "not generated"],
      ["masking", receipt.masking_mode || "not generated"],
      ["language hints", (receipt.language_hints || []).join(", ") || "none"],
    ];
    target.innerHTML = rows
      .map(
        ([label, value]) => `
          <div class="receipt-row">
            <strong>${escapeHtml(label)}</strong>
            <span class="hash">${escapeHtml(value)}</span>
          </div>
        `,
      )
      .join("");
  }

  function renderLanguageRail(languages) {
    const target = document.getElementById("language-rail");
    if (!target) return;
    target.innerHTML = (languages || [])
      .map((language) => `<span class="language-chip">${escapeHtml(language)}</span>`)
      .join("");
  }

  function renderFamilyTabs() {
    const target = document.getElementById("category-tabs");
    if (!target) return;
    const families = ["all", ...Object.keys(state.taxonomy.family_counts || {})];
    target.innerHTML = "";
    families.forEach((family) => {
      const count =
        family === "all"
          ? state.taxonomy.category_count || 0
          : state.taxonomy.family_counts?.[family] || 0;
      const button = document.createElement("button");
      button.type = "button";
      button.className = `tab-button${family === state.family ? " active" : ""}`;
      button.textContent = `${familyLabels[family] || family} · ${count}`;
      button.addEventListener("click", () => {
        state.family = family;
        state.page = 0;
        renderFamilyTabs();
        renderTaxonomy();
        renderCategoryMap();
      });
      target.appendChild(button);
    });
  }

  function renderTaxonomy() {
    const target = document.getElementById("taxonomy-cards");
    const status = document.getElementById("category-page-status");
    if (!target) return;
    const pool = categoryPool();
    const pageCount = Math.max(1, Math.ceil(pool.length / state.pageSize));
    state.page = Math.min(state.page, pageCount - 1);
    const offset = state.page * state.pageSize;
    const visible = pool.slice(offset, offset + state.pageSize);
    target.innerHTML = "";
    visible.forEach((item) => {
      const card = document.createElement("article");
      card.className = "card category-card";
      card.innerHTML = `
        <span class="chip ${severityClass(item.severity)}">${escapeHtml(item.severity)}</span>
        <h3>${escapeHtml(item.label)}</h3>
        <p>${escapeHtml(item.description)}</p>
        <ul class="micro-list">
          <li>${escapeHtml(item.why_it_matters)}</li>
          <li>${escapeHtml(item.careful_handling)}</li>
        </ul>
        <div class="chip-row">
          <span class="chip">${escapeHtml(item.family)}</span>
          ${(item.detector_kinds || []).map((kind) => `<span class="chip">${escapeHtml(kind)}</span>`).join("")}
        </div>
        <ul class="micro-list">
          ${(item.where_found || []).slice(0, 4).map((place) => `<li>${escapeHtml(place)}</li>`).join("")}
        </ul>
      `;
      target.appendChild(card);
    });
    if (status) {
      status.textContent = `page ${state.page + 1} of ${pageCount} · ${pool.length} visible`;
    }
  }

  function renderCategoryMap() {
    const target = document.getElementById("category-map");
    if (!target) return;
    const counts = state.taxonomy.family_counts || {};
    const families = Object.entries(counts).filter(([family]) => {
      return state.family === "all" || family === state.family;
    });
    if (!families.length) {
      target.innerHTML = "";
      return;
    }
    const positions = [
      [18, 24],
      [42, 14],
      [70, 22],
      [84, 48],
      [66, 76],
      [36, 78],
      [16, 58],
      [50, 48],
      [28, 42],
      [76, 64],
      [58, 30],
      [22, 76],
      [88, 30],
      [12, 40],
      [46, 86],
      [62, 58],
      [34, 62],
      [78, 82],
      [52, 68],
    ];
    target.innerHTML = families
      .map(([family, count], index) => {
        const [x, y] = positions[index % positions.length];
        const size = Math.min(112, 54 + Number(count) * 10);
        const speed = 7 + (index % 6);
        return `
          <div class="privacy-orb" style="--x:${x}%; --y:${y}%; --size:${size}px; --speed:${speed}s">
            ${escapeHtml(familyLabels[family] || family)}<br>${escapeHtml(count)}
          </div>
        `;
      })
      .join("");
  }

  function renderPrinciples(items) {
    const target = document.getElementById("principle-cards");
    if (!target) return;
    target.innerHTML = (items || [])
      .map(
        (item) => `
          <article class="card principle-card">
            <span class="chip">${escapeHtml(item.principle_id)}</span>
            <h3>${escapeHtml(item.label)}</h3>
            <p>${escapeHtml(item.implementation_note)}</p>
            <div class="chip-row">
              ${(item.source_refs || []).map((ref) => `<span class="chip">${escapeHtml(ref)}</span>`).join("")}
            </div>
          </article>
        `,
      )
      .join("");
  }

  function renderSources(items) {
    const target = document.getElementById("source-cards");
    if (!target) return;
    target.innerHTML = (items || [])
      .map(
        (item) => `
          <article class="card source-card">
            <span class="chip">${escapeHtml(item.reference_id)}</span>
            <h3>${escapeHtml(item.publisher)}</h3>
            <p><a href="${escapeHtml(item.url)}">${escapeHtml(item.title)}</a></p>
            <p>${escapeHtml(item.use_note)}</p>
          </article>
        `,
      )
      .join("");
  }

  function wirePager() {
    const previous = document.getElementById("prev-category-page");
    const next = document.getElementById("next-category-page");
    if (previous) {
      previous.addEventListener("click", () => {
        state.page = Math.max(0, state.page - 1);
        renderTaxonomy();
      });
    }
    if (next) {
      next.addEventListener("click", () => {
        const pageCount = Math.max(1, Math.ceil(categoryPool().length / state.pageSize));
        state.page = Math.min(pageCount - 1, state.page + 1);
        renderTaxonomy();
      });
    }
  }

  function hydrate(payload) {
    const data = payload || fallback;
    const taxonomy = data.taxonomy || fallback.taxonomy;
    state.taxonomy = taxonomy;
    setText("category-count", taxonomy.category_count || 0);
    setText("language-count", taxonomy.language_count || 0);
    setText("deterministic-count", taxonomy.deterministic_category_count || 0);
    setText("run-count", (data.run_records || []).length);
    renderSummaryCards(data.sample_category_summaries || []);
    renderReceipt(data.sample_receipt || {});
    renderLanguageRail(taxonomy.language_hints || []);
    renderFamilyTabs();
    renderTaxonomy();
    renderCategoryMap();
    renderPrinciples(taxonomy.design_principles || []);
    renderSources(taxonomy.source_references || []);
  }

  wirePager();
  fetch("proof/privacy-membrane.json", { cache: "no-store" })
    .then((response) => (response.ok ? response.json() : fallback))
    .then(hydrate)
    .catch(() => hydrate(fallback));
})();
