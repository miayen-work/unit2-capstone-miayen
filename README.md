# Cloudly Enterprise RAG Assistant

Unit 2 Capstone for GA Data and AI bootcamp - a Python CLI multi-agent Retrieval-Augmented
Generation (RAG) system that answers qualitative and quantitative questions about a fictional
SaaS company's ("Cloudly") enterprise documentation and business data.

Runs entirely locally: [Chroma](https://www.trychroma.com/) as the vector store, SQLite as the
structured database, [Sentence Transformers](https://www.sbert.net/) for local embeddings, and
[Google Gemini](https://ai.google.dev/) as the LLM. No cloud infrastructure required.

## Architecture

```
                         ┌─────────────────────┐
                  query  │   Manager Agent      │
        user ──────────► │  (manager.py)        │
                         │  classify_query()    │
                         └──────────┬───────────┘
                                    │ classifies as one of:
                     ┌──────────────┼──────────────┐
                     │ qualitative  │ quantitative  │ complex (both)
                     ▼              ▼               ▼
         ┌───────────────────┐ ┌────────────────────┐
         │ Qualitative Agent │ │ Quantitative Agent  │
         │ (qualitative_     │ │ (quantitative_      │
         │  agent.py)        │ │  agent.py)          │
         │                   │ │                     │
         │ 1. embed query    │ │ 1. NL question       │
         │ 2. search Chroma  │ │    -> SQL (Gemini)   │
         │ 3. Gemini answers │ │ 2. validate_sql()    │
         │    from retrieved │ │    (blocks writes,   │
         │    chunks, cites  │ │    non-SELECT)       │
         │    sources used   │ │ 3. run against       │
         │                   │ │    SQLite            │
         │                   │ │ 4. Gemini summarizes │
         │                   │ │    rows in plain     │
         │                   │ │    language          │
         └─────────┬─────────┘ └──────────┬──────────┘
                    │                      │
                    └──────────┬───────────┘
                               ▼
                     combined / single result
                               │
                               ▼
                        CLI formats & prints
                     (tokenomics summary every
                        10 queries, on exit)
```

Every LLM call (manager classification, qualitative answer, SQL generation, result
summarization) is logged through `tokenomics.log_usage()`, which tracks token counts and cost
per agent for the running session.

## Data

Since this capstone runs with no real enterprise data source, the qualitative and quantitative
datasets are self-authored, describing a fictional SaaS company, "Cloudly":

**Documents** (`data/documents/`, ingested into Chroma) - company policies:
- `refund_policy.md`, `onboarding.md`, `vacation_policy.md`, `security_policy.md`,
  `support_sla.md`, `code_review_policy.md`, `customer_complaints_policy.md`,
  `expense_policy.md`, `employee_satisfaction_benchmark.md`,
  `customer_success_strategies.md`

**Tables** (`data/database/schema.sql`, loaded into SQLite):
- `customers(id, name, company, region, signup_date)`
- `subscriptions(id, customer_id, plan, monthly_amount, start_date, status)`
- `revenue_by_month(id, month, region, revenue)`
- `employees(id, name, department, satisfaction_score, survey_date)`
- `code_review_tickets(id, opened_at, reviewed_at, turnaround_hours)`
- `expense_requests(id, employee_name, amount, request_date)`

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and add a Gemini API key (from
   [aistudio.google.com/apikey](https://aistudio.google.com/apikey))
3. One-time data setup (creates the SQLite database and ingests documents into Chroma):
   ```
   python -m scripts.setup_data
   ```
4. Run the CLI:
   ```
   python -m src.cli
   ```
5. Type a question at the `>` prompt. Type `exit` or `quit` to stop (prints a tokenomics cost
   summary if any queries were run).

## Running tests

```
python -m pytest tests/
```

All tests mock the Gemini API (no key or network access needed, no quota used) - they verify
our code's logic (routing, SQL validation, error handling, source attribution, cost math), not
the quality of Gemini's actual responses. Live runs of the CLI are the only way to verify real
model behavior end-to-end.

## Sample queries

**Confirmed working end-to-end against the real Gemini API:**

- "What is our refund policy?" (qualitative) - correct answer, cited exactly
  `refund_policy.md` as the source.
- "How many active subscriptions do we have?" (quantitative) - correctly generated
  `SELECT COUNT(*) FROM subscriptions WHERE status = 'active'`, returned 10.
- "When did Priya sign up?" (quantitative) - correctly generated a `LIKE` query on
  `customers.name`, answered in plain language ("February 20, 2025").
- "What's our customer churn rate?" (quantitative) - correctly computed
  cancelled / total subscriptions (16.67%) using the business-term mapping in the
  quantitative agent's prompt.
- A complex refund-policy + subscription-count question - correctly answered both
  halves and combined them into one response.
- **"What's our policy on expense approvals, and how many expense requests last
  quarter would have required manager sign-off under that policy?"** (harder query,
  deliberate keyword red herring) - correctly classified as complex despite being
  phrased around "policy"; qualitative half cited `expense_policy.md` and explained
  the $500/$5,000 thresholds; quantitative half correctly resolved "last quarter" to
  2026-04-01 through 2026-06-30 (relative to the real run date) and found exactly 3
  qualifying requests, matching the seed data precisely.
- **"Analyze our sales performance and recommend policy changes based on our
  customer success strategies"** (complex, open-ended recommendation) - correctly
  classified as complex; qualitative half gave three specific, document-grounded
  recommendations (expand QBRs to Basic/Pro accounts, maintain proactive health
  checks, resolve complaints before renewal) citing `customer_success_strategies.md`;
  quantitative half correctly computed revenue by region ordered descending
  (NA $64,000 > EMEA $36,200 > APAC $35,500), verified against the seed data.
- Real API failures (rate limits, server overload) were also confirmed handled
  gracefully by the CLI - it prints an error and keeps running rather than crashing.


## Known limitations

- **Qualitative retrieval over a small corpus**: with only 10 documents, the top-3
  semantic search used earlier in development sometimes missed the right document for
  oddly-phrased or compound questions (e.g. a code-review question phrased heavily
  around "ticketing data" and "turnaround times" initially failed to retrieve
  `code_review_policy.md`). Raised the qualitative agent's default retrieval count to
  5 results to reduce this risk; not exhaustively re-verified across every query.
- **Qualitative agent originally refused to give recommendations**: its answer prompt
  was initially strict "answer only from literal facts in context," which caused it
  to say "I don't know" on open-ended analysis/recommendation questions even when a
  relevant document existed. Loosened the prompt to allow grounded synthesis for
  analysis/recommendation questions specifically, while keeping strict fact-grounding
  for factual questions - confirmed fixed on the customer-success-strategies query
  above.
