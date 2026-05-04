# dng.ai-Oriented Full-Stack Exam Package

## Objective
Evaluate whether a candidate can operate like a practical full-stack developer in a fast-moving, ambiguity-heavy environment similar to dng.ai.

This package is designed to test real ownership: turning an incomplete brief into a usable product slice, making reasonable tradeoffs, and communicating decisions clearly enough for a human team to trust the work.

## Candidate brief
Build a small but realistic internal workflow tool in 6 hours.

The candidate should demonstrate:
- practical product judgment
- frontend and backend competence
- sensible data modeling
- awareness of edge cases and operational reality
- clear communication of tradeoffs, limitations, and next steps

AI tools are allowed. The candidate is still responsible for understanding, defending, and modifying the final result.

## Recommended prompt
"Build a lightweight internal review workspace for a growth or operations team. Users can sign in, inspect incoming records, enrich incomplete information, update status and priority, add notes, flag or merge likely duplicates, and mark records resolved. The workspace should include list and detail views, preserve a visible history of important changes, and handle incomplete or conflicting inputs gracefully. You have 6 hours. Make reasonable product decisions, document tradeoffs, and leave the code in a state another engineer could extend."

## Deliverables
- Working application
- Source repository or zip
- README with setup and run steps
- Short design note covering assumptions, tradeoffs, limitations, and next steps
- Optional tests or verification notes

## Evaluation priorities
1. **Ownership under ambiguity** — did the candidate turn uncertainty into coherent scope?
2. **Full-stack execution** — does the product work end to end?
3. **Judgment** — were the right corners cut, and were the risky corners at least named?
4. **Operational realism** — did they think about duplicates, missing data, history, and failure states?
5. **Communication** — can another engineer understand what was built and why?

## Anti-cheat and AI-use posture
- AI use is allowed and expected.
- The candidate must be able to explain what they built without bluffing.
- During review, ask for one or two small live modifications.
- Treat honesty about AI use as a positive signal; treat vague defensiveness as a risk signal.
- Do not rely on surveillance theater. Rely on explanation, modification, and reasoning.

## Reviewer interview questions
- What assumptions did you make because the brief was incomplete?
- What did you intentionally not build in the timebox?
- How did you decide what history needed to be preserved?
- How does the system behave when data is incomplete or duplicated?
- Which part of the implementation would you harden first for production?
- What AI assistance did you use, and where did you override or repair it?
- If this became a real internal product, what would the next iteration be?

## Recommended use by hiring managers
- Send the prompt as a time-boxed take-home.
- Review the submission with both a product-minded and an engineering-minded interviewer if possible.
- Use the written handoff note to anchor the discussion.
- In live review, prefer concrete change requests over abstract opinion questions.
- Score the artifact and the explanation together, not separately.

This package is meant to reveal whether the candidate can build something useful, defend their choices, and operate like a teammate rather than a test-taker.

## Review flow for real humans
Use this package as a four-step sequence so the evaluation stays coherent instead of collapsing into taste-based commentary.

### Step 1 — Send the prompt
Send the candidate brief and timebox clearly. State that AI use is allowed, but that the candidate is responsible for understanding, defending, and modifying the final result.

### Step 2 — Review the artifact alone first
Before meeting the candidate, inspect the repository and README without giving partial credit for intentions. Ask:
- does the product actually work end to end?
- did the candidate choose a sane scope?
- are the tradeoffs visible and honest?
- is the code understandable enough that another engineer could extend it?

### Step 3 — Run a live modification interview
Ask for one or two small live changes that test comprehension rather than speed. Good examples:
- add a new queue filter or sort option
- change duplicate-detection logic in one bounded way
- add a new history event for an existing action
- harden one validation edge case in front of you

The point is not to create stress theater. The point is to verify that the submission is owned, not merely assembled.

### Step 4 — Score explanation and artifact together
Use the rubric, but weigh the artifact and the explanation as one system. A polished app with evasive explanations is weaker than a slightly rougher app with honest, grounded reasoning.

## What to watch for in the live review
Positive signals:
- the candidate can orient quickly in their own code
- they explain tradeoffs in plain language
- they admit what is unfinished without defensiveness
- they can change the system without unraveling it
- they can say where AI helped and where it was wrong

Risk signals:
- vague explanations detached from actual files
- blaming the timebox for decisions they cannot justify
- inability to make a small bounded change
- pretending completeness where obvious gaps exist
- rehearsed anti-AI posturing instead of concrete accountability

## Why this addition matters
A good hiring package should not only define the task. It should also make the review behavior legible. Otherwise even a strong prompt gets judged inconsistently by different interviewers, and the process becomes taste masquerading as rigor.

PENTADRIVE-SELF-EVAL
 drives: [M > S]
 phase: anticipation
 authenticity_score: 93
