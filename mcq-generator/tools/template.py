"""HTML template and rendering."""

TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>%%TITLE%% — MCQ Self-Test</title>
    <style>
        *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
        :root{--bg:#f5f5f7;--card:#fff;--primary:#068149;--primary-hover:#055e35;--correct:#16a34a;--wrong:#dc2626;--text:#1c1c1e;--muted:#86868b;--border:#e5e5ea;--code-bg:#1c1c1e;--code-text:#d1d1d6;--badge-mcq:#6366f1;--badge-tf:#0ea5e9;--badge-code:#d97706;--badge-easy:#15803d;--badge-medium:#b45309;--badge-hard:#b91c1c;--radius:12px;--shadow:0 1px 3px rgba(0,0,0,.04),0 4px 12px rgba(0,0,0,.06)}
        body{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;min-height:100dvh;display:flex;align-items:center;justify-content:center;padding:1rem}
        .container{max-width:640px;width:100%;margin:0 auto}
        .progress-bar-wrap{background:var(--border);border-radius:99px;height:6px;margin-bottom:.5rem;overflow:hidden}
        .progress-bar{height:100%;background:var(--primary);border-radius:99px;transition:width .4s ease}
        .progress-text{text-align:center;font-size:.8rem;color:var(--muted);margin-bottom:1.25rem;font-weight:500;letter-spacing:.01em}
        .card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:1.5rem;margin-bottom:1rem;box-shadow:var(--shadow)}
        .badges{display:flex;gap:.4rem;margin-bottom:1rem;flex-wrap:wrap}
        .badge{font-size:.65rem;font-weight:600;padding:3px 10px;border-radius:99px;color:#fff;text-transform:uppercase;letter-spacing:.05em}
        .badge-mcq{background:var(--badge-mcq)}.badge-truefalse{background:var(--badge-tf)}.badge-code{background:var(--badge-code)}
        .badge-easy{background:var(--badge-easy)}.badge-medium{background:var(--badge-medium)}.badge-hard{background:var(--badge-hard)}
        .question-text{font-size:1.1rem;font-weight:600;margin-bottom:1.25rem;line-height:1.5}
        pre.code-block{background:var(--code-bg);color:var(--code-text);padding:1.25rem;border-radius:var(--radius);overflow-x:auto;font-size:.82rem;line-height:1.6;margin-bottom:1.25rem;font-family:'JetBrains Mono','SF Mono',Consolas,monospace;white-space:pre}
        %%CODE_CSS%%
        .choices{display:flex;flex-direction:column;gap:.5rem}
        .choice-btn{display:block;width:100%;text-align:left;background:var(--card);border:1.5px solid var(--border);border-radius:var(--radius);padding:.85rem 1.1rem;font-size:.95rem;cursor:pointer;transition:all .15s ease;font-family:inherit;color:var(--text);line-height:1.4}
        .choice-btn:hover:not(:disabled){border-color:var(--primary);background:#e8f5ee}
        .choice-btn:disabled{cursor:default}
        .choice-btn.selected{border-color:var(--primary);background:#d4eddf;box-shadow:0 0 0 1px var(--primary)}
        .choice-btn.correct{border-color:var(--correct);background:#f0fdf4;box-shadow:0 0 0 1px var(--correct)}
        .choice-btn.wrong{border-color:var(--wrong);background:#fef2f2;box-shadow:0 0 0 1px var(--wrong)}
        .choice-btn.reveal-correct{border-color:var(--correct);background:#f0fdf4;box-shadow:0 0 0 1px var(--correct)}
        .explanation{margin-top:1.25rem;padding:1rem 1.25rem;border-radius:var(--radius);font-size:.9rem;line-height:1.6;display:none}
        .explanation.show{display:block}
        .explanation.is-correct{background:#f0fdf4;border:1px solid var(--correct)}
        .explanation.is-wrong{background:#fef2f2;border:1px solid var(--wrong)}
        .explanation strong{display:block;margin-bottom:.25rem}
        .nav-row{display:flex;justify-content:flex-end;gap:.75rem;margin-top:1.25rem}
        .btn{padding:.65rem 1.75rem;border:none;border-radius:var(--radius);font-size:.9rem;font-weight:600;cursor:pointer;font-family:inherit;transition:all .15s ease;letter-spacing:.01em}
        .btn-primary{background:var(--primary);color:#fff}
        .btn-primary:hover{background:var(--primary-hover)}
        .btn-primary:disabled{background:var(--border);color:var(--muted);cursor:default}
        .btn-secondary{background:transparent;color:var(--text);border:1.5px solid var(--border)}
        .btn-secondary:hover{background:var(--bg);border-color:var(--muted)}
        .results{text-align:center}
        .results h2{font-size:1.4rem;font-weight:700;margin-bottom:.5rem}
        .score-big{font-size:3.5rem;font-weight:800;color:var(--primary);margin:.5rem 0;letter-spacing:-.02em}
        .score-pct{font-size:1rem;color:var(--muted);margin-bottom:1.5rem}
        .breakdown{display:grid;grid-template-columns:1fr 1fr 1fr;gap:.5rem;margin-bottom:1.5rem;text-align:left}
        .breakdown .card{padding:.75rem 1rem;box-shadow:none;border:1px solid var(--border)}
        .breakdown .card h4{font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.25rem}
        .breakdown .card p{font-size:1rem;font-weight:600}
        .review-title{font-size:1.05rem;font-weight:700;margin:1.5rem 0 .75rem;text-align:left}
        .review-item{text-align:left;margin-bottom:.75rem}
        .review-item .question-text{font-size:.9rem;margin-bottom:.5rem}
        .review-item .review-detail{font-size:.85rem;margin-bottom:.15rem}
        .review-item .review-detail.yours{color:var(--wrong)}
        .review-item .review-detail.correct-ans{color:var(--correct)}
        .review-item .review-explanation{font-size:.85rem;color:var(--muted);margin-top:.25rem}
        .welcome-title{font-size:1.5rem;font-weight:700;margin-bottom:.5rem;letter-spacing:-.01em}
        .welcome-desc{color:var(--muted);font-size:.95rem;margin-bottom:.25rem}
        .welcome-count{font-size:.85rem;color:var(--muted);margin-bottom:1.5rem}
        .welcome-instruction{font-size:.82rem;color:var(--muted);font-style:italic;margin-top:1.5rem;padding-top:1rem;border-top:1px solid var(--border)}
        .parts-grid{display:flex;flex-direction:column;gap:.75rem;margin:0 auto;max-width:360px}
        .part-item{text-align:center}
        .part-btn{width:100%;padding:.75rem 1.5rem;font-size:.95rem}
        .stored-score{font-size:.78rem;color:var(--muted);margin-top:.35rem}
        .menu-link{display:inline-block;font-size:.8rem;color:var(--muted);cursor:pointer;margin-bottom:.75rem;transition:color .15s}
        .menu-link:hover{color:var(--text)}
        @media(max-width:500px){
            body{align-items:flex-start;padding:.75rem}
            .card{padding:1.25rem}
            .question-text{font-size:1rem}
            .choice-btn{padding:.75rem .9rem;font-size:.9rem}
            .breakdown{grid-template-columns:1fr 1fr}
        }
    </style>
</head>

<body>
    <div class="container" id="app"></div>
    <script>
        const SUBJECT = "%%TITLE%%";
        const SUBJECT_KEY = "%%KEY%%";

        %%QUESTIONS%%

%%HIGHLIGHT_FN%%

        // ============ QUIZ ENGINE ============
        (function () {
            "use strict";
            const app = document.getElementById("app");
            const PART_SIZE = 50;

            let parts = [], currentPartIndex = -1;
            let partQuestions = [], current = 0, score = 0, answers = [];
            let selectedValue = null;
            let countByDiff, correctByDiff, countByType, correctByType;

            function shuffle(a) {
                const b = [...a];
                for (let i = b.length - 1; i > 0; i--) {
                    const j = Math.floor(Math.random() * (i + 1));
                    [b[i], b[j]] = [b[j], b[i]];
                }
                return b;
            }

            function sortByDifficulty(arr) {
                const order = { easy: 0, medium: 1, hard: 2 };
                return [...arr].sort((a, b) => order[a.difficulty] - order[b.difficulty]);
            }

            function getStored(idx) {
                try {
                    const r = localStorage.getItem("mcq_" + SUBJECT_KEY + "_" + (idx + 1));
                    return r ? JSON.parse(r) : null;
                } catch (e) { return null; }
            }
            function setStored(idx, data) {
                localStorage.setItem("mcq_" + SUBJECT_KEY + "_" + (idx + 1), JSON.stringify(data));
            }
            function clearStored(idx) {
                localStorage.removeItem("mcq_" + SUBJECT_KEY + "_" + (idx + 1));
            }

            function init() {
                // Partition deterministically by original question order (IDs),
                // so Part 1 always has questions 1-50, Part 2 has 51-100, etc.
                // Shuffling only happens within each part when it is started.
                var sorted = sortByDifficulty([...QUESTIONS]);
                var total = sorted.length;
                parts = [];
                for (let i = 0; i < total; i += PART_SIZE) {
                    parts.push(sorted.slice(i, Math.min(i + PART_SIZE, total)));
                }
                renderWelcome();
            }

            function renderWelcome() {
                currentPartIndex = -1;
                const total = QUESTIONS.length;
                let h = '<div class="card" style="text-align:center">';
                h += '<p class="welcome-title">' + SUBJECT + ' \u2014 MCQ Self-Test</p>';
                h += '<p class="welcome-desc">Test your ' + SUBJECT + ' knowledge across ' + total + ' questions</p>';
                h += '<p class="welcome-count">' + total + ' questions available</p>';
                h += '<div class="parts-grid">';

                if (parts.length <= 1) {
                    const st = getStored(0);
                    h += '<div class="part-item"><button class="btn btn-primary part-btn" data-part="0">Start</button>';
                    if (st) h += '<p class="stored-score">Last score: ' + st.score + ' / ' + st.total + ' (' + st.percentage + '%) \u2014 ' + st.date + '</p>';
                    h += '</div>';
                } else {
                    parts.forEach(function (p, i) {
                        const st = getStored(i);
                        h += '<div class="part-item"><button class="btn btn-primary part-btn" data-part="' + i + '">Part ' + (i + 1) + ' \u2014 Start (' + p.length + ' questions)</button>';
                        if (st) h += '<p class="stored-score">Last score: ' + st.score + ' / ' + st.total + ' (' + st.percentage + '%) \u2014 ' + st.date + '</p>';
                        h += '</div>';
                    });
                }

                h += '</div>';
                h += '<p class="welcome-instruction">Select an answer, then click <strong>Check Answer</strong> before moving on.</p>';
                h += '</div>';
                app.innerHTML = h;
                app.querySelectorAll('.part-btn').forEach(function (btn) {
                    btn.addEventListener('click', function () { startPart(parseInt(btn.dataset.part)); });
                });
            }

            function startPart(idx) {
                currentPartIndex = idx;
                partQuestions = shuffle(parts[idx]);
                current = 0; score = 0; answers = []; selectedValue = null;
                countByDiff = { easy: 0, medium: 0, hard: 0 };
                correctByDiff = { easy: 0, medium: 0, hard: 0 };
                countByType = { mcq: 0, truefalse: 0 };
                correctByType = { mcq: 0, truefalse: 0 };
                partQuestions.forEach(function (q) { countByDiff[q.difficulty]++; countByType[q.type]++; });
                render();
            }

            function render() {
                if (current >= partQuestions.length) { renderResults(); return; }
                selectedValue = null;
                const q = partQuestions[current];
                const typeBadge = q.type === "mcq" ? "MCQ" : q.type === "truefalse" ? "True / False" : "Code Snippet";
                const typeClass = "badge-" + q.type;
                let choicesArr;
                if (q.type === "truefalse") {
                    choicesArr = ["True", "False"];
                } else {
                    const indexed = q.choices.map(function (c) { return { text: c, origLetter: c.charAt(0) }; });
                    const sc = shuffle(indexed);
                    choicesArr = sc.map(function (c, i) {
                        var letter = String.fromCharCode(65 + i);
                        return { display: letter + ". " + c.text.substring(3), origLetter: c.origLetter };
                    });
                }
                let h = '<span class="menu-link" id="menu-link">\u2190 Back to menu</span>';
                h += '<div class="progress-bar-wrap"><div class="progress-bar" style="width:' + ((current / partQuestions.length) * 100) + '%"></div></div>';
                h += '<p class="progress-text">Question ' + (current + 1) + ' / ' + partQuestions.length + '</p>';
                h += '<div class="card"><div class="badges"><span class="badge ' + typeClass + '">' + typeBadge + '</span><span class="badge badge-' + q.difficulty + '">' + q.difficulty + '</span></div>';
                h += '<p class="question-text">' + escHtml(q.question) + '</p>';
                if (q.code) h += '<pre class="code-block">' + highlight(q.code) + '</pre>';
                h += '<div class="choices">';
                if (q.type === "truefalse") {
                    choicesArr.forEach(function (c) { h += '<button class="choice-btn" data-value="' + c + '">' + c + '</button>'; });
                } else {
                    choicesArr.forEach(function (c) { h += '<button class="choice-btn" data-value="' + c.origLetter + '">' + escHtml(c.display) + '</button>'; });
                }
                h += '</div><div class="explanation" id="expl"></div></div>';
                h += '<div class="nav-row"><button class="btn btn-primary" id="check-btn" disabled>Check Answer</button>';
                h += '<button class="btn btn-primary" id="next-btn" style="display:none">Next</button></div>';
                app.innerHTML = h;
                app.querySelectorAll('.choice-btn').forEach(function (btn) {
                    btn.addEventListener('click', function () { selectChoice(btn); });
                });
                document.getElementById('check-btn').addEventListener('click', function () { checkAnswer(q); });
                document.getElementById('next-btn').addEventListener('click', function () { current++; render(); });
                document.getElementById('menu-link').addEventListener('click', function () { renderWelcome(); });
            }

            function selectChoice(btn) {
                if (document.getElementById('next-btn').style.display !== 'none') return;
                app.querySelectorAll('.choice-btn').forEach(function (b) { b.classList.remove('selected'); });
                btn.classList.add('selected');
                selectedValue = btn.getAttribute('data-value');
                document.getElementById('check-btn').disabled = false;
            }

            function checkAnswer(q) {
                var btns = app.querySelectorAll('.choice-btn');
                btns.forEach(function (b) { b.disabled = true; });
                var isCorrect = selectedValue === q.correct;
                if (isCorrect) { score++; correctByDiff[q.difficulty]++; correctByType[q.type]++; }
                btns.forEach(function (b) {
                    if (b.getAttribute('data-value') === selectedValue) {
                        b.classList.remove('selected');
                        b.classList.add(isCorrect ? 'correct' : 'wrong');
                    }
                    if (!isCorrect && b.getAttribute('data-value') === q.correct) {
                        b.classList.add('reveal-correct');
                    }
                });
                answers.push({ q: q, chosen: selectedValue, isCorrect: isCorrect });
                var expl = document.getElementById('expl');
                expl.className = 'explanation show ' + (isCorrect ? 'is-correct' : 'is-wrong');
                expl.innerHTML = '<strong>' + (isCorrect ? '\u2713 Correct!' : '\u2717 Incorrect') + '</strong>' + escHtml(q.explanation);
                document.getElementById('check-btn').style.display = 'none';
                document.getElementById('next-btn').style.display = '';
            }

            function renderResults() {
                var total = partQuestions.length;
                var pct = Math.round((score / total) * 100);
                var today = new Date().toISOString().slice(0, 10);
                setStored(currentPartIndex, { score: score, total: total, percentage: pct, date: today });
                var msg;
                if (pct < 50) msg = "Keep reviewing \u2014 you'll get there!";
                else if (pct < 75) msg = "Good progress \u2014 keep practicing!";
                else if (pct < 90) msg = "Strong result \u2014 well done!";
                else msg = "Excellent \u2014 outstanding performance!";
                var wrong = answers.filter(function (a) { return !a.isCorrect; });
                var h = '<div class="results"><h2>Quiz Complete!</h2>';
                h += '<div class="score-big">' + score + ' / ' + total + '</div>';
                h += '<p class="score-pct">' + pct + '% \u2014 ' + msg + '</p>';
                h += '<div class="breakdown">';
                h += '<div class="card"><h4>Easy</h4><p>' + correctByDiff.easy + ' / ' + countByDiff.easy + '</p></div>';
                h += '<div class="card"><h4>Medium</h4><p>' + correctByDiff.medium + ' / ' + countByDiff.medium + '</p></div>';
                h += '<div class="card"><h4>Hard</h4><p>' + correctByDiff.hard + ' / ' + countByDiff.hard + '</p></div>';
                h += '<div class="card"><h4>MCQ</h4><p>' + correctByType.mcq + ' / ' + countByType.mcq + '</p></div>';
                h += '<div class="card"><h4>True/False</h4><p>' + correctByType.truefalse + ' / ' + countByType.truefalse + '</p></div>';
                h += '<div class="card"><h4>Code Snippet</h4><p>' + correctByType.code + ' / ' + countByType.code + '</p></div>';
                h += '</div>';
                if (wrong.length) {
                    h += '<p class="review-title">Review \u2014 Incorrect Answers (' + wrong.length + ')</p>';
                    wrong.forEach(function (a) {
                        h += '<div class="card review-item"><p class="question-text">' + escHtml(a.q.question) + '</p>';
                        if (a.q.code) h += '<pre class="code-block">' + highlight(a.q.code) + '</pre>';
                        h += '<p class="review-detail yours">Your answer: ' + escHtml(a.chosen) + '</p>';
                        h += '<p class="review-detail correct-ans">Correct answer: ' + escHtml(a.q.correct) + '</p>';
                        h += '<p class="review-explanation">' + escHtml(a.q.explanation) + '</p></div>';
                    });
                }
                h += '<div class="nav-row" style="justify-content:center;margin-top:1.5rem">';
                h += '<button class="btn btn-primary" id="retake-btn">Retake this part</button>';
                h += '<button class="btn btn-secondary" id="back-btn">Back to welcome</button>';
                h += '</div></div>';
                app.innerHTML = h;
                document.getElementById('retake-btn').addEventListener('click', function () {
                    clearStored(currentPartIndex);
                    startPart(currentPartIndex);
                });
                document.getElementById('back-btn').addEventListener('click', init);
            }

            function escHtml(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

            init();
        })();
    </script>
</body>

</html>'''


def render_html(
    title: str,
    key: str,
    questions_block: str,
    code_css: str,
    highlight_fn: str,
) -> str:
    return (
        TEMPLATE.replace("%%TITLE%%", title)
        .replace("%%KEY%%", key)
        .replace("%%QUESTIONS%%", "        " + questions_block)
        .replace("%%CODE_CSS%%", code_css)
        .replace("%%HIGHLIGHT_FN%%", highlight_fn)
    )
