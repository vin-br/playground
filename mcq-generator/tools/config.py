"""Subject configuration: code-highlighting and known fixes.

Subjects are auto-detected from JSON input files (subject + subject_key fields).
Only subjects that need syntax highlighting for code snippets require an entry
in CODE_HIGHLIGHT below.  All other subjects get a no-op highlight function.
"""

# ── Code highlighting per subject key (optional) ─────────────────────────────
# Only needed for subjects whose questions include code snippets.

CODE_HIGHLIGHT: dict[str, dict[str, str]] = {
    "html": {
        "code_css": (
            "pre.code-block .kw{color:#b8a9f0}"
            "pre.code-block .str{color:#a6e3a1}"
            "pre.code-block .tag{color:#89b4fa}"
            "pre.code-block .attr{color:#f9e2af}"
            "pre.code-block .cm{color:#6c7086;font-style:italic}"
            "pre.code-block .num{color:#fab387}"
        ),
        "highlight": r"""
        function highlight(code){
            let s=escHtml(code);
            s=s.replace(/(\/\/[^\n]*)/g,'<span class="cm">$1</span>');
            s=s.replace(/(&lt;\/?[\w-]+)/g,'<span class="tag">$1</span>');
            s=s.replace(/(&gt;)/g,'<span class="tag">$1</span>');
            s=s.replace(/([\w-]+)(=)/g,'<span class="attr">$1</span>=');
            s=s.replace(/("(?:[^"\\]|\\.)*")/g,'<span class="str">$1</span>');
            return s;
        }""",
    },
    "css": {
        "code_css": (
            "pre.code-block .kw{color:#b8a9f0}"
            "pre.code-block .str{color:#a6e3a1}"
            "pre.code-block .prop{color:#89b4fa}"
            "pre.code-block .val{color:#f9e2af}"
            "pre.code-block .cm{color:#6c7086;font-style:italic}"
            "pre.code-block .sel{color:#f38ba8}"
            "pre.code-block .num{color:#fab387}"
            "pre.code-block .unit{color:#94e2d5}"
        ),
        "highlight": r"""
        function highlight(code){
            let s=escHtml(code);
            s=s.replace(/(\/\*[\s\S]*?\*\/)/g,'<span class="cm">$1</span>');
            s=s.replace(/(\/\/[^\n]*)/g,'<span class="cm">$1</span>');
            s=s.replace(/(&lt;\/?[\w-]+)/g,'<span class="sel">$1</span>');
            s=s.replace(/(&gt;)/g,'<span class="sel">$1</span>');
            s=s.replace(/([\w-]+)\s*:/g,'<span class="prop">$1</span>:');
            s=s.replace(/:\s*([^;}{]+)/g,': <span class="val">$1</span>');
            s=s.replace(/("(?:[^"\\]|\\.)*")/g,'<span class="str">$1</span>');
            return s;
        }""",
    },
    "javascript": {
        "code_css": (
            "pre.code-block .kw{color:#b8a9f0}"
            "pre.code-block .str{color:#a6e3a1}"
            "pre.code-block .num{color:#fab387}"
            "pre.code-block .cm{color:#6c7086;font-style:italic}"
            "pre.code-block .fn{color:#89b4fa}"
            "pre.code-block .op{color:#89dceb}"
        ),
        "highlight": r"""
        function highlight(code){
            let s=escHtml(code);
            s=s.replace(/(\/\/[^\n]*)/g,'<span class="cm">$1</span>');
            s=s.replace(/(\/\*[\s\S]*?\*\/)/g,'<span class="cm">$1</span>');
            s=s.replace(/\b(const|let|var|function|return|if|else|for|while|new|class|import|export|from|async|await|try|catch|finally|throw|typeof|instanceof|switch|case|break|default|this|true|false|null|undefined|of|in)\b/g,'<span class="kw">$1</span>');
            s=s.replace(/('(?:[^'\\]|\\.)*')/g,'<span class="str">$1</span>');
            s=s.replace(/(`(?:[^`\\]|\\.)*`)/g,'<span class="str">$1</span>');
            s=s.replace(/("(?:[^"\\]|\\.)*")/g,'<span class="str">$1</span>');
            s=s.replace(/\b(\d+\.?\d*)\b/g,'<span class="num">$1</span>');
            return s;
        }""",
    },
    "csharp": {
        "code_css": (
            "pre.code-block .kw{color:#b8a9f0}"
            "pre.code-block .str{color:#a6e3a1}"
            "pre.code-block .num{color:#fab387}"
            "pre.code-block .cm{color:#6c7086;font-style:italic}"
            "pre.code-block .fn{color:#89b4fa}"
            "pre.code-block .type{color:#f9e2af}"
        ),
        "highlight": r"""
        function highlight(code){
            let s=escHtml(code);
            s=s.replace(/(\/\/[^\n]*)/g,'<span class="cm">$1</span>');
            s=s.replace(/(\/\*[\s\S]*?\*\/)/g,'<span class="cm">$1</span>');
            s=s.replace(/\b(using|namespace|class|public|private|protected|internal|static|void|int|string|bool|double|decimal|float|var|new|return|if|else|for|foreach|while|switch|case|break|default|try|catch|finally|throw|async|await|abstract|virtual|override|sealed|interface|enum|struct|this|base|null|true|false|readonly|const|in|out|ref|is|as|typeof|get|set|where|select|from|orderby|ascending|descending|partial)\b/g,'<span class="kw">$1</span>');
            s=s.replace(/\b(List|Dictionary|Stack|Queue|IEnumerable|IQueryable|Task|ActionResult|IActionResult|DbContext|DbSet|Console|Math|String|DateTime|Object)\b/g,'<span class="type">$1</span>');
            s=s.replace(/("(?:[^"\\]|\\.)*")/g,'<span class="str">$1</span>');
            s=s.replace(/\b(\d+\.?\d*)\b/g,'<span class="num">$1</span>');
            return s;
        }""",
    },
}

# Default no-op highlight (for subjects without code snippets)
DEFAULT_CODE_CSS = ""
DEFAULT_HIGHLIGHT = r"""
        function highlight(code){ return escHtml(code); }"""


def get_highlight(key: str) -> tuple[str, str]:
    """Return (code_css, highlight_fn) for a subject key."""
    entry = CODE_HIGHLIGHT.get(key)
    if entry:
        return entry["code_css"], entry["highlight"]
    return DEFAULT_CODE_CSS, DEFAULT_HIGHLIGHT


# ── Known broken questions that need patching ────────────────────────────────

FIXES: dict[str, list[tuple[int, str]]] = {
    "mcq-html.html": [
        (41, '{ id: 41, type: "mcq", difficulty: "easy", question: "What is the correct way to write an HTML comment?", choices: ["A. // comment", "B. /* comment */", "C. \\x3C!-- comment --\\x3E", "D. # comment"], correct: "C", explanation: "HTML comments use the \\x3C!-- ... --\\x3E syntax. // and /* */ are JavaScript/CSS comment syntax. # is used in Python and shell scripts." },'),
    ],
    "mcq-css.html": [
        (6, '{ id: 6, type: "mcq", difficulty: "easy", question: "What is the correct way to add a CSS comment?", choices: ["A. // comment", "B. \\x3C!-- comment --\\x3E", "C. /* comment */", "D. # comment"], correct: "C", explanation: "CSS uses /* comment */ for comments. // is JavaScript, \\x3C!-- --\\x3E is HTML, and # is Python/shell. CSS does not support single-line comment syntax." },'),
    ],
    "mcq-javascript.html": [],
}

JS_REPLACEMENTS = [
    ('choices: ["A. <!-- comment -->"', 'choices: ["A. \\x3C!-- comment --\\x3E"'),
    ('<!-- --> is HTML', '\\x3C!-- --\\x3E is HTML'),
]
