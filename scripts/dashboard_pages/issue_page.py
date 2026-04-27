import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# ==============================
# UI HELPERS & STYLING
# ==============================

def style_chart(fig, is_trend=False):
    """Mengatur style grafik agar standar enterprise (Font Inter, Hitam, Grid Bersih)"""
    layout_params = dict(
        font=dict(family="Inter, sans-serif", size=17, color="#000000"),
        title_font=dict(size=18, color="#000000", weight="bold"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=60, b=50),
        legend=dict(font=dict(size=14)),
        bargap=0.25  # Menjaga jarak antar bar agar proporsional
    )
    
    if is_trend:
        layout_params['margin'] = dict(l=10, r=10, t=40, b=90)

    fig.update_layout(**layout_params)

    fig.update_xaxes(
        tickfont=dict(size=14 if is_trend else 17, color="#000000"),
        title_font=dict(size=18, color="#000000"),
        showgrid=False,
        linecolor="#e5e7eb",
        tickangle=-90 if is_trend else 0 
    )

    fig.update_yaxes(
        tickfont=dict(size=17, color="#000000"),
        title_font=dict(size=18, color="#000000"),
        showgrid=True,
        gridcolor="#e5e7eb",
        linecolor="#e5e7eb"
    )
    
    fig.update_traces(
        textposition="outside",
        textfont=dict(size=16, color="#000000")
    )
    return fig

# --- CACHED CHART BUILDERS ---
@st.cache_data(show_spinner=False)
def build_status_pie(status_df):
    """Membangun Pie Chart Status dengan Caching"""
    fig = px.pie(
        status_df, 
        names="status", 
        values="count", 
        hole=0.5, 
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    return style_chart(fig)

@st.cache_data(show_spinner=False)
def build_severity_bar(sev_df):
    """Membangun Bar Chart Severity dengan Caching"""
    fig = px.bar(
        sev_df, 
        x="severity", 
        y="count", 
        text="count", 
        color="severity",
        color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"}
    )
    return style_chart(fig)

def safe_bar(df, title, color="#3b82f6"):
    """Fallback logic & Force X-Axis labels agar tidak loncat"""
    if df.empty:
        empty_df = pd.DataFrame({"week_label": [], "count": []})
        fig = px.bar(empty_df, x="week_label", y="count", title=title)
    else:
        df = df.copy()
        df["week_label"] = pd.to_datetime(df["week_date"]).dt.strftime("%d-%b")

        fig = px.bar(
            df, 
            x="week_label", 
            y="count", 
            text="count", 
            title=title,
            color_discrete_sequence=[color]
        )

        fig.update_xaxes(
            tickmode="array",
            tickvals=df["week_label"],
            ticktext=df["week_label"]
        )

    return style_chart(fig, is_trend=True)

def render_kpi_card(title, value):
    """KPI Card Enterprise Look"""
    html = f"""
    <div style="
        border:1px solid #e5e7eb;
        border-left:6px solid #2563eb;
        border-radius:14px;
        padding:14px 16px;
        background:white;
        box-shadow:0 4px 12px rgba(0,0,0,0.08);
        height:115px;
        display:flex;
        flex-direction:column;
        justify-content:center;
        font-family:'Inter', sans-serif;
    ">
        <div style="
            font-size:14px;
            font-weight:800;
            color:#111827;
            text-transform:uppercase;
            margin-bottom:4px;
        ">
            {title}
        </div>
        <div style="
            font-size:28px;
            font-weight:900;
            color:#111827;
            line-height:1;
        ">
            {value}
        </div>
    </div>
    """
    components.html(html, height=120)

def render_clean_table(df, max_height=400):
    """Digunakan untuk tabel Trend Data (Pivoted) dengan limitasi 200 rows"""
    if df.empty:
        return st.info("Tidak ada data untuk ditampilkan")
    
    # Limit table rendering untuk performa UI
    df = df.head(200)
        
    cols_to_show = [c for c in df.columns]
    html_table = df[cols_to_show].to_html(index=False, border=0, justify="center")

    styled = f"""
    <div style="font-family:'Inter', sans-serif; overflow-x:auto; max-height:{max_height}px; overflow-y:auto; 
        border-radius:10px; border:1px solid #e5e7eb;">
    <style>
    table {{border-collapse: collapse; width: 100%; font-size: 13px; color: #374151;}}
    th {{
        background-color:#1e293b;
        color:white;
        padding:10px 6px;
        position:sticky;
        top:0;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.05em;
    }}
    td {{
        padding:8px 6px;
        text-align:center;
        border-bottom:1px solid #f3f4f6;
    }}
    tr:nth-child(even) {{background:#f9fafb;}}
    tr:hover {{background:#f3f4f6; transition: 0.2s;}}
    </style>
    {html_table}
    </div>
    """
    row_count = len(df)
    dynamic_height = min(80 + row_count * 38, max_height)
    components.html(styled, height=dynamic_height)

def render_issue_table_colored(df):
    """Tabel utama dengan Header Hitam, Row Coloring berdasarkan Severity"""
    
    # Tetap limit 200 row di tabel utama jika data sangat besar
    df = df.head(200)

    def get_row_style(row):
        sev = str(row.get("severity", "")).lower()
        if sev == "high":
            return 'background-color: #fee2e2;'
        elif sev == "medium":
            return 'background-color: #fef3c7;'
        elif sev == "low":
            return 'background-color: #dcfce7;'
        return ''

    cols = [c for c in df.columns if c != "severity_rank"]
    header_html = "".join([f"<th style='padding:10px 6px; text-align:center;'>{c.replace('_', ' ').upper()}</th>" for c in cols])

    rows_html = ""
    for _, row in df.iterrows():
        style = get_row_style(row)
        cells = "".join([f"<td style='padding:8px 6px; border-bottom:1px solid #e5e7eb; text-align:center;'>{row[c]}</td>" for c in cols])
        rows_html += f"<tr style='{style}'>{cells}</tr>"

    html_content = f"""
    <div style="overflow-x:auto; border:1px solid #e5e7eb; border-radius:10px; font-family:'Inter', sans-serif;">
        <table style="width:100%; border-collapse:collapse; font-size:13px;">
            <thead>
                <tr style="background:#1e293b; color:white; font-weight:700;">
                    {header_html}
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
    
    row_count = len(df)
    dynamic_height = min(80 + row_count * 40, 500) 
    components.html(html_content, height=dynamic_height)

# ==============================
# MAIN PAGE FUNCTION
# ==============================
def show_issue_page(df, selected_block, selected_week):

    st.markdown("## 🚨 Issue & Action Tracking")

    if df is None or df.empty:
        st.warning("Tidak ada data issue")
        return

    # Deep Copy & Cleaning
    df = df.copy()
    if "issue_detail" in df.columns:
        df = df.dropna(subset=["issue_detail"], how="all")

    # Filter Grup Issue
    df_issue = df[df["metric_group"] == "issue"].copy()
    df_issue["week_date"] = pd.to_datetime(df_issue["week_date"], errors="coerce")
    current_week_dt = pd.to_datetime(selected_week)

    # Filter Data Minggu Terpilih
    df_issue_now = df_issue[df_issue["week_date"] == current_week_dt].copy().reset_index(drop=True)

    if df_issue_now.empty:
        st.info(f"Tidak ada issue pada minggu {selected_week} untuk block {selected_block}")
        return

    # Standardize Data
    df_issue_now["status"] = df_issue_now["status"].fillna("unknown").astype(str).str.strip().str.lower()
    df_issue_now["severity"] = df_issue_now["severity"].fillna("Low").astype(str).str.strip().str.capitalize()
    df_issue_now["week_date"] = df_issue_now["week_date"].dt.date 
    
    severity_order = {"High": 3, "Medium": 2, "Low": 1}
    df_issue_now["severity_rank"] = df_issue_now["severity"].map(severity_order).fillna(0)
    
    issue_cols = ["week_date", "block", "issue_category", "issue_detail", "impact_area", "severity", "status", "pic"]
    final_issue_cols = [c for c in issue_cols if c in df_issue_now.columns]

    # 2. TOP SUMMARY
    st.markdown(f"📌 Menampilkan **{len(df_issue_now)} issue** | Block: **{selected_block}**")

    # 3. KPI SECTION
    open_issue = len(df_issue_now[df_issue_now["status"] == "open"])
    progress_issue = len(df_issue_now[df_issue_now["status"].isin(["progress", "on progress", "in progress"])])
    closed_issue = len(df_issue_now[df_issue_now["status"] == "closed"])
    high_severity = len(df_issue_now[df_issue_now["severity_rank"] == 3])

    cols = st.columns(4)
    with cols[0]: render_kpi_card("Open Issue", open_issue)
    with cols[1]: render_kpi_card("In Progress", progress_issue)
    with cols[2]: render_kpi_card("Closed", closed_issue)
    with cols[3]: render_kpi_card("High Severity", high_severity)

    # 4. DETAILED TABLE WITH FILTERS
    st.markdown("---")
    st.markdown("### 🎛️ Detailed Issue Tracking")
    
    f1, f2, f3, f4 = st.columns(4)
    with f1: cat_filter = st.selectbox("Category", ["All"] + sorted(df_issue_now["issue_category"].dropna().unique().tolist()))
    with f2: sev_filter = st.selectbox("Severity", ["All"] + sorted(df_issue_now["severity"].dropna().unique().tolist()))
    with f3: status_filter = st.selectbox("Status", ["All"] + sorted(df_issue_now["status"].dropna().unique().tolist()))
    with f4: pic_filter = st.selectbox("PIC", ["All"] + sorted(df_issue_now["pic"].dropna().unique().tolist()))

    display_df = df_issue_now.copy()
    if cat_filter != "All": display_df = display_df[display_df["issue_category"] == cat_filter]
    if sev_filter != "All": display_df = display_df[display_df["severity"] == sev_filter]
    if status_filter != "All": display_df = display_df[display_df["status"] == status_filter]
    if pic_filter != "All": display_df = display_df[display_df["pic"] == pic_filter]

    st.markdown(f"**📊 Data Issue (Sorted by Priority)**")

    if not display_df.empty:
        display_df = display_df.sort_values(by=["severity_rank", "status"], ascending=[False, True])
        render_issue_table_colored(display_df[final_issue_cols + (["severity_rank"] if "severity_rank" in display_df.columns else [])])
    else:
        st.info("Tidak ada data untuk kombinasi filter yang dipilih")

    # 5. VISUAL ANALYTICS
    st.markdown("<div style='margin-top:-20px'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📊 Visual Analytics")
    v_col1, v_col2 = st.columns(2)

    with v_col1:
        st.markdown("##### 📌 Status Distribution")
        status_df = df_issue_now["status"].value_counts().reset_index()
        status_df.columns = ["status", "count"]
        fig_pie = build_status_pie(status_df)
        st.plotly_chart(fig_pie, use_container_width=True)

    with v_col2:
        st.markdown("##### 🚨 Severity Breakdown")
        sev_df = df_issue_now["severity"].value_counts().reset_index()
        sev_df.columns = ["severity", "count"]
        fig_sev = build_severity_bar(sev_df)
        st.plotly_chart(fig_sev, use_container_width=True)

    # 6. TREND ANALYSIS (15 WEEKS)
    st.markdown("---")
    st.markdown("### 📈 Trend Issue (Last 15 Weeks)")
    
    if not df_issue.empty:
        trend_prep = df_issue.copy()
        # Normalisasi status agar konsisten dengan filter grup
        trend_prep["status"] = trend_prep["status"].fillna("unknown").astype(str).str.lower().str.strip()
        # Mapping status progress yang variatif ke satu nama 'progress' agar bar chart rapi
        trend_prep["status"] = trend_prep["status"].replace(["on progress", "in progress"], "progress")
        
        trend_prep["week_date_only"] = trend_prep["week_date"].dt.date
        
        all_weeks = sorted(trend_prep["week_date_only"].unique())[-15:]
        target_statuses = ["open", "progress", "closed"]
        
        full_index = pd.MultiIndex.from_product(
            [all_weeks, target_statuses],
            names=["week_date", "status"]
        )
        
        trend_group = (
            trend_prep.groupby(["week_date_only", "status"])
            .size()
            .reindex(full_index, fill_value=0)
            .reset_index(name="count")
        )
        
        open_t = trend_group[trend_group["status"] == "open"]
        prog_t = trend_group[trend_group["status"] == "progress"]
        closed_t = trend_group[trend_group["status"] == "closed"]

        c1, c2, c3 = st.columns(3)
        with c1: st.plotly_chart(safe_bar(open_t, "🔴 Open", "#ef4444"), use_container_width=True)
        with c2: st.plotly_chart(safe_bar(prog_t, "🟡 Progress", "#f59e0b"), use_container_width=True)
        with c3: st.plotly_chart(safe_bar(closed_t, "🟢 Closed", "#10b981"), use_container_width=True)

        st.markdown("#### 📋 Trend Data Summary")
        if not trend_group.empty:
            trend_pivot = trend_group.pivot(index="week_date", columns="status", values="count").fillna(0)
            trend_pivot = trend_pivot.reset_index()
            trend_pivot.columns.name = None
            trend_pivot = trend_pivot.sort_values("week_date", ascending=False)
            render_clean_table(trend_pivot, max_height=300)