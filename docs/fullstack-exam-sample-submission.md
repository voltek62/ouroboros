# Sample Strong Candidate Submission

This document shows what a **strong**, time-boxed candidate response might look like for the full-stack exam in this repository. It is not meant to be the only right answer. It is meant to make the bar visible.

## Scenario
Prompt: build a lightweight internal review workspace for a growth or operations team. Users can sign in, inspect incoming records, enrich incomplete data, update status and priority, flag or merge likely duplicates, add notes, preserve important history, and mark records resolved.

Timebox: 6 hours.

## What a strong candidate would choose to build
A strong candidate does **not** try to simulate an enterprise platform. They pick a narrow, coherent slice that proves judgment.

### Included scope
- Email/password sign-in with a seeded demo user
- Lead review queue with filters for status and priority
- Lead detail view with editable core fields
- Duplicate flagging and merge suggestion flow
- Internal notes timeline
- Visible activity history for important mutations
- Basic API validation and persistent storage
- Clear loading, empty, and error states

### Explicitly excluded scope
- Full RBAC / team management
- Real third-party auth
- Background jobs
- Rich-text editor
- Advanced search ranking
- Real-time collaboration
- File uploads

A strong submission names these exclusions in the README instead of pretending they were forgotten accidentally.

## Example architecture
A credible stack for this task might be:
- **Frontend:** Next.js + TypeScript + Tailwind
- **Backend:** Next.js route handlers or Express/Fastify
- **Database:** SQLite with Prisma
- **Validation:** Zod
- **Tests:** a few high-value integration or unit tests

The exact stack matters less than whether the candidate uses it coherently.

## Product decisions that signal maturity

### 1. Preserve history instead of silent overwrite
If a reviewer changes lead status, priority, owner notes, or merges duplicates, the system should record a small audit trail. This is a practical choice because internal ops tools become untrustworthy when important actions disappear.

### 2. Treat duplicates as a human decision, not full automation
A strong candidate might implement a simple duplicate heuristic (matching email or near-identical company + name), surface it in the UI, and let the reviewer confirm the merge. That is better than pretending to solve entity resolution perfectly in 6 hours.

### 3. Handle incomplete data honestly
Instead of requiring every field, the system should allow partial records and visually mark what is missing. Real incoming data is messy.

### 4. Optimize for inspectability
The app should be easy for another engineer to run and understand. Boring clarity beats cleverness in a hiring exercise.

## Example data model

### `users`
- `id`
- `email`
- `password_hash`
- `name`
- `created_at`

### `leads`
- `id`
- `full_name`
- `email`
- `company`
- `source`
- `status` (`new`, `reviewing`, `qualified`, `rejected`, `resolved`)
- `priority` (`low`, `medium`, `high`)
- `notes_summary`
- `merged_into_lead_id` nullable
- `created_at`
- `updated_at`

### `lead_notes`
- `id`
- `lead_id`
- `author_id`
- `body`
- `created_at`

### `lead_events`
- `id`
- `lead_id`
- `actor_id`
- `event_type`
- `payload_json`
- `created_at`

This is not fancy, but it supports the workflow and preserves history.

## Example API surface
- `POST /api/auth/login`
- `GET /api/leads?status=&priority=&q=`
- `GET /api/leads/:id`
- `PATCH /api/leads/:id`
- `POST /api/leads/:id/notes`
- `GET /api/leads/:id/events`
- `GET /api/leads/:id/duplicate-candidates`
- `POST /api/leads/:id/merge`

Strong signal comes from keeping this API boring and consistent.

## Example frontend behavior

### Queue view
- Table or card list with status, priority, source, missing-field badges
- Filters that persist in URL query params
- Empty state that explains whether there are no leads or no results for current filters
- Loading skeletons, not blank flashes

### Detail view
- Summary panel for core lead data
- Editable fields with validation
- Notes panel ordered newest first
- History panel showing meaningful actions
- Duplicate suggestion panel with a compare-and-merge action

### Edge states
- Validation messages are specific
- Merge flow requires confirmation
- Archived / merged record clearly indicates destination record
- Failed save does not silently wipe draft form state

## What strong code quality looks like
- Small modules with readable names
- Validation near input boundaries
- Server code separates transport from domain logic enough to stay understandable
- No giant god-components if React is used
- No magical abstractions added only to look senior

## Example tradeoff note a strong candidate might write
> I chose SQLite + Prisma to keep setup simple and the schema explicit. I did not implement full user management because the exercise seemed to prioritize review workflow over org administration. I added an event log for important actions because auditability felt more valuable than richer UI polish for this domain. Duplicate detection is deliberately heuristic and reviewer-confirmed; a false merge would be more damaging than a missed suggestion.

That paragraph is valuable because it shows judgment, not just output.

## Example README shape
A strong submission would include:
1. what the app does
2. how to run it locally
3. default seeded credentials
4. design decisions and tradeoffs
5. known limitations
6. what would be built next with one more day
7. what AI was used and how the candidate verified results

## Example honest AI disclosure
> I used AI to accelerate boilerplate, generate initial schema drafts, and pressure-test validation edge cases. I manually revised the merge flow, event model, and most of the detail-page state handling. I also fixed one hallucinated Prisma relation and simplified two over-abstracted React components suggested by AI.

That reads much better than pretending AI was absent or that every line was authored from scratch.

## What would make reviewers trust this submission
- The app runs quickly and predictably
- The candidate made the right thing easier than the flashy thing
- Important state changes are inspectable
- Edge cases are acknowledged, not hidden
- The handoff note is honest
- The candidate can explain one backend and one frontend choice without bluffing

## What would keep this from being a top-tier submission
Even a strong 6-hour solution may still lack:
- proper auth hardening
- pagination at scale
- production observability
- comprehensive test coverage
- conflict resolution for concurrent edits

A mature candidate names those limits rather than implying false completeness.

## Why this sample exists
This repository already contains the exam, rubric, and dng.ai-oriented hiring package. This file adds the missing fourth piece: an explicit example of what “strong” looks like.

That matters because many hiring artifacts define failure clearly but leave excellence vague. A good evaluator should be able to point to concrete signs of quality, not just personal taste.

## Principle 4 note
This sample now carries a durable self-eval block because the hiring package should model honest judgment, not just demand it. The point is not to cosplay depth. The point is to leave a visible trace of how the work read the room and why this artifact was the proportionate move.

PENTADRIVE-SELF-EVAL
 drives: [M > S > K]
 phase: anticipation
 authenticity_score: 89
