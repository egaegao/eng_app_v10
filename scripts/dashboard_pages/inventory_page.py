import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# ==============================
# CONFIG & HELPERS
# ==============================
METRIC_ORDER = ["exposed", "buried", "flooded"]

METRIC_LABEL = {
    "exposed": "Exposed",
    "buried": "Buried",
    "flooded": "Flooded",
}

METRIC_COLOR = {
    "exposed": "#2563eb",
    "buried": "#64748b",
    "flooded": "#dc2626",
}


def format_ton(val):
    if val is None or pd.isna(val):
        return "-"
    return f"{int(round(val)):,}".replace(",", ".")


def render_kpi_card(title, actual_val, delta_wow=None):
    def get_delta_html(delta, title_type):
        if delta is None:
            return ""

        # LOGIKA WARNA INVENTORY:
        # Exposed naik = Bagus (Hijau). Selain itu (Buried/Flooded) naik = Buruk (Merah).
        is_positive_metric = title_type.lower() in ["exposed", "exposed ratio"]
        
        if is_positive_metric:
            color = "#16a34a" if delta >= 0 else "#dc2626"
            bg_color = "#f0fdf4" if delta >= 0 else "#fef2f2"
        else:
            color = "#dc2626" if delta >= 0 else "#16a34a"
            bg_color = "#fef2f2" if delta >= 0 else "#f0fdf4"

        symbol = "▲" if delta >= 0 else "▼"

        return f"""
        <div style="
            display:flex; 
            flex-direction:column; 
            align-items:center; 
            background-color:{bg_color}; 
            padding:6px 10px; 
            border-radius:8px;
            min-width:80px;
            border:1px solid #e5e7eb;
        ">
            <span style="font-size:11px; color:#6b7280; font-weight:700;">WoW</span>
            <span style="color:{color}; font-weight:900; font-size:18px;">
                {symbol}{abs(delta):.1f}%
            </span>
        </div>
        """

    wow_html = get_delta_html(delta_wow, title)

    card_html = f"""
    <div style="
        border:1px solid #e5e7eb;
        border-left:6px solid #2563eb;
        border-radius:14px;
        padding:14px 16px;
        background:white;
        font-family:'Inter', sans-serif;
        box-shadow:0 4px 12px rgba(0,0,0,0.08);
        height:120px;
        display:flex;
        justify-content:space-between;
        align-items:center;
    ">
        <div>
            <div style="
                font-size:14px; 
                font-weight:800; 
                color:#111827; 
                text-transform:uppercase; 
                margin-bottom:6px;
                letter-spacing:0.3px;
            ">
                {title}
            </div>
            <div style="font-size:32px; font-weight:900; color:#111827;">
                {actual_val}
            </div>
        </div>
        <div style="display:flex; gap:10px;">
            {wow_html}
        </div>
    </div>
    """
    components.html(card_html, height=140)


def render_clean_table(df, height=350):
    # PATCH 3: LIMIT TABLE (Mencegah UI berat jika data besar)
    df = df.head(200)
    
    html = df.to_html(index=False, border=0, justify="center")

    styled = f"""
    <div id="inventory-table-container" style="overflow-x:auto; max-height:{height}px; overflow-y:auto; border-radius:10px; border:1px solid #e5e7eb; margin-bottom:15px;">
    <style>
    #inventory-table-container table {{
        border-collapse: collapse;
        width: 100%;
        font-size: 14px;
        font-family: 'Inter', sans-serif;
    }}
    #inventory-table-container thead th {{
        background-color: #1e293b !important;
        color: #ffffff !important;
        font-weight: 700;
        text-align: center;
        vertical-align: middle;
        padding: 12px 8px;
        border-bottom: 2px solid #0f172a;
        position: sticky;
        top: 0;
        z-index: 10;
    }}
    #inventory-table-container tbody tr:last-child {{
        background-color: #f1f5f9;
        font-weight: 800;
    }}
    #inventory-table-container td {{
        color: #111827;
        font-weight: 500;
        text-align: center;
        vertical-align: middle;
        padding: 10px 8px;
        border-bottom: 1px solid #f1f5f9;
        font-family: 'Inter', sans-serif;
    }}
    #inventory-table-container tr:nth-child(even) {{
        background-color: #f9fafb;
    }}
    #inventory-table-container tr:hover {{
        background-color: #f1f5f9 !important;
    }}
    </style>
    {html}
    </div>
    """
    st.markdown(styled, unsafe_allow_html=True)


# PATCH 2: CACHE LINE CHART (Mencegah rebuild berulang yang berat)
@st.cache_data(show_spinner=False)
def build_line_chart(df_metric, metric_key, metric_label):
    if df_metric.empty:
        return None

    chart_df = df_metric.copy()
    chart_df["period_label"] = chart_df["week_date"].dt.strftime("%d-%b")
    chart_df["value_fmt"] = chart_df["actual"].apply(lambda x: format_ton(x))

    fig = px.line(
        chart_df,
        x="week_date",
        y="actual",
        markers=True,
        title=f"Trend {metric_label}",
        template="plotly_white",
    )

    fig.update_traces(
        mode="lines+markers",
        line_shape="spline",
        line=dict(width=4, color=METRIC_COLOR.get(metric_key, "#2563eb")),
        marker=dict(size=9, color=METRIC_COLOR.get(metric_key, "#2563eb")),
        customdata=chart_df[["period_label", "value_fmt"]].to_numpy(),
        hovertemplate="%{customdata[0]}<br>Actual : %{customdata[1]} ton<extra></extra>",
    )

    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=45, b=20),
        showlegend=False,
        xaxis_title="",
        yaxis_title="",
        hovermode="x unified",
        plot_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=14, color="#000000"),
        title_font=dict(size=16, color="#000000"),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#e5e7eb",
            font_size=14,
            font_family="Inter",
            font_color="#000000",
        ),
    )

    fig.update_xaxes(
        showgrid=False,
        tickfont=dict(size=12, color="#000000"),
        tickmode="array",
        tickvals=chart_df["week_date"],
        ticktext=chart_df["period_label"],
        tickangle=90,
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#e5e7eb",
        tickfont=dict(size=13, color="#000000"),
    )

    return fig


# ==============================
# MAIN PAGE
# ==============================
def show_inventory_page(df, selected_block, selected_week):
    # PATCH: Inventory tidak pakai category → override agar filter global tidak merusak query
    selected_category = "All"
    
    # Snapshot data awal
    df_original = df.copy()

    # CSS UI INJECTION
    st.markdown("""
        <style>
        .stSelectbox label p {
            font-size: 16px !important;
            font-weight: 800 !important;
            color: #000000 !important;
            padding-bottom: 5px;
        }
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border: 2px solid #2563eb !important;
            border-radius: 10px !important;
            color: #000000 !important;
            font-weight: 600 !important;
        }
        div[data-testid="stMarkdownContainer"] p {
            color: #111827;
        }
        ul[role="listbox"] {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
        }
        li[role="option"] {
            color: #000000 !important;
            font-weight: 500 !important;
        }
        li[role="option"]:hover {
            background-color: #f1f5f9 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## 📦 Inventory Analysis")

    if df is None or df.empty:
        st.warning("Data inventory kosong")
        return

    df = df.copy()

    required_cols = ["week_date", "block", "metric", "actual", "unit"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.warning(f"Kolom Inventory belum lengkap: {missing}")
        return

    # Normalisasi Data
    df["week_date"] = pd.to_datetime(df["week_date"], errors="coerce").dt.normalize()
    df["metric"] = df["metric"].astype(str).str.strip().str.lower()
    df["block"] = df["block"].astype(str).str.strip()
    df["actual"] = pd.to_numeric(df["actual"], errors="coerce").fillna(0)

    df = df.dropna(subset=["week_date"])
    df = df[df["metric"].isin(METRIC_ORDER)]

    if df.empty:
        st.warning("Data inventory tidak tersedia untuk block ini.")
        return

    # User Selection Timestamp
    selected_week_ts = pd.to_datetime(selected_week).normalize()

    # Prep historical data relative to choice
    df_upto_week = df[df["week_date"] <= selected_week_ts].copy()
    
    # Filter Data Minggu Ini
    df_current = df[df["week_date"] == selected_week_ts].copy()
    
    if df_current.empty:
        st.warning(f"⚠️ Tidak ada data untuk minggu {selected_week_ts.strftime('%d-%b-%Y')} pada block {selected_block}.")
        if not df_upto_week.empty:
            latest_avail = df_upto_week["week_date"].max()
            df_current = df[df["week_date"] == latest_avail].copy()
    
    # =========================
    # WEEK OVER WEEK (WoW) LOGIC
    # =========================
    all_weeks_sorted = sorted(df["week_date"].unique())
    prev_week = None
    
    current_display_date = df_current["week_date"].iloc[0] if not df_current.empty else None
    display_date_str = current_display_date.strftime("%d-%b-%Y") if current_display_date else selected_week_ts.strftime("%d-%b-%Y")
    
    if current_display_date in all_weeks_sorted:
        idx = all_weeks_sorted.index(current_display_date)
        if idx > 0:
            prev_week = all_weeks_sorted[idx - 1]

    df_prev = df[df["week_date"] == prev_week] if prev_week else pd.DataFrame()

    prev_summary = (
        df_prev.groupby("metric", observed=True)["actual"]
        .sum()
        .reindex(METRIC_ORDER, fill_value=0)
        if not df_prev.empty else pd.Series(0, index=METRIC_ORDER)
    )

    def calc_delta(curr, prev):
        if prev == 0 or prev is None:
            return None
        return (curr - prev) / prev * 100

    # Summary Display
    current_summary = (
        df_current.groupby("metric", observed=True)["actual"]
        .sum()
        .reindex(METRIC_ORDER, fill_value=0)
    )

    exposed = current_summary.get("exposed", 0)
    buried = current_summary.get("buried", 0)
    flooded = current_summary.get("flooded", 0)

    total = exposed + buried + flooded
    exposed_ratio = (exposed / total * 100) if total > 0 else 0

    # WoW untuk Exposed Ratio
    prev_total = prev_summary.sum()
    prev_exposed = prev_summary.get("exposed", 0)
    prev_ratio = (prev_exposed / prev_total * 100) if prev_total > 0 else None
    
    delta_ratio = None
    if prev_ratio is not None and prev_ratio != 0:
        delta_ratio = (exposed_ratio - prev_ratio) / prev_ratio * 100

    # =========================
    # 1. CARD HIGHLIGHT
    # =========================
    st.markdown("### 📊 Key Highlight")
    if not df_current.empty and current_display_date != selected_week_ts:
        st.info(f"Menampilkan data terakhir tersedia: {current_display_date.strftime('%d-%b-%Y')}")

    delta_exposed = calc_delta(exposed, prev_summary["exposed"])
    delta_buried = calc_delta(buried, prev_summary["buried"])
    delta_flooded = calc_delta(flooded, prev_summary["flooded"])

    col1, col2, col3, col4 = st.columns(4)
    with col1: render_kpi_card("Exposed", f"{format_ton(exposed)} ton", delta_exposed)
    with col2: render_kpi_card("Buried", f"{format_ton(buried)} ton", delta_buried)
    with col3: render_kpi_card("Flooded", f"{format_ton(flooded)} ton", delta_flooded)
    with col4: render_kpi_card("Exposed Ratio", f"{exposed_ratio:.1f}%", delta_ratio)

    st.write("")

    # =========================
    # 2. TABEL WEEKLY INVENTORY DATA
    # =========================
    st.markdown("### 📋 Weekly Inventory Data")
    table_rows = []
    
    for metric in METRIC_ORDER:
        table_rows.append({
            "Category": METRIC_LABEL[metric],
            "Week Date": display_date_str,
            "Actual (ton)": format_ton(current_summary.get(metric, 0)),
        })

    table_df = pd.DataFrame(table_rows)
    total_row = pd.DataFrame([{"Category": "TOTAL", "Week Date": display_date_str, "Actual (ton)": format_ton(total)}])
    table_df = pd.concat([table_df, total_row], ignore_index=True)
    render_clean_table(table_df, height=310)

    # =========================
    # 3. LATEST COMPOSITION
    # =========================
    st.write("")
    st.markdown(f"### 🧠 Latest Composition ({display_date_str})")

    comp_df = pd.DataFrame({
        "Metric": ["Exposed", "Buried", "Flooded"],
        "Value": [exposed, buried, flooded],
    })

    fig_comp = px.bar(
        comp_df,
        x="Metric",
        y="Value",
        color="Metric",
        text="Value",
        template="plotly_white",
        color_discrete_map={
            "Exposed": METRIC_COLOR["exposed"],
            "Buried": METRIC_COLOR["buried"],
            "Flooded": METRIC_COLOR["flooded"],
        },
    )

    fig_comp.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        textfont=dict(size=24, color="black", family="Inter"),
        marker=dict(opacity=0.95),
        hovertemplate="%{x}: %{text:,.0f} ton<extra></extra>",
    )

    y_max = max(comp_df["Value"].max() * 1.35, 1)
    fig_comp.update_layout(
        height=440,
        margin=dict(l=50, r=20, t=50, b=50),
        showlegend=True,
        legend_title_text="Metric",
        legend=dict(font=dict(size=14, color="black")),
        font=dict(family="Inter", size=14, color="#000000"),
        yaxis=dict(
            range=[0, y_max],
            title_font=dict(size=16, color="black"),
            tickfont=dict(size=15, color="black")
        ),
        xaxis=dict(
            title_font=dict(size=16, color="black"),
            tickfont=dict(size=16, color="black")
        )
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # =========================
    # 4. WEEKLY COMPOSITION (REVISED STYLE)
    # =========================
    st.write("")
    st.markdown("### 📊 Weekly Composition (Selected Week + Previous 2 Weeks)")

    df_original["week_date"] = pd.to_datetime(df_original["week_date"], errors="coerce").dt.normalize()
    all_weeks_global = sorted(df_original["week_date"].dropna().unique().tolist())

    if selected_week_ts in all_weeks_global:
        idx = all_weeks_global.index(selected_week_ts)
    else:
        idx = len(all_weeks_global) - 1 if all_weeks_global else 0

    start_idx = max(0, idx - 2)
    comp_weeks = all_weeks_global[start_idx: idx + 1]

    df_comp = df[df["week_date"].isin(comp_weeks)].copy()

    if df_comp.empty:
        st.warning("⚠️ Tidak ada data historis untuk komposisi mingguan pada block ini.")
    else:
        weekly_comp = (
            df_comp.groupby(["week_date", "metric"], observed=True)["actual"]
            .sum()
            .reset_index()
        )

        weekly_comp["metric_label"] = weekly_comp["metric"].map(METRIC_LABEL)
        weekly_comp["week_label"] = weekly_comp["week_date"].dt.strftime("%d-%b")
        weekly_comp["actual_fmt"] = weekly_comp["actual"].apply(format_ton)

        weekly_comp["week_date"] = pd.Categorical(
            weekly_comp["week_date"],
            categories=comp_weeks,
            ordered=True
        )
        weekly_comp = weekly_comp.sort_values("week_date")

        fig_bar = px.bar(
            weekly_comp,
            x="week_label",
            y="actual",
            color="metric_label",
            barmode="group",
            text="actual", 
            template="plotly_white",
            color_discrete_map={
                "Exposed": METRIC_COLOR["exposed"],
                "Buried": METRIC_COLOR["buried"],
                "Flooded": METRIC_COLOR["flooded"],
            },
        )

        fig_bar.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
            textfont=dict(size=20, color="black", family="Inter"),
            marker=dict(opacity=0.95),
            hovertemplate="%{fullData.name}: %{y:,.0f} ton<extra></extra>",
        )

        fig_bar.update_layout(
            height=420,
            margin=dict(l=50, r=20, t=40, b=50),
            legend=dict(
                orientation="h",
                y=1.02,
                x=1,
                xanchor="right",
                font=dict(size=14, color="black")
            ),
            font=dict(family="Inter", size=14, color="#000000"),
            bargap=0.28,
            xaxis=dict(
                title="Week",
                title_font=dict(size=16, color="black"),
                tickfont=dict(size=15, color="black")
            ),
            yaxis=dict(
                title="Tonnage (ton)",
                title_font=dict(size=16, color="black"),
                tickfont=dict(size=15, color="black")
            )
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # =========================
    # 5. INVENTORY TREND PER CATEGORY
    # =========================
    st.write("")
    st.markdown("### 📈 Inventory Trend per Category")
    st.markdown("---")

    all_weeks_full = sorted(df["week_date"].unique().tolist())
    week_windows = []
    w_size = 7

    for i in range(0, len(all_weeks_full), w_size):
        chunk = all_weeks_full[max(0, len(all_weeks_full) - (i + w_size)): len(all_weeks_full) - i]
        if chunk:
            label = f"{chunk[0].strftime('%d-%b')} → {chunk[-1].strftime('%d-%b')}"
            week_windows.append({"label": label, "start": chunk[0], "end": chunk[-1]})

    selected_range = None
    if week_windows:
        selected_range = st.selectbox(
            "Select Period Trend (7 Weeks Window):",
            options=week_windows,
            format_func=lambda x: x["label"]
        )

    # PATCH: Hardening Trend Range (Default ke 7 minggu terakhir)
    if selected_range:
        df_trend = df[(df["week_date"] >= selected_range["start"]) & (df["week_date"] <= selected_range["end"])].copy()
    else:
        last_weeks = sorted(df["week_date"].dropna().unique())[-7:]
        df_trend = df[df["week_date"].isin(last_weeks)].copy()

    trend_summary = df_trend.groupby(["week_date", "metric"], observed=True)["actual"].sum().reset_index().sort_values(["metric", "week_date"])
    trend_items = [("exposed", "Exposed"), ("buried", "Buried"), ("flooded", "Flooded")]

    cols = st.columns(3)
    for i, (metric_key, metric_label) in enumerate(trend_items):
        df_metric = trend_summary[trend_summary["metric"] == metric_key].copy()
        with cols[i]:
            fig = build_line_chart(df_metric, metric_key, metric_label)
            if fig: st.plotly_chart(fig, use_container_width=True)
            else: st.info(f"Tidak ada data trend untuk {metric_label}")