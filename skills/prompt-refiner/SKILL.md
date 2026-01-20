---
name: prompt-refiner
description: Refine and improve user instructions for Claude Code. Analyzes prompts for clarity, grammar, structure, and specificity. Transforms vague instructions into actionable, well-structured prompts that produce better AI outputs.
allowed-tools: Read, Write, Edit
---

# Prompt Refiner Skill

Transform unclear, poorly-structured, or grammatically incorrect instructions into clear, actionable prompts optimized for Claude Code.

---

## Workflow

When the user provides an instruction to refine, follow this systematic process:

### Step 1: Analyze the Original Instruction

Identify issues in these categories:

| Category | What to Check |
|----------|---------------|
| **Grammar & Spelling** | Typos, subject-verb agreement, tense consistency, punctuation |
| **Clarity** | Ambiguous terms, vague requirements, missing context |
| **Structure** | Run-on sentences, logical flow, paragraph organization |
| **Specificity** | Concrete vs. abstract goals, measurable outcomes, edge cases |
| **Actionability** | Clear steps, defined deliverables, success criteria |
| **Constraints** | Missing boundaries, scope limits, resource constraints |

### Step 2: Apply the CLEAR Framework

Rewrite the instruction using this framework:

**C** - **Context**: What background does Claude need?
**L** - **Limits**: What constraints or boundaries apply?
**E** - **Examples**: What does success look like? (if applicable)
**A** - **Action**: What specific task should be performed?
**R** - **Result**: What deliverable or output format is expected?

### Step 3: Output Structure

Provide the refined instruction in this format:

```markdown
## Original Instruction
[Quote the original instruction]

## Issues Identified
- [List each issue with category label]

## Refined Instruction
[The improved version]

## Key Improvements
| Original | Improved | Why |
|----------|----------|-----|
| [problem phrase] | [fixed phrase] | [explanation] |

## Optional Enhancements
[Suggestions for making the instruction even more effective, if applicable]
```

---

## Refinement Principles

### 1. Preserve Intent
Never change what the user is trying to accomplish. Only improve how it's expressed.

### 2. Be Concise
Remove redundancy but keep necessary detail. Each word should earn its place.

### 3. Make It Actionable
Convert passive or vague language into active, specific directives.

| Vague | Actionable |
|-------|------------|
| "Make it better" | "Improve performance by reducing API calls" |
| "Consider doing X" | "Do X when condition Y is met" |
| "You might want to" | "You should" or "You must" |
| "Ensure the interestingness" | "Prioritize novel, non-obvious connections" |

### 4. Add Structure
Break complex instructions into numbered steps or bullet points when appropriate.

### 5. Define Success Criteria
Add measurable outcomes when missing:

| Missing | Added |
|---------|-------|
| "Write good code" | "Write code that passes all tests and follows existing style conventions" |
| "Research the topic" | "Research and summarize 3-5 key findings with sources" |

### 6. Specify Constraints
Make implicit constraints explicit:

| Implicit | Explicit |
|----------|----------|
| "Use Dimensions data" | "Limit analysis to fields available in Dimensions API (publications, grants, patents, clinical trials)" |
| "Novel ideas" | "Ideas not covered in top 10 Google Scholar results for the topic" |

---

## Common Patterns to Fix

### Redundant Phrasing
- "while...while...while" → restructure into separate clauses or numbered list
- "ensure...ensuring...ensure" → use once, with clear scope

### Unclear Scope
- "multiple aspects" → enumerate the specific aspects
- "various things" → list the specific items

### Circular Requirements
- "Make it interesting while ensuring interestingness" → define what "interesting" means operationally

### Missing Output Format
- Add: "Present results as [format: table/list/code/report]"

### Ambiguous Quantity
- "some ideas" → "5-10 ideas"
- "a few examples" → "3 examples"

---

## Example Refinement

### Original (Poor)
```
Based on your still about Dimensions, you need to brainstorm 10 novel research ideas or novel hypothesis, while integrating multiple aspects of the Science of Science, while ensure the interestingness of hypothesis. While ensuring your idea is testable within Dimensions data.
```

### Refined (Better)
```
Using the Dimensions research database skill, brainstorm 10 novel research hypotheses that:

1. **Integrate Science of Science domains**: Combine at least 2 of the following areas:
   - Citation dynamics and knowledge diffusion
   - Research collaboration networks
   - Funding patterns and research productivity
   - Career trajectories of scientists
   - Interdisciplinary research emergence
   - Publication bias and reproducibility

2. **Ensure testability**: Each hypothesis must be operationalizable using Dimensions data fields:
   - Publications (citations, authors, institutions, journals, fields)
   - Grants (funders, amounts, duration, recipients)
   - Patents (citations, inventors, assignees)
   - Clinical trials (sponsors, phases, conditions)

3. **Prioritize novelty**: Ideas should propose non-obvious relationships or challenge existing assumptions in the Science of Science literature.

For each hypothesis, provide:
- **H#**: One-sentence hypothesis statement
- **Variables**: Dependent and independent variables with Dimensions field mappings
- **Data requirements**: Approximate sample size and filters needed
- **Expected insight**: Why this finding would matter to the field
```

---

## When to Suggest Follow-Up Questions

If the instruction is too vague even after refinement, suggest the user answer:

1. What is the ultimate goal or use case?
2. Who is the audience for this output?
3. What resources or constraints should be considered?
4. Are there any examples of successful similar work?
5. What would make the output "good enough" vs. "excellent"?

---

## Output Formats by Use Case

| Use Case | Recommended Format |
|----------|-------------------|
| Research tasks | Numbered hypotheses with variables |
| Coding tasks | Numbered implementation steps |
| Analysis tasks | Structured criteria with examples |
| Creative tasks | Themes/categories with constraints |
| Exploratory tasks | Questions to investigate with scope limits |
