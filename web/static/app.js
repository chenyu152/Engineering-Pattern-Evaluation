let networkInstance = null;
let cachedPatterns = [];
let lastSolveResult = null;
let currentCodeTab = 'sol';

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    loadOverview();
    loadPatterns();
    loadGraph();
});

function initNavigation() {
    const navButtons = document.querySelectorAll(".nav-btn");
    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabId = btn.getAttribute("data-tab");
            switchTab(tabId);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

    const targetBtn = document.querySelector(`.nav-btn[data-tab="${tabId}"]`);
    const targetContent = document.getElementById(`tab-${tabId}`);
    
    if (targetBtn) targetBtn.classList.add("active");
    if (targetContent) targetContent.classList.add("active");

    const titles = {
        overview: "📊 全局概览与证据金字塔",
        evaluator: "🎯 架构决策与 Trade-off 评估器",
        graph: "🕸️ 交互式证据与拓扑关系图谱",
        library: "📚 方案库与代码切片浏览器",
        sandbox: "🧪 实时沙箱健康度审计",
        miner: "⛏️ 仓库逆向架构挖掘器"
    };
    document.getElementById("page-title").innerText = titles[tabId] || "系统面板";

    if (tabId === "graph") {
        setTimeout(loadGraph, 100);
    }
}

async function refreshData() {
    await loadOverview();
    await loadPatterns();
    await loadGraph();
}

async function loadOverview() {
    try {
        const res = await fetch("/api/overview");
        const data = await res.json();

        document.getElementById("stat-total-patterns").innerText = data.total_patterns;
        document.getElementById("stat-controlled-count").innerText = data.evidence_distribution["Controlled_Sandbox"] || data.total_patterns;
        document.getElementById("stat-graph-nodes").innerText = data.graph_node_count;
        document.getElementById("stat-active-rate").innerText = "100%";

        // Render Evidence Pyramid Bars
        const pyramidEl = document.getElementById("evidence-pyramid-bars");
        pyramidEl.innerHTML = "";
        for (const [level, count] of Object.entries(data.evidence_distribution)) {
            pyramidEl.innerHTML += `
                <div style="margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                        <span><b>${level}</b> (Level Evidence)</span>
                        <span><b>${count}</b> 个方案</span>
                    </div>
                    <div style="height: 8px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden;">
                        <div style="height: 100%; width: ${(count/data.total_patterns)*100}%; background: var(--accent-blue);"></div>
                    </div>
                </div>
            `;
        }

        // Render Category Distribution
        const catEl = document.getElementById("category-distribution-list");
        catEl.innerHTML = "";
        for (const [cat, count] of Object.entries(data.category_distribution)) {
            catEl.innerHTML += `
                <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border-color); font-size: 13px;">
                    <span>🏷️ ${cat}</span>
                    <span class="badge badge-purple">${count} 个模式</span>
                </div>
            `;
        }
    } catch (e) {
        console.error("Failed to load overview:", e);
    }
}

async function runEvaluation() {
    const query = document.getElementById("eval-query-input").value;
    if (!query) return;

    try {
        const res = await fetch("/api/evaluate", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({query})
        });
        const data = await res.json();

        document.getElementById("eval-result-container").classList.remove("hidden");
        document.getElementById("eval-inferred-cat").innerText = data.task_analysis.inferred_category;

        // Details
        const detailsEl = document.getElementById("eval-analysis-details");
        detailsEl.innerHTML = `
            <div>
                <p class="text-muted" style="font-size: 12px;">推断架构分类</p>
                <p><b>${data.task_analysis.inferred_category}</b></p>
            </div>
            <div>
                <p class="text-muted" style="font-size: 12px;">硬性约束提取</p>
                <p><b>${data.task_analysis.key_requirements.join(" | ")}</b></p>
            </div>
            <div>
                <p class="text-muted" style="font-size: 12px;">潜在踩坑风险 (Reflexion Memory)</p>
                <p style="color: var(--accent-red);"><b>${data.task_analysis.potential_risks.join(" ; ") || "无明显高危边界"}</b></p>
            </div>
        `;

        // Tradeoff Table
        const tbody = document.querySelector("#tradeoff-table tbody");
        tbody.innerHTML = "";
        data.top_candidates.forEach(c => {
            const badgeClass = c.recommendation_verdict.includes("STRONGLY") ? "badge-green" : (c.recommendation_verdict.includes("VIABLE") ? "badge-yellow" : "badge-red");
            tbody.innerHTML += `
                <tr>
                    <td><b>${c.pattern_name}</b></td>
                    <td><b>${c.suitability_score}</b></td>
                    <td style="color: var(--accent-green);">${c.pros.slice(0, 2).map(p => `• ${p}`).join("<br/>")}</td>
                    <td style="color: var(--accent-orange);">${c.cons.slice(0, 2).map(co => `• ${co}`).join("<br/>")}</td>
                    <td style="color: var(--accent-red);">${c.critical_failure_risks.slice(0, 2).map(f => `• ${f}`).join("<br/>")}</td>
                    <td><span class="badge ${badgeClass}">${c.recommendation_verdict}</span></td>
                </tr>
            `;
        });

        // Selection info
        document.getElementById("selected-pattern-title").innerText = `🎯 最终推荐方案：${data.top_candidates[0].pattern_name}`;
        document.getElementById("selected-pattern-rationale").innerText = data.decision_rationale;

    } catch (e) {
        alert("评估失败: " + e.message);
    }
}

async function generateSolutionCode() {
    const query = document.getElementById("eval-query-input").value;
    try {
        const res = await fetch("/api/solve", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({query})
        });
        const data = await res.json();
        lastSolveResult = data;

        document.getElementById("solution-output-area").classList.remove("hidden");
        switchCodeTab('sol');
    } catch (e) {
        alert("代码生成失败: " + e.message);
    }
}

function switchCodeTab(tab) {
    currentCodeTab = tab;
    document.querySelectorAll(".code-tabs .tab-btn").forEach((btn, idx) => {
        btn.classList.toggle("active", (tab === 'sol' && idx === 0) || (tab === 'test' && idx === 1) || (tab === 'adr' && idx === 2));
    });

    if (!lastSolveResult) return;
    const block = document.getElementById("code-display-block");
    if (tab === 'sol') block.innerText = lastSolveResult.solution_code;
    else if (tab === 'test') block.innerText = lastSolveResult.test_code;
    else if (tab === 'adr') block.innerText = lastSolveResult.adr_summary;
}

async function loadGraph() {
    const container = document.getElementById("vis-graph-container");
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
                shadow: true
            },
            edges: {
                smooth: { type: 'continuous' }
            },
            physics: {
                stabilization: true,
                barnesHut: {
                    gravitationalConstant: -3000,
                    springLength: 95,
                    springConstant: 0.04
                }
            }
        };

        if (networkInstance) {
            networkInstance.destroy();
        }
        networkInstance = new vis.Network(container, data, options);
    } catch (e) {
        console.error("Failed to render graph:", e);
    }
}

async function loadPatterns() {
    try {
        const res = await fetch("/api/patterns");
        const data = await res.json();
        cachedPatterns = data.patterns;
        renderPatternCards(cachedPatterns);
    } catch (e) {
        console.error("Failed to load patterns:", e);
    }
}

function renderPatternCards(patterns) {
    const grid = document.getElementById("pattern-cards-grid");
    grid.innerHTML = "";

    patterns.forEach(p => {
        const statusBadge = p.status === "Active" ? "badge-green" : "badge-yellow";
        grid.innerHTML += `
            <div class="pattern-card" onclick="openPatternDetail('${p.id}')">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <span class="badge badge-purple">${p.category}</span>
                    <span class="badge ${statusBadge}">${p.status}</span>
                </div>
                <h4>${p.pattern_name}</h4>
                <p>${p.problem_statement}</p>
                <div style="display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted); border-top: 1px solid var(--border-color); padding-top: 8px;">
                    <span>置信度: <b>${p.confidence_score}</b></span>
                    <span>${p.evidence.evidence_level}</span>
                </div>
            </div>
        `;
    });
}

function filterLibrary() {
    const search = document.getElementById("lib-search-input").value.toLowerCase();
    const cat = document.getElementById("lib-category-select").value;

    const filtered = cachedPatterns.filter(p => {
        const matchSearch = !search || p.pattern_name.toLowerCase().includes(search) || p.problem_statement.toLowerCase().includes(search);
        const matchCat = !cat || p.category === cat;
        return matchSearch && matchCat;
    });

    renderPatternCards(filtered);
}

function openPatternDetail(id) {
    const p = cachedPatterns.find(x => x.id === id);
    if (!p) return;

    document.getElementById("modal-pattern-title").innerText = p.pattern_name;
    const body = document.getElementById("modal-pattern-body");
    
    body.innerHTML = `
        <div style="margin-bottom: 16px;">
            <span class="badge badge-purple">${p.category}</span>
            <span class="badge badge-green">${p.standard_reference}</span>
            <span class="badge badge-yellow">Confidence: ${p.confidence_score}</span>
        </div>
        <p style="margin-bottom: 16px;"><b>核心问题：</b> ${p.problem_statement}</p>
        <p style="margin-bottom: 16px;"><b>架构解法：</b> ${p.chosen_solution_summary}</p>
        
        <h4 style="margin: 16px 0 8px;">⚖️ 架构权衡 (Trade-offs)</h4>
        <ul>
            ${p.tradeoffs.map(t => `<li style="margin-bottom: 6px;"><b>${t.dimension}:</b> <span style="color: var(--accent-green);">${t.advantage}</span> (代价: <span style="color: var(--accent-orange);">${t.disadvantage}</span>)</li>`).join("")}
        </ul>

        <h4 style="margin: 16px 0 8px;">⚠️ 失败边界与防御 (Failure Modes)</h4>
        <ul>
            ${p.failure_modes.map(f => `<li style="margin-bottom: 6px; color: var(--accent-red);"><b>触发条件:</b> ${f.trigger_condition} <br/><b>防御策略:</b> ${f.mitigation_strategy}</li>`).join("")}
        </ul>

        <h4 style="margin: 16px 0 8px;">💻 可运行参考代码切片</h4>
        <pre><code style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #cbd5e1;">${p.reference_code.code_content}</code></pre>
    `;

    document.getElementById("detail-modal").classList.remove("hidden");
}

function closeModal(event) {
    document.getElementById("detail-modal").classList.add("hidden");
}

async function runSandboxAudit() {
    const tbody = document.querySelector("#audit-table tbody");
    tbody.innerHTML = `<tr><td colspan="5" class="text-center" style="color: var(--accent-blue);">🧪 沙箱子进程正在并行运行单测测试集，请稍候...</td></tr>`;

    try {
        const res = await fetch("/api/audit", { method: "POST" });
        const data = await res.json();

        tbody.innerHTML = "";
        data.results.forEach(r => {
            const passBadge = r.test_passed ? '<span class="badge badge-green">PASSED (100%)</span>' : '<span class="badge badge-red">FAILED</span>';
            tbody.innerHTML += `
                <tr>
                    <td><code>${r.id}</code></td>
                    <td><b>${r.pattern_name}</b></td>
                    <td>${passBadge}</td>
                    <td><b>${r.new_confidence}</b></td>
                    <td><span class="badge badge-green">${r.status}</span></td>
                </tr>
            `;
        });
    } catch (e) {
        alert("审计失败: " + e.message);
    }
}

async function runRepoMining() {
    const dir = document.getElementById("miner-path-input").value;
    if (!dir) return;

    try {
        const res = await fetch("/api/mine", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({directory_path: dir})
        });
        const data = await res.json();

        const card = document.getElementById("miner-results-card");
        card.classList.remove("hidden");

        const box = document.getElementById("miner-summary-box");
        box.innerHTML = `
            <div>
                <p class="text-muted">扫描路径</p>
                <p><b>${data.scanned_directory}</b></p>
            </div>
            <div>
                <p class="text-muted">发现 ADR 文件数</p>
                <p><b>${data.adr_files_found} 个</b></p>
            </div>
            <div>
                <p class="text-muted">成功提取入库</p>
                <p style="color: var(--accent-green);"><b>${data.successfully_mined_count} 个 DecisionSlice</b></p>
            </div>
        `;
        await refreshData();
    } catch (e) {
        alert("挖掘失败: " + e.message);
    }
}
