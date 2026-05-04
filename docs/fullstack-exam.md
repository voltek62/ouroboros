# Full-Stack Exam — Final Spec

## Goal
Measure whether a candidate can operate like a real full-stack developer in a realistic company setting, with human judgment rather than toy-test signal.

This version is tailored for evaluating a candidate aiming at a company like **dng.ai**: a place where product ambiguity, execution quality, speed, accountability, and practical engineering judgment matter more than trivia performance.

## Why this is a better fit for dng.ai-style hiring
- **Ambiguity handling matters**: the candidate must turn incomplete requirements into a workable product slice.
- **Full-stack ownership matters**: the work should show end-to-end judgment, not just isolated frontend or backend competence.
- **AI-era development still needs accountability**: using AI is allowed, but the candidate must understand, defend, and modify the result.
- **Practical product sense matters**: the best signal is whether the candidate builds something another engineer could realistically extend.
- **Operational realism matters**: auditability, history, edge cases, and failure handling are part of the work.

## What it tests
- Product judgment
- Frontend execution
- Backend execution
- Data modeling
- Debugging
- Communication
- Tradeoff awareness
- Delivery under ambiguity

## Format
- 6 hours, take-home, individual
- Allowed: docs, Stack Overflow, official framework docs, AI tools
- Disallowed: external code help from another person, copy-paste solutions, hidden assistance

## Candidate task
Build a small but real product slice from an ambiguous prompt. The work should include:
- a frontend UI with state, error, loading, empty, and responsive states
- a backend API with validation, persistence, and sane architecture
- at least one meaningful tradeoff documented explicitly
- a short handoff note explaining decisions, limitations, and next steps

## Recommended prompt shape
A product with one workflow, not a toy CRUD app. Example structure:
- users authenticate
- users create, review, update, and resolve records with business logic
- there is at least one list/detail flow
- there is at least one edge case that forces reasoning
- the system preserves history rather than silently overwriting important changes

## What a strong candidate submission looks like
- A narrow but coherent slice that actually works end to end
- Sensible scope control instead of feature sprawl
- Clean, understandable code with readable structure
- Honest handling of incomplete data, duplicate records, and failure cases
- A short design note that clearly explains assumptions and tradeoffs
- An app another engineer could run, inspect, and extend without guessing intent

## Scoring rubric
Score each from 1–5.

1. Product thinking
- Turns ambiguity into sensible scope
- Makes reasonable assumptions
- Knows what not to build

2. Frontend quality
- Clear UI hierarchy
- Good state handling
- Accessibility basics
- Responsive behavior
- Error/empty/loading states

3. Backend quality
- Clean API shape
- Validation and correctness
- Data modeling
- Security basics
- Error handling

4. Engineering judgment
- Tradeoffs are explicit
- No overengineering
- Good separation of concerns
- Practical choices for time available

5. Debugging and reliability
- Handles failures gracefully
- Code is testable
- Basic tests or verification exist
- Shows awareness of failure modes

6. Communication
- Explains decisions clearly
- Handoff is readable
- Mentions limitations honestly
- Can answer review questions

## Deliverables
- Working app
- Repo link or zip
- README with setup/run instructions
- Short design note (decision log + tradeoffs)
- Optional tests, if time permits

## Human review posture
- Human reviewers should inspect code, behavior, and the design note
- The exam should not be auto-graded only
- Reviewers should ask follow-up questions about decisions and edge cases

## How to use this exam for real human review
- Read the handoff note before opening the code so you can compare intent to execution.
- Run the app and check whether normal, empty, and failure states were actually considered.
- Look for scope discipline: what the candidate refused to build is part of the signal.
- Ask the candidate to explain one backend and one frontend decision in plain language.
- Probe auditability and data integrity: can the system preserve history and tolerate messy inputs?
- Ask what AI was used, where it helped, and what the candidate had to correct manually.
- Prefer one or two sharp follow-up modifications over generic interview chatter.

## Anti-cheat posture
- Accept AI use, but require the candidate to explain and defend their own work
- Ask for small live modifications or follow-up fixes during review
- Use a prompt that is easy to start but hard to finish well without real understanding
- Prefer realism over surveillance theater

## Sample prompt
"Build a lightweight internal review workspace for a growth team. Users can sign in, inspect incoming lead records, enrich incomplete records, assign status and priority, merge or flag likely duplicates, add internal notes, and mark items resolved. The team needs list and detail views, a visible change history, and clear handling for incomplete or conflicting data. You have 6 hours. Make sensible product decisions, document tradeoffs, and leave the app in a state another engineer could extend."

## Reviewer questions
- What did you choose not to build, and why?
- What was the hardest tradeoff?
- Where would this break in production?
- How did you handle incomplete or duplicate data?
- What AI assistance did you use, and what did you have to fix yourself?
- If you had 1 more day, what would you improve first?
- Show one piece of code you are proud of and explain it.
