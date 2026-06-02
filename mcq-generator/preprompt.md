# MCQ Generation Preprompt

Copy the prompt below into an AI chat alongside your course content and `question_template.json` to generate quiz questions.

---

## Prompt

I'm providing two things:

1. A **JSON template** showing the exact output format
2. **Course content** in Markdown (may include Mermaid diagrams)

Generate **[N]** questions for the subject **"[SUBJECT]"** (use `subject_key: "[KEY]"` — lowercase, no spaces), based strictly on the course content provided.

### Output format

- Return a single valid JSON object matching the template structure exactly
- `id` values must be sequential starting from **[START_ID]**
- Remove all `_comment` fields from the output
- **Raw JSON only** — no markdown fences (` ``` `), no commentary, no explanations outside the JSON

### Question type distribution

Adjust these ratios depending on the subject:

| Type        | Format                              | Target % |
|-------------|-------------------------------------|----------|
| `mcq`       | 4 choices (A–D)                     | ~80%     |
| `truefalse` | True / False only                   | ~20%     |

### Difficulty distribution

| Level    | Target % |
|----------|----------|
| `easy`   | ~30%     |
| `medium` | ~50%     |
| `hard`   | ~20%     |

### Answer distribution

- Across all `mcq` and `code` questions: ~25% A, ~25% B, ~25% C, ~25% D
- For `truefalse`: roughly 50/50 True and False

### Quality rules

1. **Grounded in content** — every question must be directly answerable from the provided course material. Do not introduce outside knowledge.
2. **Plausible distractors** — wrong choices must be realistic mistakes a learner might make: off-by-one errors, confusing similar concepts, common misconceptions. No obviously absurd options.
3. **No meta-choices** — never use "All of the above", "None of the above", or "Both A and B".
4. **Choice format** — each choice starts with `A. `, `B. `, `C. `, or `D. ` followed by the complete answer text.
5. **Explanations** — each explanation must:
   - State why the correct answer is right
   - Explain why at least the most plausible distractor is wrong
6. **Code snippets** (for `type: "code"` only — skip if not applicable):
   - Minimal and self-contained, 5–15 lines max
   - Use `\n` for newlines inside the JSON string
   - Escape `<` as `\x3C` inside all string values to prevent HTML parsing issues
7. **No duplicates** — each question must test a distinct concept or angle

### Template

Template file added to the conversation

### Course content

Course file added to the conversation