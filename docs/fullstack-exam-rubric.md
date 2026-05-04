# Full-Stack Exam — Human Review Rubric

Use this rubric to evaluate whether a candidate operates like a real full-stack developer, not just someone who can assemble a demo.

## Scoring scale
- **1 — Weak**: major gaps, fragile reasoning, or unfinished essentials
- **2 — Below bar**: some signal, but not enough for confidence
- **3 — Acceptable**: solid baseline, would benefit from guidance
- **4 — Strong**: clearly capable, good judgment, dependable execution
- **5 — Excellent**: unusually strong signal, thoughtful, clear, and production-aware

## 1. Product thinking
Look for:
- sensible scope control
- clear assumptions where requirements were ambiguous
- useful workflow choices rather than feature sprawl
- awareness of what mattered most in the timebox

Questions:
- What did they intentionally leave out?
- Did they reduce complexity in a smart way?
- Do their assumptions improve the product or just avoid difficulty?

## 2. Frontend quality
Look for:
- coherent information hierarchy
- good interaction flow
- loading, empty, and error states
- responsive behavior
- accessibility basics
- maintainable component structure

Questions:
- Is the UI merely functional, or actually usable?
- Do edge states feel considered?
- Would another engineer want to continue from this frontend?

## 3. Backend quality
Look for:
- clear API design
- validation and data integrity
- reasonable data model
- security basics
- useful error handling
- understandable server structure

Questions:
- Are the endpoints shaped coherently?
- Did they validate inputs or trust everything?
- Does the persistence model fit the product?

## 4. Engineering judgment
Look for:
- explicit tradeoffs
- pragmatic architecture
- no obvious overengineering
- meaningful separation of concerns
- evidence they matched design to time constraints

Questions:
- Did they make the system more complicated than necessary?
- Are abstractions earned?
- Do choices reflect real-world judgment?

## 5. Reliability and debugging awareness
Look for:
- graceful failure handling
- basic tests or convincing manual verification
- clear awareness of failure modes
- code that is debuggable and inspectable

Questions:
- Where would this fail first in production?
- Did they acknowledge weak spots honestly?
- Can they reason about bugs or only happy paths?

## 6. Communication
Look for:
- concise setup instructions
- readable README or handoff note
- honest discussion of limitations
- ability to explain choices during review

Questions:
- Can they defend their architecture without bluffing?
- Is the handoff useful to the next engineer?
- Do they communicate like a teammate?

## Decision guidance
- **Mostly 4s and 5s**: strong hire signal
- **Mostly 3s**: viable signal, depends on team needs and interview follow-up
- **Any 1 in a core area**: likely below bar unless there is strong compensating evidence
- **Strong artifact + weak explanation**: treat cautiously
- **Mediocre artifact + excellent explanation**: also treat cautiously

The point is alignment between what they built, why they built it that way, and how honestly they can discuss its limitations.
