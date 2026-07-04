(function () {
  const fallback = {
    taxonomy: {
      category_count: 0,
      language_count: 0,
      deterministic_category_count: 0,
      categories: [],
      boundary_notes: [],
    },
    sample_receipt: {},
    sample_category_summaries: [],
    run_records: [],
  };

  function text(value) {
    return String(value ?? "");
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

  function renderSummaryCards(items) {
    const target = document.getElementById("summary-cards");
    if (!target) return;
    target.innerHTML = "";
    if (!items.length) {
      target.innerHTML = "<article class=\"card\"><h3>No proof rows yet.</h3><p>Run the proof export to populate this surface.</p></article>";
      return;
    }
    items.forEach((item, index) => {
      const width = Math.min(98, 22 + Number(item.count || 0) * 18 + index * 8);
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `
        <span class="chip ${severityClass(item.severity)}">${text(item.severity)}</span>
        <h3>${text(item.label)}</h3>
        <p>${text(item.count)} finding(s) in the fixture. Highest confidence: ${text(item.highest_confidence)}.</p>
        <div class="bar" style="--w: ${width}%"><span></span></div>
        <div class="chip-row"><span class="chip">${text(item.category_id)}</span></div>
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
            <strong>${label}</strong>
            <span class="hash">${value}</span>
          </div>
        `,
      )
      .join("");
  }

  function renderTaxonomy(categories) {
    const target = document.getElementById("taxonomy-cards");
    if (!target) return;
    target.innerHTML = "";
    categories.slice(0, 12).forEach((item, index) => {
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `
        <span class="chip ${severityClass(item.severity)}">${text(item.severity)}</span>
        <h3>${text(item.label)}</h3>
        <p>${text(item.description)}</p>
        <div class="chip-row">
          <span class="chip">${text(item.family)}</span>
          ${(item.detector_kinds || []).map((kind) => `<span class="chip">${text(kind)}</span>`).join("")}
        </div>
        <div class="bar" style="--w: ${Math.min(92, 28 + index * 5)}%"><span></span></div>
      `;
      target.appendChild(card);
    });
  }

  function hydrate(payload) {
    const data = payload || fallback;
    const taxonomy = data.taxonomy || fallback.taxonomy;
    setText("category-count", taxonomy.category_count || 0);
    setText("language-count", taxonomy.language_count || 0);
    setText("deterministic-count", taxonomy.deterministic_category_count || 0);
    setText("run-count", (data.run_records || []).length);
    renderSummaryCards(data.sample_category_summaries || []);
    renderReceipt(data.sample_receipt || {});
    renderTaxonomy(taxonomy.categories || []);
  }

  fetch("proof/privacy-membrane.json", { cache: "no-store" })
    .then((response) => (response.ok ? response.json() : fallback))
    .then(hydrate)
    .catch(() => hydrate(fallback));
})();
