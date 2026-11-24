"""Dispatch three deep harvest-upgrade lanes to the VS Code agent panels over CDP.

Each lane owns a distinct directory so pushes cannot collide, and each carries the verified
facts it needs so no agent has to rediscover them. Kilo is the publisher; Zoo and Copilot write
to their own dirs and push only their own files.
"""
import sys

sys.path.insert(0, ".")
from screen_control.vscode_panels import Panels  # noqa: E402

REPO = "https://github.com/eltonaguiar/antigravity_review_Nov192026.git"
BASE = "42_HARVEST_UPGRADE_2026-11-24"

COMMON = (
    "WORK IN REPO " + REPO + " . If it is not on this machine, clone it to ~/antigravity_review. "
    "The public page is docs/index.html and the harvest page is docs/harvest.html; its data is "
    "docs/data/harvest_signals.json (71 rows). Every claim must cite a file path or a command "
    "output. Never invent a number. If blocked, write BLOCKED plus the exact error and keep going "
    "on the rest. Before any push: git pull --rebase origin main, then push; if rejected, rebase "
    "again and retry. Never force push. Do not touch docs/index.html. "
)

KILO = COMMON + (
    "YOU ARE THE SOLE PUBLISHER for this round. Own " + BASE + "/kilocode/. "
    "TASK: fix the harvest page's rule drift and its classification bugs, with tests. "
    "VERIFIED FACT you may rely on: the published labels are a pure function of the raw counts. "
    "score = (2*strong_buy + buy - sell - 2*strong_sell)/analysts ; buy_side = (strong_buy+buy)/analysts. "
    "Rule: STRONG_BUY if score>=1.0 and buy_side>=0.75 ; BUY if score>=0.3 and buy_side>=0.50 ; "
    "STRONG_SELL if score<=-1.0 and buy_side<=0.15 ; SELL if score<=-0.3 and buy_side<=0.30 ; else HOLD. "
    "That reproduces 71/71 published labels today. But docs/harvest.html legend and "
    "HARVEST_METHODOLOGY.md section 5 still publish the OLD score-only rule, which matches only "
    "60/71 (mismatches: INTC QCOM ADBE SBUX AMGN PFE SO XOM PEP PM SPG). "
    "(1) Stop hand-writing the legend: generate the rule text from the same constants used to "
    "classify, so it cannot drift again. (2) Add a test that recomputes every label from counts and "
    "fails on any mismatch. (3) direction must be computed ONCE in the pipeline and stored in the "
    "JSON; the page must not re-derive it. Add a test asserting KPI counts equal row counts. "
    "Known symptom: DUK at -2.1 renders STABLE while WMT at +2.1 renders IMPROVING, and the header "
    "claims 16 deteriorating against 15 visible rows. (4) Trend threshold must respect the noise "
    "floor: require abs(delta) >= max(2pp, 100/analysts) AND at least 2 net analyst moves; store "
    "n_prior and n_now and tag CHURN_CONTAMINATED when coverage count changed. "
    "(5) Add a per-symbol reason-code enum: NO_COVERAGE_STRUCTURAL, NO_COVERAGE_VENDOR, "
    "SYMBOL_UNMAPPED, ACCESS_DENIED_403, RATE_LIMITED_429, EMPTY_RESPONSE, STALE_OK. Never render an "
    "empty cell without one. (6) Add universe/taxonomy.json with 250-400 leaf nodes over three "
    "orthogonal axes asset_class x wrapper x exposure, each leaf carrying signal_availability "
    "{sell_side: none|look_through|direct, crowd, official_rating}. "
    "Deliver tests that pass, a short REPORT.md listing each fix with before/after evidence, then "
    "make ONE consolidated push covering your directory. Reply STEP DONE with the commit sha."
)

ZOO = COMMON + (
    "Own " + BASE + "/zoocode/. You are the independent verifier: do NOT read Kilo's code first, "
    "derive everything yourself from docs/data/harvest_signals.json. "
    "(1) Recompute every label from the raw counts and publish a mismatch ledger. "
    "(2) Test the claimed rule (STRONG_BUY score>=1.0 and buy_side>=0.75; BUY >=0.3 and >=0.50; "
    "STRONG_SELL <=-1.0 and <=0.15; SELL <=-0.3 and <=0.30; else HOLD) against all 71 rows and say "
    "whether it holds or not. (3) Investigate BRK-B: counts 0/1/3/3/3 on 10 analysts means three "
    "Strong Sells on Berkshire - decide whether that is vendor symbol mapping, a rating-scale error, "
    "or real, and show your evidence. (4) Verify the direction bug: DUK at -2.1 STABLE vs WMT at "
    "+2.1 IMPROVING, and whether KPI counts disagree with row counts. (5) Compute the noise floor "
    "100/analysts per symbol and list which IMPROVING/DETERIORATING labels sit inside noise. "
    "(6) MONTE CARLO: under a null of unchanged analyst opinion, resample each symbol's distribution "
    "keeping N fixed, measure how often a shift of at least the observed magnitude appears by chance, "
    "and report a p-value per symbol. State which 'revisions' survive at 5 percent after "
    "Benjamini-Hochberg. Publish the method and seed so it reproduces. "
    "Write results as JSON plus REPORT.md. Push ONLY files under your own directory, and only after "
    "pulling with rebase. Reply STEP DONE with the commit sha and headline numbers."
)

COPILOT = COMMON + (
    "Own " + BASE + "/ghcopilot/. TASK: add the two signal layers the page is missing, using free "
    "public endpoints only, no credentials. "
    "(1) LOOK-THROUGH CONSENSUS for funds: sell-side analysts rate companies, not funds, so ETFs "
    "currently show zero coverage. Compute fund-level values as holdings-weighted aggregates of the "
    "equity consensus you already have: fund_buy_side = sum(w_i * buy_side_i)/sum(w_i) over covered "
    "holdings, plus coverage_pct = sum(w_i covered)/sum(w_i). Take holdings from issuer daily CSV "
    "files or SEC N-PORT. Label every derived value as derived, not a published rating, and state the "
    "coverage share. Do at least SPY QQQ VTI EEM plus one sector and one bond ETF. "
    "(2) CROWD LAYER from Polymarket Gamma API and, if reachable, Kalshi public endpoints: capture "
    "implied probability, bid/ask spread, volume, liquidity, open interest and time to resolution. "
    "Build the two-layer model: Layer A direct per-symbol matches (rare, record the market id and a "
    "match_confidence of exact|ticker_mention|semantic), Layer B an explicit event-to-asset mapping "
    "table where each row carries the transmission mechanism, expected sign, confidence and a "
    "historical beta with a CI where you can estimate one. Never publish a bare correlation without "
    "the mechanism. "
    "(3) Write the analyst-scorecard specification: the event-study maths, the seven biases that must "
    "be disclosed, and exactly which fields are free versus paid. Do not fabricate P/L. "
    "Respect robots and ToS, rate-limit politely. Push ONLY files under your own directory. "
    "Reply STEP DONE with the commit sha and what actually returned data."
)

panels = Panels()
for name, msg in (("kilo", KILO), ("zoo", ZOO), ("copilot", COPILOT)):
    try:
        r = panels.send(name, msg, verify=False)
        print(f"{name:8} sent -> {r}")
    except Exception as e:
        print(f"{name:8} FAILED {type(e).__name__}: {str(e)[:160]}")
panels.close()
