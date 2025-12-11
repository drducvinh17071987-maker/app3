import streamlit as st
import pandas as pd
import numpy as np

# -------------------------
# App metadata
# -------------------------
APP_NAME = "App 3 – ET Mode (Core 80)"
APP_VERSION = "2.2.0"

st.set_page_config(page_title=APP_NAME, layout="wide")
st.title(APP_NAME)
st.caption(f"Version {APP_VERSION}")

st.write(
    """
This app shows how the Core-80 transform compresses three different HRV
profiles (high / medium / low) into one common dynamical pattern.
"""
)

CORE_REF = 80.0          # fixed reference (80)
ET_DEV_SCALE = 300.0     # scale for (1 - E) so that curves stay close together


# -------------------------
# Utility functions
# -------------------------
def parse_series(text: str):
    """Parse comma-separated HRV values into a numpy array."""
    try:
        parts = [p.strip() for p in text.split(",") if p.strip() != ""]
        values = np.array([float(p) for p in parts], dtype=float)
        if values.size < 2:
            return None, "Please enter at least two values for each series."
        return values, None
    except Exception:
        return None, "Input must be numbers separated by commas."


def step_pct_change(series: np.ndarray):
    """
    Step-by-step %HRV:
    first step = 0, then 100 * (x[i] - x[i-1]) / x[i-1]
    """
    pct = [0.0]
    for i in range(1, len(series)):
        prev = series[i - 1]
        curr = series[i]
        if prev == 0:
            pct.append(0.0)
        else:
            pct.append(100.0 * (curr - prev) / prev)
    return np.array(pct, dtype=float)


def compute_T_and_E(pct_hrv: np.ndarray):
    """Core-80 transform: T from %HRV, then ET value E."""
    T = pct_hrv / CORE_REF
    E = 1.0 - T**2
    return T, E


def compute_et_dev(E: np.ndarray):
    """Deviation from the neutral state, scaled for plotting."""
    return (1.0 - E) * ET_DEV_SCALE


# -------------------------
# Layout – tabs
# -------------------------
tab1, tab2 = st.tabs(
    ["Overview – raw HRV & ET", "Detail – %HRV, T, ET (3 profiles)"]
)

# ===========================================================
# TAB 1 – raw HRV + ET deviation (overview)
# ===========================================================
with tab1:
    st.subheader("Input – three HRV profiles (ms)")

    default_A = "80,78,76,75,74,60,74,75,76,78"
    default_B = "60,58,57,56,55,45,55,56,57,58"
    default_C = "40,39,38,37,37,30,37,37,38,39"

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        text_A = st.text_area("A – high HRV", value=default_A, height=80)
    with col_b:
        text_B = st.text_area("B – medium HRV", value=default_B, height=80)
    with col_c:
        text_C = st.text_area("C – low HRV", value=default_C, height=80)

    if st.button("Compute raw HRV & ET", type="primary", key="btn_tab1"):
        A_raw, errA = parse_series(text_A)
        B_raw, errB = parse_series(text_B)
        C_raw, errC = parse_series(text_C)

        errors = [e for e in [errA, errB, errC] if e is not None]
        if errors:
            st.error(" / ".join(errors))
        else:
            # Ensure same length
            n = min(len(A_raw), len(B_raw), len(C_raw))
            A_raw = A_raw[:n]
            B_raw = B_raw[:n]
            C_raw = C_raw[:n]
            steps = np.arange(1, n + 1)

            # %HRV for each
            A_pct = step_pct_change(A_raw)
            B_pct = step_pct_change(B_raw)
            C_pct = step_pct_change(C_raw)

            # T, E, ET_dev
            A_T, A_E = compute_T_and_E(A_pct)
            B_T, B_E = compute_T_and_E(B_pct)
            C_T, C_E = compute_T_and_E(C_pct)

            A_dev = compute_et_dev(A_E)
            B_dev = compute_et_dev(B_E)
            C_dev = compute_et_dev(C_E)

            # -------- Raw HRV plot --------
            st.markdown("---")
            st.subheader("Raw HRV (ms)")

            df_raw = pd.DataFrame(
                {
                    "Step": steps,
                    "A_raw": A_raw,
                    "B_raw": B_raw,
                    "C_raw": C_raw,
                }
            ).set_index("Step")

            st.line_chart(df_raw, height=260)

            # -------- ET deviation plot --------
            st.subheader("ET deviation curves (scaled)")

            df_dev = pd.DataFrame(
                {
                    "Step": steps,
                    "A_ET_dev": A_dev,
                    "B_ET_dev": B_dev,
                    "C_ET_dev": C_dev,
                }
            ).set_index("Step")

            st.line_chart(df_dev, height=260)

            st.markdown(
                """
**Interpretation (overview)**  
* The three raw HRV profiles are very different in absolute value.  
* After the Core-80 transform, all three ET-deviation curves follow almost the
  same pattern: spikes and recoveries are aligned, amplitude differs only slightly.
"""
            )

# ===========================================================
# TAB 2 – %HRV, T, ET (detail)
# ===========================================================
with tab2:
    st.subheader("Tab 2 – %HRV, T and ET (three profiles)")

    default_A2 = "80,78,76,75,74,60,74,75,76,78"
    default_B2 = "60,58,57,56,55,45,55,56,57,58"
    default_C2 = "40,39,38,37,37,30,37,37,38,39"

    col_a2, col_b2, col_c2 = st.columns(3)

    with col_a2:
        text_A2 = st.text_area("A – high HRV", value=default_A2, height=80)
    with col_b2:
        text_B2 = st.text_area("B – medium HRV", value=default_B2, height=80)
    with col_c2:
        text_C2 = st.text_area("C – low HRV", value=default_C2, height=80)

    if st.button("Compute %HRV, T, ET", type="primary", key="btn_tab2"):
        A_raw2, errA2 = parse_series(text_A2)
        B_raw2, errB2 = parse_series(text_B2)
        C_raw2, errC2 = parse_series(text_C2)

        errors2 = [e for e in [errA2, errB2, errC2] if e is not None]
        if errors2:
            st.error(" / ".join(errors2))
        else:
            n2 = min(len(A_raw2), len(B_raw2), len(C_raw2))
            A_raw2 = A_raw2[:n2]
            B_raw2 = B_raw2[:n2]
            C_raw2 = C_raw2[:n2]
            steps2 = np.arange(1, n2 + 1)

            # %HRV
            A_pct2 = step_pct_change(A_raw2)
            B_pct2 = step_pct_change(B_raw2)
            C_pct2 = step_pct_change(C_raw2)

            # T, E, ET_dev
            A_T2, A_E2 = compute_T_and_E(A_pct2)
            B_T2, B_E2 = compute_T_and_E(B_pct2)
            C_T2, C_E2 = compute_T_and_E(C_pct2)

            A_dev2 = compute_et_dev(A_E2)
            B_dev2 = compute_et_dev(B_E2)
            C_dev2 = compute_et_dev(C_E2)

            # ---------- tables (compact, trong expander) ----------
            with st.expander("Detailed values (%HRV, T, ET)"):
                df_pct = pd.DataFrame(
                    {
                        "Step": steps2,
                        "A_%HRV": np.round(A_pct2, 3),
                        "B_%HRV": np.round(B_pct2, 3),
                        "C_%HRV": np.round(C_pct2, 3),
                    }
                )

                df_T = pd.DataFrame(
                    {
                        "Step": steps2,
                        "A_T": np.round(A_T2, 5),
                        "B_T": np.round(B_T2, 5),
                        "C_T": np.round(C_T2, 5),
                    }
                )

                df_E = pd.DataFrame(
                    {
                        "Step": steps2,
                        "A_ET": np.round(A_E2, 6),
                        "B_ET": np.round(B_E2, 6),
                        "C_ET": np.round(C_E2, 6),
                    }
                )

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.markdown("**Table – step-by-step %HRV**")
                    st.dataframe(
                        df_pct,
                        use_container_width=True,
                        hide_index=True,
                        height=220,
                    )

                with c2:
                    st.markdown("**Table – T values (from %HRV)**")
                    st.dataframe(
                        df_T,
                        use_container_width=True,
                        hide_index=True,
                        height=220,
                    )

                with c3:
                    st.markdown("**Table – ET values**")
                    st.dataframe(
                        df_E,
                        use_container_width=True,
                        hide_index=True,
                        height=220,
                    )

            # ---------- plots ----------
            st.markdown("---")
            st.markdown("### Plot – %HRV (A, B, C)")

            df_pct_plot = pd.DataFrame(
                {
                    "Step": steps2,
                    "A_%HRV": A_pct2,
                    "B_%HRV": B_pct2,
                    "C_%HRV": C_pct2,
                }
            ).set_index("Step")

            st.line_chart(df_pct_plot, height=260)

            st.markdown("### Plot – ET deviation from %HRV (scaled)")

            df_dev_plot = pd.DataFrame(
                {
                    "Step": steps2,
                    "A_ET_dev": A_dev2,
                    "B_ET_dev": B_dev2,
                    "C_ET_dev": C_dev2,
                }
            ).set_index("Step")

            st.line_chart(df_dev_plot, height=260)

            st.markdown(
                """
**Interpretation (detail)**  
* %HRV lines show different amplitudes between A / B / C.  
* After the Core-80 transform, ET-deviation curves follow almost the same
  pattern; main spikes and recoveries are aligned in time.  
* This illustrates how different bodies can be mapped into one shared
  dynamical pattern.
"""
            )
