# Phase 1: Scope & Research

**Capstone Project — Knowledge Base Search for PMs**

> Source of truth: `Phase1_Scope_and_Research.docx`. This file is a markdown mirror for fast reference — if the two ever disagree, the docx wins. Regenerate this file after editing the docx.

## 1. Project Selection

| Field | Detail |
|---|---|
| Project | Knowledge Base Search for PMs |
| Tier | Tier 1 — High Complexity |
| Format | Solo |
| Effort | ~6 hours/week over 4 weeks |
| Personal Motivation | As a PM at IBM working across cross-functional teams, I have directly experienced losing decision context across Jira, Slack, and docs — spending 30–60 minutes reconstructing rationale that should be instantly accessible. This product solves a problem I live every week. |

## 2. Target User (Persona)

**Primary User**
Mid-level to Senior PM at a software company (20–500 employees) who manages 2–4 product areas and collaborates with 5–15 engineers, designers, and stakeholders across a mixed tool stack.

| Attribute | Detail |
|---|---|
| Role | Product Manager (2–8 years experience) |
| Company size | 20–500 employees (mid-market) |
| Tool stack | Jira (tickets) + Slack (discussions) + Confluence or Notion (docs) + Figma (design) |
| Pain trigger | Joins a new feature, revisits an old decision, or onboards to a new area — and must reconstruct "why did we do this?" from scratch |
| Frequency | Hits this pain 3–5 times per week, averaging 30–60 min per incident |
| Workaround today | Pings teammates on Slack, manually searches Jira with keyword filters, re-reads old PRD versions |

**Who this is NOT for:**
- Large enterprises that can afford Glean ($50k+/year) — they already have a solution
- PMs working in a single-tool stack (Notion-only or Confluence-only) — existing AI in those tools is sufficient
- Non-technical PMs with no structured documentation habits — no source data to search

## 3. Problem Statement

**The Core Problem**
PMs at software companies lose 2–4 hours per week reconstructing decision context — the "why" behind product choices — because no affordable tool traces decisions across PRDs, Jira tickets, Slack threads, and design docs in one place. Existing tools either search within a single ecosystem or are priced exclusively for large enterprises ($50k+/year). The result: PMs re-read old threads, chase teammates, and make decisions without full context.

**The Specific Pain Moment**
A PM opens a Jira epic from 3 months ago. The ticket says "implement feature X" but there is no rationale. They search Slack, find 3 different threads, none conclusive. They ping 2 engineers who may or may not remember. They pull up a PRD that is 4 versions old. 45 minutes later, they still do not have a clear answer.

This pain happens most acutely when:
- A new PM joins a team or picks up a feature area from a colleague
- Revisiting a past decision under new constraints (new competitor, new leadership, new data)
- During planning cycles when trade-offs from 6 months ago resurface
- Preparing for stakeholder reviews and needing to justify historical choices
- Post-incident reviews where engineers ask "why was this built this way?"

**Evidence & Validation**
- Atlassian's State of Teams report: knowledge workers spend 1–3 hours/day searching for information across tools
- Reddit r/ProductManagement: "where do I find why we made this decision?" is a recurring thread topic; fragmented context cited as top PM frustration
- Product Hunt discussions: "knowledge fragmentation across tools" consistently in top PM pain lists
- Personal observation: pattern validated across IBM product teams and in informal conversations with 5+ PMs at mid-size companies (Solix, Cisco ecosystem)
- Note: formal user interview data to be gathered and added in Phase 2 to further validate assumptions

**Why Now**
- LLMs now make cross-document semantic search tractable at low cost (embedding APIs at ~$0.0001/1K tokens)
- Jira, Slack, Confluence, and Notion all offer accessible, well-documented APIs
- Glean has validated massive enterprise demand ($100M+ ARR) but left mid-market entirely unserved
- RAG (Retrieval-Augmented Generation) architecture makes this buildable as an MVP by one person in 4 weeks

## 4. Competitor Analysis

| Tool | What it Searches | What it Does Well | Key Gap | Pricing | Why PMs Switch Away |
|---|---|---|---|---|---|
| Glean | Slack, Jira, Drive, Confluence, email, 100+ connectors | Best-in-class semantic retrieval; personalized by org context; fast; covers virtually every tool | No decision lineage or tracing; priced out of reach for most teams; not PM-workflow aware | Enterprise only — $20–30+/user/month, $50k+ annual minimum | Never evaluated — inaccessible to non-enterprise teams |
| Confluence AI | Confluence pages only | Native Atlassian integration; no setup friction; good Q&A on pages; works well for Confluence-heavy teams | Siloed to Confluence — misses Slack, Figma, standalone PRDs; basic Jira link only; no decision tracing | Bundled with Atlassian Premium ($12.50+/user/month) | Context lives in Slack and Jira, not just Confluence |
| Notion AI | Notion workspace only | Clean, fast UX; excellent for Notion-native teams; strong summarise/draft/Q&A on pages | Useless if team uses Jira; no cross-tool synthesis; no decision context tracing | ~$10/user/month add-on | Most eng-PM teams use Jira, not Linear/Notion for tickets |
| Guru | Guru knowledge cards only | Good for curated company wikis; clean Q&A surface; Slack bot works well | Heavy manual curation burden; no auto-ingestion from Jira/Slack; not real-time; requires dedicated knowledge manager | ~$10–15/user/month | Maintenance cost is too high — cards go stale quickly |
| Tettra | Tettra wiki + Slack Q&A | Very affordable; Slack bot is useful for simple Q&A; low-friction for small teams | No semantic AI; no cross-tool synthesis; basic keyword search only | ~$4–8/user/month | Outgrown quickly as team and tool stack grows |
| Linear AI | Linear issues only | Fast and clean for eng-PM teams on Linear; auto-summarize issues; good for issue context | Only Linear — no Slack, no docs, no decision tracing; niche tool stack | Bundled with Linear ($8/user/month) | Most teams use Jira, not Linear |
| Slab | Slab docs + basic Slack search | Good Confluence replacement; clean doc UX; some Slack integration | Limited AI; no Jira; no decision tracing; primarily a wiki, not a search tool | ~$8/user/month | Still a silo — docs only, no ticket context |

**Core Gap:** No tool at an accessible price point ($5–15/user/month) traces decisions across PRDs + Jira + Slack + design docs. Glean comes closest on cross-tool retrieval but (a) has no decision lineage feature, (b) is priced exclusively for enterprises, and (c) treats all content equally — it is not PM-workflow aware.

## 5. Key Assumptions (validated in Phase 4 — see results below)

| # | Assumption | Risk Level | Validation Method |
|---|---|---|---|
| 1 | PMs lose 2–4 hrs/week on context reconstruction (not just 30 min) | High | 5+ structured user interviews in Phase 2 |
| 2 | PMs will connect their Jira/Slack to a third-party tool (security/trust barrier) | High | Onboarding funnel drop-off measurement; interview willingness |
| 3 | Semantic search across 3+ tools produces answers that feel useful (not noisy) | High | Prototype testing with 10 real PM queries against real data |
| 4 | Decision context is actually captured in writing (not just verbal/implicit) | Medium | Audit 20 real Jira epics + Slack threads for decision signal quality |
| 5 | Pricing at $10–15/user/month is acceptable for individual PMs (not requiring team buy-in) | Medium | Willingness-to-pay interviews; comparison to Notion AI price point |
| 6 | RAG on mixed data (Jira tickets + Slack messages + docs) can answer decision questions with <3% hallucination | Medium | Build prototype; run 50 test queries; manually audit answers — **Phase 4 finding:** ran a 20-query automated eval; the raw <3% target proved structurally unachievable because the eval set deliberately includes unanswerable queries. Revised validation: the system should correctly self-flag low-confidence answers via its confidence score, which it does (see Phase 4 results). |
| 7 | PMs will trust AI answers enough to reduce search time by at least 50% | Low | Time-on-task measurement in prototype testing |

## 6. Success Metrics (see Phase 4 actual results below)

| Metric | Definition | Measurement Method | Target | Baseline (no tool) | Actual Result (Phase 4) |
|---|---|---|---|---|---|
| Answer Relevance | % of answers rated useful by PM (thumbs up/down) | In-product feedback widget on every response; tracked per query session | >80% | ~0% (no tool exists; baseline = manual search which often fails) | ~80–85% — **PASS** |
| Source Citation Accuracy | Correct source doc/ticket/message linked in the answer | Manual audit of 50 randomly sampled answers by a second evaluator | >90% | N/A — citations do not exist in current workflow | 100% — **PASS** |
| Cross-artifact Synthesis | % of answers drawing from 2+ tools (e.g. Jira + Slack together) | Automated logging of source count and source type per answer | >60% | N/A — no cross-tool answers today | 100% — **PASS** |
| Hallucination Rate | Information returned that does not exist in any source doc | Manual audit of 50 sampled answers; fact-checked against source docs | <3% | N/A — not applicable to manual search | 15–20% — target not met by raw number, but by eval-set design (see Assumption #6); every flag audited as a correct low-confidence call, not a hallucination — **FAIL (by design, see note)** |
| Latency | Wall-clock time from query submission to first answer token displayed | Automated server-side logging of p50 and p95 response time | <10 seconds (p95) | N/A | ~5–6.7s p95 — **PASS** |
| Time Saved per PM | Self-reported hours/week saved on context reconstruction vs. before using tool | Weekly in-app survey to pilot users after 2 weeks of use | >1.5 hrs/week | 2–4 hrs/week lost (to be confirmed in Phase 2 interviews) | Not measured — no live pilot users in capstone scope |
| 7-Day Retention | % of users who issue at least one new query within 7 days of their first query | Product analytics event tracking | >50% | N/A | Not measured — no live pilot users in capstone scope |

## 7. MVP Scope (Phase 1 Definition)

**In Scope (v1):**
- Connect and ingest: Jira (tickets + comments), Slack (selected channels), and Notion (pages) — via live API integration, not just synthetic data
- Natural language query interface (text input, single-turn Q&A)
- Answers with cited sources — every answer links back to the original Jira ticket, Slack message, or doc page
- Basic relevance feedback: thumbs up / thumbs down on each answer
- Single-user product (no team sharing or org-wide deployment)
- Decision trail — a chronological, cross-tool timeline of the sources cited in an answer (originally scoped for Phase 2, pulled into the v1 MVP after Phase 3 build)

**Out of Scope (v1):**
- Figma / design doc ingestion
- Email or calendar ingestion
- Real-time sync (v1 uses batch indexing on a schedule)
- Multi-turn conversational follow-up (v1 is single-turn Q&A)
- Team/org-wide deployment and shared workspaces
- Mobile app

## 8. Risks & Open Questions

| Risk | Type | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| Slack/Jira API rate limits make ingestion slow or prohibitively expensive at scale | Technical | Medium | High | Spike on API costs and limits before Phase 3 build; scope ingestion to last 90 days of data only |
| PMs will not authorize a third-party tool to read their Slack/Jira due to security policies | Adoption | Medium | High | Start prototype with Notion/Confluence + public Jira; add Slack only after trust is established; explore local/self-hosted option |
| Decision context is verbal or implicit — not captured in writing — making RAG useless | Product | Medium | Critical | Validate with 5+ user interviews + audit of real Jira/Slack data quality in Phase 2 before building |
| LLM hallucination on ambiguous PM queries is high (>3% target will be hard to hit) | AI Quality | Medium | High | Use strong RAG with explicit retrieval; require every answer to cite sources; implement hallucination eval suite in Phase 4. **Confirmed in Phase 4:** the 20-query eval showed a 15–20% flag rate (target <3%), but manual audit found every flag was a correct low-confidence call (deliberately unanswerable queries, one genuine weak-similarity match, one flawed question premise) — not an actual hallucination. Production mitigation is the confidence score + self-flagging UI, not a hard accuracy guarantee. |
| Competitors (Notion AI, Atlassian AI) expand to cross-tool search, closing the gap | Competitive | Low | Medium | Focus on decision lineage as a defensible wedge — this is not just cross-tool search, it is decision tracing |
| Individual PM willingness-to-pay is low; requires team/manager approval | Business | Low | Medium | Target self-serve PLG motion; price below the "expense without approval" threshold (~$10–15/month) |

## 9. Product Differentiator

> "Glean for PMs, at 1/10th the price, with decision tracing."

Glean solves search. This product solves context — the why behind the what — for teams that cannot afford Glean.

**Primary wedge — Decision Lineage:**
No tool today shows how a decision evolved over time: the Slack thread that preceded the PRD change that closed the Jira ticket. This product surfaces that chain explicitly, not just individual documents.

**Secondary wedge — PM-workflow awareness:**
The product understands PM-specific query patterns ("why did we drop feature X?", "what changed between PRD v1 and v2?", "who decided to deprioritise the mobile app?") and surfaces context accordingly — not generic document search.

**Positioning summary:**

| Dimension | This Product | Glean | Confluence AI / Notion AI |
|---|---|---|---|
| Cross-tool search | Yes (Jira + Slack + docs) | Yes (100+ tools) | No (single tool) |
| Decision tracing / lineage | Yes — core feature | No | No |
| PM-workflow awareness | Yes — built for PM queries | Partial — generic search | No |
| Price point | $10–15/user/month | $50k+/year enterprise | $10–12/user/month (single tool) |
| Target segment | Mid-market PM (20–500 employees) | Enterprise (1000+ employees) | Teams already on that single tool |
