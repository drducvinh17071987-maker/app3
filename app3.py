import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# ----------------- App metadata -----------------
APP_NAME = "App 3 – ET Mode (Core 80, 3 HRV profiles)"
APP_VERSION = "2.3.0"

st.set_page_config(page_title=APP_NAME, layout="wide")
st.title(APP_NAME)
st.caption(f"Version: {APP_VERSION}")

# ----------------- Utility functions -----------------
def parse_series(text: str, default_values):
    """Parse comma-separated string into a list of floats."""
    if not text:
        return default_values
    parts = [p.strip() for p in text.split(",") if p.strip() != ""]
    values = []
    for p in parts:
        try:
            values.append(float(p))
        except ValueError:
            return default_values
    if len(values) < 2:
        return default_values
    return values


def compute_pct_change(series):
    """Step-by-step % change of HRV (first point = 0%)."""
    pct = [0.0]
    for i in range(1, len(series)):
        prev = series[i - 1]
        curr = series[i]
        if prev == 0:
            pct.append(0.0)
        else:
            pct.append((curr - prev) / prev * 100.0)
    return pct


def compute_T_from_pct(pct_series, core_value=80.0):
    """Normalize %HRV to T using fixed core value (80)."""
    return [x / core_value for x in pct_series]


def compute_E_from_T(T_series):
    """Energy-like metric from T."""
    return [1.0 - (t ** 2) for t in T_series]


def build_pct_T_E_tables(A_raw, B_raw, C_raw):
    """From raw HRV 3 người -> bảng %HRV, T, E."""
    A_pct = compute_pct_change(A_raw)
    B_pct = compute_pct_change(B_raw)
    C_pct = compute_pct_change(C_raw)

    A_T = compute_T_from_pct(A_pct)
    B_T = compute_T_from_pct(B_pct)
    C_T = compute_T_from_pct(C_pct)

    A_E = compute_E_from_T(A_T)
    B_E = compute_E_from_T(B_T)
    C_E = compute_E_from_T(C_T)

    steps = list(range(1, len(A_raw) + 1))

    df_pct = pd.DataFrame(
        {"Step": steps, "A_%HRV": A_pct, "B_%HRV": B_pct, "C_%HRV": C_pct}
    )

    df_T_E = pd.DataFrame(
        {
            "Step": steps,
            "A_T": A_T,
            "B_T": B_T,
            "C_T": C_T,
            "A_ET": A_E,
            "B_ET": B_E,
            "C_ET": C_E,
        }
    )

    return df_pct, df_T_E


def compute_ET_deviation(df_T_E, base_scale=1000.0):
    """
    Từ bảng T & E -> độ lệch ET = (1 - E) * base_scale.
    base_scale cố định để ET luôn cùng đơn vị;
    room sẽ do slider điều khiển trục Y.
    """
    A_dev = [(1.0 - e) * base_scale for e in df_T_E["A_ET"]]
    B_dev = [(1.0 - e) * base_scale for e in df_T_E["B_ET"]]
    C_dev = [(1.0 - e) * base_scale for e in df_T_E["C_ET"]]

    steps = df_T_E["Step"].tolist()
    df_dev = pd.DataFrame(
        {"Step": steps, "A_ET_dev": A_dev, "B_ET_dev": B_dev, "C_ET_dev": C_dev}
    )
    return df_dev


def make_et_chart(df_dev, room_value, title: str):
    """
    Vẽ biểu đồ ET deviation với trục Y khóa domain theo room_value.
    room_value = “room” bạn nhập (ví dụ 300, 500, 1000).
    """
    df_long = df_dev.melt("Step", var_name="Profile", value_name="ET_dev")
    chart = (
        alt.Chart(df_long)
        .mark_line()
        .encode(
            x=alt.X("Step:Q", axis=alt.Axis(title="Step")),
            y=alt.Y(
                "ET_dev:Q",
                axis=alt.Axis(title=f"ET deviation (room = {room_value:g})"),
                scale=alt.Scale(domain=[0, room_value]),
            ),
            color=alt.Color("Profile:N", legend=alt.Legend(title="Profile")),
        )
        .properties(height=260, title=title)
    )
    return chart


# ----------------- Default HRV profiles -----------------
A_default = [80, 78, 76, 75, 79, 80, 78, 76, 75, 77]
B_default = [60, 58, 56, 55, 59, 60, 58, 56, 55, 57]
C_default = [40, 38, 36, 35, 37, 39, 40, 38, 36, 37]

# ----------------- Tabs -----------------
tab_overview, tab_detail = st.tabs(
    ["Overview – raw HRV & ET deviation", "Detail – %HRV, T, ET"]
)

# =========================================================
# TAB 1 – OVERVIEW
# =========================================================
with tab_overview:
    st.subheader("Overview – raw HRV and ET deviation (3 profiles)")

    # Room cho biểu đồ ET overview (khóa trục Y)
    room_overview = st.number_input(
        "ET room for overview plot (Y-axis max)",
        min_value=10.0,
        max_value=20000.0,
        value=3000.0,
        step=50.0,
        help="Thay đổi room để đường ET nằm cao/thấp hơn trên trục Y.",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        text_A = st.text_area(
            "A – high HRV (comma-separated)",
            value=", ".join(str(x) for x in A_default),
            height=80,
        )
    with col2:
        text_B = st.text_area(
            "B – medium HRV (comma-separated)",
            value=", ".join(str(x) for x in B_default),
            height=80,
        )
    with col3:
        text_C = st.text_area(
            "C – low HRV (comma-separated)",
            value=", ".join(str(x) for x in C_default),
            height=80,
        )

    if st.button("Compute raw HRV & ET (overview)"):
        A_raw = parse_series(text_A, A_default)
        B_raw = parse_series(text_B, B_default)
        C_raw = parse_series(text_C, C_default)

        df_pct, df_T_E = build_pct_T_E_tables(A_raw, B_raw, C_raw)
        df_dev = compute_ET_deviation(df_T_E, base_scale=1000.0)

        steps = df_T_E["Step"].tolist()
        df_raw_plot = pd.DataFrame(
            {"Step": steps, "A_raw": A_raw, "B_raw": B_raw, "C_raw": C_raw}
        ).set_index("Step")

        st.write("### Raw HRV (ms)")
        st.line_chart(df_raw_plot)

        st.write("### ET deviation curves (from raw %HRV)")
        et_chart = make_et_chart(
            df_dev, room_overview, title="ET deviation (overview)"
        )
        st.altair_chart(et_chart, use_container_width=True)

        st.write(
            "**Interpretation (overview):** "
            "Raw HRV cho thấy ngưỡng khác nhau giữa A / B / C, "
            "còn ET deviation cho thấy mức độ mỗi cơ thể rời khỏi trạng thái trung tính."
        )

# =========================================================
# TAB 2 – DETAIL
# =========================================================
with tab_detail:
    st.subheader("Detail – %HRV, T, ET (three profiles)")

    room_detail = st.number_input(
        "ET room for detailed plot (Y-axis max)",
        min_value=10.0,
        max_value=20000.0,
        value=3000.0,
        step=50.0,
        help="Thay đổi room để quan sát rõ hơn độ chênh ET giữa A / B / C.",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        text_A2 = st.text_area(
            "A – high HRV (detail)",
            value=", ".join(str(x) for x in A_default),
            height=80,
        )
    with col2:
        text_B2 = st.text_area(
            "B – medium HRV (detail)",
            value=", ".join(str(x) for x in B_default),
            height=80,
        )
    with col3:
        text_C2 = st.text_area(
            "C – low HRV (detail)",
            value=", ".join(str(x) for x in C_default),
            height=80,
        )

    if st.button("Compute %HRV, T, ET"):
        A_raw2 = parse_series(text_A2, A_default)
        B_raw2 = parse_series(text_B2, B_default)
        C_raw2 = parse_series(text_C2, C_default)

        df_pct2, df_T_E2 = build_pct_T_E_tables(A_raw2, B_raw2, C_raw2)
        df_dev2 = compute_ET_deviation(df_T_E2, base_scale=1000.0)

        # Tables – gọn, hiển thị song song
        st.markdown("### Tables – step-by-step values")
        col_tbl1, col_tbl2 = st.columns(2)
        with col_tbl1:
            st.markdown("**Table – %HRV**")
            st.dataframe(df_pct2, height=220, use_container_width=True)
        with col_tbl2:
            st.markdown("**Table – T and ET**")
            st.dataframe(df_T_E2, height=220, use_container_width=True)

        # Plot %HRV
        st.markdown("### Plot – %HRV (A, B, C)")
        df_pct_plot = df_pct2.set_index("Step")[["A_%HRV", "B_%HRV", "C_%HRV"]]
        st.line_chart(df_pct_plot)

        # Plot ET deviation (detail) với room cố định
        st.markdown("### Plot – ET deviation from %HRV (room-controlled)")
        et_chart_detail = make_et_chart(
            df_dev2, room_detail, title="ET deviation (detail, 3 profiles)"
        )
        st.altair_chart(et_chart_detail, use_container_width=True)

        st.markdown(
            """
**Interpretation (detail):**

- `%HRV` vẫn phụ thuộc biên độ riêng của từng profile (A/B/C).  
- ET deviation nén ba profile về cùng một khung động học: cùng pattern tăng/giảm,
  khác nhau chủ yếu ở mức lệch khỏi trung tính.  
- Room cho phép bạn phóng to/thu nhỏ độ lệch này để quan sát hoặc so sánh nhiều cá thể.
"""
        )
