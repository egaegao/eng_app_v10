import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# ==============================
# CONFIG & HELPERS
# ==============================
METRIC_LABEL = {
    "rain_hours": "Rain Hours",
    "rain_frequency": "Frequency",
    "rainfall": "Rainfall (mm)",
    "slippery_hours": "Slippery Hours",
    "slippery_ratio": "Slippery Ratio (%)"
}

AGG_MAP = {
    "rain_hours": "sum",
    "rain_frequency": "sum",
    "rainfall": "sum",
    "slippery_hours": "sum",
    "slippery_ratio": "mean"
}

# --- CACHED CHART FUNCTIONS ---

@st.cache_data(show_spinner=False)
def build_weather_trend(chart_df, x_col, label, trend_type):
    """
    Fungsi build chart trend yang di-cache untuk performa maksimal.
    """
    fig = px.line(
        chart_df, x=x_col, y=["actual", "plan"], 
        title=f"Trend {label}", markers=True, template="plotly_white",
        color_discrete_map={"actual": "#2563eb", "plan": "#64748b"}
    )
    
    fig.update_traces(line_shape="spline", line=dict(width=4), marker=dict(size=10))
    fig.update_traces(patch={"line": {"dash": "dot", "width": 3}}, selector={"name": "plan"})

    # Custom Hover Data
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>Actual: %{customdata[1]}<extra></extra>",
        customdata=chart_df[["label", "actual_fmt"]],
        selector={"name": "actual"}
    )
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>Plan: %{customdata[1]}<extra></extra>",
        customdata=chart_df[["label", "plan_fmt"]],
        selector={"name": "plan"}
    )

    fig.update_xaxes(
        showgrid=True, gridwidth=1, gridcolor="#e5e7eb", griddash="dot",
        tickmode="array", tickvals=chart_df[x_col], ticktext=chart_df["label"],
        tickangle=0, tickfont=dict(size=17, color="#000000", family="Inter"), automargin=True
    )

    fig.update_yaxes(
        showgrid=True, gridwidth=1, gridcolor="#e5e7eb",
        tickfont=dict(size=16, color="#000000", family="Inter"),
        title_text="Value", title_font=dict(size=18, color="#000000", family="Inter")
    )

    fig.update_layout(
        height=400, margin=dict(l=50, r=20, t=70, b=70),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=14, color="black")),
        font=dict(family="Inter", size=12, color="black"),
        hoverlabel=dict(bgcolor="white", font_size=14, font_family="Inter", font_color="black", bordercolor="#e5e7eb"),
        hovermode="x unified"
    )
    return fig

@st.cache_data(show_spinner=False)
def build_weather_snapshot(snap_df, title_text, color_map, max_val):
    """
    Fungsi build chart bar snapshot yang di-cache.
    """
    fig_snap = px.bar(
        snap_df, x="Type", y="Value", text="Value", 
        color="Type", color_discrete_map=color_map,
        template="plotly_white"
    )
    
    fig_snap.update_traces(
        texttemplate='%{text:.2f}', textposition='outside',
        textfont=dict(size=20, color="black", family="Inter")
    )
    
    fig_snap.update_layout(
        height=380,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(range=[0, max_val], tickfont=dict(size=16, color="black")),
        xaxis=dict(tickfont=dict(size=18, color="black")),
        margin=dict(l=10, r=10, t=60, b=10),
        showlegend=False,
        title=dict(text=title_text, font=dict(size=22, color="black"))
    )
    return fig_snap

# --- UI COMPONENTS ---

def render_kpi_card(title, actual_val, delta_wow=None, delta_plan=None):
    def get_delta_html(delta, label_prefix=""):
        if delta is None: return ""
        color = "#dc2626" if delta >= 0 else "#16a34a"
        bg_color = "#fef2f2" if delta >= 0 else "#f0fdf4"
        symbol = "▲" if delta >= 0 else "▼"
        return f"""
            <div style="display:flex; flex-direction:column; align-items:center; background-color:{bg_color}; 
                 padding:6px 10px; border-radius:8px; min-width: 80px; border: 1px solid #e5e7eb;">
                <span style="font-size:11px; color:#6b7280; font-weight:700; text-transform:uppercase;">{label_prefix}</span>
                <span style="color:{color}; font-weight:900; font-size:18px;">{symbol}{abs(delta):.1f}%</span>
            </div>
        """
    wow_html = get_delta_html(delta_wow, "WoW")
    plan_html = get_delta_html(delta_plan, "PLAN")
    card_html = f"""
    <div style="border:1px solid #e5e7eb; border-left:6px solid #2563eb; border-radius:14px; padding:14px 16px;
        background:white; font-family: 'Inter', sans-serif; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        height: 120px; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="font-size:14px; font-weight:800; color:#111827; text-transform:uppercase; margin-bottom:6px;">{title}</div>
            <div style="font-size:32px; font-weight:900; color:#111827;">{actual_val}</div>
        </div>
        <div style="display:flex; gap:10px;">{wow_html}{plan_html}</div>
    </div>
    """
    components.html(card_html, height=140)

def render_clean_table(df, max_height=500):
    df = df.head(200)
    html_table = df.to_html(index=False, border=0, justify="center")
    row_count = len(df)
    dynamic_height = min(max_height, 70 + (row_count * 38))

    styled = f"""
    <div id="weather-table-container" style="overflow-x:auto; max-height:{max_height}px; overflow-y:auto; 
        border-radius:10px; border:1px solid #e5e7eb; margin-bottom: 5px;">
    <style>
    #weather-table-container table {{ border-collapse: collapse; width: 100%; font-size: 14px; font-family: 'Inter', sans-serif; }}
    #weather-table-container th {{ background-color: #1e293b; color: white; font-weight: 700; text-align: center; padding: 12px 8px; position: sticky; top: 0; z-index: 10; }}
    #weather-table-container td {{ color: #111827; text-align: center; padding: 10px 8px; border-bottom: 1px solid #e2e8f0; }}
    #weather-table-container tr:nth-child(odd) td {{ background-color: #ffffff; font-weight: 600; }}
    #weather-table-container tr:nth-child(even) td {{ background-color: #eef2ff; font-weight: 500; }}
    #weather-table-container tr:hover td {{ background-color: #f1f5f9 !important; }}
    </style>
    {html_table}
    </div>
    """
    components.html(styled, height=dynamic_height, scrolling=True)

# ==============================
# MAIN PAGE
# ==============================
def show_weather_page(df, selected_block, selected_week):
    selected_category = "All"
    
    st.markdown("## 🌧️ Weather Impact Analysis")

    if df is None or df.empty:
        st.warning("Tidak ada data weather")
        return

    df = df.copy()

    # 1. STANDARISASI KOLOM & NORMALISASI
    for col in ["metric", "actual", "plan", "date", "week_date"]:
        if col not in df.columns:
            found = next((c for c in df.columns if c.lower() == col), None)
            if found:
                df.rename(columns={found: col}, inplace=True)
            elif col == "plan":
                df["plan"] = 0

    # 2. CLEANING & DATETIME NORMALIZATION
    valid_metrics = list(METRIC_LABEL.keys())
    df["metric"] = df["metric"].astype(str).str.strip().str.lower()
    df = df[df["metric"].isin(valid_metrics)]
    
    df["actual"] = pd.to_numeric(df["actual"], errors="coerce").fillna(0)
    df["plan"] = pd.to_numeric(df["plan"], errors="coerce").fillna(0)
    
    # Normalize dates to avoid timestamp/timezone mismatch
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["week_date"] = pd.to_datetime(df["week_date"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["date", "week_date"])

    # 3. PREPARE WEEKLY DATA
    current_week = pd.to_datetime(selected_week).normalize()
    all_weeks_full = sorted(df["week_date"].dropna().unique())

    prev_week = None
    if current_week in all_weeks_full:
        idx = list(all_weeks_full).index(current_week)
        if idx > 0:
            prev_week = all_weeks_full[idx - 1]

    df_now = df[df["week_date"] == current_week]
    df_prev = df[df["week_date"] == prev_week] if prev_week else pd.DataFrame()

    if df_now.empty:
        st.warning(f"⚠️ Tidak ada data untuk minggu {selected_week}")
        return

    # ===============================
    # KPI MODE UI
    # ===============================
    kpi_mode = st.radio(
        "Mode KPI",
        ["Weekly", "MTD", "YTD", "Custom"],
        horizontal=True,
        key="weather_kpi_mode"
    )

    if kpi_mode == "Custom":
        custom_range = st.date_input(
            "Pilih Range KPI",
            value=(current_week.date(), current_week.date()),
            key="weather_custom_range"
        )
    else:
        custom_range = None

    # ===============================
    # KPI DATA SOURCE (PATCHED & ISOLATED)
    # ===============================
    df_kpi_source = df.copy()

    if kpi_mode == "Weekly":
        kpi_df = df_now.copy()

    elif kpi_mode == "MTD":
        start_month = current_week.replace(day=1)
        kpi_df = df_kpi_source[
            (df_kpi_source["date"] >= start_month) &
            (df_kpi_source["date"] <= current_week)
        ]

    elif kpi_mode == "YTD":
        start_year = current_week.replace(month=1, day=1)
        kpi_df = df_kpi_source[
            (df_kpi_source["date"] >= start_year) &
            (df_kpi_source["date"] <= current_week)
        ]

    elif kpi_mode == "Custom" and custom_range and len(custom_range) == 2:
        # Patch: Normalize custom range dates
        start = pd.to_datetime(custom_range[0]).normalize()
        end = pd.to_datetime(custom_range[1]).normalize()
        kpi_df = df_kpi_source[
            (df_kpi_source["date"] >= start) &
            (df_kpi_source["date"] <= end)
        ]
    else:
        kpi_df = df_now.copy()

    # Fallback to avoid errors
    if kpi_df.empty:
        kpi_df = df_now.copy()

    # ============================================
    # 📊 KPI SUMMARY (HIGHLIGHTS)
    # ============================================
    st.markdown("### 📊 Key Highlight")
    
    cols = st.columns(5)
    metrics_list = [
        ("rain_hours","Rain Hours"),
        ("rain_frequency","Frequency"),
        ("rainfall","Rainfall"),
        ("slippery_hours","Slippery Hours"),
        ("slippery_ratio","Slippery Ratio (%)")
    ]

    for i, (m_key, label) in enumerate(metrics_list):
        agg = AGG_MAP.get(m_key, "sum")
        
        m_now = kpi_df[kpi_df["metric"] == m_key]
        
        val_act = m_now["actual"].sum() if agg == "sum" else m_now["actual"].mean()
        val_pln = m_now["plan"].sum() if agg == "sum" else m_now["plan"].mean()
        
        # WoW selalu dihitung berdasarkan perbandingan weekly (df_now vs df_prev)
        if not df_prev.empty:
            m_prev = df_prev[df_prev["metric"] == m_key]
            val_prev = m_prev["actual"].sum() if agg == "sum" else m_prev["actual"].mean()
        else:
            val_prev = 0

        # Hanya tampilkan WoW di mode Weekly
        if kpi_mode == "Weekly":
            delta_wow = ((val_act - val_prev) / val_prev * 100) if val_prev > 0 else None
        else:
            delta_wow = None
            
        delta_plan = ((val_act - val_pln) / val_pln * 100) if val_pln > 0 else None

        with cols[i]:
            render_kpi_card(label, round(val_act, 1), delta_wow, delta_plan)

    # ============================================
    # 📅 DAILY TABLE (RESTRICTED TO WEEKLY)
    # ============================================
    st.write("") 
    st.markdown("### 📅 Daily Detail (Actual vs Plan)")
    
    dates = sorted(df_now["date"].unique())
    rows = []
    for metric, label in METRIC_LABEL.items():
        df_m = df_now[df_now["metric"] == metric]
        row_act = {"Metric": f"{label} (Actual)"}
        row_pln = {"Metric": f"{label} (Plan)"}
        
        for d in dates:
            day_data = df_m[df_m["date"] == d]
            date_str = pd.Timestamp(d).strftime("%d-%b")
            row_act[date_str] = round(day_data["actual"].sum(), 1)
            row_pln[date_str] = round(day_data["plan"].sum(), 1)
            
        rows.append(row_act)
        rows.append(row_pln)

    table_df = pd.DataFrame(rows)
    render_clean_table(table_df)

    # ============================================
    # 📈 TREND
    # ============================================
    st.markdown("<div style='margin-top:-25px'></div>", unsafe_allow_html=True)
    st.markdown("### 📈 Trend Actual vs Plan")
    st.markdown("---")

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    with col_ctrl1:
        trend_option = st.radio("Trend Type", ["Daily", "Weekly"], horizontal=True)
    with col_ctrl2:
        metric_filter = st.selectbox("Metric Filter", ["All"] + list(METRIC_LABEL.values()))
    
    selected_range_trend = None
    if trend_option == "Weekly":
        with col_ctrl3:
            all_weeks_list = sorted(df["week_date"].dropna().unique().tolist())
            week_windows = []
            w_size = 8  
            for i in range(0, len(all_weeks_list), w_size):
                chunk = all_weeks_list[max(0, len(all_weeks_list) - (i + w_size)): len(all_weeks_list) - i]
                if chunk:
                    label_range = f"{chunk[0].strftime('%d-%b')} → {chunk[-1].strftime('%d-%b')}"
                    week_windows.append({"label": label_range, "start": chunk[0], "end": chunk[-1]})
            if week_windows:
                selected_range_trend = st.selectbox("Range Minggu", options=week_windows, format_func=lambda x: x["label"])

    metric_items = list(METRIC_LABEL.items())
    if metric_filter != "All":
        metric_items = [(k, v) for k, v in metric_items if v == metric_filter]

    for i in range(0, len(metric_items), 2):
        t_col1, t_col2 = st.columns(2)
        pair = metric_items[i:i+2]

        for col, (m_key, label) in zip([t_col1, t_col2], pair):
            df_m = df[df["metric"] == m_key]
            if df_m.empty: continue

            if trend_option == "Daily":
                chart_data = df_m[df_m["week_date"] == current_week].copy()
                if chart_data.empty: continue
                chart_df = chart_data.groupby("date").agg({"actual":"sum", "plan":"sum"}).reset_index()
                x_col = "date"
            else:
                if selected_range_trend:
                    df_range = df_m[
                        (df_m["week_date"] >= selected_range_trend["start"]) & 
                        (df_m["week_date"] <= selected_range_trend["end"])
                    ]
                else:
                    last_weeks = sorted(df_m["week_date"].dropna().unique())[-8:]
                    df_range = df_m[df_m["week_date"].isin(last_weeks)]
                
                chart_df = df_range.groupby("week_date").agg({"actual":"mean", "plan":"mean"}).reset_index()
                x_col = "week_date"

            chart_df["label"] = chart_df[x_col].dt.strftime("%d-%b")
            chart_df["actual_fmt"] = chart_df["actual"].apply(lambda x: f"{x:.1f}".replace(".", ","))
            chart_df["plan_fmt"] = chart_df["plan"].apply(lambda x: f"{x:.1f}".replace(".", ","))

            fig = build_weather_trend(chart_df, x_col, label, trend_option)
            
            with col:
                st.plotly_chart(fig, use_container_width=True)

    # ============================================
    # 📊 SNAPSHOT WEEKLY (ALWAYS BASED ON df_now)
    # ============================================
    st.write("")
    st.markdown("### 📊 Snapshot Weekly Impact (Actual vs Plan)")
    st.markdown("---")

    cols_snap = st.columns(3)
    
    for i, (m_key, label) in enumerate(METRIC_LABEL.items()):
        df_m = df_now[df_now["metric"] == m_key]
        if df_m.empty: continue

        agg_type = AGG_MAP.get(m_key, "sum")
        v_act = df_m["actual"].sum() if agg_type == "sum" else df_m["actual"].mean()
        v_pln = df_m["plan"].sum() if agg_type == "sum" else df_m["plan"].mean()
        
        snap_df = pd.DataFrame({"Type": ["Actual", "Plan"], "Value": [v_act, v_pln]})
        agg_label = "SUM" if agg_type == "sum" else "AVG"
        title_text = f"<b>{label} ({agg_label})</b>"
        
        if m_key == "slippery_ratio":
            color_map = {"Actual": "#dc2626", "Plan": "#fca5a5"}
        else:
            color_map = {"Actual": "#2563eb", "Plan": "#94a3b8"}

        max_val = max(v_act, v_pln) * 1.3 if max(v_act, v_pln) > 0 else 10
        
        fig_snap = build_weather_snapshot(snap_df, title_text, color_map, max_val)

        with cols_snap[i % 3]:
            st.plotly_chart(fig_snap, use_container_width=True)