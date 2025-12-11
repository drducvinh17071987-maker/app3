import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# App metadata
# ---------------------------------------------------------
APP_NAME = "App 3 – ET Mode (Core 80 from %HRV)"
APP_VERSION = "2.0.0"

st.set_page_config(page_title=APP_NAME, layout="wide")
st.title(APP_NAME)
st.caption(f"Version: {APP_VERSION}")

st.write(
    "This app applies the ET core-80 transformation on HRV series from three "
    "individuals (A: high HRV, B: medium HRV, C: low HRV). "
    "Pipeline per person:\n\n"
    "HRV → step-by-step %HRV → T = %HRV / 80 → E = 1 − T²."
)

# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def parse_hrv_input(text: str):
    """
    Parse '80, 78, 76' into [80.0, 78.0, 76.0].
    """
    if not text:
        return []
    items = [x.strip() for x in text.split(",")]
    values = []
    for x in items:
        if x == "":
            continue
        try:
            values.append(float(x))
        except ValueError:
            raise ValueError(f"Invalid value: '{x}' (not a number).")
    return values


def compute_pct_hrv(hrv_list):
    """
    Compute step-by-step %HRV:
    %HRV[i] = 100 * (HRV[i] - HRV[i-1]) / HRV[i-1]
    First point = 0.0
    """
    n = len(hrv_list)
    if n == 0:
        return []
    if n == 1:
        return [0.0]

    pct = [0.0]
    for i in range(1, n):
        prev = hrv_list[i - 1]
        curr = hrv_list[i]
        if prev == 0:
            pct.append(0.0)
        else:
            pct.append(100.0 * (curr - prev) / prev)
    return pct


def et_from_pct(pct_list):
    """
    ET core-80 from %HRV:
    T[i] = %HRV[i] / 80
    E[i] = 1 - T[i]^2
    Returns (T_list, E_list).
    """
    T = [x / 80.0 for x in pct_list]
    E = [1.0 - (t * t) for t in T]
    return T, E


# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------

tab1, tab2 = st.tabs(["Overview – raw HRV & ET", "Detail – %HRV, T, ET (3 profiles)"])

# Default example series
default_A = "80,78,76,75,77,79,80,78,76,77"
default_B = "60,58,56,55,57,59,60,58,56,57"
default_C = "40,38,36,35,37,39,40,38,36,37"


# =========================================================
# TAB 1 – OVERVIEW (RAW HRV & ET)
# =========================================================

with tab1:
    st.subheader("Tab 1 – Raw HRV vs ET (3 individuals)")

    col1, col2 = st.columns([1, 2])

    with col1:
        hrv_A_text = st.text_area("A – high HRV (comma-separated):", default_A, height=80)
        hrv_B_text = st.text_area("B – medium HRV:", default_B, height=80)
        hrv_C_text = st.text_area("C – low HRV:", default_C, height=80)

        st.caption("Values must be separated by commas. Example: 80, 78, 76, 75, 77...")

        btn_overview = st.button("Compute raw HRV & ET")

    with col2:
        if btn_overview:
            try:
                A = parse_hrv_input(hrv_A_text)
                B = parse_hrv_input(hrv_B_text)
                C = parse_hrv_input(hrv_C_text)

                if not (A or B or C):
                    st.warning("Please enter at least one HRV profile.")
                else:
                    # ---------- Raw HRV ----------
                    df_raw = pd.DataFrame({
                        "A_raw": A,
                        "B_raw": B,
                        "C_raw": C
                    })
                    df_raw.index = range(1, len(df_raw) + 1)
                    df_raw.index.name = "Step"

                    st.markdown("### Raw HRV (ms)")
                    st.line_chart(df_raw, height=260)

                    # ---------- ET from %HRV, core 80 ----------
                    pctA = compute_pct_hrv(A) if A else []
                    pctB = compute_pct_hrv(B) if B else []
                    pctC = compute_pct_hrv(C) if C else []

                    _, EA = et_from_pct(pctA) if pctA else ([], [])
                    _, EB = et_from_pct(pctB) if pctB else ([], [])
                    _, EC = et_from_pct(pctC) if pctC else ([], [])

                    df_et = pd.DataFrame({
                        "A_ET": EA,
                        "B_ET": EB,
                        "C_ET": EC
                    })
                    df_et.index = range(1, len(df_et) + 1)
                    df_et.index.name = "Step"

                    st.markdown("### ET curves (from %HRV, core 80)")
                    st.line_chart(df_et, height=260)

                    st.markdown(
                        """
                        **Interpretation (overview):**

                        - Raw HRV (top chart) separates A / B / C by baseline.
                        - ET curves (bottom chart), computed from %HRV with a single constant 80,
                          have almost identical shapes; amplitude differences become extremely small.
                        - This shows how ET core-80 compresses different bodies into one common
                          dynamical geometry.
                        """
                    )

            except ValueError as e:
                st.error(str(e))


# =========================================================
# TAB 2 – DETAIL (%HRV, T, ET)
# =========================================================

with tab2:
    st.subheader("Tab 2 – %HRV, T, ET tables and plots (3 individuals)")

    col3, col4 = st.columns([1, 2])

    with col3:
        hrv_A_text2 = st.text_area("A – high HRV:", default_A, height=80)
        hrv_B_text2 = st.text_area("B – medium HRV:", default_B, height=80)
        hrv_C_text2 = st.text_area("C – low HRV:", default_C, height=80)

        st.caption("Same HRV inputs as Tab 1, used here to show the full ET pipeline.")

        btn_detail = st.button("Compute %HRV, T, ET (core 80)")

    with col4:
        if btn_detail:
            try:
                A2 = parse_hrv_input(hrv_A_text2)
                B2 = parse_hrv_input(hrv_B_text2)
                C2 = parse_hrv_input(hrv_C_text2)

                if not (A2 or B2 or C2):
                    st.warning("Please enter at least one HRV profile.")
                else:
                    # ---------- 1. %HRV ----------
                    pctA = compute_pct_hrv(A2) if A2 else []
                    pctB = compute_pct_hrv(B2) if B2 else []
                    pctC = compute_pct_hrv(C2) if C2 else []

                    df_pct = pd.DataFrame({
                        "A_%HRV": pctA,
                        "B_%HRV": pctB,
                        "C_%HRV": pctC
                    })
                    df_pct.index = range(1, len(df_pct) + 1)
                    df_pct.index.name = "Step"

                    st.markdown("### Table – step-by-step %HRV")
                    st.dataframe(df_pct, height=200)

                    # ---------- 2. T = %HRV / 80 ----------
                    TA, _ = et_from_pct(pctA) if pctA else ([], [])
                    TB, _ = et_from_pct(pctB) if pctB else ([], [])
                    TC, _ = et_from_pct(pctC) if pctC else ([], [])

                    df_T = pd.DataFrame({
                        "A_T": TA,
                        "B_T": TB,
                        "C_T": TC
                    })
                    df_T.index = df_pct.index

                    st.markdown("### Table – T values (T = %HRV / 80)")
                    st.dataframe(df_T, height=200)

                    # ---------- 3. E = 1 - T^2 ----------
                    # (We recompute ET to keep code clear)
                    _, EA2 = et_from_pct(pctA) if pctA else ([], [])
                    _, EB2 = et_from_pct(pctB) if pctB else ([], [])
                    _, EC2 = et_from_pct(pctC) if pctC else ([], [])

                    df_ET = pd.DataFrame({
                        "A_ET": EA2,
                        "B_ET": EB2,
                        "C_ET": EC2
                    })
                    df_ET.index = df_pct.index

                    st.markdown("### Table – ET values (E = 1 - T²)")
                    st.dataframe(df_ET, height=200)

                    # ---------- Plots ----------
                    st.markdown("### Plot – %HRV (A, B, C)")
                    st.line_chart(df_pct, height=250)

                    st.markdown("### Plot – ET curves from %HRV (core 80)")
                    st.line_chart(df_ET, height=250)

                    st.markdown(
                        """
                        **Interpretation (detail):**

                        - %HRV table shows different amplitudes for A / B / C.
                        - T = %HRV / 80 puts all three into the same normalized Lorentz input range.
                        - ET = 1 − T² compresses these differences even further: the ET curves are
                          almost indistinguishable between A, B and C.
                        - The same code can be applied to any other individuals: as long as you
                          provide HRV time series, the app computes %HRV, T and ET in exactly the
                          same way.
                        """
                    )

            except ValueError as e:
                st.error(str(e))
