# Testing — MRIIRS AURA

## Automated tests

Run after installing dependencies:

```bash
python -m unittest -v
```

The test suite validates:
- Homepage returns HTTP 200 and contains the AURA name and full form.
- Health endpoint reports the brand, full form and populated knowledge base.
- B.Com-to-MCA eligibility question returns the answer requiring Mathematics and at least 50% marks.
- MCA fee question returns the MCA-specific fee, not a generic fee response.
- Combined MCA duration-and-fee question returns both figures in one answer.
- MCA-without-Mathematics question explains the 10+2 / graduation condition.
- Rechecking wording routes to the revaluation record.
- Unverified daily class-timing questions return a safe fallback rather than a fee answer.
- Admission question returns actionable steps and application-number guidance.
- Hostel question returns actual room-category details.
- An unrelated query returns a safe no-match answer rather than an arbitrary FAQ.
- Category endpoint returns the expected topics.
- Empty and overlong questions are rejected.
- Feedback endpoint validates its vote.

## Manual test checklist

| Input | Expected result |
|---|---|
| `What is MRIIRS?` | Full institutional name and institute overview |
| `Can a B.Com graduate apply for MCA?` | Mathematics-at-10+2-or-graduation and 50% eligibility conditions |
| `What is the MCA fee?` | MCA-specific fee answer with caution to confirm latest fee |
| `What is the duration and fee of MCA?` | Both standard duration and fee instalments, with session caveat |
| `Can I apply for MCA without Mathematics?` | Direct Mathematics condition from the programme page |
| `What are the class timings for MCA?` | Safe fallback; no unrelated programme answer |
| `How do I request rechecking?` | Revaluation / verification guidance |
| `How do I apply for admission?` | Online portal, steps and application number |
| `What is the nearest metro station?` | Named stations and shuttle caveat |
| `Are placements guaranteed?` | Explicitly says no guarantee |
| `What is today's cricket score?` | Safe fallback; does not invent an answer |

## Test environment note

The project is designed for Python 3.10+ and Flask 3.x. Automated tests run locally with Flask's built-in test client and do not need a browser or public internet connection after dependencies are installed.
