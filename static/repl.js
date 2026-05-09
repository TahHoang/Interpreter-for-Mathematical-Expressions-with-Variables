/**
 * repl.js — Logic giao diện cho Y2 Math REPL
 */

// ── DOM refs ──────────────────────────────────────────────────────────────────
const editor       = document.getElementById("editor");
const terminal     = document.getElementById("terminal");
const lineNumbers  = document.getElementById("line-numbers");
const varTbody     = document.getElementById("var-tbody");
const btnRun       = document.getElementById("btn-run");
const btnReset     = document.getElementById("btn-reset");
const btnClearEd   = document.getElementById("btn-clear-editor");
const btnClearTerm = document.getElementById("btn-clear-terminal");
const statusDot    = document.getElementById("status-dot");
const statusText   = document.getElementById("status-text");

// ── State ─────────────────────────────────────────────────────────────────────
let isRunning = false;

// ── Line numbers ──────────────────────────────────────────────────────────────
function updateLineNumbers() {
  const lines = editor.value.split("\n").length;
  lineNumbers.textContent = Array.from({length: lines}, (_, i) => i + 1).join("\n");
}

editor.addEventListener("input", updateLineNumbers);
editor.addEventListener("scroll", () => {
  lineNumbers.scrollTop = editor.scrollTop;
});
updateLineNumbers();

// ── Tab key: insert 2 spaces instead of focus-change ─────────────────────────
editor.addEventListener("keydown", (e) => {
  if (e.key === "Tab") {
    e.preventDefault();
    const start = editor.selectionStart;
    const end   = editor.selectionEnd;
    editor.value = editor.value.slice(0, start) + "  " + editor.value.slice(end);
    editor.selectionStart = editor.selectionEnd = start + 2;
    updateLineNumbers();
  }

  // Ctrl+Enter hoặc Cmd+Enter → Run
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    e.preventDefault();
    runCode();
  }
});

// ── Status indicator ──────────────────────────────────────────────────────────
function setStatus(state, text) {
  statusDot.className = "status-dot" + (state ? " " + state : "");
  statusText.textContent = text;
}

// ── Chạy code ─────────────────────────────────────────────────────────────────
async function runCode() {
  if (isRunning) return;
  const code = editor.value.trim();
  if (!code) return;

  isRunning = true;
  btnRun.disabled = true;
  setStatus("loading", "Đang chạy…");

  try {
    const res = await fetch("/api/run", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ code }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    appendResult(code, data);
    updateVarTable(data.variables || {});
    setStatus("", "Sẵn sàng");

  } catch (err) {
    appendResult(code, { output: "", error: "Không thể kết nối đến server: " + err.message, variables: {} });
    setStatus("error", "Lỗi kết nối");
  } finally {
    isRunning = false;
    btnRun.disabled = false;
  }
}

// ── Append một block kết quả vào terminal ─────────────────────────────────────
function appendResult(code, data) {
  const block = document.createElement("div");
  block.className = "term-block";

  // Hiển thị code người dùng đã gõ (rút gọn nếu dài)
  const preview = code.length > 60 ? code.slice(0, 60).replace(/\n/g, " ") + "…" : code.replace(/\n/g, " ↵ ");
  block.innerHTML = `
    <div class="term-input-line">
      <span class="prompt">&gt;&gt;</span>
      <span class="code-preview">${escHtml(preview)}</span>
    </div>
  `;

  // Output
  if (data.output && data.output.trim()) {
    const out = document.createElement("div");
    out.className = "term-output";
    out.textContent = data.output;
    block.appendChild(out);
  }

  // Error
  if (data.error) {
    const err = document.createElement("div");
    err.className = "term-error";
    err.textContent = data.error;
    block.appendChild(err);
  }

  // Hiển thị biến mới được tạo (dưới dạng pills)
  const vars = data.variables || {};
  const varKeys = Object.keys(vars);
  if (varKeys.length > 0) {
    const pillsRow = document.createElement("div");
    pillsRow.className = "term-vars";
    varKeys.forEach(k => {
      const pill = document.createElement("span");
      pill.className = "term-var-pill";
      pill.textContent = `${k} = ${fmtNum(vars[k])}`;
      pillsRow.appendChild(pill);
    });
    block.appendChild(pillsRow);
  }

  // Không có output, không error, không variable → báo OK
  if (!data.output?.trim() && !data.error && varKeys.length === 0) {
    const ok = document.createElement("div");
    ok.className = "term-output";
    ok.style.color = "var(--text-muted)";
    ok.textContent = "(không có output)";
    block.appendChild(ok);
  }

  terminal.appendChild(block);
  terminal.scrollTop = terminal.scrollHeight;
}

// ── Cập nhật bảng biến (sidebar) ─────────────────────────────────────────────
function updateVarTable(vars) {
  const entries = Object.entries(vars);
  if (entries.length === 0) {
    varTbody.innerHTML = '<tr class="var-empty"><td colspan="2">Chưa có biến nào</td></tr>';
    return;
  }
  varTbody.innerHTML = entries
    .map(([k, v]) => `<tr><td>${escHtml(k)}</td><td>${fmtNum(v)}</td></tr>`)
    .join("");
}

// ── Reset session ─────────────────────────────────────────────────────────────
async function resetSession() {
  try {
    await fetch("/api/reset", { method: "POST" });
  } catch (_) {}

  // Clear UI
  terminal.innerHTML = `
    <div class="terminal-welcome">
      <span class="term-comment">// Session đã reset — bảng biến được xóa</span>
    </div>
  `;
  varTbody.innerHTML = '<tr class="var-empty"><td colspan="2">Chưa có biến nào</td></tr>';
  editor.value = "";
  updateLineNumbers();
  setStatus("", "Sẵn sàng");
}

// ── Example buttons ───────────────────────────────────────────────────────────
document.querySelectorAll(".example-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    editor.value = btn.dataset.code;
    updateLineNumbers();
    editor.focus();
  });
});

// ── Event listeners ───────────────────────────────────────────────────────────
btnRun.addEventListener("click", runCode);
btnReset.addEventListener("click", resetSession);
btnClearEd.addEventListener("click", () => {
  editor.value = "";
  updateLineNumbers();
  editor.focus();
});
btnClearTerm.addEventListener("click", () => {
  terminal.innerHTML = "";
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function escHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function fmtNum(n) {
  if (typeof n !== "number") return String(n);
  // Hiển thị số nguyên không có .0
  if (Number.isInteger(n)) return String(n);
  // Tối đa 6 chữ số thập phân, bỏ số 0 thừa
  return parseFloat(n.toFixed(6)).toString();
}