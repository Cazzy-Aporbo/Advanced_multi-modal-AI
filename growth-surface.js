(function initRepositoryGrowthSurface() {
  const roots = Array.from(document.querySelectorAll("[data-repository-growth]"));
  if (!roots.length) {
    return;
  }

  const sources = ["proof/repository-growth.json", "/v1/growth/snapshot"];

  const renderLoading = () => `
    <article class="runtime-pulse-card">
      <div class="section-label">Loading</div>
      <h3>Waiting for repository signals</h3>
      <p>The growth surface is loading GitHub and proof-backed repository metrics.</p>
    </article>
  `;

  roots.forEach((root) => {
    root.innerHTML = renderLoading();
  });

  fetchFirstJson(sources)
    .then((payload) => {
      roots.forEach((root) => {
        root.innerHTML = renderGrowth(payload);
      });
    })
    .catch(() => {
      roots.forEach((root) => {
        root.innerHTML = `
          <article class="runtime-pulse-card">
            <div class="section-label">Unavailable</div>
            <h3>The repository signal surface could not be loaded.</h3>
            <p>Open <code>proof/repository-growth.md</code> directly for the last exported snapshot.</p>
          </article>
        `;
      });
    });

  async function fetchFirstJson(paths) {
    for (const path of paths) {
      try {
        const response = await fetch(path, { cache: "no-store" });
        if (!response.ok) {
          continue;
        }
        return await response.json();
      } catch (error) {
        void error;
      }
    }
    throw new Error("repository growth payload unavailable");
  }

  function renderGrowth(payload) {
    const toplineCards = [
      {
        label: "Reach",
        title: `${compactNumber(payload.stars)} stars · ${compactNumber(payload.forks)} forks`,
        body: `${compactNumber(payload.watchers)} watchers, ${compactNumber(payload.subscribers)} subscribers, and ${compactNumber(payload.contributor_count)} contributors.`,
      },
      {
        label: "Traffic",
        title: `${compactNumber(payload.views_14d)} views · ${compactNumber(payload.clones_14d)} clones`,
        body: payload.traffic_window_available
          ? `${compactNumber(payload.unique_visitors_14d)} unique visitors and ${compactNumber(payload.unique_cloners_14d)} unique cloners across the current two-week window.`
          : "Traffic endpoints are not always available, so this lane falls back to the proof and repository counts that can still be checked locally.",
      },
      {
        label: "Proof",
        title: `${compactNumber(payload.route_count)} routes · ${compactNumber(payload.test_count)} tests`,
        body: `${compactNumber(payload.proof_export_count)} proof exports, ${compactNumber(payload.public_surface_count)} public surfaces, and ${compactNumber(payload.community_file_count)} contribution files are currently visible.`,
      },
      {
        label: "Posture",
        title: `${compactNumber(payload.open_issues)} open issues · ${compactNumber(payload.open_pull_requests)} open pull requests`,
        body: `${compactNumber(payload.release_count)} releases and ${compactNumber(payload.community_health_percent)} community-health points from the GitHub profile surface.`,
      },
    ];

    const notes = Array.isArray(payload.notes) && payload.notes.length
      ? `<ul class="list">${payload.notes.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
      : `<p class="map-note">The metrics lane is active and does not need extra qualifiers right now.</p>`;

    const topics = Array.isArray(payload.topics) && payload.topics.length
      ? payload.topics.map((item) => `<span class="connection-chip">${escapeHtml(item)}</span>`).join("")
      : `<span class="connection-chip">proof-backed repository</span>`;

    return `
      ${toplineCards.map(renderCard).join("")}
      <article class="runtime-pulse-card">
        <div class="section-label">Collection</div>
        <h3>${escapeHtml(payload.collection_mode)} · ${escapeHtml(payload.default_branch)}</h3>
        <p>This surface combines GitHub repository signals with the same route, test, and proof counts used elsewhere in the runtime.</p>
        <div class="connection-stack">${topics}</div>
      </article>
      <article class="runtime-pulse-card">
        <div class="section-label">Notes</div>
        <h3>What to keep an eye on</h3>
        ${notes}
        <div class="hero-actions" style="margin-top: 14px;">
          <a class="pill" href="proof/repository-growth.md">Open the growth report</a>
          <a class="pill" href="CONTRIBUTING.md">Read contributing</a>
        </div>
      </article>
    `;
  }

  function renderCard(card) {
    return `
      <article class="runtime-pulse-card">
        <div class="section-label">${escapeHtml(card.label)}</div>
        <h3>${escapeHtml(card.title)}</h3>
        <p>${escapeHtml(card.body)}</p>
      </article>
    `;
  }

  function compactNumber(value) {
    const numeric = Number(value || 0);
    if (numeric >= 1_000_000) {
      return `${(numeric / 1_000_000).toFixed(1)}M`;
    }
    if (numeric >= 1_000) {
      return `${(numeric / 1_000).toFixed(1)}K`;
    }
    return `${numeric}`;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }
})();
