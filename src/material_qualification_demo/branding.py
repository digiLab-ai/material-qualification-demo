INDIGO = "#16425B"
KEPPEL = "#16D5C2"
KEY_LIME = "#EBF38B"
WHITE = "#F8FAFC"
SLATE = "#334155"
MUTED = "#64748B"

BRAND_CSS = f"""
<style>
:root {{
    --indigo: {INDIGO};
    --keppel: {KEPPEL};
    --keylime: {KEY_LIME};
    --white: {WHITE};
    --slate: {SLATE};
    --muted: {MUTED};
}}
.main .block-container {{
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}}
h1, h2, h3 {{
    color: var(--indigo);
}}
.digilab-card {{
    border: 1px solid rgba(22,66,91,0.15);
    border-radius: 16px;
    padding: 1rem 1.25rem;
    background: linear-gradient(180deg, rgba(22,213,194,0.08), rgba(235,243,139,0.10));
}}
.metric-caption {{
    color: var(--muted);
    font-size: 0.9rem;
}}
</style>
"""
