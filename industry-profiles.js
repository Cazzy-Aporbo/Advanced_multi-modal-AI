(function () {
  function onReady(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
      return;
    }
    callback();
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  async function loadProfiles() {
    const candidates = ["proof/industry-profiles.json", "/v1/industries/profiles"];
    for (const url of candidates) {
      try {
        const response = await fetch(url, { cache: "no-store" });
        if (response.ok) {
          return await response.json();
        }
      } catch (_error) {
        // try the next source
      }
    }
    return null;
  }

  function buildSummary(bundle, profiles) {
    const profileCount = Number(bundle?.profile_count || profiles.length || 0);
    const routeCount = profiles.reduce(
      (sum, profile) => sum + Number((profile.anchor_routes || []).length),
      0,
    );
    const proofCount = profiles.reduce(
      (sum, profile) => sum + Number((profile.proof_surfaces || []).length),
      0,
    );
    const modalitySet = new Set(
      profiles.flatMap((profile) => profile.primary_modalities || []),
    );

    return [
      {
        value: profileCount,
        label: "field profiles",
        note: "distinct operational lenses tied to live routes",
      },
      {
        value: routeCount,
        label: "anchor routes",
        note: "named entry points where review still matters",
      },
      {
        value: proofCount,
        label: "proof links",
        note: "artifacts that keep the public story smaller than the code",
      },
      {
        value: modalitySet.size,
        label: "modality spans",
        note: "audio, image, text, tabular, and video in varying combinations",
      },
    ];
  }

  function buildModalityCounts(profiles) {
    const counts = new Map();
    profiles.forEach((profile) => {
      (profile.primary_modalities || []).forEach((modality) => {
        counts.set(modality, (counts.get(modality) || 0) + 1);
      });
    });
    return Array.from(counts.entries()).sort((left, right) => right[1] - left[1]);
  }

  function renderSummary(host, bundle, profiles) {
    const summary = buildSummary(bundle, profiles);
    host.innerHTML = summary
      .map(
        (item) => `
          <article class="summary-chip">
            <strong>${escapeHtml(item.value)}</strong>
            <span>${escapeHtml(item.label)}</span>
            <p>${escapeHtml(item.note)}</p>
          </article>
        `,
      )
      .join("");
  }

  function renderModalityBars(host, profiles) {
    const counts = buildModalityCounts(profiles);
    const maxCount = Math.max(...counts.map(([, count]) => count), 1);
    host.innerHTML = counts
      .map(
        ([label, count]) => `
          <div class="modality-row">
            <label>${escapeHtml(label)}</label>
            <div class="modality-track">
              <div class="modality-fill" style="--width:${(count / maxCount) * 100}%"></div>
            </div>
            <span>${escapeHtml(count)}</span>
          </div>
        `,
      )
      .join("");
  }

  function renderRail(host, profiles, activeIndex) {
    host.innerHTML = profiles
      .map((profile, index) => {
        const modalities = (profile.primary_modalities || [])
          .map((item) => `<span class="chip">${escapeHtml(item)}</span>`)
          .join("");
        return `
          <button class="card ${index === activeIndex ? "is-active" : ""}" type="button" data-index="${index}">
            <small>${String(index + 1).padStart(2, "0")} · ${escapeHtml(profile.profile_id)}</small>
            <h3 class="card-title">${escapeHtml(profile.label)}</h3>
            <p>${escapeHtml(profile.why_multimodal_matters)}</p>
            <div class="chip-row">${modalities}</div>
          </button>
        `;
      })
      .join("");
  }

  function renderDetail(host, profile, bundle) {
    const routes = profile.anchor_routes || [];
    const routeMarkup = routes.length
      ? routes
          .map(
            (route, index) => `
              <span class="route-pill">${escapeHtml(route)}</span>
              ${index < routes.length - 1 ? '<span class="route-arrow">→</span>' : ""}
            `,
          )
          .join("")
      : '<span class="route-pill">No route mapping recorded.</span>';

    const listMarkup = (items) =>
      Array.isArray(items) && items.length
        ? `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
        : "<p>No items recorded here yet.</p>";

    const proofLinks = (profile.proof_surfaces || [])
      .map(
        (path) => `
          <a class="proof-link" href="${escapeHtml(path)}">${escapeHtml(path)}</a>
        `,
      )
      .join("");

    const continuationLinks = (bundle.continuation_links || [])
      .map(
        (path) => `
          <a class="proof-link" href="${escapeHtml(path)}">${escapeHtml(path)}</a>
        `,
      )
      .join("");

    host.innerHTML = `
      <div class="detail-label">${escapeHtml(profile.profile_id)} · active read</div>
      <h2 class="detail-title">${escapeHtml(profile.label)}</h2>
      <p>${escapeHtml(profile.why_multimodal_matters)}</p>

      <div class="route-chain">${routeMarkup}</div>

      <div class="detail-grid">
        <article class="list-shell">
          <strong>Strict checks</strong>
          ${listMarkup(profile.strict_checks)}
        </article>
        <article class="list-shell">
          <strong>Signal questions</strong>
          ${listMarkup(profile.signal_questions)}
        </article>
        <article class="list-shell">
          <strong>Supply chain focus</strong>
          <p>${escapeHtml(profile.supply_chain_focus)}</p>
        </article>
        <article class="list-shell" id="proof-links">
          <strong>Proof links</strong>
          <div class="proof-links">${proofLinks || '<span class="proof-link">No proof links recorded.</span>'}</div>
        </article>
      </div>

      <div class="proof-links" style="margin-top:18px;">
        ${continuationLinks}
      </div>
    `;
  }

  onReady(async function () {
    const summaryHost = document.getElementById("industry-summary");
    const barsHost = document.getElementById("industry-modality-bars");
    const railHost = document.getElementById("industry-rail");
    const detailHost = document.getElementById("industry-detail");
    if (!summaryHost || !barsHost || !railHost || !detailHost) return;

    const bundle = await loadProfiles();
    const profiles = Array.isArray(bundle?.profiles) ? bundle.profiles : [];
    if (!profiles.length) {
      detailHost.innerHTML = `
        <div class="empty">
          The industry surface could not load the latest bundle yet. Rebuild
          <code>proof/industry-profiles.json</code> or open the live API route.
        </div>
      `;
      return;
    }

    let activeIndex = 0;

    const sync = () => {
      renderSummary(summaryHost, bundle, profiles);
      renderModalityBars(barsHost, profiles);
      renderRail(railHost, profiles, activeIndex);
      renderDetail(detailHost, profiles[activeIndex], bundle);
    };

    railHost.addEventListener("click", (event) => {
      const button = event.target.closest("[data-index]");
      if (!button) return;
      activeIndex = Number(button.getAttribute("data-index") || 0);
      sync();
    });

    sync();
  });
})();
