/**
 * visualizer.js — Animated Compiler Visualizer
 *
 * Animation sequence:
 *   1. Pipeline bar lights up "Lexer"
 *   2. Scan bar sweeps across — tokens fly in one by one
 *   3. Pipeline advances to "Parser" — AST nodes build top-down
 *   4. Pipeline advances to "Evaluator" — steps slide in with active highlight
 *   5. Symbol table pills pop in
 *   6. All pipeline steps show "done"
 */

// ── DOM ───────────────────────────────────────────────────────────────────────
const vizInput    = document.getElementById("viz-input");
const btnAnalyze  = document.getElementById("btn-analyze");
const tokenGrid   = document.getElementById("token-grid");
const astTree     = document.getElementById("ast-tree");
const stepsList   = document.getElementById("steps-list");
const varsSection = document.getElementById("vars-section");
const varsPills   = document.getElementById("vars-pills");
const tokCount    = document.getElementById("tok-count");
const errorBanner = document.getElementById("error-banner");
const errorPhase  = document.getElementById("error-phase");
const errorMsg    = document.getElementById("error-msg");
const scanBar     = document.getElementById("scan-bar");
const scanFill    = document.getElementById("scan-fill");
const speedSlider = document.getElementById("speed-slider");

const pipeLex   = document.getElementById("pipe-lex");
const pipeParse = document.getElementById("pipe-parse");
const pipeEval  = document.getElementById("pipe-eval");
const hdrLex    = document.getElementById("hdr-lex");
const hdrParse  = document.getElementById("hdr-parse");
const hdrEval   = document.getElementById("hdr-eval");

// ── Speed control ─────────────────────────────────────────────────────────────
// slider 1–5 → delay ms per item: 1=300ms, 5=40ms
function itemDelay() {
  const v = parseInt(speedSlider.value);   // 1..5
  return Math.round(300 / (v * 0.8 + 0.2));
}

// ── Utility: sleep ────────────────────────────────────────────────────────────
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ── Abort controller — cancels in-flight animation when user re-runs ──────────
let abortCtrl = null;
function freshAbort() {
  if (abortCtrl) abortCtrl.abort();
  abortCtrl = new AbortController();
  return abortCtrl.signal;
}

// ── Entry points ──────────────────────────────────────────────────────────────
vizInput.addEventListener("keydown", e => { if (e.key === "Enter") analyze(); });
btnAnalyze.addEventListener("click", analyze);
window.addEventListener("DOMContentLoaded", analyze);

async function analyze() {
  const source = vizInput.value.trim();
  const signal = freshAbort();
  clearAll();
  if (!source) return;

  btnAnalyze.disabled = true;

  try {
    const res  = await fetch("/api/visualize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source }),
      signal,
    });
    const data = await res.json();
    await animateAll(data, source, signal);
  } catch (err) {
    if (err.name !== "AbortError") {
      showError("network", "Không thể kết nối đến server: " + err.message);
    }
  } finally {
    btnAnalyze.disabled = false;
  }
}

// ── Master animation sequence ─────────────────────────────────────────────────
async function animateAll(data, source, signal) {

  // ── Phase 1: Lexer ──────────────────────────────────────────────────────────
  setPipeState("lex", "active");
  hdrLex.classList.add("ph-active");

  if (data.tokens?.length) {
    await animateScanBar(source, signal);
    if (signal.aborted) return;
    await animateTokens(data.tokens, signal);
    if (signal.aborted) return;
  }

  if (data.error?.phase === "lexer") {
    showError("lexer", data.error.message);
    setPipeState("lex", "done");
    return;
  }

  setPipeState("lex", "done");
  hdrLex.classList.remove("ph-active");
  await sleep(180);

  // ── Phase 2: Parser ─────────────────────────────────────────────────────────
  setPipeState("parse", "active");
  hdrParse.classList.add("ph-active");

  if (data.ast) {
    await animateAST(data.ast, signal);
    if (signal.aborted) return;
  }

  if (data.error?.phase === "parser") {
    showError("parser", data.error.message);
    setPipeState("parse", "done");
    return;
  }

  setPipeState("parse", "done");
  hdrParse.classList.remove("ph-active");
  await sleep(180);

  // ── Phase 3: Evaluator ──────────────────────────────────────────────────────
  setPipeState("eval", "active");
  hdrEval.classList.add("ph-active");

  if (data.steps?.length) {
    await animateSteps(data.steps, signal);
    if (signal.aborted) return;
  }

  if (data.variables && Object.keys(data.variables).length) {
    await animateVars(data.variables, signal);
    if (signal.aborted) return;
  }

  if (data.error?.phase === "eval") {
    showError("eval", data.error.message);
  }

  setPipeState("eval", "done");
  hdrEval.classList.remove("ph-active");
}

// ── Pipeline state ─────────────────────────────────────────────────────────────
function setPipeState(phase, state) {
  const el = { lex: pipeLex, parse: pipeParse, eval: pipeEval }[phase];
  el.classList.remove("active", "done");
  if (state) el.classList.add(state);
}

// ── Animation: scan bar ───────────────────────────────────────────────────────
async function animateScanBar(source, signal) {
  scanBar.classList.add("show");
  const steps = 30;
  const delay = Math.max(10, itemDelay() * 0.3);
  for (let i = 1; i <= steps; i++) {
    if (signal.aborted) break;
    scanFill.style.width = (i / steps * 100) + "%";
    await sleep(delay);
  }
  scanBar.classList.remove("show");
  scanFill.style.width = "0";
}

// ── Animation: tokens fly in one by one ──────────────────────────────────────
async function animateTokens(tokens, signal) {
  tokenGrid.innerHTML = "";
  const real = tokens.filter(t => t.type !== "EOF" && t.type !== "NEWLINE");
  tokCount.textContent = real.length + " tokens";

  for (let i = 0; i < tokens.length; i++) {
    if (signal.aborted) break;
    const tok = tokens[i];
    const pill = makePill(tok);
    // stagger delay via animation-delay
    pill.style.animationDelay = "0ms";  // already staggered by awaited sleep
    tokenGrid.appendChild(pill);

    // briefly highlight the new pill
    pill.classList.add("tok-highlight");
    await sleep(itemDelay());
    pill.classList.remove("tok-highlight");
    await sleep(20);
  }
}

function makePill(tok) {
  const pill = document.createElement("div");
  pill.className = "tok-pill tok-" + tok.type;
  pill.title = `Type: ${tok.type}\nValue: ${tok.value}\nLine: ${tok.line}, Col: ${tok.col}`;
  pill.innerHTML = `
    <span class="tok-type">${tok.type}</span>
    <span class="tok-val">${escHtml(tok.value === "<EOF>" ? "⊣" : tok.value)}</span>
  `;
  return pill;
}

// ── Animation: AST builds node by node (BFS order) ───────────────────────────
async function animateAST(rootData, signal) {
  astTree.innerHTML = "";

  // We build the DOM tree but hide each node, then reveal BFS
  const allRows = [];

  function buildHidden(nodeData, parentEl) {
    const wrap = document.createElement("div");
    wrap.className = "ast-node-wrap";
    wrap.style.opacity = "0";
    wrap.style.animation = "none";   // disable auto CSS animation; we control it

    const row = document.createElement("div");
    row.className = "ast-node-row";

    const icon = document.createElement("span");
    icon.className = "ast-icon";
    icon.textContent = nodeIcon(nodeData.type);

    const label = document.createElement("span");
    label.className = "ast-label lbl-" + nodeData.type;
    label.textContent = nodeData.label;

    row.appendChild(icon);
    row.appendChild(label);
    wrap.appendChild(row);
    allRows.push({ wrap, row });

    if (nodeData.children?.length) {
      const kids = document.createElement("div");
      kids.className = "ast-children";
      nodeData.children.forEach(c => buildHidden(c, kids));
      wrap.appendChild(kids);
    }

    parentEl.appendChild(wrap);
  }

  buildHidden(rootData, astTree);

  // Reveal one by one with animation
  for (const { wrap, row } of allRows) {
    if (signal.aborted) break;
    wrap.style.animation = "";
    wrap.style.opacity   = "";
    row.classList.add("ast-highlight");
    await sleep(itemDelay() * 1.2);
    row.classList.remove("ast-highlight");
    await sleep(20);
  }
}

// ── Animation: eval steps slide in one by one ─────────────────────────────────
async function animateSteps(steps, signal) {
  stepsList.innerHTML = "";
  const delay = itemDelay();

  for (let i = 0; i < steps.length; i++) {
    if (signal.aborted) break;
    const s   = steps[i];
    const row = document.createElement("div");
    row.className = `step-row step-${s.phase} step-active`;
    row.style.animationDelay = "0ms";

    const result = typeof s.result === "number" ? fmtNum(s.result) : String(s.result);
    row.innerHTML = `
      <span class="step-num">${i + 1}</span>
      <span class="step-expr">${escHtml(s.expr)}</span>
      <span class="step-arrow">→</span>
      <span class="step-result">${escHtml(result)}</span>
      <span class="step-badge badge-${s.phase}">${s.phase}</span>
    `;
    stepsList.appendChild(row);
    stepsList.scrollTop = stepsList.scrollHeight;

    await sleep(delay);
    row.classList.remove("step-active");
    await sleep(30);
  }
}

// ── Animation: symbol table pills pop in ──────────────────────────────────────
async function animateVars(vars, signal) {
  varsSection.style.display = "block";
  varsPills.innerHTML = "";

  for (const [k, v] of Object.entries(vars)) {
    if (signal.aborted) break;
    const pill = document.createElement("span");
    pill.className = "var-pill";
    pill.textContent = `${k} = ${fmtNum(v)}`;
    varsPills.appendChild(pill);
    await sleep(itemDelay() * 0.6);
  }
}

// ── Error banner ──────────────────────────────────────────────────────────────
function showError(phase, msg) {
  errorBanner.classList.add("show");
  errorPhase.textContent = phase;
  errorMsg.textContent   = msg;
}

// ── Clear everything ──────────────────────────────────────────────────────────
function clearAll() {
  tokenGrid.innerHTML  = '<span class="empty">Đang quét source...</span>';
  astTree.innerHTML    = '<span class="empty">Đang xây dựng AST...</span>';
  stepsList.innerHTML  = '<span class="empty">Đang evaluate...</span>';
  varsPills.innerHTML  = "";
  varsSection.style.display = "none";
  tokCount.textContent = "";
  errorBanner.classList.remove("show");
  scanBar.classList.remove("show");
  scanFill.style.width = "0";

  [pipeLex, pipeParse, pipeEval].forEach(p => p.classList.remove("active","done"));
  [hdrLex, hdrParse, hdrEval].forEach(h => h.classList.remove("ph-active"));
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function nodeIcon(type) {
  return {
    Program:"◈", Assignment:"←", BinaryOp:"⊕",
    FuncCall:"ƒ", UnaryMinus:"−", Number:"#",
    VarRef:"$", WriteCmd:"▶", WritelnCmd:"▶", StringLiteral:'"',
  }[type] || "·";
}

function escHtml(s) {
  return String(s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function fmtNum(n) {
  if (typeof n !== "number") return String(n);
  return Number.isInteger(n) ? String(n) : parseFloat(n.toFixed(6)).toString();
}