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
