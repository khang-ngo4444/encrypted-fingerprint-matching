/**
 * BioCipher Live Dashboard, Folder Watcher & Telemetry Stream Controller
 * Frontend Logic for Demo, Hot-Folder Tracking & Real-time FHE Matching
 * Authors: Ngo Hoang Nhat Khang & Ho Anh Tuan (VNUK)
 */

document.addEventListener("DOMContentLoaded", () => {
  // Global State
  let samplesList = [];
  let isAutomationRunning = false;
  let autoTimer = null;
  let currentSampleIndex = 0;
  let lastEventId = null;
  let lastLogId = 0;
  let autoScrollEnabled = true;
  let currentFilter = "all";
  let logsStore = [];

  // DOM Elements
  const navTabs = document.querySelectorAll(".nav-tab");
  const tabPanes = document.querySelectorAll(".tab-pane");
  const selectSample = document.getElementById("select-sample");
  const btnTriggerScan = document.getElementById("btn-trigger-scan");
  const toggleAutomation = document.getElementById("toggle-automation");
  const tbodyMatching = document.getElementById("tbody-matching");
  const terminalConsole = document.getElementById("terminal-console");
  const badgeTopMatch = document.getElementById("badge-top-match");

  // Hot Folder Elements
  const displayCheckPath = document.getElementById("display-check-path");
  const btnCopyPath = document.getElementById("btn-copy-path");
  const btnOpenCheckFolder = document.getElementById("btn-open-check-folder");
  const btnOpenSampleFolder = document.getElementById("btn-open-sample-folder");
  const liveIngestionBanner = document.getElementById("live-ingestion-banner");
  const bannerFile = document.getElementById("banner-file");
  const bannerMsg = document.getElementById("banner-msg");

  // Telemetry Log Controls
  const btnToggleAutoscroll = document.getElementById("btn-toggle-autoscroll");
  const btnClearLogs = document.getElementById("btn-clear-logs");
  const btnExportLogs = document.getElementById("btn-export-logs");
  const filterChips = document.querySelectorAll(".filter-chip");

  // Pipeline Nodes
  const nodeSensor = document.getElementById("node-sensor");
  const nodeEsp32 = document.getElementById("node-esp32");
  const nodeNetwork = document.getElementById("node-network");
  const nodeServer = document.getElementById("node-server");
  const nodeDecrypt = document.getElementById("node-decrypt");
  const connectors = document.querySelectorAll(".pipeline-connector");
  const btnFullscreen = document.getElementById("btn-fullscreen");

  // 1. Tab Navigation
  navTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const targetId = `tab-${tab.dataset.tab}`;
      navTabs.forEach((t) => t.classList.remove("active"));
      tabPanes.forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // 2. Fetch Fingerprint Samples
  async function loadSamples() {
    try {
      const res = await fetch("/api/samples");
      const data = await res.json();
      if (data.samples && data.samples.length > 0) {
        samplesList = data.samples;
        selectSample.innerHTML = "";

        const demoFavorites = ["101_1", "101_2", "101_8", "102_1", "105_1", "107_3", "110_1"];
        demoFavorites.forEach((id) => {
          const opt = document.createElement("option");
          opt.value = id;
          opt.textContent = `${id} (Demo Chuẩn)`;
          selectSample.appendChild(opt);
        });

        const separator = document.createElement("option");
        separator.disabled = true;
        separator.textContent = "────────── Tất cả 80 mẫu ──────────";
        selectSample.appendChild(separator);

        samplesList.forEach((s) => {
          if (!demoFavorites.includes(s.id)) {
            const opt = document.createElement("option");
            opt.value = s.id;
            opt.textContent = `${s.id} (Ngón ${s.finger} - Lần ${s.scan})`;
            selectSample.appendChild(opt);
          }
        });

        selectSample.value = "101_1";
      }
    } catch (err) {
      console.warn("Could not load sample list from server:", err);
    }
  }

  // 3. Telemetry Log Stream Renderer
  function appendLogEntry(entry) {
    logsStore.push(entry);
    if (logsStore.length > 600) logsStore.shift();

    const line = document.createElement("div");
    line.className = `term-line ${entry.level || "info"}`;
    line.dataset.tag = entry.tag;

    // Check filter match
    if (currentFilter !== "all" && entry.tag !== currentFilter) {
      line.style.display = "none";
    }

    const timeSpan = document.createElement("span");
    timeSpan.className = "log-time";
    timeSpan.textContent = `[${entry.time_str}] `;

    const tagSpan = document.createElement("span");
    tagSpan.className = `log-tag tag-${(entry.tag || "").toLowerCase()}`;
    tagSpan.textContent = `[${entry.tag}] `;

    const msgSpan = document.createElement("span");
    msgSpan.className = "log-msg";
    msgSpan.textContent = entry.message;

    line.appendChild(timeSpan);
    line.appendChild(tagSpan);
    line.appendChild(msgSpan);

    terminalConsole.appendChild(line);

    if (autoScrollEnabled) {
      terminalConsole.scrollTop = terminalConsole.scrollHeight;
    }
  }

  function applyLogFilter(filterKey) {
    currentFilter = filterKey;
    filterChips.forEach((chip) => {
      chip.classList.toggle("active", chip.dataset.filter === filterKey);
    });

    const lines = terminalConsole.querySelectorAll(".term-line");
    lines.forEach((l) => {
      if (filterKey === "all") {
        l.style.display = "";
      } else {
        l.style.display = l.dataset.tag === filterKey ? "" : "none";
      }
    });

    if (autoScrollEnabled) {
      terminalConsole.scrollTop = terminalConsole.scrollHeight;
    }
  }

  // Filter Chip Click
  filterChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      applyLogFilter(chip.dataset.filter);
    });
  });

  // Log Control Buttons
  btnToggleAutoscroll.addEventListener("click", () => {
    autoScrollEnabled = !autoScrollEnabled;
    btnToggleAutoscroll.classList.toggle("active", autoScrollEnabled);
    btnToggleAutoscroll.textContent = `Tự Cuộn: ${autoScrollEnabled ? "BẬT" : "TẮT"}`;
    if (autoScrollEnabled) {
      terminalConsole.scrollTop = terminalConsole.scrollHeight;
    }
  });

  btnClearLogs.addEventListener("click", async () => {
    try {
      await fetch("/api/clear-logs", { method: "POST" });
    } catch (e) {}
    terminalConsole.innerHTML = "";
    logsStore = [];
  });

  btnExportLogs.addEventListener("click", () => {
    if (logsStore.length === 0) {
      alert("Chưa có log để xuất!");
      return;
    }
    const content = logsStore
      .map((l) => `[${l.time_str}] [${l.tag}] ${l.message}`)
      .join("\r\n");
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `BioCipher_Audit_Logs_${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  });

  // 4. Animate Hardware Pipeline Stages
  async function animatePipelineSequence(queryId) {
    [nodeSensor, nodeEsp32, nodeNetwork, nodeServer, nodeDecrypt].forEach((n) => {
      n.classList.remove("active-stage", "scanning");
    });
    connectors.forEach((c) => c.classList.remove("flowing"));

    // Stage 1: AS608 Optical Sensor
    nodeSensor.classList.add("active-stage", "scanning");
    await sleep(220);

    // Stage 2: ESP32 Edge Device
    nodeSensor.classList.remove("scanning");
    connectors[0].classList.add("flowing");
    nodeEsp32.classList.add("active-stage");
    await sleep(280);

    // Stage 3: Secure Channel
    connectors[1].classList.add("flowing");
    nodeNetwork.classList.add("active-stage");
    await sleep(180);

    // Stage 4: Raspberry Pi 5 Server FHE (No Secret Key)
    connectors[2].classList.add("flowing");
    nodeServer.classList.add("active-stage");
    await sleep(350);

    // Stage 5: Key Holder Decryption
    connectors[3].classList.add("flowing");
    nodeDecrypt.classList.add("active-stage");
    await sleep(180);

    // Stop flow animation
    connectors.forEach((c) => c.classList.remove("flowing"));
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // 5. Render Results Table
  function renderResultsTable(data) {
    tbodyMatching.innerHTML = "";
    const topMatch = data.top_match;

    // Update Top Badge
    if (topMatch.decision.includes("KHỚP")) {
      badgeTopMatch.textContent = `KHỚP: ${topMatch.target_id} (CÙNG NGÓN)`;
      badgeTopMatch.className = "badge-match";
      badgeTopMatch.style.borderColor = "var(--accent-ok)";
      badgeTopMatch.style.color = "var(--accent-ok)";
    } else {
      badgeTopMatch.textContent = `TỪ CHỐI (KHOẢNG CÁCH > NGƯỠNG)`;
      badgeTopMatch.className = "badge-match";
      badgeTopMatch.style.borderColor = "var(--accent-warn)";
      badgeTopMatch.style.color = "var(--accent-warn)";
    }

    data.candidates.forEach((c) => {
      const tr = document.createElement("tr");
      if (c.rank_fhe === 1) {
        tr.className = "top-match-row";
      }

      const tdTarget = document.createElement("td");
      tdTarget.innerHTML = `<b>${c.target_id}</b>`;

      const tdSame = document.createElement("td");
      tdSame.innerHTML = c.same_finger
        ? `<span style="color:var(--accent-ok); font-weight:700;">Đúng</span>`
        : `<span style="color:var(--text-dim);">Khác</span>`;

      const tdPlain = document.createElement("td");
      tdPlain.textContent = c.d_plain.toFixed(3);

      const tdFHE = document.createElement("td");
      tdFHE.innerHTML = `<span class="text-enc" style="font-weight:700;">${c.d_fhe.toFixed(3)}</span>`;

      const tdErr = document.createElement("td");
      tdErr.textContent = `${c.rel_err_pct.toFixed(4)}%`;

      const tdRankPlain = document.createElement("td");
      tdRankPlain.textContent = `#${c.rank_plain}`;

      const tdRankFHE = document.createElement("td");
      tdRankFHE.innerHTML = `<b class="text-enc">#${c.rank_fhe}</b>`;

      const tdStatus = document.createElement("td");
      if (c.rank_fhe === 1) {
        tdStatus.innerHTML = `<span class="tag-match">KHỚP</span>`;
      } else {
        tdStatus.innerHTML = `<span class="tag-diff">—</span>`;
      }

      tr.appendChild(tdTarget);
      tr.appendChild(tdSame);
      tr.appendChild(tdPlain);
      tr.appendChild(tdFHE);
      tr.appendChild(tdErr);
      tr.appendChild(tdRankPlain);
      tr.appendChild(tdRankFHE);
      tr.appendChild(tdStatus);

      tbodyMatching.appendChild(tr);
    });
  }

  // 6. Manual Scan Execution
  async function runMatch(queryId = null) {
    if (!queryId) {
      queryId = selectSample.value;
      if (queryId === "RANDOM" && samplesList.length > 0) {
        queryId = samplesList[Math.floor(Math.random() * samplesList.length)].id;
      }
    }

    btnTriggerScan.disabled = true;
    btnTriggerScan.innerHTML = `<span class="pulse"></span> Đang xử lý...`;

    const animPromise = animatePipelineSequence(queryId);

    try {
      const res = await fetch("/api/run-flow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query_id: queryId, threshold: 150.0 })
      });
      const data = await res.json();
      await animPromise;

      if (data.candidates) {
        renderResultsTable(data);
      }
    } catch (err) {
      console.error("Match error:", err);
    } finally {
      btnTriggerScan.disabled = false;
      btnTriggerScan.innerHTML = `<span>Quét & So Khớp</span>`;
    }
  }

  // 7. Polling Background Worker: Watches /api/live-status
  let bannerTimer = null;
  async function pollLiveStatus() {
    try {
      const res = await fetch(`/api/live-status?since_id=${lastLogId}`);
      if (!res.ok) return;
      const data = await res.json();

      // 1. Process new logs
      if (data.new_logs && data.new_logs.length > 0) {
        data.new_logs.forEach((log) => {
          if (log.id > lastLogId) {
            appendLogEntry(log);
            lastLogId = log.id;
          }
        });
      }

      // 2. Update folder path info
      if (data.watcher && data.watcher.folder_path) {
        displayCheckPath.textContent = data.watcher.folder_path;
        displayCheckPath.title = data.watcher.folder_path;
      }

      // 3. Process new event from Hot-Folder Watcher
      const evt = data.latest_event;
      if (evt && evt.event_id && evt.event_id !== lastEventId) {
        lastEventId = evt.event_id;

        // Show Live Ingestion Banner
        bannerFile.textContent = evt.file_name;
        bannerMsg.textContent = `Đã phát hiện file vân tay mới paste vào check_folder/ (Kích thước: ${(evt.file_size || 0).toLocaleString()} bytes)`;
        liveIngestionBanner.classList.remove("hidden");
        liveIngestionBanner.classList.add("flash-banner");

        if (bannerTimer) clearTimeout(bannerTimer);
        bannerTimer = setTimeout(() => {
          liveIngestionBanner.classList.remove("flash-banner");
          liveIngestionBanner.classList.add("hidden");
        }, 5000);

        // Update dropdown selection if matching
        if (evt.query_id) {
          selectSample.value = evt.query_id;
        }

        // Trigger visual pipeline sequence
        animatePipelineSequence(evt.query_id);

        // Update Results Table
        if (evt.match_data && evt.match_data.candidates) {
          renderResultsTable(evt.match_data);
        }
      }
    } catch (err) {
      // Background poll silently continues
    }
  }

  // Poll every 350ms
  setInterval(pollLiveStatus, 350);

  // 8. Hot-Folder Action Buttons
  btnOpenCheckFolder.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/open-folder");
      const data = await res.json();
      if (!data.opened) {
        navigator.clipboard.writeText(data.path);
        alert(`Đường dẫn thư mục: ${data.path}\n(Đã sao chép vào Clipboard)`);
      }
    } catch (e) {
      alert("Không thể mở thư mục tự động, hãy mở thủ công tại check_folder/");
    }
  });

  btnOpenSampleFolder.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/open-sample-folder");
      const data = await res.json();
      if (!data.opened) {
        navigator.clipboard.writeText(data.path);
        alert(`Đường dẫn kho mẫu: ${data.path}\n(Đã sao chép vào Clipboard)`);
      }
    } catch (e) {
      alert("Hãy mở thư mục sample_fingerprints_to_paste/");
    }
  });

  btnCopyPath.addEventListener("click", () => {
    navigator.clipboard.writeText(displayCheckPath.textContent).then(() => {
      btnCopyPath.textContent = "✓";
      setTimeout(() => (btnCopyPath.textContent = "📋"), 1500);
    });
  });

  // 9. Direct File Upload via Drag-and-Drop or Paste (Ctrl+V)
  async function uploadAndProcessFile(file) {
    if (!file) return;
    try {
      const arrayBuffer = await file.arrayBuffer();
      await fetch("/api/upload-file", {
        method: "POST",
        headers: {
          "Content-Type": "application/octet-stream",
          "X-File-Name": file.name || "pasted_fingerprint.bmp"
        },
        body: arrayBuffer
      });
      // The background watcher on check_folder will detect and process this immediately!
    } catch (err) {
      console.error("Direct upload failed:", err);
    }
  }

  // Drag and drop onto Node 1 / Scanner
  nodeSensor.addEventListener("dragover", (e) => {
    e.preventDefault();
    nodeSensor.classList.add("drag-over");
  });
  nodeSensor.addEventListener("dragleave", () => {
    nodeSensor.classList.remove("drag-over");
  });
  nodeSensor.addEventListener("drop", (e) => {
    e.preventDefault();
    nodeSensor.classList.remove("drag-over");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      uploadAndProcessFile(e.dataTransfer.files[0]);
    }
  });

  // Global window drop
  window.addEventListener("dragover", (e) => e.preventDefault());
  window.addEventListener("drop", (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      uploadAndProcessFile(e.dataTransfer.files[0]);
    }
  });

  // Global clipboard paste (Ctrl+V)
  window.addEventListener("paste", (e) => {
    if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
      e.preventDefault();
      uploadAndProcessFile(e.clipboardData.files[0]);
    }
  });

  // 10. Automation Controller
  toggleAutomation.addEventListener("change", (e) => {
    isAutomationRunning = e.target.checked;
    if (isAutomationRunning) {
      runAutoLoop();
    } else {
      if (autoTimer) clearTimeout(autoTimer);
    }
  });

  const demoSequence = ["101_1", "101_2", "101_8", "102_1", "105_1", "107_3", "110_1"];
  async function runAutoLoop() {
    if (!isAutomationRunning) return;

    const nextSample = demoSequence[currentSampleIndex % demoSequence.length];
    currentSampleIndex++;
    selectSample.value = nextSample;

    await runMatch(nextSample);

    if (isAutomationRunning) {
      autoTimer = setTimeout(runAutoLoop, 5500);
    }
  }

  // 11. Event Listeners
  btnTriggerScan.addEventListener("click", () => {
    runMatch();
  });

  selectSample.addEventListener("change", () => {
    runMatch();
  });

  btnFullscreen.addEventListener("click", () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch((err) => console.log(err));
    } else {
      document.exitFullscreen().catch((err) => console.log(err));
    }
  });

  // 12. Startup Initialization
  loadSamples().then(() => {
    runMatch("101_1");
  });
});
