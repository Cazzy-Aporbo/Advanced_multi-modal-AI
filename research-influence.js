(function () {
  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function compact(value) {
    return new Intl.NumberFormat(undefined, { notation: "compact" }).format(Number(value || 0));
  }

  function percent(value) {
    return `${Math.round(Number(value || 0) * 100)}%`;
  }

  function scoreWidth(value) {
    const numeric = Number(value || 0);
    return `${Math.max(4, Math.min(100, numeric))}%`;
  }

  async function loadPayload() {
    const response = await fetch("proof/research-influence.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Unable to load research influence proof: ${response.status}`);
    }
    return response.json();
  }

  function renderMetrics(bundle, samples) {
    const metrics = [
      ["sources", bundle.source_count, "papers close to the work"],
      ["routes", bundle.route_count, "API paths in the proof slice"],
      ["tests", bundle.test_count, "checks counted by attestation"],
      [
        "risk score",
        percent(samples.epistemic_risk.score),
        `${samples.epistemic_risk.band} epistemic band`,
      ],
    ];
    document.getElementById("metric-grid").innerHTML = metrics
      .map(
        ([label, value, note]) => `
          <article class="metric-card">
            <span class="kicker">${escapeHtml(label)}</span>
            <strong>${escapeHtml(typeof value === "number" ? compact(value) : value)}</strong>
            <p>${escapeHtml(note)}</p>
          </article>
        `,
      )
      .join("");
  }

  function renderSources(sources) {
    document.getElementById("source-grid").innerHTML = sources
      .map(
        (source) => `
          <article class="source-card">
            <small>${escapeHtml(source.field)} · ${escapeHtml(source.year)}</small>
            <h3>${escapeHtml(source.title)}</h3>
            <p>${escapeHtml(source.repository_translation)}</p>
            <div class="chip-row">
              ${(source.mechanisms || []).map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join("")}
            </div>
            <button class="mini-button" type="button" data-source-id="${escapeHtml(source.source_id)}">Which checks moved?</button>
          </article>
        `,
      )
      .join("");
  }

  function renderMechanisms(mechanisms) {
    document.getElementById("mechanism-rail").innerHTML = mechanisms
      .map(
        (item) => `
          <article class="mechanism-card" data-source-ids="${escapeHtml((item.source_ids || []).join(" "))}">
            <small>${escapeHtml(item.implementation_status)}</small>
            <h3>${escapeHtml(item.label)}</h3>
            <div class="meter"><span style="--width:${scoreWidth(item.score)}"></span></div>
            <p>${escapeHtml(item.why_it_matters)}</p>
            <p>${escapeHtml(item.next_test)}</p>
            <div class="chip-row">
              ${(item.runtime_routes || []).slice(0, 4).map((route) => `<span class="chip">${escapeHtml(route)}</span>`).join("")}
            </div>
          </article>
        `,
      )
      .join("");
  }

  function buildQuestions(bundle, samples) {
    const firstProposal = (samples.harness_improvement.proposals || [])[0] || {};
    const firstGap = (bundle.feature_matrix || [])
      .slice()
      .sort((left, right) => Number(left.representation_score || 0) - Number(right.representation_score || 0))[0];
    const freshness = (samples.epistemic_risk.indicators || []).find(
      (item) => item.indicator_id === "freshness",
    );
    return [
      {
        label: "what",
        title: "What changed?",
        copy:
          firstProposal.expected_behavior ||
          "A repeated trace can become a proposal only after it is visible in proof.",
      },
      {
        label: "where",
        title: "Where does it run?",
        copy: `${bundle.route_count} API routes are present. The newest checks sit under /v1/research and return typed results, not page-only copy.`,
      },
      {
        label: "who",
        title: "Who must look again?",
        copy: `The trust route names ${samples.trust_calibration.missing_controls.length || "no"} thin controls in this slice. Human control and oversight stay visible when the harm level rises.`,
      },
      {
        label: "when",
        title: "When does evidence grow old?",
        copy:
          freshness?.evidence ||
          "Freshness is measured as part of the epistemic-risk route, beside source diversity and review state.",
      },
      {
        label: "why",
        title: "Why pause?",
        copy: `Deliberation returned ${samples.deliberation_assessment.recommendation}. A route can wait because disagreement is data, not a failure of polish.`,
      },
      {
        label: "more",
        title: "What needs another pass?",
        copy: firstGap
          ? `${firstGap.label}: ${firstGap.representation_gap}`
          : "The next pass should add proof where the runtime has fewer fixtures than questions.",
      },
    ];
  }

  function renderQuestionConsole(bundle, samples) {
    const questions = buildQuestions(bundle, samples);
    const label = document.getElementById("question-label");
    const title = document.getElementById("question-title");
    const copy = document.getElementById("question-copy");
    const buttons = document.getElementById("question-buttons");
    if (!label || !title || !copy || !buttons) return;

    let active = 0;
    function show(index) {
      active = index;
      const item = questions[index];
      label.textContent = item.label;
      title.textContent = item.title;
      copy.textContent = item.copy;
      buttons.querySelectorAll("button").forEach((button, buttonIndex) => {
        button.setAttribute("aria-pressed", String(buttonIndex === index));
      });
    }

    buttons.innerHTML = questions
      .map(
        (item, index) =>
          `<button type="button" data-question-index="${index}" aria-pressed="false">${escapeHtml(item.label)}</button>`,
      )
      .join("");
    buttons.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-question-index]");
      if (!button) return;
      show(Number(button.dataset.questionIndex));
    });
    show(0);
    window.setInterval(() => show((active + 1) % questions.length), 6200);
  }

  function wireSourceFilters() {
    document.querySelectorAll("[data-source-id]").forEach((button) => {
      button.addEventListener("click", () => {
        const sourceId = button.getAttribute("data-source-id") || "";
        document.querySelectorAll(".mechanism-card").forEach((card) => {
          const sourceIds = card.getAttribute("data-source-ids") || "";
          card.classList.toggle("is-highlighted", sourceIds.split(" ").includes(sourceId));
        });
        document.getElementById("mechanisms")?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  }

  function renderFeatureMatrix(featureMatrix) {
    document.getElementById("feature-matrix").innerHTML = featureMatrix
      .map(
        (item) => `
          <article class="matrix-row">
            <div>
              <span class="kicker">${escapeHtml(item.feature_id)}</span>
              <h3>${escapeHtml(item.label)}</h3>
            </div>
            <div>
              <div class="path-line"></div>
              <p>${escapeHtml(item.representation_gap)}</p>
            </div>
            <div>
              <p>${escapeHtml(item.next_six_month_problem)}</p>
              <div class="meter"><span style="--width:${scoreWidth(item.representation_score)}"></span></div>
            </div>
          </article>
        `,
      )
      .join("");
  }

  function renderSamples(samples) {
    const proposal = samples.harness_improvement.proposals[0] || {};
    const trustMissing = samples.trust_calibration.missing_controls || [];
    const epistemicIndicators = samples.epistemic_risk.indicators || [];
    const cards = [
      {
        label: "harness",
        title: `${samples.harness_improvement.promoted_proposal_count} proposal promoted`,
        copy: proposal.expected_behavior || "No repeated weakness was promoted.",
        lines: (proposal.acceptance_gate || []).slice(0, 3),
      },
      {
        label: "deliberation",
        title: samples.deliberation_assessment.recommendation,
        copy: `Disagreement score ${samples.deliberation_assessment.disagreement_score}.`,
        lines: samples.deliberation_assessment.next_questions || [],
      },
      {
        label: "trust",
        title: `${samples.trust_calibration.band} band`,
        copy: `Review required: ${samples.trust_calibration.review_required}.`,
        lines: trustMissing.length ? trustMissing : ["No missing controls in this sample."],
      },
      {
        label: "epistemic",
        title: `${samples.epistemic_risk.band} band`,
        copy: `Score ${samples.epistemic_risk.score}.`,
        lines: epistemicIndicators.map((item) => `${item.label}: ${item.score}`),
      },
    ];
    document.getElementById("sample-grid").innerHTML = cards
      .map(
        (card) => `
          <article class="sample-card">
            <small>${escapeHtml(card.label)}</small>
            <h3>${escapeHtml(card.title)}</h3>
            <p>${escapeHtml(card.copy)}</p>
            <ul>
              ${card.lines.slice(0, 4).map((line) => `<li>${escapeHtml(line)}</li>`).join("")}
            </ul>
          </article>
        `,
      )
      .join("");
  }

  function renderRoadmap(roadmap) {
    document.getElementById("roadmap-grid").innerHTML = roadmap
      .map(
        (item) => `
          <article class="timeline-card matrix-row">
            <div>
              <span class="kicker">${escapeHtml(item.horizon)}</span>
              <h3>${escapeHtml(item.label)}</h3>
            </div>
            <p>${escapeHtml(item.problem)}</p>
            <div>
              <p>${escapeHtml(item.engineering_response)}</p>
              <span class="chip">${escapeHtml(item.proof_to_add)}</span>
            </div>
          </article>
        `,
      )
      .join("");
  }

  async function init() {
    try {
      const payload = await loadPayload();
      const bundle = payload.bundle;
      const samples = payload.sample_outputs;
      renderMetrics(bundle, samples);
      renderQuestionConsole(bundle, samples);
      renderSources(bundle.sources || []);
      renderMechanisms(bundle.mechanisms || []);
      renderFeatureMatrix(bundle.feature_matrix || []);
      renderSamples(samples);
      renderRoadmap(bundle.roadmap || []);
      wireSourceFilters();
    } catch (error) {
      document.getElementById("metric-grid").innerHTML = `
        <article class="metric-card">
          <span class="kicker">proof unavailable</span>
          <strong>Hold</strong>
          <p>${escapeHtml(error.message)}</p>
        </article>
      `;
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
