"""
Generates synthetic Finlo data: Jira tickets, Slack threads, Notion pages.
Output: data/synthetic/jira_tickets.json, slack_threads.json, notion_pages.json

Designed to support all 20 evaluation queries:
- Q1-5:  cross-tool synthesis (Jira + Slack + Notion)
- Q6-10: single-source factual (hallucination test)
- Q11-15: decision reconstruction
- Q16-18: competitive/strategic context
- Q19:   low-confidence (Q3 board meeting — not documented)
- Q20:   no-results (marketing budget — not mentioned anywhere)
"""
import json
from pathlib import Path

OUT = Path(__file__).parent / "synthetic"
OUT.mkdir(exist_ok=True)


# ── JIRA TICKETS ──────────────────────────────────────────────────────────────

JIRA = [
    {
        "external_id": "FINLO-112",
        "title": "Mobile App MVP",
        "description": (
            "Build the iOS and Android MVP for the Finlo mobile app. "
            "Target DAU: 2,000 in first 90 days post-launch. "
            "Scope: push notifications, dashboard view, ticket status updates. "
            "Assigned to Varun's team (3 engineers). "
            "Original Q2 target date: April 30, 2024."
        ),
        "comments": [
            {
                "author": "Arjun K",
                "body": (
                    "Beta cohort results are in — DAU tracking at 1,180, roughly 40% below "
                    "the 2,000 projection. Retention at day-7 is 28%, below our 45% target."
                ),
                "created_at": "2024-01-19T11:00:00Z"
            },
            {
                "author": "Sanya R",
                "body": (
                    "Blocking decision needed — API v2 resource conflict. Three enterprise "
                    "customers flagged API v2 as a renewal blocker this week: Apex, Nordvik, "
                    "TeleCo. We cannot staff both mobile and API v2 simultaneously."
                ),
                "created_at": "2024-01-19T14:30:00Z"
            },
            {
                "author": "Nitesh R",
                "body": (
                    "Decision: deprioritising mobile to Q4. Redirecting Varun's team to API v2. "
                    "Rationale documented in #product-roadmap thread (Jan 23). "
                    "PRD updated to v2 — mobile moved to Future Scope in Section 4.2."
                ),
                "created_at": "2024-01-23T17:00:00Z"
            },
            {
                "author": "Nitesh R",
                "body": (
                    "Closing epic. Deprioritised per Q2 planning. "
                    "Revisit in Q4 2024 once API v2 is stable and mobile DAU projections are revised."
                ),
                "created_at": "2024-01-31T10:00:00Z"
            }
        ],
        "status": "Cancelled",
        "author": "Nitesh R",
        "created_at": "2023-11-01T09:00:00Z",
        "updated_at": "2024-01-31T10:00:00Z",
        "url": "https://finlo.atlassian.net/browse/FINLO-112"
    },
    {
        "external_id": "API-89",
        "title": "API v2 Platform — enterprise-grade rate limiting and webhook support",
        "description": (
            "Rebuild the API layer to support per-tenant rate limiting, webhook delivery with "
            "retry logic, and OAuth 2.0 scopes. This is the primary blocker for three enterprise "
            "renewals: Apex Corp ($180k ARR), Nordvik ($95k ARR), TeleCo ($210k ARR). "
            "All three flagged API v2 as a hard requirement in their January 2024 renewal calls. "
            "Engineering lead: Varun S. Original target: GA by March 31, 2024."
        ),
        "comments": [
            {
                "author": "Varun S",
                "body": (
                    "Rate limiting module complete. Webhook retry logic is 60% done. "
                    "On track for March 31 if no further scope changes."
                ),
                "created_at": "2024-02-14T09:30:00Z"
            },
            {
                "author": "Sanya R",
                "body": (
                    "Apex flagged a new requirement: they need per-endpoint rate limit "
                    "configuration, not just per-tenant. Adding to scope."
                ),
                "created_at": "2024-02-20T15:00:00Z"
            },
            {
                "author": "Varun S",
                "body": (
                    "Per-endpoint config adds ~2 weeks to the timeline. "
                    "Revised GA estimate: April 14, 2024."
                ),
                "created_at": "2024-02-21T10:00:00Z"
            },
            {
                "author": "Nitesh R",
                "body": (
                    "Accepted the delay. Communicated revised date to Apex, Nordvik, TeleCo — "
                    "all three confirmed April 14 is acceptable for renewal."
                ),
                "created_at": "2024-02-21T14:00:00Z"
            }
        ],
        "status": "In Progress",
        "author": "Nitesh R",
        "created_at": "2024-01-24T08:00:00Z",
        "updated_at": "2024-02-21T14:00:00Z",
        "url": "https://finlo.atlassian.net/browse/API-89"
    },
    {
        "external_id": "PRODUCT-134",
        "title": "Usage-based pricing — implementation and customer migration",
        "description": (
            "Implement usage-based pricing to replace the current per-seat flat fee ($49/seat/month). "
            "Trigger: three enterprise prospects declined in Q4 2023 citing pricing inflexibility. "
            "New model: $0.08 per API call with volume tiers at 10k, 100k, and 1M calls/month. "
            "Requires: billing system update, usage metering pipeline, customer migration comms. "
            "Decision made in #pricing-strategy on Feb 1, 2024 after a 6-week evaluation."
        ),
        "comments": [
            {
                "author": "Priya M",
                "body": (
                    "Billing system update scoped. Stripe usage-based billing supports our model "
                    "natively. Migration path for existing customers: grandfather current pricing "
                    "for 6 months, then opt-in to new model."
                ),
                "created_at": "2024-02-08T11:00:00Z"
            },
            {
                "author": "Nitesh R",
                "body": (
                    "Approved the 6-month grandfather period. Key risk: high-volume customers "
                    "may pay more under usage-based. Need modelling before GA."
                ),
                "created_at": "2024-02-09T14:00:00Z"
            },
            {
                "author": "Priya M",
                "body": (
                    "Usage modelling complete. 3 of 47 existing customers would pay more "
                    "under new model. Offering custom enterprise contracts for those 3."
                ),
                "created_at": "2024-02-15T16:00:00Z"
            }
        ],
        "status": "In Progress",
        "author": "Priya M",
        "created_at": "2024-02-01T09:00:00Z",
        "updated_at": "2024-02-15T16:00:00Z",
        "url": "https://finlo.atlassian.net/browse/PRODUCT-134"
    },
    {
        "external_id": "FINLO-67",
        "title": "Enterprise SSO — SAML 2.0 and Okta integration",
        "description": (
            "Add SAML 2.0 SSO support and a first-party Okta integration. "
            "Required by Nordvik and TeleCo as part of their security review for renewal. "
            "Scope: IdP-initiated login, JIT provisioning, role mapping from IdP groups."
        ),
        "comments": [
            {
                "author": "Varun S",
                "body": (
                    "SSO is live in staging. Nordvik IT have tested and approved. "
                    "TeleCo review scheduled for next week."
                ),
                "created_at": "2024-01-30T14:00:00Z"
            }
        ],
        "status": "Done",
        "author": "Varun S",
        "created_at": "2023-12-15T09:00:00Z",
        "updated_at": "2024-01-30T14:00:00Z",
        "url": "https://finlo.atlassian.net/browse/FINLO-67"
    },
    {
        "external_id": "FINLO-145",
        "title": "CSV and JSON data export for enterprise customers",
        "description": (
            "Allow enterprise customers to export usage data, audit logs, and ticket history "
            "in CSV and JSON formats. Apex requested this for compliance reporting. "
            "Also required for GDPR data portability requests."
        ),
        "comments": [
            {
                "author": "Arjun K",
                "body": (
                    "Export pipeline built using background jobs (Celery). Large exports are "
                    "async — user gets an email with a download link. Max export size: 500MB."
                ),
                "created_at": "2024-01-22T11:00:00Z"
            }
        ],
        "status": "Done",
        "author": "Arjun K",
        "created_at": "2023-12-20T09:00:00Z",
        "updated_at": "2024-01-22T11:00:00Z",
        "url": "https://finlo.atlassian.net/browse/FINLO-145"
    },
    {
        "external_id": "PRODUCT-23",
        "title": "Q2 2024 Roadmap — planning and sign-off",
        "description": (
            "Define and lock Q2 2024 roadmap. Key priorities: API v2 GA, usage-based pricing "
            "launch, enterprise SSO. Items explicitly deferred to Q4: mobile app, dashboard "
            "redesign, Slack integration v2. Roadmap locked Feb 5 after leadership review."
        ),
        "comments": [
            {
                "author": "Nitesh R",
                "body": (
                    "Q2 roadmap locked. Three pillars: (1) API v2 GA by April 14, "
                    "(2) usage-based pricing GA by May 1, (3) enterprise SSO already shipped. "
                    "Mobile and dashboard pushed to Q4."
                ),
                "created_at": "2024-02-05T17:00:00Z"
            }
        ],
        "status": "Done",
        "author": "Nitesh R",
        "created_at": "2024-01-25T09:00:00Z",
        "updated_at": "2024-02-05T17:00:00Z",
        "url": "https://finlo.atlassian.net/browse/PRODUCT-23"
    },
    {
        "external_id": "FINLO-178",
        "title": "Dashboard redesign — new navigation and dark mode",
        "description": (
            "Redesign the main dashboard with a new left-nav layout and dark mode support. "
            "User research from Nov 2023 showed 67% of users wanted dark mode. "
            "Deferred from Q2 to Q4 2024 due to engineering bandwidth constraints — "
            "all available capacity committed to API v2 and usage-based pricing."
        ),
        "comments": [
            {
                "author": "Nitesh R",
                "body": (
                    "Deferring to Q4. Bandwidth fully committed to API v2 and pricing work. "
                    "Design explorations can continue in Q2 so we are ready to build in Q4."
                ),
                "created_at": "2024-02-05T17:30:00Z"
            }
        ],
        "status": "Backlog",
        "author": "Riya D",
        "created_at": "2023-12-01T09:00:00Z",
        "updated_at": "2024-02-05T17:30:00Z",
        "url": "https://finlo.atlassian.net/browse/FINLO-178"
    },
    {
        "external_id": "FINLO-99",
        "title": "Real-time usage metering pipeline",
        "description": (
            "Build a real-time usage metering pipeline to count API calls per tenant. "
            "Required for usage-based pricing. Stack: Kafka (AWS MSK) for event streaming, "
            "ClickHouse for aggregation, Redis for real-time counters. "
            "Must handle 10k events/second at p99 < 50ms."
        ),
        "comments": [
            {
                "author": "Varun S",
                "body": (
                    "Kafka cluster provisioned on AWS MSK. ClickHouse schema designed. "
                    "Redis counters implemented. Load tested at 12k events/sec — "
                    "p99 latency 38ms. Ready for pricing team integration."
                ),
                "created_at": "2024-02-18T14:00:00Z"
            }
        ],
        "status": "Done",
        "author": "Varun S",
        "created_at": "2024-02-01T09:00:00Z",
        "updated_at": "2024-02-18T14:00:00Z",
        "url": "https://finlo.atlassian.net/browse/FINLO-99"
    },
    {
        "external_id": "PRODUCT-31",
        "title": "Pricing strategy review — flat fee vs usage-based",
        "description": (
            "Evaluate switching from per-seat flat fee ($49/seat/month) to usage-based pricing. "
            "Context: 3 enterprise prospects lost in Q4 2023 due to pricing inflexibility. "
            "6-week analysis covering competitive benchmarking and financial modelling."
        ),
        "comments": [
            {
                "author": "Priya M",
                "body": (
                    "Financial model complete. Usage-based at $0.08/call with volume tiers "
                    "increases projected ARR by 34% over 18 months. Recommend switching."
                ),
                "created_at": "2024-01-29T16:00:00Z"
            },
            {
                "author": "Nitesh R",
                "body": (
                    "Decision: switching to usage-based. Rationale: better aligns with enterprise "
                    "procurement patterns, removes per-seat friction for large teams, and our "
                    "metering infrastructure (FINLO-99) makes it feasible now."
                ),
                "created_at": "2024-02-01T11:00:00Z"
            }
        ],
        "status": "Done",
        "author": "Priya M",
        "created_at": "2023-12-20T09:00:00Z",
        "updated_at": "2024-02-01T11:00:00Z",
        "url": "https://finlo.atlassian.net/browse/PRODUCT-31"
    },
    {
        "external_id": "API-52",
        "title": "Webhook support — delivery guarantees and retry logic",
        "description": (
            "Implement webhook delivery with at-least-once guarantees. "
            "Retry policy: exponential backoff, maximum 5 retries over 24 hours. "
            "Delivery logs retained for 72 hours. "
            "Customer-configurable endpoint URLs and HMAC-SHA256 secret signing."
        ),
        "comments": [
            {
                "author": "Arjun K",
                "body": (
                    "Webhook delivery queue implemented using Celery + Redis. "
                    "Secret signing uses HMAC-SHA256. Retry logic tested — "
                    "confirmed at-least-once delivery. Dead letter queue in place for failed deliveries."
                ),
                "created_at": "2024-02-10T11:00:00Z"
            }
        ],
        "status": "Done",
        "author": "Arjun K",
        "created_at": "2024-01-24T09:00:00Z",
        "updated_at": "2024-02-10T11:00:00Z",
        "url": "https://finlo.atlassian.net/browse/API-52"
    },
]


# ── SLACK THREADS ─────────────────────────────────────────────────────────────

SLACK = [
    {
        "external_id": "C_product-roadmap_1705968720",
        "channel": "#product-roadmap",
        "messages": [
            {
                "author": "Sanya R",
                "text": (
                    "We need to have a real talk about mobile. Three enterprise deals — Apex, "
                    "Nordvik, and TeleCo — all flagged API v2 as a renewal blocker this week. "
                    "Combined ARR at risk: $485k. We cannot staff both mobile and API v2."
                ),
                "ts": "2024-01-23T16:12:00Z"
            },
            {
                "author": "Arjun K",
                "text": (
                    "Mobile beta DAU is 1,180 against our 2,000 target — 40% below projection. "
                    "Day-7 retention is 28% vs our 45% target. We need to face the trade-off."
                ),
                "ts": "2024-01-23T16:18:00Z"
            },
            {
                "author": "Riya D",
                "text": (
                    "From a design perspective the mobile UX still needs 3-4 more weeks of polish. "
                    "It is not ready for public launch even if we kept the resources."
                ),
                "ts": "2024-01-23T16:25:00Z"
            },
            {
                "author": "Nitesh R",
                "text": (
                    "Decision: moving mobile to Q4 and redirecting Varun's team to API v2. "
                    "Rationale — $485k ARR at risk outweighs the mobile opportunity at current "
                    "DAU projections. I will update the PRD and close FINLO-112."
                ),
                "ts": "2024-01-23T16:31:00Z"
            },
            {
                "author": "Varun S",
                "text": "Understood. Will start API v2 scoping tomorrow and share revised timeline by EOW.",
                "ts": "2024-01-23T16:45:00Z"
            }
        ],
        "url": "https://finlo.slack.com/archives/C_product-roadmap/p1705968720"
    },
    {
        "external_id": "C_product-roadmap_1704364800",
        "channel": "#product-roadmap",
        "messages": [
            {
                "author": "Nitesh R",
                "text": (
                    "Kicking off Q2 planning. Proposed priorities: (1) API v2 GA, "
                    "(2) usage-based pricing, (3) continue SSO rollout. "
                    "Mobile and dashboard redesign are Q4 candidates. Thoughts?"
                ),
                "ts": "2024-01-04T09:00:00Z"
            },
            {
                "author": "Sanya R",
                "text": (
                    "Strongly agree on API v2 as P1. The enterprise pipeline is blocked until "
                    "we ship it. Three deals worth $485k are waiting."
                ),
                "ts": "2024-01-04T09:20:00Z"
            },
            {
                "author": "Priya M",
                "text": (
                    "Usage-based pricing needs to be Q2 — we lost 3 enterprise prospects in Q4 "
                    "because our per-seat model does not fit their procurement process."
                ),
                "ts": "2024-01-04T09:35:00Z"
            },
            {
                "author": "Arjun K",
                "text": (
                    "Agree on Q2 priorities. One flag: dashboard redesign keeps getting pushed. "
                    "NPS comments mention it 40% of the time. At some point we need to commit."
                ),
                "ts": "2024-01-04T09:50:00Z"
            },
            {
                "author": "Nitesh R",
                "text": (
                    "Noted on dashboard. Q4 is a real slot, not a graveyard. "
                    "If API v2 ships on time we will have bandwidth. Locking Q2 pillars as discussed."
                ),
                "ts": "2024-01-04T10:05:00Z"
            }
        ],
        "url": "https://finlo.slack.com/archives/C_product-roadmap/p1704364800"
    },
    {
        "external_id": "C_pricing-strategy_1706745600",
        "channel": "#pricing-strategy",
        "messages": [
            {
                "author": "Priya M",
                "text": (
                    "Sharing the pricing model analysis. TL;DR: switching from $49/seat to "
                    "usage-based at $0.08/API call increases projected ARR by 34% over 18 months. "
                    "The per-seat model is hurting enterprise deals."
                ),
                "ts": "2024-02-01T09:00:00Z"
            },
            {
                "author": "Nitesh R",
                "text": "The 34% ARR uplift is compelling. What is the downside risk for existing customers?",
                "ts": "2024-02-01T09:15:00Z"
            },
            {
                "author": "Priya M",
                "text": (
                    "3 of 47 existing customers would pay more under usage-based. "
                    "Proposing custom enterprise contracts for those 3 with a 6-month "
                    "grandfather period for everyone else."
                ),
                "ts": "2024-02-01T09:30:00Z"
            },
            {
                "author": "Sanya R",
                "text": (
                    "Sales perspective: this is the right move. I have lost 2 deals in the last "
                    "month where the prospect said our per-seat pricing does not fit how their "
                    "finance team thinks about SaaS spend."
                ),
                "ts": "2024-02-01T09:45:00Z"
            },
            {
                "author": "Nitesh R",
                "text": (
                    "Decision: switching to usage-based pricing. $0.08/call with volume tiers "
                    "at 10k, 100k, 1M calls/month. 6-month grandfather for existing customers. "
                    "Custom contracts for the 3 at-risk accounts. Priya to update the PRD."
                ),
                "ts": "2024-02-01T11:00:00Z"
            }
        ],
        "url": "https://finlo.slack.com/archives/C_pricing-strategy/p1706745600"
    },
    {
        "external_id": "C_pricing-strategy_1705276800",
        "channel": "#pricing-strategy",
        "messages": [
            {
                "author": "Priya M",
                "text": (
                    "Starting a 6-week pricing evaluation. The question: switch from flat "
                    "per-seat to usage-based? We lost Apex (initial eval), DataCo, and Meridian "
                    "in Q4 2023 due to pricing inflexibility."
                ),
                "ts": "2024-01-15T10:00:00Z"
            },
            {
                "author": "Sanya R",
                "text": (
                    "Meridian's exact words: 'your pricing assumes a static team size but we "
                    "add and remove API access dynamically.' That is a recurring objection."
                ),
                "ts": "2024-01-15T10:20:00Z"
            },
            {
                "author": "Nitesh R",
                "text": (
                    "Glean is charging $50k+ annually for enterprise. We are at $49/seat/month. "
                    "The gap to mid-market is real. Let us run the full analysis before deciding."
                ),
                "ts": "2024-01-15T10:35:00Z"
            }
        ],
        "url": "https://finlo.slack.com/archives/C_pricing-strategy/p1705276800"
    },
    {
        "external_id": "C_engineering_1706140800",
        "channel": "#engineering",
        "messages": [
            {
                "author": "Varun S",
                "text": (
                    "API v2 scoping complete. Breakdown: rate limiting (2 weeks), "
                    "webhook delivery (2 weeks), OAuth 2.0 scopes (1 week), "
                    "per-endpoint rate config (2 weeks — added by Apex). "
                    "Total: 7 weeks. Target GA: April 14."
                ),
                "ts": "2024-01-25T09:00:00Z"
            },
            {
                "author": "Arjun K",
                "text": (
                    "The per-endpoint rate config is the wildcard — requires changes to the "
                    "auth middleware and billing pipeline. I can pair with you on that piece."
                ),
                "ts": "2024-01-25T09:20:00Z"
            },
            {
                "author": "Varun S",
                "text": "Let us start on the auth middleware changes this week while rate limiting is in review.",
                "ts": "2024-01-25T09:35:00Z"
            }
        ],
        "url": "https://finlo.slack.com/archives/C_engineering/p1706140800"
    },
    {
        "external_id": "C_product-eng-sync_1706486400",
        "channel": "#product-eng-sync",
        "messages": [
            {
                "author": "Nitesh R",
                "text": (
                    "Sprint planning Jan 29 – Feb 9. Priorities: (1) Varun team: API v2 rate "
                    "limiting module, (2) Arjun: webhook delivery queue, "
                    "(3) Riya: dashboard redesign explorations (not for build yet). Any blockers?"
                ),
                "ts": "2024-01-28T10:00:00Z"
            },
            {
                "author": "Arjun K",
                "text": "Webhook queue needs the new Celery worker config. DevOps said it will be ready by Jan 30.",
                "ts": "2024-01-28T10:15:00Z"
            },
            {
                "author": "Riya D",
                "text": "Will start with nav explorations. Three concepts ready by Feb 7 for async feedback.",
                "ts": "2024-01-28T10:20:00Z"
            }
        ],
        "url": "https://finlo.slack.com/archives/C_product-eng-sync/p1706486400"
    },
    {
        "external_id": "C_product-roadmap_1705363200",
        "channel": "#product-roadmap",
        "messages": [
            {
                "author": "Sanya R",
                "text": (
                    "Competitor update: Glean just announced a $100M Series D at a $1.2B "
                    "valuation. They are doubling down on enterprise. Their minimum deal size "
                    "is $50k annually — they are not coming for our mid-market segment."
                ),
                "ts": "2024-01-16T14:00:00Z"
            },
            {
                "author": "Nitesh R",
                "text": (
                    "This is exactly the wedge we identified. Glean optimises for Fortune 500. "
                    "Our opportunity is the 20-500 employee company that cannot afford Glean "
                    "but has the same knowledge fragmentation problem."
                ),
                "ts": "2024-01-16T14:20:00Z"
            },
            {
                "author": "Priya M",
                "text": (
                    "We should accelerate usage-based pricing. Enterprise procurement teams want "
                    "consumption billing. This helps us compete in the $10k-$50k deal range "
                    "that Glean is too expensive for."
                ),
                "ts": "2024-01-16T14:35:00Z"
            }
        ],
        "url": "https://finlo.slack.com/archives/C_product-roadmap/p1705363200"
    },
    {
        "external_id": "C_pricing-strategy_1706832000",
        "channel": "#pricing-strategy",
        "messages": [
            {
                "author": "Priya M",
                "text": (
                    "Pricing PRD v2 is ready for review. Key changes from v1: "
                    "(1) volume tiers added at 10k, 100k, 1M calls/month, "
                    "(2) enterprise custom contracts section added, "
                    "(3) grandfather period extended from 3 months to 6 months based on "
                    "customer feedback."
                ),
                "ts": "2024-02-02T10:00:00Z"
            },
            {
                "author": "Nitesh R",
                "text": (
                    "The 6-month grandfather is the right call. Gives customers time to model "
                    "actual usage before committing. Approving v2."
                ),
                "ts": "2024-02-02T10:30:00Z"
            },
            {
                "author": "Sanya R",
                "text": (
                    "One ask: can we add a section on how to communicate the change to existing "
                    "customers? I need talking points for the renewal calls."
                ),
                "ts": "2024-02-02T10:45:00Z"
            },
            {
                "author": "Priya M",
                "text": "Adding a customer comms section to v2. Updated draft by EOD.",
                "ts": "2024-02-02T11:00:00Z"
            }
        ],
        "url": "https://finlo.slack.com/archives/C_pricing-strategy/p1706832000"
    },
    {
        "external_id": "C_engineering_1707350400",
        "channel": "#engineering",
        "messages": [
            {
                "author": "Arjun K",
                "text": (
                    "Investigating a performance issue in the search endpoint. p99 latency "
                    "jumped from 180ms to 890ms yesterday around 3pm. Suspect the new "
                    "full-text index on the tickets table."
                ),
                "ts": "2024-02-08T09:00:00Z"
            },
            {
                "author": "Varun S",
                "text": (
                    "Check the EXPLAIN output. The FTS index can cause table scans if the "
                    "query planner does not pick it up with stale statistics."
                ),
                "ts": "2024-02-08T09:20:00Z"
            },
            {
                "author": "Arjun K",
                "text": (
                    "Found it — query planner was not using the index due to stale statistics. "
                    "Ran ANALYZE, p99 is back to 175ms. No customer impact."
                ),
                "ts": "2024-02-08T10:15:00Z"
            }
        ],
        "url": "https://finlo.slack.com/archives/C_engineering/p1707350400"
    },
    {
        "external_id": "C_product-eng-sync_1707004800",
        "channel": "#product-eng-sync",
        "messages": [
            {
                "author": "Nitesh R",
                "text": (
                    "API v2 launch date discussion. Varun shared revised timeline — April 14 "
                    "due to per-endpoint rate config scope addition from Apex. "
                    "Original target was March 31. How do we feel about the slip?"
                ),
                "ts": "2024-02-04T10:00:00Z"
            },
            {
                "author": "Sanya R",
                "text": (
                    "Checked with Apex, Nordvik, and TeleCo. All three said April 14 is "
                    "acceptable. Rushing and shipping a buggy API is worse than a 2-week slip."
                ),
                "ts": "2024-02-04T10:15:00Z"
            },
            {
                "author": "Varun S",
                "text": "The per-endpoint config is non-trivial. 2 weeks is the right estimate, not a padded one.",
                "ts": "2024-02-04T10:25:00Z"
            },
            {
                "author": "Nitesh R",
                "text": (
                    "Aligned. April 14 is the new target. "
                    "Updating PRODUCT-23 and communicating to enterprise accounts."
                ),
                "ts": "2024-02-04T10:35:00Z"
            }
        ],
        "url": "https://finlo.slack.com/archives/C_product-eng-sync/p1707004800"
    },
]


# ── NOTION PAGES ──────────────────────────────────────────────────────────────

NOTION = [
    {
        "external_id": "notion-mobile-prd-v2",
        "title": "Mobile App PRD v2",
        "content": (
            "# Mobile App PRD — v2\n"
            "Owner: Nitesh R | Last updated: Jan 24, 2024 | Status: Deferred to Q4\n\n"
            "## Change log\n"
            "v1 (Nov 2023): Initial scope — iOS and Android MVP, push notifications, dashboard view.\n"
            "v2 (Jan 24, 2024): Section 4.2 updated — Mobile moved to Future Scope. "
            "Decision made Jan 23 in #product-roadmap. Engineering bandwidth redirected to API v2 "
            "following $485k ARR renewal risk across Apex, Nordvik, TeleCo.\n\n"
            "## 1. Problem statement\n"
            "PMs and engineers at Finlo customers increasingly work from mobile. "
            "A mobile app would improve daily active usage and reduce churn for remote-first teams.\n\n"
            "## 2. Goals\n"
            "Target DAU: 2,000 within 90 days of launch.\n"
            "Day-7 retention target: 45%.\n"
            "Reduce churn by 8% for mobile-first customer segments.\n\n"
            "## 3. Beta results (updated Jan 2024)\n"
            "Beta cohort DAU came in at 1,180 — 40% below the 2,000 target. "
            "Day-7 retention was 28%, below the 45% target. "
            "This data weakened the case for Q2 prioritisation.\n\n"
            "## 4. Scope\n"
            "### 4.1 In scope (original v1)\n"
            "Push notifications for @mentions and ticket updates.\n"
            "Dashboard with key metrics.\n"
            "Ticket status view and comment threads.\n\n"
            "### 4.2 Mobile — Future Scope (updated v2)\n"
            "Mobile app development is deferred to Q4 2024. "
            "Primary reason: engineering bandwidth reallocated to API v2 following three enterprise "
            "renewal risks totalling $485k ARR (Apex, Nordvik, TeleCo). "
            "Secondary reason: beta DAU 40% below projection reduces urgency. "
            "This section will be revisited in Q3 planning with updated DAU data.\n\n"
            "## 5. Open questions for Q4 revisit\n"
            "Native iOS/Android vs React Native?\n"
            "Target power users (PMs) or all roles?\n"
            "Revised DAU target given beta data?\n"
        ),
        "author": "Nitesh R",
        "created_at": "2023-11-01T09:00:00Z",
        "updated_at": "2024-01-24T14:00:00Z",
        "url": "https://finlo.notion.so/Mobile-App-PRD-v2"
    },
    {
        "external_id": "notion-api-v2-spec",
        "title": "API v2 Platform Specification",
        "content": (
            "# API v2 Platform Specification\n"
            "Owner: Varun S | Last updated: Feb 21, 2024 | Status: In progress — GA April 14\n\n"
            "## Context\n"
            "API v2 is the primary blocker for three enterprise renewals: "
            "Apex Corp ($180k ARR), Nordvik ($95k ARR), TeleCo ($210k ARR). "
            "Combined at-risk ARR: $485k. "
            "Decision to prioritise API v2 over mobile app made Jan 23, 2024 in #product-roadmap.\n\n"
            "## Requirements\n\n"
            "### Per-tenant rate limiting\n"
            "Configurable limits per API key. Default: 1,000 req/min. "
            "Enterprise: custom limits up to 50,000 req/min.\n\n"
            "### Per-endpoint rate limiting (added Feb 20)\n"
            "Apex requested per-endpoint configuration so that the search endpoint can have "
            "different limits from write endpoints. "
            "Rate limit config stored in Redis and checked at the API gateway layer. "
            "Added 2 weeks to the timeline — revised GA: April 14, 2024. Original target was March 31.\n\n"
            "### Webhook delivery\n"
            "At-least-once delivery guarantee. "
            "Exponential backoff retry: 5 retries over 24 hours. "
            "HMAC-SHA256 secret signing. Delivery logs retained 72 hours.\n\n"
            "### OAuth 2.0 scopes\n"
            "Scopes: read:tickets, write:tickets, read:users, admin. "
            "Per-key scope configuration available in the dashboard.\n\n"
            "## Timeline\n"
            "Rate limiting complete: Feb 14.\n"
            "Webhook delivery complete: Feb 10.\n"
            "OAuth scopes complete: Feb 28.\n"
            "Per-endpoint rate config complete: March 14.\n"
            "QA and staging: March 15 – April 7.\n"
            "GA: April 14, 2024.\n"
        ),
        "author": "Varun S",
        "created_at": "2024-01-24T09:00:00Z",
        "updated_at": "2024-02-21T14:00:00Z",
        "url": "https://finlo.notion.so/API-v2-Platform-Spec"
    },
    {
        "external_id": "notion-pricing-prd-v2",
        "title": "Pricing Strategy PRD v2",
        "content": (
            "# Pricing Strategy PRD\n"
            "Owner: Priya M | Version: v2 | Last updated: Feb 2, 2024\n\n"
            "## Change log\n"
            "v1 (Jan 15): Initial analysis — flat per-seat vs usage-based comparison.\n"
            "v2 (Feb 2): Volume tiers added. Enterprise custom contracts section added. "
            "Grandfather period extended from 3 months to 6 months based on customer feedback. "
            "Customer comms talking points added.\n\n"
            "## Decision\n"
            "Switching from per-seat flat fee ($49/seat/month) to usage-based pricing ($0.08/API call). "
            "Decision made Feb 1, 2024 in #pricing-strategy by Nitesh R. "
            "Rationale: 34% projected ARR uplift over 18 months, removes per-seat friction for "
            "enterprise procurement, aligns with how enterprise teams buy SaaS.\n\n"
            "## Pricing tiers\n"
            "Starter: 0 to 10k calls/month at $0.08 per call.\n"
            "Growth: 10k to 100k calls/month at $0.06 per call.\n"
            "Scale: 100k to 1M calls/month at $0.04 per call.\n"
            "Enterprise: over 1M calls/month on a custom contract.\n\n"
            "## Existing customer migration\n"
            "6-month grandfather period for all existing customers — current flat-fee pricing maintained "
            "until September 2024. "
            "3 customers identified whose usage would cost more under new model — "
            "offering custom enterprise contracts. "
            "Migration comms to be sent March 1, 2024.\n\n"
            "## Customer communication talking points\n"
            "1. You only pay for what you use — teams that use Finlo heavily get better value as they scale.\n"
            "2. Your current pricing is locked for 6 months — no changes until September 2024.\n"
            "3. If your usage means you would pay more, we will reach out personally with a custom plan.\n\n"
            "## Why we switched\n"
            "Three enterprise prospects declined in Q4 2023 due to pricing inflexibility. "
            "Glean's $50k+ annual pricing validates enterprise demand but prices out mid-market. "
            "Usage-based removes the per-seat objection and fits enterprise procurement patterns.\n"
        ),
        "author": "Priya M",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-02-02T11:00:00Z",
        "url": "https://finlo.notion.so/Pricing-Strategy-PRD-v2"
    },
    {
        "external_id": "notion-q2-roadmap",
        "title": "Q2 2024 Roadmap",
        "content": (
            "# Q2 2024 Roadmap\n"
            "Owner: Nitesh R | Locked: Feb 5, 2024\n\n"
            "## Q2 pillars\n\n"
            "### 1. API v2 GA (P0)\n"
            "Target date: April 14, 2024. "
            "Unblocks $485k in enterprise renewals (Apex, Nordvik, TeleCo). "
            "Engineering lead: Varun S.\n\n"
            "### 2. Usage-based pricing launch (P0)\n"
            "Target date: May 1, 2024. "
            "Switches billing from $49/seat to $0.08/API call with volume tiers. "
            "Business lead: Priya M.\n\n"
            "### 3. Enterprise SSO (shipped Q1)\n"
            "SAML 2.0 and Okta integration shipped Jan 30. "
            "Nordvik approved. TeleCo review pending.\n\n"
            "## Deferred items\n"
            "Mobile app: deferred to Q4. "
            "Beta DAU 40% below target. Engineering bandwidth needed for API v2. "
            "Decision made Jan 23 in #product-roadmap.\n\n"
            "Dashboard redesign: deferred to Q4. "
            "67% of users requested dark mode (Nov 2023 research) but engineering capacity is "
            "fully committed to API v2 and pricing work. "
            "Riya continuing design explorations in Q2 so build can start in Q4.\n\n"
            "Slack integration v2: Q4 candidate pending Q2 bandwidth review.\n\n"
            "## Planning notes\n"
            "Q2 planning kicked off Jan 4 in #product-roadmap. "
            "Mobile app deprioritisation decided Jan 23 after enterprise renewal risk surfaced. "
            "Roadmap locked Feb 5 after leadership review.\n"
        ),
        "author": "Nitesh R",
        "created_at": "2024-01-25T09:00:00Z",
        "updated_at": "2024-02-05T17:00:00Z",
        "url": "https://finlo.notion.so/Q2-2024-Roadmap"
    },
    {
        "external_id": "notion-engineering-architecture",
        "title": "Engineering Architecture Overview",
        "content": (
            "# Finlo Engineering Architecture\n"
            "Owner: Varun S | Last updated: Feb 2024\n\n"
            "## Stack\n"
            "Backend: Python (FastAPI), PostgreSQL, Redis, Celery.\n"
            "Frontend: React, TypeScript.\n"
            "Infrastructure: AWS (ECS, RDS, ElastiCache, MSK).\n"
            "Search: Elasticsearch for full-text. ChromaDB for semantic search (new in API v2).\n\n"
            "## Key architectural decisions\n\n"
            "### PostgreSQL over MongoDB (Dec 2023)\n"
            "We evaluated MongoDB for ticket storage but chose PostgreSQL. "
            "Reasons: (1) our data is highly relational — tickets, comments, users, and orgs "
            "all have FK relationships; (2) the team has deeper PostgreSQL expertise; "
            "(3) MongoDB's flexible schema would make the billing metering pipeline harder to "
            "query precisely. Decision made by Varun S and Arjun K after a 2-week spike.\n\n"
            "### Kafka for usage metering (Feb 2024)\n"
            "Real-time usage metering pipeline uses Kafka (AWS MSK) for event streaming and "
            "ClickHouse for aggregation. Required for usage-based pricing. "
            "Handles 12k events/second at p99 latency of 38ms.\n\n"
            "### Celery and Redis for async jobs (Q3 2023)\n"
            "Background job processing — email, exports, webhook delivery — uses Celery with "
            "Redis as the broker. Chosen over SQS for local dev parity and simpler retry config.\n"
        ),
        "author": "Varun S",
        "created_at": "2023-09-01T09:00:00Z",
        "updated_at": "2024-02-01T09:00:00Z",
        "url": "https://finlo.notion.so/Engineering-Architecture"
    },
    {
        "external_id": "notion-competitor-analysis",
        "title": "Competitor Analysis — Q1 2024",
        "content": (
            "# Competitor Analysis\n"
            "Owner: Nitesh R | Last updated: Jan 16, 2024\n\n"
            "## Summary\n"
            "No tool at an accessible price point ($10–15/user/month) traces decisions across "
            "PRDs, Jira, and Slack. Glean comes closest on cross-tool retrieval but is "
            "enterprise-only at $50k+ annually and has no decision lineage feature.\n\n"
            "## Glean\n"
            "Strengths: best-in-class semantic retrieval, 100+ connectors, fast.\n"
            "Weakness: enterprise-only pricing ($50k+ annual minimum), no decision tracing.\n"
            "Recent: $100M Series D in Jan 2024 at $1.2B valuation — doubling down on Fortune 500.\n"
            "Our opportunity: Glean leaves the 20–500 employee mid-market entirely unserved.\n\n"
            "## Confluence AI\n"
            "Strengths: native Atlassian integration, no setup friction.\n"
            "Weakness: siloed to Confluence only — misses Slack and standalone PRDs entirely.\n\n"
            "## Notion AI\n"
            "Strengths: clean UX, excellent for Notion-native teams.\n"
            "Weakness: useless if team uses Jira. No cross-tool synthesis.\n\n"
            "## Finlo positioning\n"
            "Our wedge is decision tracing across tools at mid-market pricing. "
            "Not just cross-tool search — the why behind the what. "
            "Surfacing the Slack thread that preceded the PRD change that closed the Jira ticket. "
            "Price target: $10–15/user/month. Glean for PMs at 1/10th the price.\n"
        ),
        "author": "Nitesh R",
        "created_at": "2024-01-10T09:00:00Z",
        "updated_at": "2024-01-16T14:00:00Z",
        "url": "https://finlo.notion.so/Competitor-Analysis-Q1-2024"
    },
    {
        "external_id": "notion-enterprise-playbook",
        "title": "Enterprise Customer Playbook",
        "content": (
            "# Enterprise Customer Playbook\n"
            "Owner: Sanya R | Last updated: Feb 2024\n\n"
            "## Active enterprise accounts\n\n"
            "### Apex Corp — $180k ARR\n"
            "Renewal due: April 2024.\n"
            "Key requirement: API v2 with per-endpoint rate limiting.\n"
            "Secondary ask: CSV/JSON data export (shipped in FINLO-145).\n"
            "Champion: Marcus D, Head of Engineering.\n\n"
            "### Nordvik — $95k ARR\n"
            "Renewal due: March 2024.\n"
            "Key requirement: SAML 2.0 SSO (shipped in FINLO-67).\n"
            "Also requires API v2 before full renewal commitment.\n"
            "Champion: Lena H, VP Product.\n\n"
            "### TeleCo — $210k ARR\n"
            "Renewal due: April 2024.\n"
            "Key requirements: API v2 and SAML SSO.\n"
            "SAML review with TeleCo IT scheduled for next week.\n"
            "Champion: Raj P, CTO.\n\n"
            "## Renewal strategy\n"
            "All three accounts are contingent on API v2 GA on April 14. "
            "SSO is shipped. Export is shipped. API v2 is the single remaining blocker.\n"
        ),
        "author": "Sanya R",
        "created_at": "2024-01-05T09:00:00Z",
        "updated_at": "2024-02-10T14:00:00Z",
        "url": "https://finlo.notion.so/Enterprise-Customer-Playbook"
    },
    {
        "external_id": "notion-q3-planning-notes",
        "title": "Q3 2024 Planning Notes",
        "content": (
            "# Q3 2024 Planning Notes\n"
            "Owner: Nitesh R | Status: Early draft — planning begins June 2024\n\n"
            "## Carry-forward from Q2\n"
            "Items deferred from Q2 that are candidates for Q3 or Q4:\n"
            "Mobile app (Q4 candidate — depends on API v2 outcome and revised DAU projections).\n"
            "Dashboard redesign (Q4 — design explorations completing in Q2).\n"
            "Slack integration v2 (Q3 candidate — customer demand growing).\n\n"
            "## Potential Q3 themes\n"
            "Expansion and retention: deepen enterprise features post API v2 GA.\n"
            "Self-serve growth: improve onboarding funnel for SMB customers.\n"
            "Platform reliability: observability improvements and SLA hardening.\n\n"
            "## Open questions\n"
            "Will API v2 GA on April 14 free up enough bandwidth for mobile in Q4?\n"
            "What does usage-based pricing adoption look like by June?\n"
            "Should we invest in a Slack app for Finlo in Q3?\n"
        ),
        "author": "Nitesh R",
        "created_at": "2024-02-15T09:00:00Z",
        "updated_at": "2024-02-15T09:00:00Z",
        "url": "https://finlo.notion.so/Q3-2024-Planning-Notes"
    },
]


# ── WRITE FILES ───────────────────────────────────────────────────────────────

def write(name, data):
    path = OUT / name
    path.write_text(json.dumps(data, indent=2))
    return path

p1 = write("jira_tickets.json", JIRA)
p2 = write("slack_threads.json", SLACK)
p3 = write("notion_pages.json", NOTION)

print(f"✓ {len(JIRA):>3} Jira tickets   → {p1}")
print(f"✓ {len(SLACK):>3} Slack threads  → {p2}")
print(f"✓ {len(NOTION):>3} Notion pages   → {p3}")
print(f"\nTotal source documents: {len(JIRA) + len(SLACK) + len(NOTION)}")
