/**
 * visualizer.js — Compiler Visualizer frontend
 * Kết nối POST /api/visualize, render 3 panel: Lexer · AST · Evaluator
 */

const vizInput   = document.getElementById("viz-input");
const btnAnalyze = document.getElementById("btn-analyze");
const tokenGrid  = document.getElementById("token-grid");
const astTree    = document.getElementById("ast-tree");
const stepsList  = document.getElementById("steps-list");
const varsSection= document.getElementById("vars-section");
const varsPills  = document.getElementById("vars-pills");
const tokCount   = document.getElementById("tok-count");
const errorBanner= document.getElementById("error-banner");
const errorPhase = document.getElementById("error-phase");
const errorMsg   = document.getElementById("error-msg");

// ── Analyze on Enter hoặc click ───────────────────────────────────────────────
vizInput.addEventListener("keydown", e => { if (e.key === "Enter") analyze(); });
btnAnalyze.addEventListener("click", analyze);

// Chạy ngay khi load trang với giá trị mặc định
window.addEventListener("DOMContentLoaded", analyze);

// ── Main ──────────────────────────────────────────────────────────────────────
async function analyze() {
  const source = vizInput.value.trim();
  clearAll();
  if (!source) return;

  btnAnalyze.disabled = true;
  try {
    const res  = await fetch("/api/visualize", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ source }),
    });
    const data = await res.json();
    renderAll(data);
  } catch (err) {
    showError("network", "Không thể kết nối đến server: " + err.message);
  } finally {
    btnAnalyze.disabled = false;
  }
}

// ── Render tất cả ─────────────────────────────────────────────────────────────
function renderAll(data) {
  // Tokens (luôn render nếu có)
  if (data.tokens?.length) renderTokens(data.tokens);

  // AST
  if (data.ast) renderAST(data.ast);

  // Steps + vars
  if (data.steps?.length) renderSteps(data.steps);
  if (data.variables && Object.keys(data.variables).length) renderVars(data.variables);

  // Error (hiển thị ở panel tương ứng, không xóa kết quả đã render)
  if (data.error) showError(data.error.phase, data.error.message);
}

// ── Panel 1: Tokens ───────────────────────────────────────────────────────────
function renderTokens(tokens) {
  const real = tokens.filter(t => t.type !== "EOF");
  tokCount.textContent = real.length + " tokens";

  tokenGrid.innerHTML = "";
  tokens.forEach(tok => {
    const pill = document.createElement("div");
    pill.className = "tok-pill tok-" + tok.type;
    pill.title = `Type: ${tok.type}\nValue: ${tok.value}\nLine: ${tok.line}, Col: ${tok.col}`;
    pill.innerHTML = `
      <span class="tok-type">${tok.type}</span>
      <span class="tok-val">${escHtml(tok.value === "<EOF>" ? "⊣" : tok.value)}</span>
    `;
    tokenGrid.appendChild(pill);
  });
}

// ── Panel 2: AST tree ─────────────────────────────────────────────────────────
function renderAST(node) {
  astTree.innerHTML = "";
  astTree.appendChild(buildASTNode(node));
}

function buildASTNode(node) {
  const wrap = document.createElement("div");
  wrap.className = "ast-node-wrap";

  // Row: icon + label
  const row = document.createElement("div");
  row.className = "ast-node-row";

  const icon = document.createElement("span");
  icon.className = "ast-icon";
  icon.textContent = nodeIcon(node.type);

  const label = document.createElement("span");
  label.className = "ast-label lbl-" + node.type;
  label.textContent = node.label;

  row.appendChild(icon);
  row.appendChild(label);
  wrap.appendChild(row);

  // Children
  if (node.children?.length) {
    const kids = document.createElement("div");
    kids.className = "ast-children";
    node.children.forEach(child => kids.appendChild(buildASTNode(child)));
    wrap.appendChild(kids);
  }

  return wrap;
}

function nodeIcon(type) {
  const icons = {
    Program:    "◈",
    Assignment: "←",
    BinaryOp:   "⊕",
    FuncCall:   "ƒ",
    UnaryMinus: "−",
    Number:     "#",
    VarRef:     "$",
    WriteCmd:   "▶",
    WritelnCmd: "▶",
    StringLiteral: '"',
  };
  return icons[type] || "·";
}

// ── Panel 3: Eval steps ───────────────────────────────────────────────────────
function renderSteps(steps) {
  stepsList.innerHTML = "";
  steps.forEach((s, i) => {
    const row = document.createElement("div");
    row.className = `step-row step-${s.phase}`;

    const result = typeof s.result === "number" ? fmtNum(s.result) : String(s.result);

    row.innerHTML = `
      <span class="step-num">${i + 1}</span>
      <span class="step-expr">${escHtml(s.expr)}</span>
      <span class="step-arrow">→</span>
      <span class="step-result">${escHtml(result)}</span>
      <span class="step-badge badge-${s.phase}">${s.phase}</span>
    `;
    stepsList.appendChild(row);
  });
}

// ── Symbol table ──────────────────────────────────────────────────────────────
function renderVars(vars) {
  varsSection.style.display = "block";
  varsPills.innerHTML = Object.entries(vars)
    .map(([k, v]) => `<span class="var-pill">${escHtml(k)} = ${fmtNum(v)}</span>`)
    .join("");
}

// ── Error banner ──────────────────────────────────────────────────────────────
function showError(phase, msg) {
  errorBanner.classList.add("show");
  errorPhase.textContent = phase;
  errorMsg.textContent   = msg;
}

// ── Clear ─────────────────────────────────────────────────────────────────────
function clearAll() {
  tokenGrid.innerHTML  = '<span class="empty">Đang phân tích...</span>';
  astTree.innerHTML    = '<span class="empty">Đang xây dựng AST...</span>';
  stepsList.innerHTML  = '<span class="empty">Đang evaluate...</span>';
  varsPills.innerHTML  = "";
  varsSection.style.display = "none";
  tokCount.textContent = "";
  errorBanner.classList.remove("show");
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function escHtml(s) {
  return String(s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function fmtNum(n) {
  if (typeof n !== "number") return String(n);
  return Number.isInteger(n) ? String(n) : parseFloat(n.toFixed(6)).toString();
}