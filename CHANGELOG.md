# Changelog

> **Format:** `## vX.Y.Z — YYYY-MM-DD — commit message`
> Use the text after the date as your `git commit -m "..."` message.
> Keep entries to 3 lines max. Use imperative mood (fix, add, remove — not fixed, added).

## v1.1.2 — 2026-03-11 — feat: chatbot UI polish and domain context improvements

- Rename chatbot to "PNS 챗봇", set Korean greeting as default, add glassmorphism FAB (72px)
- Add markdown rendering in chat (bold, headings, bullet dots), expand panel to 460×640px, increase fonts
- Add shipping domain context to system prompt (Busan → POD → Destination flow, always show POD)
- Update README with chatbot, i18n, dataflow.md/chatbot.md docs, and LLM env vars

## v1.1.1 — 2026-03-11 — fix: chatbot fuzzy destination matching and multilingual support

- Add fuzzy destination matching (exact substring + difflib) so users can type partial/misspelled names
- Fix data loader to use contains-fallback when exact destination match fails across carriers
- Add Korean language support and full destination list in system prompt for LLM fallback

## v1.1.0 — 2026-03-11 — feat: add AI chatbot for freight rate Q&A

- Add chatbot backend (data_loader, context_builder, llm_client) with OpenAI/Gemini dual support
- Add POST /api/chat endpoint with intent detection, data filtering, and LLM-powered responses
- Add floating chat button + expandable ChatPanel UI in bottom-right corner of dashboard

## v1.0.2 — 2026-03-11 — add: English/Korean UI toggle for freight dashboards

- Add top-right language toggle and shared i18n context for EN/KR interface text
- Translate dashboard labels, tables, empty states, and error messages across ONE, HAPAG, and Summary views
- Keep source data values in English where needed, including destinations, container types, currencies, and route data

## v1.0.1 — 2026-03-11 — fix: API connectivity and cross-platform path issues

- Fix API port detection bug caused by Flask debug reloader overwriting `.api_port`
- Add React dev server proxy to eliminate port mismatch issues
- Fix Windows-style path in `ONE_processor.py` for macOS compatibility
