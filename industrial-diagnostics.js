(function initIndustrialDiagnosticsSurface() {
  const summaryRoot = document.querySelector("[data-industrial-diagnostics-summary]");
  const scenariosRoot = document.querySelector("[data-industrial-diagnostics-scenarios]");
  const detailRoot = document.querySelector("[data-industrial-diagnostics-detail]");
  if (!summaryRoot || !scenariosRoot || !detailRoot) {
    return;
  }

  loadBundle()
    .then((bundle) => {
      renderSummary(summaryRoot, bundle);
      renderScenarios(scenariosRoot, bundle);
      renderDetail(detailRoot, bundle);
    })
    .catch(() => {
      detailRoot.innerHTML = `
        <p class="map-note">
          The industrial diagnostics bundle could not be loaded. Open
          <code>proof/industrial-diagnostics.md</code> directly for the latest export.
        </p>
      `;
    });

  async function loadBundle() {
    const sources = ["proof/industrial-diagnostics.json"];
    for (const source of sources) {
      const response = await fetch(source, { cache: "no-store" });
      if (response.ok) {
        return response.json();
      }
    }
    throw new Error("industrial diagnostics bundle unavailable");
  }

  function renderSummary(root, bundle) {
    const sample = bundle.sample_response;
    const cards = [
      {
        label: "Scenarios",
        title: `${bundle.scenarios.scenarios.length} declared lanes`,
        body: "Diesel, hydraulic, and electrical examples stay executable and typed.",
      },
      {
        label: "Diagnoses",
        title: `${sample.diagnoses.length} matched diagnoses`,
        body: "Rules stay deterministic and list the signals that tripped them.",
      },
      {
        label: "Compliance",
        title: `${sample.compliance_findings.length} findings`,
        body: "OSHA, ISO, and IEC checks travel with the same diagnostic pass.",
      },
      {
        label: "Proof",
        title: `${sample.proof_tree.length} proof nodes · ${sample.audit_trail.length} audit entries`,
        body: "The response includes both a readable tree and a sealed audit chain.",
      },
      {
        label: "Propagation",
        title: `${sample.fault_graph.nodes.length} nodes · ${sample.fault_graph.edges.length} edges`,
        body: "Signals, symptoms, compliance controls, and blocked actions remain tied together.",
      },
    ];
    root.innerHTML = cards
      .map(
        (card) => `
          <article class="runtime-pulse-card">
            <div class="section-label">${escapeHtml(card.label)}</div>
            <h3>${escapeHtml(card.title)}</h3>
            <p>${escapeHtml(card.body)}</p>
          </article>
        `,
      )
      .join("");
  }

  function renderScenarios(root, bundle) {
    root.innerHTML = bundle.scenarios.scenarios
      .map(
        (scenario) => `
          <article class="runtime-pulse-card">
            <div class="section-label">${escapeHtml(scenario.asset_kind)}</div>
            <h3>${escapeHtml(scenario.label)}</h3>
            <p>${escapeHtml(scenario.summary)}</p>
            <div class="connection-stack">
              ${scenario.expected_diagnosis_ids
                .map((item) => `<span class="connection-chip">${escapeHtml(item)}</span>`)
                .join("")}
            </div>
          </article>
        `,
      )
      .join("");
  }

  function renderDetail(root, bundle) {
    const sample = bundle.sample_response;
    const graphColumns = buildGraphColumns(sample.fault_graph);
    const diagnosisRows = sample.diagnoses
      .map(
        (item) => `
          <li>
            <strong>${escapeHtml(item.title)}</strong>
            <span> · ${escapeHtml(item.severity)} · confidence ${escapeHtml(item.confidence)}</span>
          </li>
        `,
      )
      .join("");
    const findingRows = sample.compliance_findings
      .map(
        (item) => `
          <li>
            <strong>${escapeHtml(item.standard)} ${escapeHtml(item.clause)}</strong>
            <span> · ${escapeHtml(item.status)} · ${escapeHtml(item.requirement)}</span>
          </li>
        `,
      )
      .join("");
    const invariantRows = sample.invariants
      .map(
        (item) => `
          <li>
            <strong>${escapeHtml(item.invariant_id)}</strong>
            <span> · holds=${escapeHtml(item.holds)}</span>
          </li>
        `,
      )
      .join("");
    root.innerHTML = `
      <div class="section-label">Sample diagnostic verdict</div>
      <h2>${escapeHtml(sample.machine_family)} · ${escapeHtml(sample.verdict)}</h2>
      <p>
        The sample pass keeps technician language, threshold matches, compliance findings,
        and formal invariants together. This is the structure the repo is trying to protect.
      </p>
      <div class="section-label" style="margin-top:1.5rem;">Fault propagation</div>
      <p class="map-note">
        Primary path: ${sample.fault_graph.primary_path.map(formatNodeId).map(escapeHtml).join(" → ")}
      </p>
      <div class="detail-grid">
        ${graphColumns
          .map(
            (column) => `
              <article class="list-shell">
                <strong>${escapeHtml(column.label)}</strong>
                <ul>
                  ${column.items
                    .map(
                      (item) => `
                        <li>
                          <strong>${escapeHtml(item.label)}</strong>
                          <span> · ${escapeHtml(item.detail || item.state || item.severity)}</span>
                        </li>
                      `,
                    )
                    .join("")}
                </ul>
              </article>
            `,
          )
          .join("")}
      </div>
      <div class="detail-grid">
        <article class="list-shell">
          <strong>Diagnoses</strong>
          <ul>${diagnosisRows}</ul>
        </article>
        <article class="list-shell">
          <strong>Compliance findings</strong>
          <ul>${findingRows}</ul>
        </article>
        <article class="list-shell">
          <strong>Formal invariants</strong>
          <ul>${invariantRows}</ul>
        </article>
      </div>
    `;
  }

  function buildGraphColumns(graph) {
    const groups = [
      ["Signals", ["sensor"]],
      ["Symptoms", ["observation"]],
      ["Diagnoses", ["diagnosis"]],
      ["Controls", ["compliance", "invariant"]],
      ["Actions", ["action", "verdict"]],
    ];
    return groups.map(([label, kinds]) => ({
      label,
      items: graph.nodes.filter((node) => kinds.includes(node.kind)),
    }));
  }

  function formatNodeId(nodeId) {
    return String(nodeId)
      .replace(/^[^:]+:/, "")
      .replaceAll("_", " ");
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
