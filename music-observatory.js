(function () {
  function escapeHtml(value) {
    if (window.AMAIResearch && typeof window.AMAIResearch.escapeHtml === "function") {
      return window.AMAIResearch.escapeHtml(value);
    }
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function compactNumber(value) {
    return new Intl.NumberFormat(undefined, { notation: "compact" }).format(Number(value || 0));
  }

  function driftTone(status) {
    return status === "elevated" ? "tone-alert" : status === "watch" ? "tone-watch" : "tone-steady";
  }

  function runTone(score) {
    if (score >= 0.7) return "tone-alert";
    if (score >= 0.38) return "tone-watch";
    return "tone-steady";
  }

  function mean(values) {
    const usable = values.filter((value) => Number.isFinite(Number(value))).map(Number);
    if (!usable.length) return 0;
    return usable.reduce((sum, value) => sum + value, 0) / usable.length;
  }

  function renderOverviewMetrics(overview) {
    return `
      <div class="music-metric-grid">
        <article class="music-metric-card">
          <small>manifest lane</small>
          <strong>${compactNumber(overview.manifest_count)}</strong>
          <span>declared audio references</span>
        </article>
        <article class="music-metric-card">
          <small>feature runs</small>
          <strong>${compactNumber(overview.feature_run_count)}</strong>
          <span>persisted extraction receipts</span>
        </article>
        <article class="music-metric-card">
          <small>segment index</small>
          <strong>${compactNumber(overview.total_segments)}</strong>
          <span>stable windows across the lane</span>
        </article>
        <article class="music-metric-card">
          <small>genre spread</small>
          <strong>${compactNumber(Object.keys(overview.genre_counts || {}).length)}</strong>
          <span>named sonic groupings</span>
        </article>
      </div>
    `;
  }

  function renderSignalBoard(segmentSlice) {
    const rows = Array.isArray(segmentSlice.rows) ? segmentSlice.rows : [];
    if (!rows.length) {
      return `<div class="music-empty-card">Signal summaries will appear once the warehouse has at least one derived run.</div>`;
    }
    const averageEntropy = mean(rows.map((row) => row.entropy_score));
    const averageTempo = mean(rows.map((row) => row.tempo_proxy_bpm));
    const averageSilence = mean(rows.map((row) => row.silence_ratio));
    const averageFlux = mean(rows.map((row) => row.spectral_flux));
    return `
      <div class="music-signal-grid">
        <article class="music-signal-card">
          <small>average entropy</small>
          <strong>${averageEntropy.toFixed(3)}</strong>
          <p>High entropy suggests the visible slice is still carrying texture rather than collapsing into one production posture.</p>
        </article>
        <article class="music-signal-card">
          <small>average tempo proxy</small>
          <strong>${averageTempo.toFixed(1)}</strong>
          <p>Tempo is derived from onset movement, which keeps rhythmic drift measurable without storing source audio in the repository.</p>
        </article>
        <article class="music-signal-card">
          <small>average silence ratio</small>
          <strong>${averageSilence.toFixed(3)}</strong>
          <p>Silence concentration helps spot padding, dead air, and editing posture before the model mistakes those choices for meaning.</p>
        </article>
        <article class="music-signal-card">
          <small>average spectral flux</small>
          <strong>${averageFlux.toFixed(3)}</strong>
          <p>Flux gives a quick read on motion and texture change, which is useful when one catalog starts sounding over-smoothed.</p>
        </article>
      </div>
    `;
  }

  function renderGenreConstellation(overview) {
    const entries = Object.entries(overview.genre_counts || {});
    if (!entries.length) {
      return `<div class="music-empty-card">Genre constellation opens once the manifest lane names more than one sonic grouping.</div>`;
    }
    const maxCount = Math.max(...entries.map(([, count]) => Number(count || 0)), 1);
    return `
      <div class="music-constellation">
        ${entries
          .slice(0, 16)
          .map(([genre, count], index) => {
            const weight = Math.max(0.32, Number(count || 0) / maxCount);
            const hue = 24 + (index % 6) * 46;
            return `
              <article class="music-genre-node" style="--weight:${weight}; --hue:${hue}">
                <strong>${escapeHtml(genre)}</strong>
                <span>${compactNumber(count)} declared references</span>
              </article>
            `;
          })
          .join("")}
      </div>
    `;
  }

  function renderDriftCards(drift) {
    const indicators = Array.isArray(drift.indicators) ? drift.indicators : [];
    if (!indicators.length) {
      return `<div class="music-empty-card">The drift lane is waiting for a persisted warehouse run.</div>`;
    }
    return `
      <div class="music-scroll-row">
        ${indicators
          .map(
            (item) => `
              <article class="music-story-card ${driftTone(item.status)}">
                <small>${escapeHtml(item.status)}</small>
                <h3>${escapeHtml(item.label)}</h3>
                <div class="music-meter"><span style="--width:${Math.round(Number(item.score || 0) * 100)}%"></span></div>
                <p>${escapeHtml(item.evidence)}</p>
                <p>${escapeHtml(item.why_it_matters)}</p>
                <strong>${escapeHtml(item.suggested_action)}</strong>
              </article>
            `,
          )
          .join("")}
      </div>
    `;
  }

  function renderChangeProof(changeProof) {
    const changes = Array.isArray(changeProof.changes) ? changeProof.changes : [];
    if (!changes.length) {
      return `<div class="music-empty-card">No change proof has been recorded yet.</div>`;
    }
    return `
      <div class="music-timeline">
        ${changes
          .map(
            (item, index) => `
              <article class="music-timeline-card">
                <span class="music-timeline-index">${String(index + 1).padStart(2, "0")}</span>
                <h3>${escapeHtml(item.title)}</h3>
                <p>${escapeHtml(item.summary)}</p>
                <small>${escapeHtml(item.entered_through)}</small>
                <ul>
                  ${(item.evidence || []).map((entry) => `<li>${escapeHtml(entry)}</li>`).join("")}
                </ul>
              </article>
            `,
          )
          .join("")}
      </div>
    `;
  }

  function renderSegmentSlice(segmentSlice) {
    const rows = Array.isArray(segmentSlice.rows) ? segmentSlice.rows : [];
    if (!rows.length) {
      return `<div class="music-empty-card">Segment rows will appear here once the feature warehouse is materialized.</div>`;
    }
    return `
      <div class="music-scroll-row">
        ${rows
          .slice(0, 12)
          .map(
            (row) => `
              <article class="music-story-card ${runTone(Number(row.silence_ratio || 0))}">
                <small>${escapeHtml(row.track_name || "segment")}</small>
                <h3>${escapeHtml(row.label || row.segment_id || "segment")}</h3>
                <p>${Number(row.start_ms || 0)}–${Number(row.end_ms || 0)} ms</p>
                <div class="music-chip-row">
                  <span>entropy ${Number(row.entropy_score || 0).toFixed(2)}</span>
                  <span>tempo ${Number(row.tempo_proxy_bpm || 0).toFixed(1)}</span>
                  <span>flux ${Number(row.spectral_flux || 0).toFixed(2)}</span>
                </div>
                <p>${escapeHtml(row.dominant_pitch_class || "pitch")} · silence ${Number(row.silence_ratio || 0).toFixed(2)}</p>
              </article>
            `,
          )
          .join("")}
      </div>
    `;
  }

  function renderWarehouseTopology(segmentSlice) {
    const rows = Array.isArray(segmentSlice.rows) ? segmentSlice.rows : [];
    if (!rows.length) {
      return `<div class="music-empty-card">The warehouse topology appears once segment windows have been materialized.</div>`;
    }
    return `
      <div class="music-topology-grid">
        ${rows
          .slice(0, 10)
          .map((row) => {
            const entropy = Math.max(8, Math.min(100, Math.round(Number(row.entropy_score || 0) * 100)));
            const repetition = Math.max(8, Math.min(100, Math.round(Number(row.repetition_ratio || 0) * 100)));
            const silence = Math.max(8, Math.min(100, Math.round(Number(row.silence_ratio || 0) * 100)));
            return `
              <article class="music-topology-card">
                <small>${escapeHtml(row.track_name || "track")}</small>
                <h3>${escapeHtml(row.label || row.segment_id || "segment")}</h3>
                <p>${Number(row.start_ms || 0)}–${Number(row.end_ms || 0)} ms · ${escapeHtml(row.dominant_pitch_class || "pitch")} center</p>
                <div class="music-topology-track">
                  <span>entropy</span>
                  <div class="music-topology-bar"><i class="music-topology-fill tone-jade" style="--fill:${entropy}%"></i></div>
                </div>
                <div class="music-topology-track">
                  <span>repetition</span>
                  <div class="music-topology-bar"><i class="music-topology-fill tone-rose" style="--fill:${repetition}%"></i></div>
                </div>
                <div class="music-topology-track">
                  <span>silence</span>
                  <div class="music-topology-bar"><i class="music-topology-fill tone-lilac" style="--fill:${silence}%"></i></div>
                </div>
              </article>
            `;
          })
          .join("")}
      </div>
    `;
  }

  function renderAlignment(alignmentPreview) {
    const windows = Array.isArray(alignmentPreview.windows) ? alignmentPreview.windows : [];
    if (!windows.length) {
      return `<div class="music-empty-card">Alignment windows will appear when transcript, audio, and frame references are present in the segment index.</div>`;
    }
    return `
      <div class="music-alignment-grid">
        ${windows
          .slice(0, 8)
          .map(
            (window) => `
              <article class="music-alignment-card">
                <small>${escapeHtml((window.modalities || []).join(" · "))}</small>
                <h3>${Number(window.span.start_ms)}–${Number(window.span.end_ms)} ms</h3>
                <p>${escapeHtml(window.note || "Aligned modal window.")}</p>
                <div class="music-chip-row">
                  <span>${Number(window.observation_count || 0)} observations</span>
                  <span>${Number(window.average_confidence || 0).toFixed(2)} confidence</span>
                </div>
              </article>
            `,
          )
          .join("")}
      </div>
    `;
  }

  function renderRecentRuns(overview) {
    const runs = Array.isArray(overview.recent_runs) ? overview.recent_runs : [];
    const manifests = Array.isArray(overview.recent_manifests) ? overview.recent_manifests : [];
    return `
      <div class="music-two-up">
        <section class="music-list-shell">
          <div class="music-section-label">Recent manifests</div>
          <div class="music-list">
            ${
              manifests.length
                ? manifests
                    .map(
                      (item) => `
                        <article class="music-list-row">
                          <strong>${escapeHtml(item.track_name)}</strong>
                          <span>${escapeHtml((item.genres || []).join(", ") || "unlabeled")}</span>
                          <small>${escapeHtml(item.source_kind)} · ${escapeHtml((item.languages || []).join(", ") || "language-open")}</small>
                        </article>
                      `,
                    )
                    .join("")
                : `<div class="music-empty-card">No manifest records yet.</div>`
            }
          </div>
        </section>
        <section class="music-list-shell">
          <div class="music-section-label">Recent runs</div>
          <div class="music-list">
            ${
              runs.length
                ? runs
                    .map(
                      (item) => `
                        <article class="music-list-row">
                          <strong>${escapeHtml(item.track_name)}</strong>
                          <span>${Number(item.segment_count || 0)} segments · ${Number(item.embedding_record_count || 0)} embeddings</span>
                          <small>entropy ${Number(item.benchmark.average_entropy_score || 0).toFixed(2)} · ${escapeHtml(item.partition_label || "default")}</small>
                        </article>
                      `,
                    )
                    .join("")
                : `<div class="music-empty-card">No feature runs yet.</div>`
            }
          </div>
        </section>
      </div>
    `;
  }

  function renderContinuationDeck() {
    const links = [
      {
        label: "written observatory",
        href: "proof/music-observatory.md",
        summary: "A readable field note for the current warehouse lane."
      },
      {
        label: "runtime proof",
        href: "proof/runtime-proof.md",
        summary: "The broader execution receipts and repeatability picture."
      },
      {
        label: "openapi surface",
        href: "openapi/openapi.json",
        summary: "The machine-readable contract behind the current routes."
      },
      {
        label: "typescript client",
        href: "sdk/typescript/src/generated-openapi.ts",
        summary: "Generated client types for teams wiring the lane into applications."
      },
      {
        label: "python client",
        href: "sdk/python/src/advanced_multimodal_ai_client/generated_openapi.py",
        summary: "Generated Python surface for warehouse and observatory calls."
      },
      {
        label: "readme",
        href: "README.md",
        summary: "Repository orientation, setup, and the broader system story."
      }
    ];
    return `
      <div class="music-link-grid">
        ${links
          .map(
            (item) => `
              <article class="music-link-card">
                <small>Continue learning</small>
                <h3>${escapeHtml(item.label)}</h3>
                <p>${escapeHtml(item.summary)}</p>
                <a class="music-cta" href="${escapeHtml(item.href)}">open</a>
              </article>
            `,
          )
          .join("")}
      </div>
    `;
  }

  function renderSnapshot(host, snapshot) {
    const overview = snapshot.overview;
    host.innerHTML = `
      <section class="music-hero-grid">
        <article class="music-hero-card">
          <div class="music-section-label">Music warehouse</div>
          <h2>Tracks stay outside git. Structure, drift, and change stay visible.</h2>
          <p>
            This lane keeps raw media at the source while retaining segment maps, derived features,
            embeddings, receipts, and comparison evidence inside the working repository.
          </p>
          <div class="music-finding-ribbon">
            ${(overview.top_findings || [])
              .slice(0, 3)
              .map((item) => `<span>${escapeHtml(item)}</span>`)
              .join("")}
          </div>
        </article>
        <article class="music-hero-card music-hero-card-alt">
          <div class="music-section-label">Live signal</div>
          ${renderOverviewMetrics(overview)}
        </article>
      </section>

      <section class="music-panel-block">
        <div class="music-section-head">
          <div>
            <small>Drift watch</small>
            <h2>The sound lane can now explain what is narrowing, smoothing, or disappearing.</h2>
          </div>
          <a class="music-cta" href="proof/music-observatory.md">open written report</a>
        </div>
        ${renderDriftCards(snapshot.drift)}
      </section>

      <section class="music-panel-block">
        <div class="music-section-head">
          <div>
            <small>Warehouse signal board</small>
            <h2>Measured audio summaries stay close to the page, so the field reads like evidence rather than mood.</h2>
          </div>
          <span class="music-inline-note">Derived from the persisted feature slice</span>
        </div>
        ${renderSignalBoard(snapshot.segment_slice)}
      </section>

      <section class="music-panel-block">
        <div class="music-section-head">
          <div>
            <small>Change proof</small>
            <h2>What changed, where it entered, and which receipts still support that reading.</h2>
          </div>
          <a class="music-cta" href="proof/benchmark-surfaces.md">open benchmark chain</a>
        </div>
        ${renderChangeProof(snapshot.change_proof)}
      </section>

      <section class="music-panel-block">
        <div class="music-section-head">
          <div>
            <small>Feature warehouse</small>
            <h2>Derived rows stay queryable, so the page can show measured segments instead of decorative sound.</h2>
          </div>
          <span class="music-inline-note">${compactNumber(snapshot.segment_slice.row_count || 0)} rows in the visible slice</span>
        </div>
        ${renderSegmentSlice(snapshot.segment_slice)}
      </section>

      <section class="music-panel-block">
        <div class="music-section-head">
          <div>
            <small>Genre constellation</small>
            <h2>The manifest lane shows where the declared catalog is thick, thin, or quietly repeating itself.</h2>
          </div>
          <span class="music-inline-note">${compactNumber(Object.keys(overview.genre_counts || {}).length)} named groupings</span>
        </div>
        ${renderGenreConstellation(overview)}
      </section>

      <section class="music-panel-block">
        <div class="music-section-head">
          <div>
            <small>Segment topology</small>
            <h2>Each visible window carries a measurable shape, so the warehouse can be scanned without opening the source media.</h2>
          </div>
          <span class="music-inline-note">entropy, repetition, and silence kept side by side</span>
        </div>
        ${renderWarehouseTopology(snapshot.segment_slice)}
      </section>

      <section class="music-panel-block">
        <div class="music-section-head">
          <div>
            <small>Cross-modal trace</small>
            <h2>One moment can be followed across transcript, audio, and frame windows.</h2>
          </div>
          <span class="music-inline-note">${compactNumber((snapshot.alignment_preview.windows || []).length)} windows</span>
        </div>
        ${renderAlignment(snapshot.alignment_preview)}
      </section>

      <section class="music-panel-block">
        <div class="music-section-head">
          <div>
            <small>Recent lane activity</small>
            <h2>Manifests and runs stay visible so the warehouse reads like working memory.</h2>
          </div>
        </div>
        ${renderRecentRuns(overview)}
      </section>

      <section class="music-panel-block">
        <div class="music-section-head">
          <div>
            <small>Continuation deck</small>
            <h2>Follow the lane into contracts, proof artifacts, generated clients, and the wider repository surface.</h2>
          </div>
        </div>
        ${renderContinuationDeck()}
      </section>
    `;
  }

  async function initMusicObservatory() {
    const host = document.querySelector("[data-music-observatory]");
    if (!host || !window.AMAIResearch || typeof window.AMAIResearch.loadMusicSnapshot !== "function") {
      return;
    }
    const snapshot = await window.AMAIResearch.loadMusicSnapshot();
    if (!snapshot) {
      host.innerHTML = `<div class="music-empty-card">The music warehouse snapshot is not available yet. Run the export path and reload the page.</div>`;
      return;
    }
    renderSnapshot(host, snapshot);
  }

  document.addEventListener("DOMContentLoaded", initMusicObservatory);
})();
