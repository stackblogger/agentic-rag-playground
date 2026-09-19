# Rules for coding agents

## Read the docs first

Before making any change in the code, read these files:

1. `README.md`: what the project is, how to run it, the settings.
2. `docs/architecture.md`: how the app is built, the code layers, and how upload, search and chat work.
3. `docs/api.md`: all API routes, responses and error codes.
4. `docs/database.md`: tables, columns and migration commands.

Follow the code layers from `docs/architecture.md`. Routes in `api/` stay thin, and the main logic goes in `services/`.

## While changing

- Change in small parts, one thing at a time, so the git history stays easy to read. Do not commit unless asked.
- If a change makes the README or a doc wrong, update it in the same change.
- The README must always look complete. No "coming soon" or future plans, no table or column lists (they are in `docs/database.md`), and no "you" or "your".
- Write code comments, docs and messages in simple, human. No fancy words.
