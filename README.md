# CampusBuddy

An AI "buddy for your entire college life": teammate and mentor matching,
lost-and-found, event "Who's going?", and a campus assistant chatbot.
Samsung Innovation Campus capstone (4 members, 21 days).

## Who owns what
| Member | Folders |
|---|---|
| 1 | `profiles/`, `matching/`, `data/profiles/`, `eval/matching/` |
| 2 | `lostfound/`, `data/items/`, `eval/lostfound/` |
| 3 | `events/`, `assistant/`, `data/events/`, `data/docs/`, `eval/events/`, `eval/assistant/` |
| 4 | `backend/`, `frontend/`, `docs/`, shared root files |

Ownership is enforced by `.github/CODEOWNERS` plus branch protection on `main`.

## Team workflow
1. Work only on your own branch, e.g. `member3-events`. Never commit to `main`.
2. Start each day with `git pull origin main`.
3. Commit daily, push your branch, open a Pull Request into `main`.
4. The folder owner approves the PR. Shared files need Member 4's approval.
5. Data in `data/` must be anonymised: no real names or phone numbers.

## Setup
```
pip install -r requirements.txt
python -m pytest
```
Add your module's libraries to `requirements.txt` through a PR to Member 4.

## Shared contract
Do not change the profile JSON or the function signatures without telling the team.
See `docs/contract.md`.
