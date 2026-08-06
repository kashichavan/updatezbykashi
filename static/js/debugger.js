/**
 * debugger.js  —  Visual Code Debugger IDE
 * All logic for Monaco editor, themes, language switching,
 * step debugging, inline value hints, and call-stack rendering.
 */

/* ─────────────────────────────────────────────────────────────────
   GLOBAL STATE
───────────────────────────────────────────────────────────────── */
window.showToast = window.showToast || function(msg, type) {
  console.log(`[Toast ${type || 'info'}]:`, msg);
};

let editor;
let currentLang          = 'python';
let breakpoints          = [];
let debugSteps           = [];
let currentStepIdx       = 0;
let activeDecorations    = [];      // line-highlight decorations
let inlineValueDecorations = [];    // inline variable hint decorations
let autoPlayTimer        = null;
let currentFontSize      = 14;

/* ─────────────────────────────────────────────────────────────────
   MOBILE BLOCKER DISMISS HANDLERS (close button & backdrop click)
───────────────────────────────────────────────────────────────── */
window.dismissMobileBlocker = function(event) {
  if (event) {
    try { event.stopPropagation(); } catch (e) {}
  }
  try {
    sessionStorage.setItem('mobile_blocker_dismissed', 'true');
  } catch (e) {}

  const blocker = document.getElementById('mobileBlocker');
  if (blocker) {
    blocker.classList.add('hidden');
    blocker.style.setProperty('display', 'none', 'important');
    blocker.style.setProperty('visibility', 'hidden', 'important');
    blocker.style.setProperty('opacity', '0', 'important');
    blocker.style.setProperty('pointer-events', 'none', 'important');
  }
};

document.addEventListener('DOMContentLoaded', () => {
  try {
    if (sessionStorage.getItem('mobile_blocker_dismissed') === 'true') {
      const blocker = document.getElementById('mobileBlocker');
      if (blocker) {
        blocker.classList.add('hidden');
        blocker.style.setProperty('display', 'none', 'important');
      }
    }
  } catch (e) {}

  const blocker = document.getElementById('mobileBlocker');
  const btnClose = document.getElementById('btnBlockerClose');
  const btnContinue = document.getElementById('btnBlockerContinue');

  if (btnClose) {
    btnClose.addEventListener('click', dismissMobileBlocker);
    btnClose.addEventListener('touchend', (e) => { e.preventDefault(); dismissMobileBlocker(); });
  }

  if (btnContinue) {
    btnContinue.addEventListener('click', dismissMobileBlocker);
    btnContinue.addEventListener('touchend', (e) => { e.preventDefault(); dismissMobileBlocker(); });
  }

  if (blocker) {
    blocker.addEventListener('click', (e) => {
      if (e.target === blocker) dismissMobileBlocker();
    });
    blocker.addEventListener('touchend', (e) => {
      if (e.target === blocker) { e.preventDefault(); dismissMobileBlocker(); }
    });
  }
});

/* ─────────────────────────────────────────────────────────────────
   LESSON / DEFAULT CODE SNIPPETS
───────────────────────────────────────────────────────────────── */
const LESSONS = {
  variables: `# 1. Python Variables & Live Inline Evaluation
x = 10
b = x + 1
print(f"x = {x}, b = {b}")

name = "Kashinath"
age = 22
age = age + 1
`,
  lists: `# 2. Lists & Append Allocation
skills = ["Python", "Django"]
print("Initial Skills:", skills)

skills.append("JavaScript")
skills.append("PostgreSQL")
print("Updated Skills:", skills)
`,
  functions: `# 3. Functions & Stack Frames
def calculate_stipend(base, bonus):
    total = base + bonus
    return total

company = "Google"
stipend = calculate_stipend(3000, 500)
print(f"Company: {company}, Stipend: \${stipend}")
`,
  twosum: `# 4. LeetCode Two Sum Algorithm
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in seen:
            return [seen[diff], i]
        seen[num] = i
    return []

numbers = [2, 7, 11, 15]
result = two_sum(numbers, 9)
print("Two Sum Result:", result)
`
};

const DEFAULT_CODE = {
  python: LESSONS.variables,

  javascript: `// JavaScript Variables & Memory
let name = "Kashinath";
let age = 22;
let skills = ["Python", "Django", "JS"];

// Update and log
age = age + 1;
skills.push("React");
console.log("Name:", name, "| Age:", age);
console.log("Skills:", skills.join(", "));

// Function & call stack demo
function greet(person) {
  let message = "Hello, " + person + "!";
  return message;
}

let result = greet(name);
console.log(result);
`,

  java: `// Java Variables & Memory
public class Main {
    public static void main(String[] args) {
        String name = "Kashinath";
        int age = 22;
        double gpa = 3.9;
        boolean isStudent = true;

        // Update age
        age = age + 1;
        System.out.println("Student: " + name + ", Age: " + age);

        // Call a method
        int stipend = calculateStipend(3000, 500);
        System.out.println("Stipend: $" + stipend);
    }

    static int calculateStipend(int base, int bonus) {
        int total = base + bonus;
        return total;
    }
}
`
};

/* ─────────────────────────────────────────────────────────────────
   THEME ENGINE
   Maps each theme key to Monaco base + color config.
   Must stay in sync with debugger.css palettes.
───────────────────────────────────────────────────────────────── */
const THEME_CONFIGS = {
  'light-blue':     { base: 'vs',      bg: '#FCFDFF', fg: '#1E293B', lineHighlight: '#EFF6FF',  lineNo: '#64748B' },
  'vscode-dark':    { base: 'vs-dark', bg: '#1E1E1E', fg: '#D4D4D4', lineHighlight: '#2A2D2E',  lineNo: '#858585' },
  'github-dark':    { base: 'vs-dark', bg: '#0D1117', fg: '#C9D1D9', lineHighlight: '#161B22',  lineNo: '#8B949E' },
  'github-light':   { base: 'vs',      bg: '#FFFFFF', fg: '#24292F', lineHighlight: '#F6F8FA',  lineNo: '#57606A' },
  'nord':           { base: 'vs-dark', bg: '#2E3440', fg: '#ECEFF4', lineHighlight: '#3B4252',  lineNo: '#D8DEE9' },
  'ocean-blue':     { base: 'vs-dark', bg: '#0F172A', fg: '#F8FAFC', lineHighlight: '#1E293B',  lineNo: '#94A3B8' },
  'emerald':        { base: 'vs',      bg: '#ECFDF5', fg: '#064E3B', lineHighlight: '#DCFCE7',  lineNo: '#047857' },
  'sunset':         { base: 'vs',      bg: '#FFFBEB', fg: '#7C2D12', lineHighlight: '#FFEDD5',  lineNo: '#C2410C' },
  'purple-pro':     { base: 'vs',      bg: '#F3E8FF', fg: '#4C1D95', lineHighlight: '#E9D5FF',  lineNo: '#6D28D9' },
  'midnight':       { base: 'vs-dark', bg: '#020617', fg: '#F8FAFC', lineHighlight: '#0F172A',  lineNo: '#94A3B8' },
  'dracula':        { base: 'vs-dark', bg: '#282A36', fg: '#F8F8F2', lineHighlight: '#343746',  lineNo: '#6272A4' },
  'solarized-dark': { base: 'vs-dark', bg: '#002B36', fg: '#839496', lineHighlight: '#073642',  lineNo: '#586E75' },
  'monokai':        { base: 'vs-dark', bg: '#272822', fg: '#F8F8F2', lineHighlight: '#2E2F2A',  lineNo: '#75715E' },
  'catppuccin':     { base: 'vs-dark', bg: '#1E1E2E', fg: '#CDD6F4', lineHighlight: '#313244',  lineNo: '#6C7086' },
  'rose-pine':      { base: 'vs-dark', bg: '#191724', fg: '#E0DEF4', lineHighlight: '#26233A',  lineNo: '#6E6A86' },
};

function defineMonacoThemes() {
  for (const [key, cfg] of Object.entries(THEME_CONFIGS)) {
    monaco.editor.defineTheme('theme-' + key, {
      base: cfg.base,
      inherit: true,
      rules: [
        { token: 'comment', fontStyle: 'italic' },
        { token: 'keyword', fontStyle: 'bold'   }
      ],
      colors: {
        'editor.background':              cfg.bg,
        'editor.foreground':              cfg.fg,
        'editor.lineHighlightBackground': cfg.lineHighlight,
        'editorLineNumber.foreground':    cfg.lineNo,
        'editorGutter.background':        cfg.bg
      }
    });
  }
}

function changeTheme(themeKey) {
  if (!THEME_CONFIGS[themeKey]) themeKey = 'light-blue';
  document.documentElement.setAttribute('data-theme', themeKey);
  localStorage.setItem('debugger_theme', themeKey);

  const selector = document.getElementById('themeSelector');
  if (selector && selector.value !== themeKey) selector.value = themeKey;

  if (window.monaco && monaco.editor) {
    monaco.editor.setTheme('theme-' + themeKey);
  }
}

/* Restore theme immediately before DOM is ready */
(function restoreTheme() {
  const saved = localStorage.getItem('debugger_theme') || 'light-blue';
  document.documentElement.setAttribute('data-theme', saved);
  document.addEventListener('DOMContentLoaded', () => {
    const selector = document.getElementById('themeSelector');
    if (selector) selector.value = saved;
  });
})();

/* ─────────────────────────────────────────────────────────────────
   MONACO EDITOR INIT
───────────────────────────────────────────────────────────────── */
require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.38.0/min/vs' } });

require(['vs/editor/editor.main'], function () {
  defineMonacoThemes();
  const currentTheme = localStorage.getItem('debugger_theme') || 'light-blue';

  editor = monaco.editor.create(document.getElementById('monacoEditorContainer'), {
    value:              DEFAULT_CODE.python,
    language:           'python',
    theme:              'theme-' + currentTheme,
    automaticLayout:    true,
    fontSize:           currentFontSize,
    fontFamily:         'Consolas, Fira Code, monospace',
    glyphMargin:        true,
    lineNumbersMinChars: 3
  });

  /* ── Breakpoint toggle on gutter click ── */
  editor.onMouseDown(function (e) {
    if (e.target.type === monaco.editor.MouseTargetType.GUTTER_GLYPH_MARGIN) {
      toggleBreakpoint(e.target.position.lineNumber);
    }
  });

  /* ── Reset debug state when user edits code ── */
  editor.onDidChangeModelContent(() => {
    if (debugSteps.length > 0) {
      debugSteps = [];
      currentStepIdx = 0;
      activeDecorations = editor.deltaDecorations(activeDecorations, []);
      clearInlineValueHints();
      updateControls();
      const banner = document.getElementById('aiExplainBanner');
      if (banner) {
        banner.innerHTML = '✏️ <strong>Code Edited:</strong> Click <strong>Start Debugging</strong> to evaluate your new code line-by-line!';
      }
    }
  });
});

/* ─────────────────────────────────────────────────────────────────
   LESSON LOADER
───────────────────────────────────────────────────────────────── */
function loadLesson(key) {
  if (!LESSONS[key]) return;
  stopAutoPlay();
  editor.setValue(LESSONS[key]);
  debugSteps    = [];
  currentStepIdx = 0;
  updateControls();
}

/* ─────────────────────────────────────────────────────────────────
   BREAKPOINTS
───────────────────────────────────────────────────────────────── */
function toggleBreakpoint(line) {
  const idx = breakpoints.indexOf(line);
  if (idx > -1) breakpoints.splice(idx, 1);
  else breakpoints.push(line);
  updateBreakpointDecorations();
}

function updateBreakpointDecorations() {
  const decos = breakpoints.map(line => ({
    range:   new monaco.Range(line, 1, line, 1),
    options: { isWholeLine: false, glyphMarginClassName: 'breakpoint-glyph' }
  }));
  editor.deltaDecorations([], decos);
}

/* ─────────────────────────────────────────────────────────────────
   LANGUAGE SWITCHING
───────────────────────────────────────────────────────────────── */
function switchLanguage(lang) {
  currentLang = lang;

  document.querySelectorAll('.lang-tab-btn').forEach(btn => btn.classList.remove('active'));
  const idMap = { python: 'langPython', javascript: 'langJS', java: 'langJava' };
  document.getElementById(idMap[lang]).classList.add('active');

  const titleMap = { python: 'main.py', javascript: 'app.js', java: 'Main.java' };
  document.getElementById('editorFileTitle').innerHTML = `<img src="/static/images/icon-type.png" width="14" height="14" alt="File"> ${titleMap[lang]}`;

  if (editor) {
    monaco.editor.setModelLanguage(editor.getModel(), lang);
    editor.setValue(DEFAULT_CODE[lang] || '');
  }

  /* Reset debug state */
  debugSteps    = [];
  currentStepIdx = 0;
  breakpoints   = [];
  activeDecorations = editor ? editor.deltaDecorations(activeDecorations, []) : [];
  clearInlineValueHints();
  updateControls();

  const capLang = lang.charAt(0).toUpperCase() + lang.slice(1);
  document.getElementById('aiExplainBanner').innerHTML =
    `💡 <strong>Switched to ${capLang}:</strong> Code loaded! Set breakpoints then click <strong>Start Debugging</strong>.`;
  document.getElementById('variablesContainer').innerHTML =
    '<div style="color:#64748b;text-align:center;padding:12px;">Switch complete — run debugger to inspect variables.</div>';
  document.getElementById('callStackList').innerHTML =
    '<div style="color:#64748b;">Global Stack Frame (Idle)</div>';
  document.getElementById('stdoutConsole').textContent = 'Console output will appear here...';
}

/* ─────────────────────────────────────────────────────────────────
   FONT SIZE CONTROL
───────────────────────────────────────────────────────────────── */
function changeFontSize(delta) {
  currentFontSize = Math.min(24, Math.max(10, currentFontSize + delta));
  if (editor) editor.updateOptions({ fontSize: currentFontSize });
  document.getElementById('fontSizeLabel').textContent = currentFontSize;
}

/* ─────────────────────────────────────────────────────────────────
   LINE HIGHLIGHTING
───────────────────────────────────────────────────────────────── */
function highlightExecutingLines(currentLine, prevLine) {
  if (!editor) return;
  const decorations = [];

  if (prevLine && prevLine > 0 && prevLine !== currentLine) {
    decorations.push({
      range:   new monaco.Range(prevLine, 1, prevLine, 1),
      options: { isWholeLine: true, className: 'previous-executing-line' }
    });
  }

  if (currentLine && currentLine > 0) {
    decorations.push({
      range:   new monaco.Range(currentLine, 1, currentLine, 1),
      options: { isWholeLine: true, className: 'active-executing-line' }
    });
  }

  activeDecorations = editor.deltaDecorations(activeDecorations, decorations);
  if (currentLine && currentLine > 0) editor.revealLineInCenter(currentLine);
}

/* ─────────────────────────────────────────────────────────────────
   CLIENT-SIDE BROWSER TRACE CACHE ENGINE
   Stores execution trace steps in sessionStorage + localStorage so identical
   code snippets execute 0ms instantly from browser cache with zero server load.
───────────────────────────────────────────────────────────────── */
function getCacheKey(lang, codeStr, bps, stdinStr) {
  const sortedBps = [...bps].sort((a, b) => a - b).join(',');
  // Safe hash encoding for strings containing Unicode/newlines in loops
  let hash = 0;
  const str = `${lang}_${sortedBps}_${codeStr}_${stdinStr || ''}`;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash |= 0;
  }
  return `dbg_v6_cache_${hash}`;
}

function getTraceFromCache(lang, codeStr, bps, stdinStr) {
  try {
    const key = getCacheKey(lang, codeStr, bps, stdinStr);
    const cached = sessionStorage.getItem(key) || localStorage.getItem(key);
    if (cached) {
      return JSON.parse(cached);
    }
  } catch (err) {
    console.warn("Trace cache read error:", err);
  }
  return null;
}

function setTraceInCache(lang, codeStr, bps, stdinStr, data) {
  try {
    const key = getCacheKey(lang, codeStr, bps, stdinStr);
    const payload = JSON.stringify(data);
    sessionStorage.setItem(key, payload);
    localStorage.setItem(key, payload);
  } catch (err) {
    console.warn("Trace cache write error:", err);
  }
}

/* ─────────────────────────────────────────────────────────────────
   START DEBUGGING  (fetch trace from Django backend or Browser Cache)
───────────────────────────────────────────────────────────────── */
async function startDebugging() {
  stopAutoPlay();
  clearInlineValueHints();
  activeDecorations = editor ? editor.deltaDecorations(activeDecorations, []) : [];

  const code     = editor.getValue();
  const stdinVal = (document.getElementById('stdinInput') ? document.getElementById('stdinInput').value : '').trim();
  const banner   = document.getElementById('aiExplainBanner');

  // Check client-side browser cache first (0ms load, zero server requests!)
  const cachedTrace = getTraceFromCache(currentLang, code, breakpoints, stdinVal);
  if (cachedTrace && cachedTrace.status === 'success' && cachedTrace.steps.length > 0) {
    debugSteps     = cachedTrace.steps;
    currentStepIdx  = 0;
    goToStep(0);
    banner.innerHTML = `⚡ <strong>Instant Browser Cache Hit (0ms):</strong> Loaded trace locally with 0 server load!`;
    showToast(`Loaded trace instantly from browser cache!`, 'success');
    return;
  }

  banner.innerHTML = `⏳ <strong>${currentLang.toUpperCase()} Debugger Engine:</strong> AST validation & compiling memory steps...`;

  const endpointMap = {
    python:     '/debugger/api/python/trace/',
    javascript: '/debugger/api/javascript/trace/',
    java:       '/debugger/api/java/trace/'
  };
  const endpoint = endpointMap[currentLang];

  try {
    const response = await fetch(endpoint, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ code, breakpoints, stdin: stdinVal })
    });
    const data = await response.json();

    if (data.status === 'success' && data.steps.length > 0) {
      debugSteps    = data.steps;
      currentStepIdx = 0;
      // Save trace into browser cache for instant future replays
      setTraceInCache(currentLang, code, breakpoints, stdinVal, data);
      goToStep(0);
      showToast(`${currentLang.toUpperCase()} Debugger initialized & cached!`, 'success');
    } else {
      banner.innerHTML = `❌ <strong>Debugger Error:</strong> ${escapeHtml(data.message || 'Execution failed.')}`;
    }
  } catch (err) {
    banner.innerHTML = '❌ <strong>Error:</strong> Could not connect to Django Debugger Backend.';
  }
}

/* ─────────────────────────────────────────────────────────────────
   STEP CONTROLS
───────────────────────────────────────────────────────────────── */
function firstStep()  { if (debugSteps.length > 0) goToStep(0); }
function lastStep()   { if (debugSteps.length > 0) goToStep(debugSteps.length - 1); }
function prevStep()   { if (currentStepIdx > 0) goToStep(currentStepIdx - 1); }
function nextStep() {
  if (currentStepIdx < debugSteps.length - 1) goToStep(currentStepIdx + 1);
  else stopAutoPlay();
}

function toggleAutoPlay() {
  if (autoPlayTimer) {
    stopAutoPlay();
  } else {
    const btn = document.getElementById('btnAutoPlay');
    btn.innerHTML = '⏸ Pause';
    btn.style.background = '#eab308';
    autoPlayTimer = setInterval(() => {
      if (currentStepIdx < debugSteps.length - 1) nextStep();
      else stopAutoPlay();
    }, 1500);
  }
}

function stopAutoPlay() {
  if (autoPlayTimer) { clearInterval(autoPlayTimer); autoPlayTimer = null; }
  const btn = document.getElementById('btnAutoPlay');
  if (btn) { btn.innerHTML = '▶ Auto Play'; btn.style.background = ''; }
}

/* ─────────────────────────────────────────────────────────────────
   GO TO STEP  (renders everything for a given index)
───────────────────────────────────────────────────────────────── */
function goToStep(idx) {
  if (debugSteps.length === 0) return;
  currentStepIdx = Math.max(0, Math.min(idx, debugSteps.length - 1));

  const step     = debugSteps[currentStepIdx];
  const prevStep = currentStepIdx > 0 ? debugSteps[currentStepIdx - 1] : null;
  const prevLine = prevStep ? prevStep.line_number : null;

  highlightExecutingLines(step.line_number, prevLine);
  applyInlineValueHints(currentStepIdx);

  document.getElementById('aiExplainBanner').innerHTML =
    `💡 <strong>Line ${step.line_number}:</strong> ${escapeHtml(step.ai_explanation)}`;

  renderVariablesCards(step.variables);
  renderCallStack(step.stack_frames);
  document.getElementById('stdoutConsole').textContent =
    step.stdout || 'Console output will appear here...';

  updateControls();
}

/* ─────────────────────────────────────────────────────────────────
   INLINE VALUE HINTS
   Injects evaluated variable values as Monaco decorations on
   every line that has been executed up to the current step.
───────────────────────────────────────────────────────────────── */
function applyInlineValueHints(upToIdx) {
  if (!editor || !debugSteps || debugSteps.length === 0) return;
  const model = editor.getModel();
  if (!model) return;

  const totalLines = model.getLineCount();
  const lineHints  = {};  // lineNumber -> [{name, raw, changed}]

  for (let i = 0; i <= upToIdx; i++) {
    const s = debugSteps[i];
    if (!s || !s.variables) continue;

    const lineNo  = s.line_number;
    const prevS   = i > 0 ? debugSteps[i - 1] : null;
    const prevVars = prevS ? prevS.variables : {};

    const hints = [];
    for (const [name, vdata] of Object.entries(s.variables)) {
      if (name.startsWith('__')) continue;
      if (typeof vdata.raw === 'string' && vdata.raw.startsWith('<')) continue;

      const prevRaw   = prevVars[name] ? prevVars[name].raw : null;
      const isNew     = !(name in prevVars);
      const isChanged = prevRaw !== null && prevRaw !== vdata.raw;

      if (isNew || isChanged) {
        let displayVal = String(vdata.raw);
        if (displayVal.length > 60) displayVal = displayVal.slice(0, 58) + '…';
        hints.push({ name, raw: displayVal, changed: isChanged });
      }
    }

    if (hints.length > 0) lineHints[lineNo] = hints;
  }

  /* Build dynamic <style> tag for ::after pseudo-elements */
  let styleTag = document.getElementById('dynamicInlineHintStyles');
  if (!styleTag) {
    styleTag = document.createElement('style');
    styleTag.id = 'dynamicInlineHintStyles';
    document.head.appendChild(styleTag);
  }

  const cssRules = [];
  const newDecos = [];

  for (const [lineNoStr, hints] of Object.entries(lineHints)) {
    const lineNo = parseInt(lineNoStr);
    if (isNaN(lineNo) || lineNo < 1 || lineNo > totalLines) continue;

    const maxCol         = model.getLineMaxColumn(lineNo);
    const parts          = hints.map(h => `${h.name} = ${h.raw}`);
    const annotationText = '  ⇒  ' + parts.join('   ');
    const className      = `inline-hint-line-${lineNo}`;
    const hasChanged     = hints.some(h => h.changed);

    const color  = hasChanged ? '#ffffff'              : '#7dd3fc';
    const bg     = hasChanged ? '#2563eb'              : 'rgba(13,21,39,0.9)';
    const border = hasChanged ? '1px solid #60a5fa'   : '1px solid rgba(56,189,248,0.35)';
    const glow   = hasChanged ? '0 0 12px rgba(37,99,235,0.5)' : 'none';

    const rule = `.${className}::after { content: ${JSON.stringify(annotationText)}; color: ${color}; background: ${bg}; padding: 2px 10px; border-radius: 6px; margin-left: 16px; font-family: 'Consolas','Fira Code',monospace; font-style: italic; font-weight: 800; font-size: 12px; border: ${border}; box-shadow: ${glow}; display: inline-block; pointer-events: none; letter-spacing: 0.3px; }`;
    cssRules.push(rule);

    newDecos.push({
      range: new monaco.Range(lineNo, maxCol, lineNo, maxCol),
      options: {
        afterContentClassName: className,
        after: {
          content:                              annotationText,
          inlineClassName:                      hasChanged ? 'inline-value-changed' : 'inline-value-hint',
          inlineClassNameAffectsLetterSpacing:  false
        },
        stickiness: monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges
      }
    });
  }

  styleTag.textContent       = cssRules.join('\n');
  inlineValueDecorations     = editor.deltaDecorations(inlineValueDecorations, newDecos);
}

function clearInlineValueHints() {
  const styleTag = document.getElementById('dynamicInlineHintStyles');
  if (styleTag) styleTag.textContent = '';
  if (editor) inlineValueDecorations = editor.deltaDecorations(inlineValueDecorations, []);
}

/* ─────────────────────────────────────────────────────────────────
   RENDER VARIABLES CARDS
   Shows the complete value — no truncation. Long values wrap inside
   a scrollable block. Lists/dicts/arrays get an expand toggle.
───────────────────────────────────────────────────────────────── */
function renderVariablesCards(vars) {
  const container = document.getElementById('variablesContainer');
  const keys      = Object.keys(vars || {});

  if (keys.length === 0) {
    if (container) container.innerHTML = '<div style="color:#94a3b8;text-align:center;padding:20px;font-size:12px;">No variables initialized at this step.</div>';
    return;
  }

  const COLLAPSE_THRESHOLD = 60;
  let html = '';

  keys.forEach((k, cardIdx) => {
    const v         = vars[k];
    const changed   = v.is_changed ? 'changed' : '';
    const fullVal   = typeof v.value === 'object' ? JSON.stringify(v.value, null, 2) : String(v.raw ?? v.value);
    const isLong    = fullVal.length > COLLAPSE_THRESHOLD;

    const isObject = !v.is_primitive
                  || ['list', 'dict', 'array', 'object', 'tuple', 'set'].includes(v.type)
                  || (typeof v.type === 'string' && (v.type.endsWith('[]') || v.type.includes('.')))
                  || (v.mem_addr && v.mem_addr.includes('HEAP'))
                  || fullVal.startsWith('{')
                  || fullVal.startsWith('[');

    const cardId  = `varcard-${cardIdx}-${k}`;
    const blockId = `varval-${cardIdx}-${k}`;
    const btnId   = `varbtn-${cardIdx}-${k}`;

    let valueBlock;
    if (!isLong) {
      valueBlock = `
        <div style="text-align:right; display:flex; flex-direction:column; gap:4px; align-items:flex-end; max-width:55%;">
          <div class="var-val-text" style="font-size:13px; font-weight:900;
                      font-family:'Consolas','Fira Code',monospace; letter-spacing:0.3px;
                      word-break:break-all; white-space:pre-wrap;">${escapeHtml(fullVal)}</div>
          <span class="mem-pointer-tag">${escapeHtml(v.mem_addr)}</span>
        </div>`;
    } else {
      valueBlock = `
        <div style="display:flex; flex-direction:column; gap:4px; align-items:flex-end;">
          <span class="mem-pointer-tag">${escapeHtml(v.mem_addr)}</span>
          <button id="${btnId}"
            onclick="(function(){
              var b = document.getElementById('${blockId}');
              var btn = document.getElementById('${btnId}');
              var open = b.style.display !== 'none';
              b.style.display = open ? 'none' : 'block';
              btn.textContent  = open ? '+ expand' : '− collapse';
            })()"
            style="background:none; border:1px solid var(--border-subtle); border-radius:6px;
                   color:var(--accent); font-size:10px; font-weight:800; cursor:pointer;
                   padding:2px 8px; font-family:monospace; white-space:nowrap;">
            + expand
          </button>
        </div>`;
    }

    html += `
      <div class="var-pill-card ${changed}" id="${cardId}"
           style="flex-direction:column; align-items:stretch; gap:6px;">

        <!-- ── Header row: name + type + mem ── -->
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">
          <div style="display:flex; flex-direction:column; gap:2px; min-width:0;">
            <div class="var-name-text">${isObject ? '📦 ' : '⚡ '}${escapeHtml(k)}</div>
            <div class="var-type-text">
              type: <em class="var-type-em">${escapeHtml(v.type)}</em>
            </div>
          </div>
          ${valueBlock}
        </div>

        ${ isLong ? `
        <!-- ── Collapsible Internal Fields & Properties ── -->
        <div id="${blockId}" style="display:none; margin-top:4px;">
          <div style="font-size:10px; font-weight:800; color:var(--text-muted); margin-bottom:4px;">Internal Fields &amp; State:</div>
          <pre class="var-val-text" style="margin:0; padding:8px 10px;
                      background:var(--bg-app); border:1px solid var(--border-subtle);
                      border-radius:8px; font-size:11px; font-weight:600;
                      font-family:'Consolas','Fira Code',monospace;
                      white-space:pre-wrap; word-break:break-all;
                      max-height:200px; overflow-y:auto; line-height:1.6;">${escapeHtml(fullVal)}</pre>
        </div>` : '' }

      </div>
    `;
  });

  if (container) container.innerHTML = html;
}

/* ─────────────────────────────────────────────────────────────────
   RENDER CALL STACK FRAMES
───────────────────────────────────────────────────────────────── */
function renderCallStack(frames) {
  const list = document.getElementById('callStackList');

  if (!frames || frames.length === 0) {
    list.innerHTML = '<div style="color:#94a3b8;">Global Stack Frame (Idle)</div>';
    return;
  }

  let html = '';
  frames.forEach((f, idx) => {
    const isTop  = idx === frames.length - 1;
    const bg     = isTop ? 'linear-gradient(135deg,rgba(30,58,138,0.6),rgba(15,23,42,0.85))' : '#141e33';
    const border = isTop ? '#3b82f6' : '#23324d';
    const color  = isTop ? '#60a5fa' : '#94a3b8';
    const shadow = isTop ? '0 0 12px rgba(37,99,235,0.3)' : 'none';

    html += `
      <div style="padding:8px 14px;background:${bg};border:1px solid ${border};border-radius:10px;font-weight:700;color:${color};box-shadow:${shadow};font-family:'Consolas','Fira Code',monospace;font-size:12px;display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
        <span>${isTop ? '👉 ' : '↳ '}${escapeHtml(f)}</span>
        ${isTop ? '<span style="font-size:10px;color:#fff;background:#2563eb;padding:2px 8px;border-radius:5px;">Active</span>' : ''}
      </div>
    `;
  });

  list.innerHTML = html;
}

/* ─────────────────────────────────────────────────────────────────
   CONTROLS STATE UPDATE
───────────────────────────────────────────────────────────────── */
function updateControls() {
  const slider   = document.getElementById('timelineSlider');
  const hasSteps = debugSteps.length > 0;
  const isFirst  = currentStepIdx === 0;
  const isLast   = currentStepIdx === debugSteps.length - 1;

  slider.disabled = !hasSteps;
  slider.max      = Math.max(0, debugSteps.length - 1);
  slider.value    = currentStepIdx;

  document.getElementById('stepBadge').textContent =
    `Step ${hasSteps ? currentStepIdx + 1 : 0} / ${debugSteps.length}`;

  document.getElementById('btnFirst').disabled    = isFirst || !hasSteps;
  document.getElementById('btnPrev').disabled     = isFirst || !hasSteps;
  document.getElementById('btnNext').disabled     = isLast  || !hasSteps;
  document.getElementById('btnLast').disabled     = isLast  || !hasSteps;
  document.getElementById('btnAutoPlay').disabled = !hasSteps;
}

/* ─────────────────────────────────────────────────────────────────
   UTILITIES
───────────────────────────────────────────────────────────────── */
function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g,  '&amp;')
    .replace(/</g,  '&lt;')
    .replace(/>/g,  '&gt;')
    .replace(/"/g,  '&quot;');
}

