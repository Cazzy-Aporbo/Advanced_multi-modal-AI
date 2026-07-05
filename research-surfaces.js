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

  async function loadRepositoryFileMap() {
    const candidates = ["proof/repository-file-map.json", "/v1/repository/file-map"];
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

  async function loadExecutionJournal() {
    const candidates = ["proof/execution-journal.json", "/v1/execution/journal"];
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

  async function loadBenchmarkSurface() {
    const candidates = ["proof/benchmark-surfaces.json", "/v1/benchmarks/reference"];
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

  async function loadCymaticSurface() {
    const candidates = ["proof/cymatic-surface.json", "/v1/research/cymatic-surface"];
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

  async function loadMusicOverview() {
    const candidates = ["proof/music-observatory.json", "/v1/music/overview"];
    for (const url of candidates) {
      try {
        const response = await fetch(url, { cache: "no-store" });
        if (response.ok) {
          const payload = await response.json();
          return payload.overview || payload;
        }
      } catch (_error) {
        // keep trying the next surface
      }
    }
    return null;
  }

  async function loadMusicSnapshot() {
    const candidates = ["proof/music-observatory.json", "/v1/music/snapshot"];
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

  async function loadOperatorSurfaceBundle() {
    const candidates = ["proof/operator-surfaces.json", "/v1/operators/surfaces"];
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

  function compactNumber(value) {
    return new Intl.NumberFormat(undefined, { notation: "compact" }).format(value);
  }

  function compactDuration(value) {
    const milliseconds = Number(value || 0);
    if (milliseconds < 1000) {
      return `${Math.round(milliseconds)} ms`;
    }
    return `${(milliseconds / 1000).toFixed(1)} s`;
  }

  function signalRailHref(laneId) {
    const mapping = {
      frontend_atlas: "index.html",
      runtime_backend: "advanced-technical-portfolio.html",
      benchmark_lane: "benchmark-observatory.html",
      music_warehouse: "music-observatory.html",
      compiled_core: "technical-portfolio.html",
      generated_clients: "technical-portfolio.html",
      evidence_exports: "field-notes.html",
      execution_memory: "field-notes.html",
      model_study: "model-observatory.html",
      operator_surface: "model-observatory.html#operator-surface",
    };
    return mapping[laneId] || "technical-portfolio.html";
  }

  function renderSignalRail(host, pulse, benchmark, journal) {
    const lanes = Array.isArray(pulse?.lanes) ? pulse.lanes : [];
    const stageSteps = Array.isArray(benchmark?.stages) ? benchmark.stages.slice(0, 5) : [];
    const recentRuns = Array.isArray(journal?.recent_runs) ? journal.recent_runs.slice(0, 4) : [];
    const totalWarnings = lanes.reduce((sum, lane) => sum + Number(lane.warning_count || 0), 0);
    const totalActive = lanes.reduce((sum, lane) => sum + Number(lane.active_count || 0), 0);

    const laneMarkup = lanes
      .map((lane, index) => {
        const emphasis = escapeHtml(lane.emphasis || "general");
        const liveScore = Math.max(0, Math.min(100, Number(lane.live_score || 0)));
        const warnings = Number(lane.warning_count || 0);
        return `
          <a class="signal-rail-card tone-${emphasis}" href="${escapeHtml(signalRailHref(lane.lane_id))}">
            <span class="signal-rail-order">${String(index + 1).padStart(2, "0")}</span>
            <strong>${escapeHtml(lane.label)}</strong>
            <p>${escapeHtml(lane.summary)}</p>
            <div class="signal-rail-meter">
              <span class="signal-rail-meter-fill" style="--width:${liveScore}%"></span>
            </div>
            <div class="signal-rail-meta">
              <span>${compactNumber(Number(lane.active_count || 0))} active traces</span>
              <span>${warnings} watchpoint${warnings === 1 ? "" : "s"}</span>
            </div>
          </a>
        `;
      })
      .join("");

    const stageMarkup = stageSteps.length
      ? stageSteps
          .map(
            (stage) => `
              <a class="signal-stage-pill" href="benchmark-observatory.html">
                <strong>${escapeHtml(stage.label)}</strong>
                <span>${compactDuration(stage.duration_ms)}</span>
              </a>
            `,
          )
          .join('<span class="signal-stage-arrow" aria-hidden="true">→</span>')
      : '<span class="signal-stage-pill empty">Benchmark stages appear here after the export runs.</span>';

    const runMarkup = recentRuns.length
      ? recentRuns
          .map(
            (run) => `
              <article class="signal-run-note">
                <strong>${escapeHtml((run.lane || "run").replaceAll("_", " "))}</strong>
                <p>${escapeHtml(run.command || "No command recorded.")}</p>
                <span>${escapeHtml(run.status || "unknown")} · ${compactDuration(run.duration_ms)}</span>
              </article>
            `,
          )
          .join("")
      : '<article class="signal-run-note empty"><strong>No recent proof runs yet.</strong><p>Run the acceptance spine to populate the latest execution memory.</p></article>';

    host.innerHTML = `
      <div class="signal-rail-shell">
        <div class="signal-rail-head">
          <div>
            <small>Live repository motion</small>
            <h2>Frontend, runtime, compiled math, and proof can be read as one field.</h2>
          </div>
          <div class="signal-rail-totals">
            <span>${compactNumber(Number(pulse?.route_count || 0))} routes</span>
            <span>${compactNumber(Number(pulse?.test_count || 0))} tests</span>
            <span>${compactNumber(Number(pulse?.model_count || 0))} models</span>
            <span>${compactNumber(totalActive)} active traces</span>
            <span>${compactNumber(totalWarnings)} watchpoints</span>
          </div>
        </div>

        <div class="signal-stage-chain">${stageMarkup}</div>

        <div class="signal-rail-strip" role="list">
          ${laneMarkup}
        </div>

        <div class="signal-run-grid">
          ${runMarkup}
        </div>
      </div>
    `;
  }

  async function hydrateSignalRail(host) {
    host.setAttribute("data-signal-state", "loading");
    const [pulse, benchmark, journal] = await Promise.all([
      loadRepositoryPulse(),
      loadBenchmarkSurface(),
      loadExecutionJournal(),
    ]);
    if (!pulse) {
      host.innerHTML = `
        <div class="signal-rail-shell signal-rail-fallback">
          <small>Repository motion unavailable</small>
          <p>The public surface could not load the latest proof exports yet.</p>
        </div>
      `;
      return;
    }
    renderSignalRail(host, pulse, benchmark, journal);
    host.setAttribute("data-signal-state", "ready");
  }

  window.AMAIResearch = {
    escapeHtml,
    listMarkup,
    loadResearchSurfaceBundle,
    loadRepositoryPulse,
    loadRepositoryFileMap,
    loadExecutionJournal,
    loadBenchmarkSurface,
    loadCymaticSurface,
    loadMusicOverview,
    loadMusicSnapshot,
    loadOperatorSurfaceBundle,
    hydrateSignalRail,
  };

  onReady(() => {
    document.querySelectorAll("[data-signal-rail]").forEach((host) => {
      hydrateSignalRail(host);
    });
  });
})();
