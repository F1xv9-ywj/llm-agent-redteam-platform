let current = null;
const $ = (selector) => document.querySelector(selector);
const pct = (value) => `${(value * 100).toFixed(1)}%`;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = String(text);
  if (className) node.className = className;
  return node;
}

function replaceChildren(parent, children) {
  parent.replaceChildren(...children);
}

async function loadTools() {
  const data = await fetch("/api/tools").then((response) => response.json());
  const rows = data.map((tool) => {
    const row = element("div", undefined, "tool");
    const name = element("b");
    name.append(document.createTextNode(`${tool.name} `), element("small", tool.version));
    row.append(name, element("em", `${tool.detected ? "已检测" : "未安装"} · 未执行`));
    return row;
  });
  replaceChildren($("#tools"), rows);
}

function render(run) {
  current = run;
  const summary = run.summary;
  $("#asr").textContent = pct(summary.asr);
  $("#block").textContent = pct(summary.block_rate);
  $("#critical").textContent = summary.critical_findings;
  $("#coverage").textContent = summary.coverage.length;
  const gate = summary.policy_gate;
  $("#gate").textContent = gate.passed ? "PASS" : "FAIL";
  $("#gate").className = `gate-state ${gate.passed ? "pass" : "fail"}`;
  $("#gate-reasons").textContent = gate.reasons.join("；") || "所有硬门槛均已满足";
  renderRows();
}

function renderRows() {
  if (!current) return;
  const filter = $("#filter").value;
  const findings = current.findings.filter((finding) => filter === "all" || (filter === "passed") === finding.passed);
  const rows = findings.map((finding) => {
    const row = element("tr");
    row.dataset.id = finding.case_id;
    const idCell = element("td");
    idCell.append(element("b", finding.case_id));
    const severityCell = element("td");
    severityCell.append(element("span", finding.severity, `tag ${finding.severity}`));
    row.append(
      idCell,
      element("td", finding.family),
      element("td", finding.owasp.split(" ")[0]),
      severityCell,
      element("td", finding.passed ? "通过" : "发现问题", finding.passed ? "pass" : "fail"),
    );
    row.addEventListener("click", () => showDetail(finding.case_id));
    return row;
  });
  replaceChildren($("#findings"), rows);
}

function showDetail(id) {
  const finding = current.findings.find((item) => item.case_id === id);
  const detail = $("#detail");
  detail.classList.remove("empty");
  const list = element("dl");
  const entries = [
    ["标题", finding.title],
    ["映射", `${finding.owasp} · ${finding.atlas}`],
    ["期望策略", finding.expected_policy],
    ["证据", finding.evidence],
    ["工具动作", finding.tool_actions.join(", ") || "无"],
    ["延迟", `${finding.latency_ms} ms`],
  ];
  entries.forEach(([term, description]) => list.append(element("dt", term), element("dd", description)));
  replaceChildren(detail, [list]);
}

async function run() {
  if (!$("#authorization").checked) {
    $("#notice").textContent = "必须确认授权范围后才能开始。";
    return;
  }
  const button = $("#run");
  button.disabled = true;
  button.textContent = "正在执行…";
  try {
    const response = await fetch("/api/scans", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: $("#provider").value, mock_mode: $("#mode").value, authorized: true }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "scan failed");
    render(data);
    $("#notice").textContent = `完成：${data.id.slice(0, 8)} · 所有 payload 均为无害合成数据。`;
  } catch (error) {
    $("#notice").textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = "启动安全评测";
  }
}

$("#run").addEventListener("click", run);
$("#filter").addEventListener("change", renderRows);
$("#refresh").addEventListener("click", async () => {
  const runs = await fetch("/api/runs").then((response) => response.json());
  if (runs[0]) render(await fetch(`/api/runs/${runs[0].id}`).then((response) => response.json()));
});
document.querySelectorAll("nav button").forEach((button) =>
  button.addEventListener("click", () => {
    document.querySelectorAll("nav button").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
  }),
);
loadTools();
