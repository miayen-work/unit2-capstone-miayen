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
  `expense_policy.md`, `employee_satisfaction_benchmark.md`

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

**Qualitative** (semantic search over documents):
- "What is our company's security policy?"
- "Explain the code review process"
- "How do we handle customer complaints?"

**Quantitative** (natural language to SQL):
- "What's our customer churn rate?" - confirmed working: correctly computes
  cancelled / total subscriptions (16.67%) from `subscriptions.status`.
- "Show me monthly revenue trends"
- "Compare Q4 performance across regions"

**Complex** (both agents, combined):
- "How does our employee satisfaction compare to industry standards and what policies
  might impact this?"
- "Analyze our sales performance and recommend policy changes based on our customer
  success strategies"

**Harder queries**:
- "Based on our documented code review process, are our current code review turnaround
  times (from the ticketing data) meeting the standard we've committed to?"
- "What's our policy on expense approvals, and how many expense requests last quarter
  would have required manager sign-off under that policy?"

> Note: this section is being filled in as queries are verified live against the real Gemini
> API (subject to free-tier rate limits) - not all of the above have been confirmed yet.
