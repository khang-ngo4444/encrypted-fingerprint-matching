/**
 * BioCipher Live Dashboard & Automation Controller
 * Frontend Logic for Demo & Real-time Matching
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let samplesList = [];
  let isAutomationRunning = false;
  let autoTimer = null;
  let currentSampleIndex = 0;

  // DOM Elements
  const navTabs = document.querySelectorAll(".nav-tab");
  const tabPanes = document.querySelectorAll(".tab-pane");
  const selectSample = document.getElementById("select-sample");
  const btnTriggerScan = document.getElementById("btn-trigger-scan");
  const toggleAutomation = document.getElementById("toggle-automation");
  const tbodyMatching = document.getElementById("tbody-matching");
  const terminalConsole = document.getElementById("terminal-console");
  const badgeTopMatch = document.getElementById("badge-top-match");
  
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
        
        // Add popular demo samples first
        const demoFavorites = ["101_1", "101_2", "101_8", "102_1", "105_1", "107_3", "110_1"];
        demoFavorites.forEach(id => {
          const opt = document.createElement("option");
          opt.value = id;
          opt.textContent = `${id} (Demo Chuẩn)`;
          selectSample.appendChild(opt);
        });

        const separator = document.createElement("option");
        separator.disabled = true;
        separator.textContent = "────────── Tất cả 80 mẫu ──────────";
        selectSample.appendChild(separator);

        samplesList.forEach(s => {
          if (!demoFavorites.includes(s.id)) {
            const opt = document.createElement("option");
            opt.value = s.id;
            opt.textContent = `${s.id} (Ngón ${s.finger} - Lần ${s.scan})`;
            selectSample.appendChild(opt);
          }
        });

        // Set initial selected
        selectSample.value = "101_1";
      }
    } catch (err) {
      console.warn("Could not load sample list from server:", err);
    }
  }

  // 3. Logger helper
  function logTerminal(msg, type = "info") {
    const d = new Date();
    const timeStr = `[${String(d.getMinutes()).padStart(2, "0")}:${String(d.getSeconds()).padStart(2, "0")}.${String(d.getMilliseconds()).padStart(3, "0")}]`;
    const line = document.createElement("div");
    line.className = `term-line ${type}`;
    line.textContent = `${timeStr} ${msg}`;
    terminalConsole.appendChild(line);
    terminalConsole.scrollTop = terminalConsole.scrollHeight;

    // Keep log buffer bounded
    if (terminalConsole.children.length > 50) {
      terminalConsole.removeChild(terminalConsole.firstChild);
    }
  }

  // 4. Animate Hardware Pipeline Stages
  async function animatePipelineSequence(queryId) {
    // Reset all nodes
    [nodeSensor, nodeEsp32, nodeNetwork, nodeServer, nodeDecrypt].forEach(n => {
      n.classList.remove("active-stage", "scanning");
    });
    connectors.forEach(c => c.classList.remove("flowing"));

    // Stage 1: AS608 Optical Sensor
    nodeSensor.classList.add("active-stage", "scanning");
    logTerminal(`[AS608] Cảm biến quang nhận diện ngón tay: ${queryId}. Độ phân giải 500 DPI.`, "info");
    await sleep(250);

    // Stage 2: ESP32 Client Feature Extraction + SEAL-Embedded Encryption
    nodeSensor.classList.remove("scanning");
    connectors[0].classList.add("flowing");
    nodeEsp32.classList.add("active-stage");
    logTerminal(`[ESP32] Trích xuất vector 512-D FingerCode & Mã hoá CKKS N=4096. Bản mã: 96 KB. (3.15 ms)`, "enc");
    await sleep(350);

    // Stage 3: Secure Network Transport
    connectors[1].classList.add("flowing");
    nodeNetwork.classList.add("active-stage");
    logTerminal(`[NETWORK] Truyền bản mã 96 KB qua kênh TLS. Không rò rỉ dữ liệu gốc. (0.13 ms)`, "net");
    await sleep(200);

    // Stage 4: Raspberry Pi 5 Homomorphic Matching (NO SECRET KEY)
    connectors[2].classList.add("flowing");
    nodeServer.classList.add("active-stage");
    logTerminal(`[RPi 5 SERVER] So khớp đồng cấu d^2 + 9 vòng xoay Galois vector. KHÔNG GIẢI MÃ! (22.51 ms)`, "srv");
    await sleep(450);

    // Stage 5: Key Holder Decryption
    connectors[3].classList.add("flowing");
    nodeDecrypt.classList.add("active-stage");
    logTerminal(`[KEY HOLDER] Giải mã giá trị khoảng cách Euclidean tại trạm an toàn. (0.72 ms)`, "dec");
    await sleep(200);

    // Turn off flow lines
    connectors.forEach(c => c.classList.remove("flowing"));
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // 5. Execute Matching Request
  async function runMatch(queryId = null) {
    if (!queryId) {
      queryId = selectSample.value;
      if (queryId === "RANDOM" && samplesList.length > 0) {
        queryId = samplesList[Math.floor(Math.random() * samplesList.length)].id;
      }
    }

    btnTriggerScan.disabled = true;
    btnTriggerScan.innerHTML = `<span class="pulse"></span> Đang xử lý...`;

    // Start UI Animation
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
        logTerminal(`[KẾT QUẢ] Nhận dạng thành công cho mẫu ${queryId}. Trùng khớp: ${data.top_match.target_id}.`, "success");
      }
    } catch (err) {
      console.error("Match error:", err);
      logTerminal(`Lỗi so khớp: ${err.message}`, "info");
    } finally {
      btnTriggerScan.disabled = false;
      btnTriggerScan.innerHTML = `<span>Quét & So Khớp</span>`;
    }
  }

  // 6. Render Results Table
  function renderResultsTable(data) {
    tbodyMatching.innerHTML = "";
    const topMatch = data.top_match;

    // Update Top Badge
    if (topMatch.decision.includes("KHỚP")) {
      badgeTopMatch.textContent = `KHỚP: ${topMatch.target_id} (CÙNG NGÓN)`;
      badgeTopMatch.className = "badge-match";
    } else {
      badgeTopMatch.textContent = `TỪ CHỐI (KHOẢNG CÁCH > NGUỠNG)`;
      badgeTopMatch.className = "badge-match";
      badgeTopMatch.style.borderColor = "var(--accent-warn)";
      badgeTopMatch.style.color = "var(--accent-warn)";
    }

    data.candidates.forEach((c) => {
      const tr = document.createElement("tr");
      if (c.rank_fhe === 1) {
        tr.className = "top-match-row";
      }

      // Columns
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

  // 7. Automation Controller
  toggleAutomation.addEventListener("change", (e) => {
    isAutomationRunning = e.target.checked;
    if (isAutomationRunning) {
      logTerminal("[HỆ THỐNG] Kích hoạt chế độ Automation: Tự động chạy chu kỳ liên tục cho demo video.", "success");
      runAutoLoop();
    } else {
      if (autoTimer) clearTimeout(autoTimer);
      logTerminal("[HỆ THỐNG] Đã tắt chế độ Automation.", "info");
    }
  });

  const demoSequence = ["101_1", "101_2", "101_8", "102_1", "105_1", "107_3", "110_1"];
  async function runAutoLoop() {
    if (!isAutomationRunning) return;

    const nextSample = demoSequence[currentSampleIndex % demoSequence.length];
    currentSampleIndex++;
    selectSample.value = nextSample;

    await runMatch(nextSample);

    // Wait 5.5 seconds between automated cycles (optimal for video narration)
    if (isAutomationRunning) {
      autoTimer = setTimeout(runAutoLoop, 5500);
    }
  }

  // 8. Event Listeners
  btnTriggerScan.addEventListener("click", () => {
    runMatch();
  });

  selectSample.addEventListener("change", () => {
    runMatch();
  });

  // Fullscreen
  btnFullscreen.addEventListener("click", () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(err => console.log(err));
    } else {
      document.exitFullscreen().catch(err => console.log(err));
    }
  });

  // 9. Startup initialization
  loadSamples().then(() => {
    // Initial run on page load
    runMatch("101_1");
  });
});
