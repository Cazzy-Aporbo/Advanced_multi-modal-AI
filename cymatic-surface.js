(function () {
  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

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

  function bandMarkup(band) {
    return `
      <div class="cymatic-meter-label">
        <span>${escapeHtml(band.label)}</span>
        <small>${Math.round(band.intensity * 100)} / 100</small>
      </div>
      <div class="cymatic-meter-track">
        <div class="cymatic-meter-fill" style="--width:${Math.round(clamp(band.intensity, 0.08, 1) * 100)}%"></div>
      </div>
    `;
  }

  function toneClass(index) {
    return `stage-tone-${(index % 6) + 1}`;
  }

  function buildSurfaceMarkup(surface, compact) {
    const stageCards = surface.stages
      .map(
        (stage, index) => `
          <button class="cymatic-stage-card ${toneClass(index)}${index === 0 ? " active" : ""}" data-stage-index="${index}" type="button">
            <strong>${String(index + 1).padStart(2, "0")} · stage</strong>
            <h4>${escapeHtml(stage.label)}</h4>
            <p>${escapeHtml(stage.human_read)}</p>
            <div class="cymatic-stage-bars">
              <div class="cymatic-stage-bar harmony"><span style="--width:${Math.round(stage.harmony_score * 100)}%"></span></div>
              <div class="cymatic-stage-bar friction"><span style="--width:${Math.round(stage.friction_score * 100)}%"></span></div>
            </div>
          </button>
        `,
      )
      .join("");

    const insightCards = surface.narratives
      .map(
        (item, index) => `
          <article class="cymatic-insight-card ${toneClass(index + 1)}">
            <small>${escapeHtml(item.audience)}</small>
            <h3>${escapeHtml(item.title)}</h3>
            <p>${escapeHtml(item.summary)}</p>
            <p>${escapeHtml(item.consequence)}</p>
          </article>
        `,
      )
      .join("");

    const continuationLinks = surface.continuation_links
      .map((item) => {
        const label = item
          .replace(".html", "")
          .replace(".md", "")
          .replace("proof/", "")
          .replaceAll("-", " ");
        return `<a class="cymatic-pill-link" href="${escapeHtml(item)}">${escapeHtml(label)}</a>`;
      })
      .join("");

    return `
      <div class="cymatic-shell" data-cymatic-compact="${compact ? "true" : "false"}">
        <div class="cymatic-topline">
          <section class="cymatic-canvas-shell">
            <canvas class="cymatic-canvas" aria-hidden="true"></canvas>
            <div class="cymatic-orbit-grid" aria-hidden="true"></div>
            <div class="cymatic-orbit orbit-a" aria-hidden="true"></div>
            <div class="cymatic-orbit orbit-b" aria-hidden="true"></div>
            <div class="cymatic-orbit orbit-c" aria-hidden="true"></div>
            <div class="cymatic-overlay">
              <div class="cymatic-label">Cymatic surface</div>
              <h2 class="cymatic-title">Sound, proof, and drift can be read in one motion.</h2>
              <p class="cymatic-copy">
                This surface listens to local audio in the browser, but its stage map and repair language
                come from the repository’s exported benchmark, pulse, and research lanes.
              </p>
              <div class="cymatic-dropzone" data-cymatic-dropzone>
                <div class="cymatic-dropzone-header">
                  <strong>Bring in a clip, song, or voice note</strong>
                  <span class="cymatic-chip" data-cymatic-audio-state>ambient mode</span>
                </div>
                <p>Drop one audio file here or open it directly. The canvas will react to live energy while the stage rail keeps the repository context nearby.</p>
                <div class="cymatic-upload-row">
                  <label class="cymatic-file-button">
                    <input class="cymatic-file-input" type="file" accept="audio/*">
                    <span>choose audio</span>
                  </label>
                  <button class="cymatic-action secondary" type="button" data-cymatic-heal>heal the field</button>
                  <button class="cymatic-action" type="button" data-cymatic-inject>inject friction</button>
                </div>
                <audio class="cymatic-audio" controls preload="metadata"></audio>
              </div>
            </div>
          </section>

          <aside class="cymatic-panel">
            <div class="cymatic-label">Current posture</div>
            <h3>How steady the repository feels right now</h3>
            <p class="cymatic-subcopy">
              The health side names what is holding. The pressure side names what still deserves a second look.
            </p>
            <div class="cymatic-meter-stack">
              ${surface.harmonic_bands.map((band) => bandMarkup(band)).join("")}
            </div>
            <div class="cymatic-slider-grid">
              <label class="cymatic-slider-wrap">
                <header>
                  <span>friction pressure</span>
                  <small data-cymatic-friction-value>${Math.round(surface.tension_index * 100)}</small>
                </header>
                <input class="cymatic-slider" data-cymatic-friction type="range" min="0" max="100" value="${Math.round(surface.tension_index * 100)}">
              </label>
              <label class="cymatic-slider-wrap">
                <header>
                  <span>repair sensitivity</span>
                  <small data-cymatic-sensitivity-value>72</small>
                </header>
                <input class="cymatic-slider" data-cymatic-sensitivity type="range" min="0" max="100" value="72">
              </label>
            </div>
            <div class="cymatic-chip-row" style="margin-top:16px;">
              <span class="cymatic-chip">${surface.route_count} routes</span>
              <span class="cymatic-chip">${surface.test_count} tests</span>
              <span class="cymatic-chip">${surface.connector_kind_count} connector kinds</span>
              <span class="cymatic-chip">${surface.total_runs} recorded runs</span>
            </div>
            <div class="cymatic-warehouse-pulse">
              <div class="cymatic-warehouse-head">
                <strong>Music warehouse</strong>
                <small>manifest, segments, and derived sound memory</small>
              </div>
              <div class="cymatic-chip-row">
                <span class="cymatic-chip">${surface.music_manifest_count} manifests</span>
                <span class="cymatic-chip">${surface.music_feature_run_count} runs</span>
                <span class="cymatic-chip">${surface.music_total_segments} segments</span>
              </div>
              <div class="cymatic-chip-row">
                ${(surface.music_top_genres || []).slice(0, 4).map((item) => `<span class="cymatic-chip">${escapeHtml(item)}</span>`).join("")}
              </div>
              <div class="cymatic-action-row" style="margin-top:14px;">
                <a class="cymatic-pill-link" href="music-observatory.html">open music observatory</a>
              </div>
            </div>
          </aside>
        </div>

        <div class="cymatic-bottomline">
          <section class="cymatic-panel">
            <div class="cymatic-label">Pipeline rail</div>
            <h3>Where a weak signal enters and how it travels</h3>
            <p class="cymatic-subcopy">Select a stage. The detail panel will translate the same stage for everyday readers, operators, and research work.</p>
            <div class="cymatic-pipeline">
              ${stageCards}
            </div>
          </section>

          <section class="cymatic-detail-panel">
            <div class="cymatic-label">Selected stage</div>
            <div data-cymatic-stage-detail></div>
            <div class="cymatic-detail-grid">
              <div class="cymatic-detail-note">
                <strong>Why it matters to people</strong>
                <div data-cymatic-human-copy></div>
              </div>
              <div class="cymatic-detail-note">
                <strong>What to improve next</strong>
                <div data-cymatic-improvement-copy></div>
              </div>
            </div>
          </section>
        </div>

        <div class="cymatic-insight-grid">
          ${insightCards}
        </div>

        <div class="cymatic-continuation">
          <div class="cymatic-label">Continue from here</div>
          <div class="cymatic-chip-row">${continuationLinks}</div>
        </div>
      </div>
    `;
  }

  function renderStageDetail(host, stage, pressure, sensitivity, stageIndex) {
    const detail = host.querySelector("[data-cymatic-stage-detail]");
    const humanCopy = host.querySelector("[data-cymatic-human-copy]");
    const improvementCopy = host.querySelector("[data-cymatic-improvement-copy]");
    if (!detail || !humanCopy || !improvementCopy) {
      return;
    }

    const effectiveHarmony = clamp(stage.harmony_score - pressure * 0.22 + sensitivity * 0.08, 0, 1);
    const effectiveFriction = clamp(stage.friction_score + pressure * 0.34 - sensitivity * 0.18, 0, 1);
    const stressLabel =
      effectiveFriction > 0.72 ? "elevated strain" :
      effectiveFriction > 0.46 ? "watch closely" :
      "holding cleanly";

    detail.innerHTML = `
      <h3 class="cymatic-stage-heading ${toneClass(stageIndex)}">${escapeHtml(stage.label)}</h3>
      <p class="cymatic-detail-copy">${escapeHtml(stage.research_read)}</p>
      <div class="cymatic-chip-row" style="margin-top:14px;">
        <span class="cymatic-chip">harmony ${Math.round(effectiveHarmony * 100)}</span>
        <span class="cymatic-chip">friction ${Math.round(effectiveFriction * 100)}</span>
        <span class="cymatic-chip">${escapeHtml(stressLabel)}</span>
      </div>
      <div class="cymatic-metric-row" style="margin-top:16px;">
        ${stage.metrics
          .map(
            (metric) => `
              <span class="cymatic-chip" title="${escapeHtml(metric.detail || "")}">
                ${escapeHtml(metric.label)} ${escapeHtml(String(metric.value))}${metric.unit ? ` ${escapeHtml(metric.unit)}` : ""}
              </span>
            `,
          )
          .join("")}
      </div>
      <div class="cymatic-chip-row" style="margin-top:14px;">
        ${stage.trace_paths.map((path) => `<span class="cymatic-chip">${escapeHtml(path)}</span>`).join("")}
      </div>
      <div class="cymatic-chip-row" style="margin-top:10px;">
        ${stage.files.map((file) => `<span class="cymatic-chip">${escapeHtml(file.split("/").slice(-1)[0])}</span>`).join("")}
      </div>
    `;

    humanCopy.textContent = stage.human_read + (pressure > 0.45
      ? " Under heavier friction, this is usually where the story starts to feel narrower than the evidence deserves."
      : " When this stage stays calm, later outputs are easier to question without panic.");
    improvementCopy.textContent = stage.business_read + " " + stage.improvement_path;
  }

  function setStage(host, state, index) {
    state.stageIndex = clamp(index, 0, state.surface.stages.length - 1);
    host.querySelectorAll("[data-stage-index]").forEach((node) => {
      node.classList.toggle("active", Number(node.dataset.stageIndex) === state.stageIndex);
    });
    renderStageDetail(
      host,
      state.surface.stages[state.stageIndex],
      state.friction / 100,
      state.sensitivity / 100,
      state.stageIndex,
    );
  }

  function drawCanvas(state) {
    const { canvas, context, analyser, dataArray, surface } = state;
    if (!canvas || !context) return;
    const width = canvas.width;
    const height = canvas.height;
    const time = performance.now() * 0.0014;
    const friction = state.friction / 100;
    const sensitivity = state.sensitivity / 100;

    context.clearRect(0, 0, width, height);

    const background = context.createLinearGradient(0, 0, width, height);
    background.addColorStop(0, "rgba(18, 12, 14, 0.82)");
    background.addColorStop(0.48, friction > 0.52 ? "rgba(62, 18, 38, 0.78)" : "rgba(16, 25, 36, 0.68)");
    background.addColorStop(1, "rgba(8, 10, 16, 0.9)");
    context.fillStyle = background;
    context.fillRect(0, 0, width, height);

    let samples;
    if (analyser && dataArray) {
      analyser.getByteFrequencyData(dataArray);
      samples = Array.from(dataArray, (value) => value / 255);
    } else {
      samples = surface.harmonic_bands.map((band, index) => {
        const wobble = Math.sin(time * (1.2 + index * 0.32)) * 0.08;
        return clamp(band.intensity + wobble - friction * band.drift * 0.22, 0.04, 1);
      });
    }

    const midY = height * 0.55;
    const bandColors = [
      "rgba(223, 156, 95, 0.92)",
      "rgba(215, 169, 184, 0.88)",
      "rgba(143, 201, 190, 0.9)",
      "rgba(169, 196, 255, 0.88)",
    ];

    for (let layer = 0; layer < 4; layer += 1) {
      context.beginPath();
      context.lineWidth = 2 + layer * 0.8;
      context.strokeStyle = bandColors[layer % bandColors.length];
      const amplitude = (38 + layer * 22) * (1 + friction * 0.72);
      for (let x = 0; x <= width; x += 8) {
        const sample = samples[(Math.floor(x / 8) + layer) % samples.length];
        const frequency = 0.008 + layer * 0.0022 + friction * 0.0018;
        const wave = Math.sin(x * frequency + time * (1.8 + layer * 0.3));
        const tremor = Math.cos(x * 0.003 + time * (1.2 + layer * 0.4)) * friction * 0.85;
        const y = midY + wave * amplitude * (sample + 0.28) + tremor * 22 - layer * 18;
        if (x === 0) {
          context.moveTo(x, y);
        } else {
          context.lineTo(x, y);
        }
      }
      context.stroke();
    }

    context.globalCompositeOperation = "lighter";
    samples.slice(0, 48).forEach((sample, index) => {
      const radius = 2 + sample * 10 + friction * 6;
      const x = ((index + 1) / 49) * width;
      const y = height * (0.22 + (index % 6) * 0.1) + Math.sin(time * 2 + index) * 10;
      const gradient = context.createRadialGradient(x, y, 0, x, y, radius * 3.4);
      gradient.addColorStop(0, "rgba(246, 239, 232, 0.88)");
      gradient.addColorStop(0.48, friction > 0.5 ? "rgba(223, 120, 138, 0.54)" : "rgba(143, 201, 190, 0.4)");
      gradient.addColorStop(1, "rgba(0, 0, 0, 0)");
      context.fillStyle = gradient;
      context.beginPath();
      context.arc(x, y, radius * (0.7 + sensitivity * 0.3), 0, Math.PI * 2);
      context.fill();
    });
    context.globalCompositeOperation = "source-over";

    requestAnimationFrame(() => drawCanvas(state));
  }

  function resizeCanvas(state) {
    if (!state.canvas) return;
    const rect = state.canvas.getBoundingClientRect();
    const ratio = window.devicePixelRatio || 1;
    state.canvas.width = Math.max(1, Math.floor(rect.width * ratio));
    state.canvas.height = Math.max(1, Math.floor(rect.height * ratio));
    state.context.setTransform(ratio, 0, 0, ratio, 0, 0);
  }

  function updateSliderLabels(host, state) {
    const frictionLabel = host.querySelector("[data-cymatic-friction-value]");
    const sensitivityLabel = host.querySelector("[data-cymatic-sensitivity-value]");
    if (frictionLabel) {
      frictionLabel.textContent = String(Math.round(state.friction));
    }
    if (sensitivityLabel) {
      sensitivityLabel.textContent = String(Math.round(state.sensitivity));
    }
  }

  async function attachAudio(state, file, host) {
    const audio = host.querySelector(".cymatic-audio");
    const indicator = host.querySelector("[data-cymatic-audio-state]");
    if (!audio || !file) return;

    if (state.audioUrl) {
      URL.revokeObjectURL(state.audioUrl);
    }
    state.audioUrl = URL.createObjectURL(file);
    audio.src = state.audioUrl;
    audio.load();
    if (indicator) {
      indicator.textContent = "audio loaded";
    }

    if (!window.AudioContext && !window.webkitAudioContext) {
      return;
    }

    const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
    if (!state.audioContext) {
      state.audioContext = new AudioContextCtor();
    }
    if (state.audioContext.state === "suspended") {
      await state.audioContext.resume();
    }

    if (!state.analyser) {
      state.analyser = state.audioContext.createAnalyser();
      state.analyser.fftSize = 256;
      state.dataArray = new Uint8Array(state.analyser.frequencyBinCount);
    }

    if (!state.audioSource) {
      state.audioSource = state.audioContext.createMediaElementSource(audio);
      state.audioSource.connect(state.analyser);
      state.analyser.connect(state.audioContext.destination);
    }
    audio.play().catch(() => {
      if (indicator) {
        indicator.textContent = "press play";
      }
    });
  }

  function initHost(host, surface) {
    const compact = host.dataset.cymaticSurfaceMode === "compact";
    host.innerHTML = buildSurfaceMarkup(surface, compact);

    const state = {
      surface,
      stageIndex: 0,
      friction: Math.round(surface.tension_index * 100),
      sensitivity: 72,
      canvas: host.querySelector(".cymatic-canvas"),
      context: host.querySelector(".cymatic-canvas").getContext("2d"),
      audioContext: null,
      audioSource: null,
      analyser: null,
      dataArray: null,
      audioUrl: null,
    };

    resizeCanvas(state);
    if (typeof ResizeObserver !== "undefined") {
      const observer = new ResizeObserver(() => resizeCanvas(state));
      observer.observe(state.canvas);
    } else {
      window.addEventListener("resize", () => resizeCanvas(state));
    }

    const frictionInput = host.querySelector("[data-cymatic-friction]");
    const sensitivityInput = host.querySelector("[data-cymatic-sensitivity]");
    const dropzone = host.querySelector("[data-cymatic-dropzone]");
    const fileInput = host.querySelector(".cymatic-file-input");
    const healButton = host.querySelector("[data-cymatic-heal]");
    const injectButton = host.querySelector("[data-cymatic-inject]");

    host.querySelectorAll("[data-stage-index]").forEach((button) => {
      button.addEventListener("click", () => {
        setStage(host, state, Number(button.dataset.stageIndex));
      });
    });

    frictionInput.addEventListener("input", () => {
      state.friction = Number(frictionInput.value);
      updateSliderLabels(host, state);
      setStage(host, state, state.stageIndex);
    });

    sensitivityInput.addEventListener("input", () => {
      state.sensitivity = Number(sensitivityInput.value);
      updateSliderLabels(host, state);
      setStage(host, state, state.stageIndex);
    });

    healButton.addEventListener("click", () => {
      state.friction = Math.max(4, Math.round(surface.tension_index * 56));
      state.sensitivity = 78;
      frictionInput.value = String(state.friction);
      sensitivityInput.value = String(state.sensitivity);
      updateSliderLabels(host, state);
      setStage(host, state, state.stageIndex);
    });

    injectButton.addEventListener("click", () => {
      state.friction = clamp(state.friction + 18, 0, 100);
      frictionInput.value = String(state.friction);
      updateSliderLabels(host, state);
      setStage(host, state, state.stageIndex);
    });

    if (fileInput) {
      fileInput.addEventListener("change", async () => {
        const file = fileInput.files && fileInput.files[0];
        if (file) {
          await attachAudio(state, file, host);
        }
      });
    }

    if (dropzone) {
      ["dragenter", "dragover"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
          event.preventDefault();
          dropzone.classList.add("dragover");
        });
      });
      ["dragleave", "dragend", "drop"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
          event.preventDefault();
          dropzone.classList.remove("dragover");
        });
      });
      dropzone.addEventListener("drop", async (event) => {
        const file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
        if (file) {
          await attachAudio(state, file, host);
        }
      });
    }

    updateSliderLabels(host, state);
    setStage(host, state, 0);
    drawCanvas(state);
  }

  async function initAllCymaticSurfaces() {
    const hosts = [...document.querySelectorAll("[data-cymatic-surface]")];
    if (!hosts.length || !window.AMAIResearch) {
      return;
    }
    const surface = await window.AMAIResearch.loadCymaticSurface();
    if (!surface) {
      hosts.forEach((host) => {
        host.innerHTML = `
          <div class="cymatic-panel">
            <div class="cymatic-label">Cymatic surface</div>
            <h3>Waiting for the generated signal bundle</h3>
            <p class="cymatic-subcopy">Run the cymatic export surface and reload this page to hydrate the live visual layer.</p>
          </div>
        `;
      });
      return;
    }
    hosts.forEach((host) => initHost(host, surface));
  }

  document.addEventListener("DOMContentLoaded", initAllCymaticSurfaces);
})();
