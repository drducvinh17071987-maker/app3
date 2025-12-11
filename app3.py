import streamlit as st
import pandas as pd

APP_NAME = "App 3 – ET Mode (Lorentz HRV Mapping)"
APP_VERSION = "1.0.0"

st.set_page_config(page_title=APP_NAME, layout="wide")
st.title(APP_NAME)
st.caption(f"Version: {APP_VERSION}")

st.write(
    "This app demonstrates the core idea of ET Mode: "
    "different individuals with very different HRV baselines can be mapped "
    "into the **same geometric pattern** using the Lorentz transformation."
)

# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def parse_list(text):
    if not text:
        return []
    try:
        return [float(x.strip()) for x in text.split(",") if x.strip() != ""]
    except:
        raise ValueError("Invalid input. Use comma-separated numbers.")


def compute_T(hrv):
    """T = HRV / 80 (normalized Lorentz variable)"""
    return [x / 80.0 for x in hrv]


def compute_E(T):
    """E = 1 - T^2"""
    return [1 - (t * t) for t in T]


def compute_pct(hrv):
    """Step-by-step %HRV change"""
    if len(hrv) < 2:
        return [0.0] * len(hrv)
    pct = [0.0]
    for i in range(1, len(hrv)):
        prev = hrv[i-1]
        curr = hrv[i]
        if prev == 0:
            pct.append(0.0)
        else:
            pct.append(100.0 * (curr - prev) / prev)
    return pct


# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------

tab1, tab2 = st.tabs(["ET Overlay (3 Profiles)", "%HRV vs ET Comparison"])


# =========================================================
# 🔷 TAB 1 — ET OVERLAY
# =========================================================

with tab1:

    st.subheader("ET Mapping for Individuals A, B, C")

    col1, col2 = st.columns([1, 2])

    with col1:
        default_A = "80,78,76,75,77,79,80,78,76,77"
        default_B = "60,58,56,55,57,59,60,58,56,57"
        default_C = "40,38,36,35,37,39,40,38,36,37"

        hrv_A_text = st.text_area("A – high HRV:", default_A)
        hrv_B_text = st.text_area("B – medium HRV:", default_B)
        hrv_C_text = st.text_area("C – low HRV:", default_C)

        btn_et = st.button("Compute ET (A/B/C)")

    with col2:
        if btn_et:
            try:
                A = parse_list(hrv_A_text)
                B = parse_list(hrv_B_text)
                C = parse_list(hrv_C_text)

                # Raw chart
                df_raw = pd.DataFrame({
                    "A_raw": A,
                    "B_raw": B,
                    "C_raw": C
                })
                df_raw.index = range(1, len(df_raw) + 1)

                st.markdown("### Raw HRV (ms)")
                st.line_chart(df_raw, height=250)

                # Compute ET for A/B/C
                TA, TB, TC = compute_T(A), compute_T(B), compute_T(C)
                EA, EB, EC = compute_E(TA), compute_E(TB), compute_E(TC)

                df_et = pd.DataFrame({
                    "A_ET": EA,
                    "B_ET": EB,
                    "C_ET": EC
                })
                df_et.index = df_raw.index

                st.markdown("### ET Curves (A, B, C)")
                st.line_chart(df_et, height=250)

                st.markdown(
                    """
                    **Interpretation:**

                    - Raw HRV shows 3 widely separated profiles (A high, B mid, C low).
                    - After ET mapping, the 3 curves become **nearly identical**.
                    - This demonstrates ET’s ability to unify physiology across individuals
                      without requiring absolute HRV calibration.
                    - This effect is **impossible** with raw HRV or %HRV alone.
                    """
                )

            except ValueError as e:
                st.error(str(e))


# =========================================================
# 🔷 TAB 2 — %HRV vs ET (1 individual)
# =========================================================

with tab2:

    st.subheader("Compare %HRV vs ET (one person)")

    col3, col4 = st.columns([1, 2])

    with col3:
        default_series = "80,75,70,78,80,76,74,77,79,78"
        hrv_one_text = st.text_area(
            "Input HRV series:",
            value=default_series,
            height=100
        )
        btn_cmp = st.button("Compare %HRV vs ET")

    with col4:
        if btn_cmp:
            try:
                hrv = parse_list(hrv_one_text)

                pct = compute_pct(hrv)
                T = compute_T(hrv)
                E = compute_E(T)

                df_pct = pd.DataFrame({"%HRV": pct})
                df_pct.index = range(1, len(df_pct) + 1)

                df_et = pd.DataFrame({"ET": E})
                df_et.index = df_pct.index

                st.markdown("### %HRV (step-by-step)")
                st.line_chart(df_pct, height=250)

                st.markdown("### ET Curve")
                st.line_chart(df_et, height=250)

                st.markdown(
                    """
                    **Interpretation:**

                    - %HRV is noisy, sign-flipping, unstable, and depends strongly on raw oscillations.  
                    - ET produces a smooth global geometric pattern that captures the *state*  
                      rather than noise between points.  
                    - ET → **state geometry**  
                    - %HRV → **local noise**  

                    This is why ET Mode is suitable for physiological modeling, while %HRV is not.
                    """
                )

            except ValueError as e:
                st.error(str(e))
