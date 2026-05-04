# Full-Stack Exam — Final Spec

## Goal
Measure whether a candidate can operate like a real full-stack developer in a realistic company setting, with human judgment rather than toy-test signal.

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
- users create/update/view an object with some business logic
- there is at least one list/detail flow
- there is at least one edge case that forces reasoning

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

## Anti-cheat posture
- Accept AI use, but require the candidate to explain and defend their own work
- Ask for small live modifications or follow-up fixes during review
- Use a prompt that is easy to start but hard to finish well without real understanding
- Prefer realism over surveillance theater

## Sample prompt
"Build a lightweight internal task-triage tool for a team. Users can sign in, view incoming items, assign priority, add notes, filter by status, and resolve items. The product has a few ambiguous rules: duplicates may exist, some items are incomplete, and the team wants to preserve history. You have 6 hours. Make sensible product decisions, document tradeoffs, and leave the app in a state another engineer could extend."

## Reviewer questions
- What did you choose not to build, and why?
- What was the hardest tradeoff?
- Where would this break in production?
- If you had 1 more day, what would you improve first?
- Show one piece of code you are proud of and explain it.
