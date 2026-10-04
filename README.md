# Agentic Booking Guardrail: Multimodal Document Validation with Human-in-the-Loop

A Proof of Concept (POC) that stops wrong-test bookings on diagnostic platforms by validating a customer's uploaded prescription or requirement document against a live test catalog **before** an order is finalized.

Built with **LangChain**, **LangGraph**, and **Multimodal RAG**.

---

## Why this exists

I booked a mandatory **10-Panel Urine Drug Test** on Tata 1mg for a job fitness screening. I uploaded a document with "10" clearly circled, yet a manual entry error caused the wrong test profile to be processed.

The Tata 1mg support team handled it professionally. They acknowledged the test was not available in their catalog and issued a full refund. But the delay cost me critical timeline momentum, and the hiring client ultimately put the project on hold.

That raised a question: **why aren't platforms using multimodal AI guardrails to validate user documents against live catalogs at the point of entry?**

This POC is my answer. It is an independent proof of concept and is not affiliated with, or based on the internal systems of, any platform. I don't know their internal tech stack.

---

## What it does

The agent takes the uploaded document and runs it through a three-stage LangGraph workflow:

1. **Visual extraction**: a multimodal LLM scans the upload and extracts the test name, the panel count (for example, "10-panel"), and the required sample type (urine vs. blood).
2. **Adaptive RAG**: the agent cross-references those requirements against a live test catalog database to find an exact match, a close alternative, or no match.
3. **Human-in-the-loop (HITL)**: if the document and the catalog disagree, LangGraph triggers a state interruption. The order cannot proceed until a call-center agent reviews and resolves the mismatch.

```
Uploaded document
        |
        v
[1] Visual extraction (multimodal LLM)
        |   test name, panel count, sample type
        v
[2] Adaptive RAG over live test catalog
        |
        +-- match found ------------> proceed with order
        |
        +-- mismatch / not found ---> [3] HITL interrupt
                                           |
                                           v
                                    Call-center review
                                           |
                                           v
                                  resume graph, finalize or correct order
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph (stateful graph, interrupts / checkpointing) |
| LLM tooling | LangChain |
| Document understanding | Multimodal LLM (vision) |
| Retrieval | Multimodal / adaptive RAG over a test-catalog store |
| Review step | Human-in-the-loop via LangGraph state interruption |

---

## Project structure

> Update this section to match the repository layout.

```
.
├── README.md
├── ...            # extraction node, retrieval node, HITL node, graph definition
└── ...            # sample catalog data and sample documents
```

---

## Getting started

> The commands below are a template. Replace them with the real ones from the repo.

```bash
# 1. Clone
git clone <your-repo-url>
cd <your-repo-folder>

# 2. Create an environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure credentials
cp .env.example .env
# add your multimodal LLM API key to .env

# 4. Run
python main.py
```

---

## Example scenario

| Step | What happens |
|---|---|
| Upload | User uploads a document with "10-Panel Urine Drug Test" and "10" circled |
| Extract | Agent reads: test = drug screen, panels = 10, sample = urine |
| Retrieve | Agent searches the catalog for a 10-panel urine drug test |
| Decision | Match found: continue. No match or panel/sample mismatch: pause the graph |
| HITL | Call-center agent reviews the flagged order, then approves, corrects, or cancels |

---

## Scope and limitations

- This is a **POC**, not a production system.
- The catalog is a stand-in for a live catalog; real integration would need the platform's APIs and data.
- Extraction quality depends on the document image quality and the multimodal model used.
- HITL is deliberate: the goal is to catch mismatches early, not to auto-resolve them.

## Roadmap ideas

- Confidence thresholds so only low-confidence matches go to human review
- Suggesting the closest available alternative to the reviewer
- Audit log of every interrupt and resolution
- Integration with a booking or order API

---

## Author

Built by the project author after a real booking error. Connect on LinkedIn to discuss the idea.

## License

Add a license of your choice (for example, MIT).