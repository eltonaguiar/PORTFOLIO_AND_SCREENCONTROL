# PROGRESS_LOG

One line per scheduled run: `YYYY-MM-DDTHH:MMZ | item N | verdict | commit`.

2026-11-22T09:55Z | item 1 | PASS — S1-S6 static gates hold on our own harness | see STATIC_GATE_AUDIT.md
2026-11-22T10:05Z | item 2 | PASS — kernel/capture.py + 8 tests (real grab, crop, 1.5x mapping) | see 01-screen-control-llm/tests
2026-11-22T11:20Z | A1 | PASS — kernel/resolve.py + 10 tests; live run proves resolve/fill/send/done/extract on Chrome via element indices
2026-11-22T11:55Z | extraction | PASS — extract.py rebuilds the app paste-all doc from the AX tree; diff vs expected = MATCH (3/3 panels)
2026-11-22T12:10Z | multi-site run | PARTIAL — arena+chatplayground reached signed-in; blocked on Chrome background key/scroll (foreground-only) and composer leaving the AX tree; rules captured in runs/20261122_multi_site_blockers.md
