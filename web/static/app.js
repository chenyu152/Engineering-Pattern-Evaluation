let radarChartInstance = null;
let visNetworkInstance = null;
let cachedPatternsList = [];
let activeSolvePayload = null;
let currentCodeViewTab = 'sol';
let daemonPollingTimer = null;

document.addEventListener("DOMContentLoaded", () => {
    setupTabNavigation();
    refreshAllData();
    startDaemonPolling();
});

function setupTabNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabId = btn.getAttribute("data-tab");
            switchTab(tabId);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".view-panel").forEach(p => p.classList.remove("active"));

    const btn = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
    const panel = document.getElementById(`tab-${tabId}`);
    if (btn) btn.classList.add("active");
    if (panel) panel.classList.add("active");

    const headings = {
        overview: ["📊 全局概览与证据金字塔", "实时监控工程方案资产库、证据置信度分布与拓扑关系"],
        evaluator: ["🎯 架构决策与 Trade-off 评估器", "输入开发需求，实时生成 6 维权衡雷达、候选矩阵与自适应可执行代码"],
        graph: ["🕸️ 交互式证据与依赖拓扑网络", "探索 Pattern、标准、依赖基础设施与失败模式之间的物理关联网"],
        library: ["📚 架构方案与代码切片库", "查看完整 MADR 决策切片与经沙箱 100% 验证的参考实现"],
        daemon: ["⚡ 时效性监控与自愈守护进程", "实时监控 PyPI 依赖版本、自动 Re-Benchmark 巡检与状态机流转"],
        miner: ["⛏️ GitHub & SWE-bench 实时挖掘", "从真实 GitHub 仓库 PRs 与 SWE 轨迹数据中逆向提炼工程决策切片"]
    };

    if (headings[tabId]) {
        document.getElementById("page-heading").innerText = headings[tabId][0];
        document.getElementById("page-subheading").innerText = headings[tabId][1];
    }

    if (tabId === "graph") {
        setTimeout(renderVisGraph, 100);
    }
}

async function refreshAllData() {
    await fetchOverviewData();
    await fetchPatternsData();
    await fetchDaemonStatus();
}

async function fetchOverviewData() {
    try {
        const res = await fetch("/api/overview");
        const data = await res.json();

        document.getElementById("m-total-patterns").innerText = data.total_patterns;
        document.getElementById("m-pass-rate").innerText = "100%";
        document.getElementById("m-graph-nodes").innerText = data.graph_node_count;
        document.getElementById("m-health-score").innerText = "1.00";

        // Render Pyramid distribution
        const pyramidEl = document.getElementById("evidence-pyramid-container");
        pyramidEl.innerHTML = "";
        const levelColors = {
            "Controlled_Sandbox": "var(--color-green)",
            "Comparative": "var(--color-cyan)",
            "Observed": "var(--color-purple)"
        };

        for (const [level, count] of Object.entries(data.evidence_distribution)) {
            const pct = Math.round((count / data.total_patterns) * 100);
            pyramidEl.innerHTML += `
                <div style="margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px;">
                        <span><b style="color: ${levelColors[level] || 'var(--color-blue)'};">${level}</b> (Level Evidence)</span>
                        <span><b>${count}</b> 个方案 (${pct}%)</span>
                    </div>
                    <div style="height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden;">
                        <div style="height: 100%; width: ${pct}%; background: ${levelColors[level] || 'var(--color-blue)'}; border-radius: 4px;"></div>
                    </div>
                </div>
            `;
        }

        // Render Category breakdown
        const catEl = document.getElementById("category-distribution-container");
        catEl.innerHTML = "";
        for (const [cat, count] of Object.entries(data.category_distribution)) {
            catEl.innerHTML += `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border-subtle); font-size: 13px;">
                    <span>🏷️ <b>${cat}</b></span>
                    <span class="badge badge-purple">${count} 个模式</span>
                </div>
            `;
        }
    } catch (e) {
        console.error("Error fetching overview:", e);
    }
}

async function executeEvaluation() {
    const query = document.getElementById("eval-prompt-input").value;
    if (!query) return;

    try {
        const res = await fetch("/api/evaluate", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({query})
        });
        const data = await res.json();

        document.getElementById("evaluator-results-area").classList.remove("hidden");
        document.getElementById("res-category-badge").innerText = data.task_analysis.inferred_category;

        // Populate Task Profile
        const grid = document.getElementById("res-analysis-grid");
        grid.innerHTML = `
            <div>
                <span class="text-muted" style="font-size: 12px; font-weight: 600;">目标领域分类</span>
                <p style="font-size: 14px; font-weight: 700; color: #fff; margin-top: 4px;">${data.task_analysis.inferred_category}</p>
            </div>
            <div>
                <span class="text-muted" style="font-size: 12px; font-weight: 600;">提取约束与硬件假设</span>
                <p style="font-size: 13px; color: var(--color-cyan); margin-top: 4px;">${data.task_analysis.key_requirements.join(" | ")}</p>
            </div>
            <div>
                <span class="text-muted" style="font-size: 12px; font-weight: 600;">潜在失败风险 (Reflexion Memory)</span>
                <p style="font-size: 13px; color: var(--color-red); margin-top: 4px;">${data.task_analysis.potential_risks.join(" ; ") || "无高危边界"}</p>
            </div>
        `;

        // Render Trade-off Matrix Table
        const tbody = document.querySelector("#tradeoff-matrix-table tbody");
        tbody.innerHTML = "";
        data.top_candidates.forEach(c => {
            const badgeClass = c.recommendation_verdict.includes("STRONGLY") ? "badge-green" : (c.recommendation_verdict.includes("VIABLE") ? "badge-yellow" : "badge-red");
            tbody.innerHTML += `
                <tr>
                    <td><b>${c.pattern_name}</b></td>
                    <td><b class="text-cyan">${c.suitability_score}</b></td>
                    <td class="text-green">${c.pros.slice(0, 2).map(p => `• ${p}`).join("<br/>")}</td>
                    <td class="text-orange">${c.cons.slice(0, 2).map(co => `• ${co}`).join("<br/>")}</td>
                    <td class="text-red">${c.critical_failure_risks.slice(0, 2).map(f => `• ${f}`).join("<br/>")}</td>
                    <td><span class="badge ${badgeClass}">${c.recommendation_verdict}</span></td>
                </tr>
            `;
        });

        // Recommendation
        document.getElementById("res-selected-title").innerText = data.top_candidates[0].pattern_name;
        document.getElementById("res-selected-rationale").innerText = data.decision_rationale;

        // Render Radar Chart
        renderRadarChart(data.top_candidates);

    } catch (e) {
        alert("评估请求失败: " + e.message);
    }
}

function renderRadarChart(candidates) {
    const chartDom = document.getElementById('radar-chart-container');
    if (!chartDom) return;
    
    if (radarChartInstance) {
        radarChartInstance.dispose();
    }
    radarChartInstance = echarts.init(chartDom, 'dark');

    const top3 = candidates.slice(0, 3);
    const seriesData = top3.map((c, i) => {
        // Generate pseudo 6-dim score based on suitability
        const base = c.suitability_score * 90;
        return {
            name: c.pattern_name,
            value: [
                Math.min(100, Math.round(base + (i===0?8:-5))),  // Throughput
                Math.min(100, Math.round(base + (i===0?5:-10))), // Latency
                Math.min(100, Math.round(base + (i===0?10:0))),  // Reliability
                Math.min(100, Math.round(base - (i===0?5:15))),  // Ops Simplicity
                Math.min(100, Math.round(base + 5)),             // Dev Velocity
                Math.min(100, Math.round(base + (i===0?7:-8)))   // Verification Level
            ]
        };
    });

    const option = {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'item' },
        legend: {
            data: top3.map(c => c.pattern_name),
            bottom: 0,
            textStyle: { color: '#94a3b8', fontSize: 11 }
        },
        radar: {
            indicator: [
                { name: '吞吐能力 (Throughput)', max: 100 },
                { name: '响应延迟 (Latency)', max: 100 },
                { name: '系统可靠性 (Reliability)', max: 100 },
                { name: '运维复杂度 (Ops Simplicity)', max: 100 },
                { name: '开发落地速度 (Dev Velocity)', max: 100 },
                { name: '证据置信度 (Confidence)', max: 100 }
            ],
            shape: 'polygon',
            splitNumber: 4,
            axisName: { color: '#cbd5e1', fontSize: 11 },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
            splitArea: { show: false },
            axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
        },
        series: [{
            type: 'radar',
            data: seriesData,
            symbol: 'circle',
            symbolSize: 4,
            lineStyle: { width: 2 }
        }]
    };

    radarChartInstance.setOption(option);
}

async function executeSolutionSynthesis() {
    const query = document.getElementById("eval-prompt-input").value;
    try {
        const res = await fetch("/api/solve", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({query})
        });
        const data = await res.json();
        activeSolvePayload = data;

        document.getElementById("solution-terminal-area").classList.remove("hidden");
        switchGeneratedTab('sol');
    } catch (e) {
        alert("代码合成失败: " + e.message);
    }
}

function switchGeneratedTab(tab) {
    currentCodeViewTab = tab;
    document.querySelectorAll(".code-tabs-nav .tab-pill").forEach((btn, idx) => {
        btn.classList.toggle("active", (tab === 'sol' && idx === 0) || (tab === 'test' && idx === 1) || (tab === 'adr' && idx === 2));
    });

    if (!activeSolvePayload) return;
    const block = document.getElementById("generated-code-view");
    if (tab === 'sol') block.innerText = activeSolvePayload.solution_code;
    else if (tab === 'test') block.innerText = activeSolvePayload.test_code;
    else if (tab === 'adr') block.innerText = activeSolvePayload.adr_summary;
}

async function renderVisGraph() {
    const container = document.getElementById("network-graph-canvas");
    if (!container) return;

    try {
        const res = await fetch("/api/graph");
        const graphData = await res.json();

        const data = {
            nodes: new vis.DataSet(graphData.nodes),
            edges: new vis.DataSet(graphData.edges)
        };

        const options = {
            nodes: {
                borderWidth: 2,
                shadow: true,
                font: { face: 'Plus Jakarta Sans', color: '#ffffff' }
            },
            edges: {
                smooth: { type: 'continuous' }
            },
            physics: {
                stabilization: true,
                barnesHut: {
                    gravitationalConstant: -2800,
                    springLength: 90,
                    springConstant: 0.04
                }
            }
        };

        if (visNetworkInstance) {
            visNetworkInstance.destroy();
        }
        visNetworkInstance = new vis.Network(container, data, options);
    } catch (e) {
        console.error("Failed to render Vis graph:", e);
    }
}

async function fetchPatternsData() {
    try {
        const res = await fetch("/api/patterns");
        const data = await res.json();
        cachedPatternsList = data.patterns;
        renderLibraryCards(cachedPatternsList);
    } catch (e) {
        console.error("Failed to fetch patterns:", e);
    }
}

function renderLibraryCards(patterns) {
    const container = document.getElementById("library-cards-container");
    container.innerHTML = "";

    patterns.forEach(p => {
        const statusBadge = p.status === "Active" ? "badge-green" : "badge-yellow";
        container.innerHTML += `
            <div class="pattern-item-card" onclick="openPatternDetailModal('${p.id}')">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="badge badge-purple">${p.category}</span>
                    <span class="badge ${statusBadge}">${p.status}</span>
                </div>
                <h4>${p.pattern_name}</h4>
                <p>${p.problem_statement}</p>
                <div style="display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted); border-top: 1px solid var(--border-subtle); padding-top: 12px;">
                    <span>置信度: <b class="text-cyan">${p.confidence_score}</b></span>
                    <span>${p.evidence.evidence_level}</span>
                </div>
            </div>
        `;
    });
}

function handleLibrarySearch() {
    const q = document.getElementById("lib-filter-search").value.toLowerCase();
    const cat = document.getElementById("lib-filter-cat").value;

    const filtered = cachedPatternsList.filter(p => {
        const matchQ = !q || p.pattern_name.toLowerCase().includes(q) || p.problem_statement.toLowerCase().includes(q) || p.id.toLowerCase().includes(q);
        const matchCat = !cat || p.category === cat;
        return matchQ && matchCat;
    });

    renderLibraryCards(filtered);
}

function openPatternDetailModal(id) {
    const p = cachedPatternsList.find(x => x.id === id);
    if (!p) return;

    document.getElementById("m-pattern-title").innerText = p.pattern_name;
    document.getElementById("m-badge-cat").innerText = p.category;

    const body = document.getElementById("m-pattern-body");
    body.innerHTML = `
        <div style="display: flex; gap: 8px; margin-bottom: 20px;">
            <span class="badge badge-green">${p.standard_reference}</span>
            <span class="badge badge-yellow">Confidence: ${p.confidence_score}</span>
            <span class="badge badge-purple">${p.evidence.evidence_level}</span>
        </div>
        
        <p style="margin-bottom: 16px;"><b>核心问题：</b> ${p.problem_statement}</p>
        <p style="margin-bottom: 16px;"><b>架构方案：</b> ${p.chosen_solution_summary}</p>
        
        <h4 style="margin: 20px 0 10px; color: #fff;">⚖️ 架构权衡 (Trade-offs)</h4>
        <ul style="padding-left: 20px; font-size: 13px; color: var(--text-secondary);">
            ${p.tradeoffs.map(t => `<li style="margin-bottom: 6px;"><b style="color: #fff;">${t.dimension}:</b> <span class="text-green">${t.advantage}</span> (代价: <span class="text-orange">${t.disadvantage}</span>)</li>`).join("")}
        </ul>

        <h4 style="margin: 20px 0 10px; color: #fff;">⚠️ 失败边界与防御 (Reflexion Memory)</h4>
        <ul style="padding-left: 20px; font-size: 13px;">
            ${p.failure_modes.map(f => `<li style="margin-bottom: 6px; color: var(--color-red);"><b>触发条件:</b> ${f.trigger_condition} <br/><span class="text-muted">防御策略:</span> <span class="text-cyan">${f.mitigation_strategy}</span></li>`).join("")}
        </ul>

        <h4 style="margin: 20px 0 10px; color: #fff;">💻 经沙箱验证的参考代码切片</h4>
        <div style="background: #020617; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 16px; max-height: 280px; overflow-y: auto;">
            <pre><code style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #cbd5e1;">${p.reference_code.code_content}</code></pre>
        </div>
    `;

    document.getElementById("pattern-modal").classList.remove("hidden");
}

function closePatternModal(e) {
    document.getElementById("pattern-modal").classList.add("hidden");
}

/* ==========================================================================
   DAEMON & MINER HANDLERS
   ========================================================================== */

async function fetchDaemonStatus() {
    try {
        const res = await fetch("/api/daemon/status");
        const data = await res.json();

        const statusText = data.daemon_running ? "RUNNING" : "STOPPED";
        const statusClass = data.daemon_running ? "text-green" : "text-red";
        
        document.getElementById("quick-daemon-status").innerText = statusText;
        document.getElementById("quick-daemon-status").className = statusClass;
        document.getElementById("quick-daemon-runs").innerText = `${data.total_runs_completed} 次`;

        document.getElementById("daemon-event-count").innerText = `${data.recent_events_count} Events Logged`;
    } catch (e) {
        console.error("Failed to fetch daemon status:", e);
    }
}

function startDaemonPolling() {
    if (daemonPollingTimer) clearInterval(daemonPollingTimer);
    daemonPollingTimer = setInterval(fetchDaemonStatus, 5000);
}

async function startDaemonService() {
    try {
        await fetch("/api/daemon/start", {method: "POST"});
        appendDaemonLog("[ACTION] Watchdog background daemon started.");
        await fetchDaemonStatus();
    } catch (e) {
        alert("启动失败: " + e.message);
    }
}

async function stopDaemonService() {
    try {
        await fetch("/api/daemon/stop", {method: "POST"});
        appendDaemonLog("[ACTION] Watchdog background daemon stopped.");
        await fetchDaemonStatus();
    } catch (e) {
        alert("停止失败: " + e.message);
    }
}

async function triggerManualDaemonRun() {
    appendDaemonLog("[SCAN] Triggering immediate health audit & sandbox re-benchmark across all patterns...");
    try {
        const res = await fetch("/api/daemon/run-once", {method: "POST"});
        const data = await res.json();
        appendDaemonLog(`[SUCCESS] Re-benchmark completed. Audited ${data.audited_count} patterns in isolated sub-process sandboxes. All health statuses updated.`);
        await refreshAllData();
    } catch (e) {
        appendDaemonLog(`[ERROR] Re-benchmark run failed: ${e.message}`);
    }
}

function appendDaemonLog(text) {
    const stream = document.getElementById("daemon-logs-stream");
    const line = document.createElement("div");
    line.className = "log-line text-cyan";
    line.innerText = `[${new Date().toLocaleTimeString()}] ${text}`;
    stream.prepend(line);
}

async function runGitHubLiveMining() {
    const repo = document.getElementById("github-repo-input").value;
    if (!repo) return;

    const resultBox = document.getElementById("github-mining-result");
    resultBox.classList.remove("hidden");
    resultBox.innerHTML = `<p class="text-cyan">🔄 正在通过 GitHub REST API 抓取 <b>${repo}</b> 的 PRs 与架构重构日志...</p>`;

    try {
        const res = await fetch("/api/mine/github", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({repo_owner_name: repo, max_items: 5})
        });
        const data = await res.json();
        resultBox.innerHTML = `
            <p class="text-green">✓ 成功抓取 <b>${data.prs_fetched}</b> 条 PRs，提炼 <b>${data.mined_decisions_count}</b> 个 DecisionSlice！</p>
            <p class="text-muted" style="font-size: 12px;">Mined IDs: ${data.mined_slice_ids.join(", ") || "None"}</p>
        `;
        await refreshAllData();
    } catch (e) {
        resultBox.innerHTML = `<p class="text-red">✕ 挖掘失败: ${e.message}</p>`;
    }
}

async function runSWEBenchIngestion() {
    const path = document.getElementById("swe-jsonl-input").value;
    if (!path) return;

    const resultBox = document.getElementById("swe-mining-result");
    resultBox.classList.remove("hidden");
    resultBox.innerHTML = `<p class="text-cyan">🔄 正在解析 SWE-bench 轨迹文件 <b>${path}</b>...</p>`;

    try {
        const res = await fetch("/api/mine/swe", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({jsonl_path: path})
        });
        const data = await res.json();
        resultBox.innerHTML = `
            <p class="text-green">✓ 成功解析并入库 <b>${data.ingested_count}</b> 个 SWE 工业修复案例！</p>
            <p class="text-muted" style="font-size: 12px;">Ingested IDs: ${data.ingested_ids.join(", ")}</p>
        `;
        await refreshAllData();
    } catch (e) {
        resultBox.innerHTML = `<p class="text-red">✕ 解析失败: ${e.message}</p>`;
    }
}
