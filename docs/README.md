# quic-testbed docs

| File | Read it to learn... |
|---|---|
| [PROJECT_GUIDE.md](PROJECT_GUIDE.md) | What every file/folder does + the step-by-step flow of the whole setup |
| [Architecture.md](Architecture.md) | How the system is built (diagrams, components, design decisions) |
| [Presentation.md](Presentation.md) | How to pitch it to your professor (STAR) + live demo commands |
| [TODO.md](TODO.md) | What is finished and what is still left |
| [PHASES.md](PHASES.md) | What happens in each project phase and why |
| [PRD.md](PRD.md) | The requirements |
| [literature_references.md](literature_references.md) | Papers, RFCs and tools cited, with verification status |
| [Project_Report_Real_Results.docx](Project_Report_Real_Results.docx) | New report draft with real results (original left untouched) |
| [coverage_and_skip_plan.md](coverage_and_skip_plan.md) | Draft report vs real data: what is covered, what to skip, what must still run |
| [draft_vs_real_corrections.md](draft_vs_real_corrections.md) | Draft claims the data contradicts, with the real numbers |
| [reusable_from_draft.md](reusable_from_draft.md) | Non-result draft content worth keeping, checked against the real environment |

One-line summary: a rootless, single-machine testbed that races **HTTP/2 (TCP)** against **HTTP/3 (QUIC)**
under emulated latency and packet loss, and finds the network conditions where one stops beating the other.
