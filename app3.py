import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# App metadata
# ---------------------------------------------------------
APP_NAME = "App 3 – ET Mode (Core 80 from %HRV)"
APP_VERSION = "2.2.0"

st.set_page_config(page_title=APP_NAME, layout="wide")
st.title(APP_NAME)
st.caption(f"Version: {APP_VERSION}")

st.write(
    "This app applies the ET core-80 transformation on HRV series from three "
    "individuals (A: high HRV, B: medium HRV, C: low HRV).\n\n"
    "Pipeline per person: **HRV → step-by-step %HRV → T = %HRV/80 → E = 1 − T²**.\n"
    "To make ET dynamics visible, we also plot **ET deviation = (1 − E) × 1000**."
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


def build_et_deviation(E_list):
    """
    Build ET deviation signal so that small changes around 1.0 become visible:
    ET_dev[i] = (1 - E[i]) * 1000
    Units: arbitrary "stress units".
    """
    return [(1.0 - e) * 1000.0 for e in E_list]


# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------

tab1, tab2 = st.tabs(
    ["Overview – raw HRV & ET", "Detail – %HRV, T, ET (3 profiles)"]
)

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
        hrv_A_text = st.text_area(
            "A – high HRV (comma-separated):",
            default_A,
            height=80,
            key="A_hrv_tab1",
        )
        hrv_B_text = st.text_area(
            "B – medium HRV:",
            default_B,
            height=80,
            key="B_hrv_tab1",
        )
        hrv_C_text = st.text_area(
            "C – low HRV:",
            default_C,
            height=80,
            key="C_hrv_tab1",
        )

        st.caption("Values must be separated by commas. Example: 80, 78, 76, 75, 77...")

        btn_overview = st.button(
            "Compute raw HRV & ET",
            key="btn_overview_tab1",
        )

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
                    df_raw = pd.DataFrame(
                        {
                            "A_raw": A,
                            "B_raw": B,
                            "C_raw": C,
                        }
                    )
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

                    # ET deviation (zoomed version to see dynamics)
                    A_dev = build_et_deviation(EA)
                    B_dev = build_et_deviation(EB)
                    C_dev = build_et_deviation(EC)

                    df_et_dev = pd.DataFrame(
                        {
                            "A_ET_dev": A_dev,
                            "B_ET_dev": B_dev,
                            "C_ET_dev": C_dev,
                        }
                    )
                    df_et_dev.index = range(1, len(df_et_dev) + 1)
                    df_et_dev.index.name = "Step"

                    st.markdown("### ET deviation curves ( (1 − E) × 1000 )")
                    st.line_chart(df_et_dev, height=260)

                    st.markdown(
                        """
                        **Interpretation (overview):**

                        - Raw HRV (top) separates A / B / C by baseline.
                        - ET deviation (bottom) shows **shape only**:
                          the three profiles share almost the same up/down pattern.
                        - ET deviation rising → stress is increasing; falling → recovery.
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
        hrv_A_text2 = st.text_area(
            "A – high HRV:",
            default_A,
            height=80,
            key="A_hrv_tab2",
        )
        hrv_B_text2 = st.text_area(
            "B – medium HRV:",
            default_B,
            height=80,
            key="B_hrv_tab2",
        )
        hrv_C_text2 = st.text_area(
            "C – low HRV:",
            default_C,
            height=80,
            key="C_hrv_tab2",
        )

        st.caption("Same HRV inputs as Tab 1, used here to show the full ET pipeline.")

        btn_detail = st.button(
            "Compute %HRV, T, ET (core 80)",
            key="btn_detail_tab2",
        )

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

                    df_pct = pd.DataFrame(
                        {
                            "A_%HRV": pctA,
                            "B_%HRV": pctB,
                            "C_%HRV": pctC,
                        }
                    )
                    df_pct.index = range(1, len(df_pct) + 1)
                    df_pct.index.name = "Step"

                    st.markdown("### Table – step-by-step %HRV")
                    st.dataframe(df_pct, height=160)

                    # ---------- 2. T = %HRV / 80 ----------
                    TA, _ = et_from_pct(pctA) if pctA else ([], [])
                    TB, _ = et_from_pct(pctB) if pctB else ([], [])
                    TC, _ = et_from_pct(pctC) if pctC else ([], [])

                    df_T = pd.DataFrame(
                        {
                            "A_T": TA,
                            "B_T": TB,
                            "C_T": TC,
                        }
                    )
                    df_T.index = df_pct.index

                    st.markdown("### Table – T values (T = %HRV / 80)")
                    st.dataframe(df_T, height=160)

                    # ---------- 3. E = 1 - T^2 ----------
                    _, EA2 = et_from_pct(pctA) if pctA else ([], [])
                    _, EB2 = et_from_pct(pctB) if pctB else ([], [])
                    _, EC2 = et_from_pct(pctC) if pctC else ([], [])

                    df_ET = pd.DataFrame(
                        {
                            "A_ET": EA2,
                            "B_ET": EB2,
                            "C_ET": EC2,
                        }
                    )
                    df_ET.index = df_pct.index

                    st.markdown("### Table – ET values (E = 1 − T²)")
                    st.dataframe(df_ET, height=160)

                    # ---------- 4. Plots ----------
                    st.markdown("### Plot – %HRV (A, B, C)")
                    st.line_chart(df_pct, height=220)

                    A_dev2 = build_et_deviation(EA2)
                    B_dev2 = build_et_deviation(EB2)
                    C_dev2 = build_et_deviation(EC2)

                    df_et_dev2 = pd.DataFrame(
                        {
                            "A_ET_dev": A_dev2,
                            "B_ET_dev": B_dev2,
                            "C_ET_dev": C_dev2,
                        }
                    )
                    df_et_dev2.index = df_pct.index

                    st.markdown("### Plot – ET deviation from %HRV ( (1 − E) × 1000 )")
                    st.line_chart(df_et_dev2, height=220)

                    st.markdown(
                        """
                        **Interpretation (detail):**

                        - %HRV shows the raw percentage changes; amplitudes differ between A / B / C.
                        - T = %HRV / 80 normalizes all three into the same Lorentz input space.
                        - ET = 1 − T² is very close to 1.0, so we plot **ET deviation**:
                          (1 − E) × 1000. This reveals the same up/down pattern for all profiles.
                        - In practice, ET deviation rising → stronger stress loading;
                          ET deviation falling → autonomic recovery.
                        """
                    )

            except ValueError as e:
                st.error(str(e))
