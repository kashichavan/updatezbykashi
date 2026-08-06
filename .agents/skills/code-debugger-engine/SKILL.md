---
name: code-debugger-engine
description: >-
  Enterprise guide and architecture patterns for multi-language interactive code execution tracers (Python 3, JavaScript V8/Node, and Java 17 JVM) integrated with Monaco Code Editor.
  Use this skill when building step-by-step debuggers, live AST trace callbacks, inline variable value decorations, call stack visualizers, heap memory pointer tracking, and web IDE code execution sandboxes.
---

# Code Debugger Engine & Monaco IDE Integration Guide

This skill provides complete architectural patterns for building step-by-step interactive code execution debuggers across **Python 3**, **JavaScript (Node/V8)**, and **Java 17 (JVM)**, seamlessly integrated with **Monaco Editor** and **Django REST endpoints**.

---

## 1. Engine Overview & Multi-Language Tracing Architecture

```text
               ┌─────────────────────────────────────────┐
               │    Monaco Editor (Frontend IDE)         │
               │  - Line Highlights & Gutter Breakpoints │
               │  - Live Inline Value Badges (⇒ x = 10)   │
               └────────────────────┬────────────────────┘
                                    │ POST /debugger/api/{lang}/trace/
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      Django Debugger Backend Engine                    │
├─────────────────────────┬────────────────────────┬─────────────────────┤
│ 🐍 Python Tracing Engine│ ⚡ JS (Node/V8) Tracer  │ ☕ Java (JVM) Tracer│
│  - AST Validation       │  - Function Scoping    │  - Primitives/Heap  │
│  - sys.settrace Hook    │  - Call Stack Push/Pop │  - JVM Stack Frame  │
└─────────────────────────┴────────────────────────┴─────────────────────┘
```

---

## 2. Python 3 Execution Tracer (`PythonExecutionTracer`)

Uses Python `sys.settrace` and `ast` validation to trace execution line-by-line:

```python
import sys, io, ast, time

class PythonExecutionTracer:
    def __init__(self, code_str, breakpoints=None):
        self.code_str = code_str
        self.lines = code_str.splitlines()
        self.breakpoints = set(breakpoints or [])
        self.steps = []
        self.prev_variables = {}
        self.stdout_buffer = io.StringIO()

    def serialize_variable(self, val):
        val_type = type(val).__name__
        mem_addr = f"0x{id(val):x}"
        return {
            'type': val_type,
            'value': repr(val),
            'raw': str(val),
            'is_primitive': isinstance(val, (int, float, str, bool, type(None))),
            'mem_addr': mem_addr
        }

    def trace_callback(self, frame, event, arg):
        if frame.f_code.co_filename != '<string>':
            return self.trace_callback

        lineno = frame.f_lineno
        line_text = self.lines[lineno - 1].strip() if 1 <= lineno <= len(self.lines) else ""
        if not line_text:
            return self.trace_callback

        current_vars = {
            k: self.serialize_variable(v)
            for k, v in frame.f_locals.items()
            if not k.startswith('__')
        }

        # Mark new or changed variables
        changed_keys = [
            k for k, v in current_vars.items()
            if k not in self.prev_variables or self.prev_variables[k].get('raw') != v.get('raw')
        ]
        for k in current_vars:
            current_vars[k]['is_changed'] = k in changed_keys

        # Update previous step's post-execution variables
        if self.steps:
            self.steps[-1]['variables'] = current_vars

        self.prev_variables = {k: v for k, v in current_vars.items()}
        self.steps.append({
            'step_index': len(self.steps),
            'line_number': lineno,
            'line_text': line_text,
            'event_type': event,
            'variables': current_vars,
            'stdout': self.stdout_buffer.getvalue()
        })
        return self.trace_callback
```

---

## 3. Monaco Editor Integration & Live Inline Decorations

To render inline variable value badges (`⇒ x = 10`, `⇒ b = 11`) next to code lines in Monaco Editor:

```javascript
/**
 * Renders inline variable value annotations next to executed code lines in Monaco Editor
 */
function applyInlineValueHints(upToIdx) {
  if (!editor || !debugSteps || debugSteps.length === 0) return;

  const model = editor.getModel();
  if (!model) return;

  const totalLines = model.getLineCount();
  const lineHints = {};

  for (let i = 0; i <= upToIdx; i++) {
    const s = debugSteps[i];
    if (!s || !s.variables) continue;
    const lineNo = s.line_number;

    const prevS = i > 0 ? debugSteps[i - 1] : null;
    const prevVars = prevS ? prevS.variables : {};

    const hints = [];
    for (const [name, vdata] of Object.entries(s.variables)) {
      if (name.startsWith('__')) continue;
      const prevRaw = prevVars[name] ? prevVars[name].raw : null;
      const isNew     = !(name in prevVars);
      const isChanged = prevRaw !== null && prevRaw !== vdata.raw;

      if (isNew || isChanged) {
        let displayVal = String(vdata.raw);
        if (displayVal.length > 30) displayVal = displayVal.slice(0, 28) + '…';
        hints.push({ name, raw: displayVal, changed: isChanged });
      }
    }

    if (hints.length > 0) {
      lineHints[lineNo] = hints;
    }
  }

  // Inject dynamic CSS rules for ::after content
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

    const maxCol = model.getLineMaxColumn(lineNo);
    const parts = hints.map(h => `${h.name} = ${h.raw}`);
    const annotationText = '  ⇒  ' + parts.join('   ');
    const className = `inline-hint-line-${lineNo}`;

    const hasChanged = hints.some(h => h.changed);
    const color = hasChanged ? '#4ade80' : '#38bdf8';
    const bg = hasChanged ? 'rgba(74, 222, 128, 0.16)' : 'rgba(56, 189, 248, 0.14)';
    const border = hasChanged ? '1px solid rgba(74, 222, 128, 0.35)' : '1px solid rgba(56, 189, 248, 0.3)';

    const rule = `.${className}::after { content: ${JSON.stringify(annotationText)}; color: ${color}; background: ${bg}; padding: 1px 7px; border-radius: 5px; margin-left: 14px; font-family: 'Consolas', monospace; font-style: italic; font-weight: 700; font-size: 12px; border: ${border}; display: inline-block; pointer-events: none; }`;

    cssRules.push(rule);

    newDecos.push({
      range: new monaco.Range(lineNo, maxCol, lineNo, maxCol),
      options: {
        afterContentClassName: className,
        after: {
          content: annotationText,
          inlineClassName: hasChanged ? 'inline-value-changed' : 'inline-value-hint',
          inlineClassNameAffectsLetterSpacing: false
        },
        stickiness: monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges
      }
    });
  }

  styleTag.textContent = cssRules.join('\n');
  inlineValueDecorations = editor.deltaDecorations(inlineValueDecorations, newDecos);
}
```

---

## 4. Best Practices for Debugger Integration

1. **Always Use `model.getLineMaxColumn(lineNo)`**:
   Never use hardcoded column numbers (e.g. `9999`) when positioning Monaco decorations; use `model.getLineMaxColumn(lineNo)` so Monaco accepts the Range.
2. **Listen to Model Content Changes**:
   Register `editor.onDidChangeModelContent()` to clear old trace state whenever code is modified.
3. **Dual Decoration Rendering**:
   Pass both `afterContentClassName` (dynamic CSS `::after`) and `after: { content, inlineClassName }` to guarantee rendering across all browsers.
4. **Mark New Variables as Changed**:
   In backend tracers, check `if k not in prev_variables or prev_variables[k] != current_vars[k]` so new variable assignments (`x = 10`, `b = 11`) are highlighted instantly.
