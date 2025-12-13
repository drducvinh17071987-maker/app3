import streamlit as st
import pandas as pd
import altair as alt

# =========================
# PAGE
# =========================
st.set_page_config(page_title="DN Sentinel Kernel (No-ML)", layout="wide")

# =========================
# DESIGN CONSTANTS
# =========================
# Per-signal K (hidden, not explained in UI)
K_HRV = 80.0
K_VO2 = 60.0

# Colors
C_GREEN = "#00C853"
C_YELLOW = "#FFD600"
C_RED = "#D50000"
C_INFO = "#90A4AE"
C_BAR_BG = "#E0E0E0"
C_CARD_BG = "#11111108"

# Drop thresholds (keep consistent across tabs to avoid future edits)
DN_GREEN = 0.95
DN_RED = 0.85

# =========================
# HELPERS
# =========================
def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def compute_state(pct_change: float, dn_core: float, K: float):
    """
    Same state logic for each tab:
    - Rise: GREEN unless spike/noise (INFO). Noise threshold = K (hidden).
    - Drop: uses DN thresholds (0.95, 0.85).
    """
    if pct_change >= K:
        return "INFO", "Possible spike / sensor noise", C_INFO
    if pct_change > 0:
        return "GREEN", "Recovery / rebound", C_GREEN
    if pct_change < 0:
        if dn_core < DN_RED:
            return "RED", "Reserve collapsing – trigger recommended", C_RED
        if dn_core < DN_GREEN:
            return "YELLOW", "Load increasing", C_YELLOW
        return "GREEN", "Stable", C_GREEN
    return "GREEN", "Stable", C_GREEN

def render_tab_single_signal(
    title: str,
    unit: str,
    x_title: str,
    k_value: float,
    key_prefix: str,
    default_prev: float,
    default_curr: float,
):
    """
    Renders one tab with the exact same layout as HRV version:
    - Top: 2 inputs + CALCULATE
    - Main: 2 columns
        Left: cards + message + raw chart (under message)
        Right: %change bar + DN Sentinel bar
    - DN Sentinel (0–2) is ONE number matching the bar.
    """

    st.subheader(title)

    # ---------- INPUTS ----------
    in1, in2 = st.columns([1, 1], gap="large")
    with in1:
        prev = st.number_input(f"{x_title} (t-1) {unit}", value=float(default_prev), step=1.0, key=f"{key_prefix}_prev")
    with in2:
        curr = st.number_input(f"{x_title} (t) {unit}", value=float(default_curr), step=1.0, key=f"{key_prefix}_curr")

    do_calc = st.button("CALCULATE", type="primary", key=f"{key_prefix}_calc")

    state_key = f"{key_prefix}_res"
    if state_key not in st.session_state:
        st.session_state[state_key] = None

    if do_calc:
        # ---------- CORE ----------
        delta = curr - prev
        pct = 0.0 if prev == 0 else 100.0 * delta / prev  # percent change

        TT_signed = pct / k_value
        TT_abs = abs(TT_signed)

        DN_core = 1.0 - (TT_abs ** 2)
        DN_core = clamp(DN_core, 0.0, 1.0)

        state, msg, s_color = compute_state(pct, DN_core, k_value)

        # ---------- DN SENTINEL (0–2): ONE NUMBER ----------
        if state == "INFO" or pct == 0:
            DN_sentinel = 1.0
        elif pct > 0:
            TT_pos = clamp(TT_signed, 0.0, 1.0)
            DN_sentinel = 1.0 + TT_pos
        else:
            DN_sentinel = DN_core

        st.session_state[state_key] = {
            "prev": prev,
            "curr": curr,
            "delta": delta,
            "pct": pct,
            "DN_core": DN_core,
            "DN_sentinel": DN_sentinel,
            "state": state,
            "msg": msg,
            "s_color": s_color,
        }

    res = st.session_state[state_key]
    if res is None:
        st.info("Nhập 2 giá trị rồi bấm **CALCULATE**.")
        return

    prev = res["prev"]
    curr = res["curr"]
    delta = res["delta"]
    pct = res["pct"]
    DN_sentinel = res["DN_sentinel"]
    DN_core = res["DN_core"]
    state = res["state"]
    msg = res["msg"]
    s_color = res["s_color"]

    # ---------- MAIN LAYOUT ----------
    left, right = st.columns([1, 1], gap="large")

    # =========================
    # LEFT COLUMN
    # =========================
    with left:
        a, b, c = st.columns([1, 1, 1], gap="medium")

        with a:
            st.markdown(
                f"""
                <div style="padding:14px;border-radius:12px;background:{C_CARD_BG};">
                  <div style="font-size:12px;opacity:0.7;">%Δ</div>
                  <div style="font-size:34px;font-weight:800;">{pct:+.1f}%</div>
                  <div style="font-size:12px;opacity:0.65;">Δ = {delta:+.3f} {unit}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with b:
            st.markdown(
                f"""
                <div style="padding:14px;border-radius:12px;background:{C_CARD_BG};">
                  <div style="font-size:12px;opacity:0.7;">DN Sentinel (0–2)</div>
                  <div style="font-size:34px;font-weight:800;">{DN_sentinel:.3f}</div>
                  <div style="font-size:12px;opacity:0.65;">(same value as the bar)</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c:
            st.markdown(
                f"""
                <div style="padding:14px;border-radius:12px;background:{s_color};color:#111;">
                  <div style="font-size:12px;font-weight:900;letter-spacing:0.5px;">STATE</div>
                  <div style="font-size:34px;font-weight:900;">{state}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        if state == "RED":
            st.error(msg)
        elif state == "YELLOW":
            st.warning(msg)
        elif state == "INFO":
            st.info(msg)
        else:
            st.success(msg)

        st.caption("Single-signal · Time-dynamic processing · No ML · No absolute threshold shown.")

        # ---- 1) RAW CHART (UNDER MESSAGE) ----
        st.subheader(f"1) {x_title} raw")
        df_raw = pd.DataFrame({"Time": ["t-1", "t"], x_title: [prev, curr]})

        chart_raw = (
            alt.Chart(df_raw)
            .mark_line(point=True)
            .encode(
                x=alt.X("Time:N", sort=["t-1", "t"], title="Time"),
                y=alt.Y(f"{x_title}:Q", title=f"{x_title} ({unit})", scale=alt.Scale(zero=False))
            )
            .properties(height=230)
        )
        st.altair_chart(chart_raw, use_container_width=True)

    # =========================
    # RIGHT COLUMN
    # =========================
    with right:
        # ---- 2) %Δ BAR ----
        st.subheader("2) %Δ (linear velocity)")
        df_pct = pd.DataFrame({"label": ["%Δ"], "value": [pct]})

        if state == "INFO":
            v_color = C_INFO
        else:
            v_color = C_GREEN if pct >= 0 else C_RED

        bar = alt.Chart(df_pct).mark_bar(color=v_color, cornerRadius=6).encode(
            y=alt.Y("label:N", title=""),
            x=alt.X("value:Q", title="% change",
                    scale=alt.Scale(domain=[-100, 100]),
                    axis=alt.Axis(format=".0f"))
        )
        zero_line = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="#333", strokeWidth=2).encode(x="x:Q")
        txt = alt.Chart(df_pct).mark_text(
            align="left", dx=8, color="#111", fontSize=16, fontWeight="bold"
        ).encode(
            y="label:N", x="value:Q", text=alt.Text("value:Q", format="+.1f")
        )
        st.altair_chart((bar + zero_line + txt).properties(height=120), use_container_width=True)

        # ---- 3) DN SENTINEL BAR ----
        st.subheader("3) DN Sentinel (0–2)")

        if state == "INFO":
            g_color = C_INFO
        elif state == "GREEN":
            g_color = C_GREEN
        elif state == "YELLOW":
            g_color = C_YELLOW
        else:
            g_color = C_RED

        bg = alt.Chart(pd.DataFrame({"x0": [0], "x1": [2], "y": ["bar"]})).mark_bar(
            color=C_BAR_BG, cornerRadius=8
        ).encode(
            x=alt.X("x0:Q", scale=alt.Scale(domain=[0, 2]), title=""),
            x2="x1:Q",
            y=alt.Y("y:N", title="")
        )

        fg = alt.Chart(pd.DataFrame({"x0": [0], "x1": [DN_sentinel], "y": ["bar"]})).mark_bar(
            color=g_color, cornerRadius=8
        ).encode(x="x0:Q", x2="x1:Q", y="y:N")

        mid = alt.Chart(pd.DataFrame({"x": [1.0]})).mark_rule(color="#111", strokeWidth=2).encode(x="x:Q")

        # thresholds reference on left side
        t85 = alt.Chart(pd.DataFrame({"x": [DN_RED]})).mark_rule(
            color="#444", strokeDash=[5, 5], strokeWidth=2
        ).encode(x="x:Q")
        t95 = alt.Chart(pd.DataFrame({"x": [DN_GREEN]})).mark_rule(
            color="#444", strokeDash=[5, 5], strokeWidth=2
        ).encode(x="x:Q")

        val = alt.Chart(pd.DataFrame({"x": [DN_sentinel], "y": ["bar"], "t": [f"{DN_sentinel:.3f}"]})).mark_text(
            align="left", dx=8, color="#111", fontSize=16, fontWeight="bold"
        ).encode(x="x:Q", y="y:N", text="t:N")

        labels_df = pd.DataFrame({
            "x": [0.15, 1.0, 1.85],
            "y": ["bar", "bar", "bar"],
            "t": ["DROP", "NEUTRAL", "RECOVERY"]
        })
        lbl = alt.Chart(labels_df).mark_text(
            dy=-22, color="#333", fontSize=11, fontWeight="bold"
        ).encode(x="x:Q", y="y:N", text="t:N")

        chart_dn = alt.layer(bg, fg, mid, t85, t95, val, lbl).properties(height=130)
        st.altair_chart(chart_dn, use_container_width=True)

        st.caption("0–1: reserve contraction (DN core) · 1.0: neutral · 1–2: recovery (1 + TT⁺).")

def render_about_tab():
    st.subheader("DN Kernel (No-ML)")

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown(
            """
**What it is**
- DN Sentinel is an always-on **deterministic** guardrail.
- It processes **one raw signal at a time** (HRV or VO₂).
- It uses only **two consecutive points** (t-1 → t).
- **No training, no inference, no model, no dataset.**
- Constant-time compute (**O(1)**), suitable for realtime.

**What it shows**
- **DN < 1.0**  → reserve contracting (DROP)
- **DN = 1.0**  → neutral
- **DN > 1.0**  → recovery / rebound (RECOVERY)

**Key point**
- Same kernel, reused across different signals.
- No fusion. No composite index. One channel per tab.
            """
        )

    with right:
        st.markdown(
            """
**How it works (concept)**

Raw signal (single channel)
↓
Relative change (velocity)
↓
Time-normalized mapping
↓
DN Sentinel (0–2) + State

**Design intent**
- DN Sentinel can run continuously,
  and optionally trigger heavier analytics only when needed.
            """
        )

# =========================
# APP HEADER
# =========================
st.title("DN Sentinel Kernel (No-ML)")

tabs = st.tabs(["HRV", "VO₂", "About"])

with tabs[0]:
    # Keep HRV tab identical structure; K=80
    render_tab_single_signal(
        title="HRV Sentinel",
        unit="ms",
        x_title="HRV",
        k_value=K_HRV,
        key_prefix="hrv",
        default_prev=20.0,
        default_curr=22.0,
    )

with tabs[1]:
    # VO2 tab identical layout; K=60
    render_tab_single_signal(
        title="VO₂ Sentinel",
        unit="ml/kg/min",
        x_title="VO₂",
        k_value=K_VO2,
        key_prefix="vo2",
        default_prev=25.0,
        default_curr=30.0,
    )

with tabs[2]:
    render_about_tab()
