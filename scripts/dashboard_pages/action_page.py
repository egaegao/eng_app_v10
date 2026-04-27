import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# =================================================================
# UI HELPERS & STYLING
# =================================================================

def style_chart(fig, is_trend=False):
    """Mengatur style grafik agar standar enterprise (Font Inter, Hitam, Grid Bersih)"""
    layout_params = dict(
        font=dict(family="Inter, sans-serif", size=17, color="#000000"),
        title_font=dict(size=18, color="#000000", weight="bold"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=60, b=50),
        legend=dict(font=dict(size=14)),
        bargap=0.25 
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

def safe_bar(df, title, color="#3b82f6"):
    """Fallback logic & Force X-Axis labels agar tidak loncat"""
    if df.empty:
        empty_df = pd.DataFrame({"week_label": [], "count": []})
        fig = px.bar(empty_df, x="week_label", y="count", title=title)
    else:
        df = df.copy()
        # Menggunakan week_date_only yang sudah dinormalisasi agar urutan benar
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
    """KPI Card Model Enterprise (Biru di sisi kiri)"""
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

def render_issue_table_colored(df):
    """Tabel utama dengan Row Coloring berdasarkan Priority & Limit 200 Row"""
    df = df.head(200)
    
    def get_row_style(row):
        prio = str(row.get("priority", "")).lower()
        if prio == "high":
            return 'background-color: #fee2e2;' # Merah muda
        elif prio == "medium":
            return 'background-color: #fef3c7;' # Kuning muda
        elif prio == "low":
            return 'background-color: #dcfce7;' # Hijau muda
        return ''

    cols = [c for c in df.columns]
    header_labels = [c.replace('_STR', '').replace('_', ' ').upper() for c in cols]
    
    header_html = "".join([f"<th style='padding:10px 6px; text-align:center;'>{label}</th>" for label in header_labels])

    rows_html = ""
    for _, row in df.iterrows():
        style = get_row_style(row)
        cells = "".join([f"<td style='padding:8px 6px; border-bottom:1px solid #e5e7eb; text-align:center;'>{'' if pd.isna(row[c]) or str(row[c]) == 'nan' else row[c]}</td>" for c in cols])
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

# =================================================================
# CACHED VISUALIZATIONS
# =================================================================

@st.cache_data(show_spinner=False)
def get_pie_chart_status(df_counts):
    fig = px.pie(df_counts, names="status", values="count", hole=0.5,
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    return style_chart(fig)

@st.cache_data(show_spinner=False)
def get_bar_chart_priority(df_counts):
    fig = px.bar(df_counts, x="priority", y="count", text="count", color="priority",
                 color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"})
    return style_chart(fig)

# =================================================================
# MAIN ACTION PAGE FUNCTION
# =================================================================

def show_action_page(df, selected_block, selected_week):
    st.markdown("## 🛠️ Action Tracker")

    if df is None or df.empty:
        st.warning("Tidak ada data action")
        return

    # 1. PRE-PROCESSING & CLEANING
    df = df.copy()
    
    # Filter Metric Group 'action'
    df_action = df[df["metric_group"] == "action"].copy()

    if df_action.empty:
        st.info(f"Tidak ada data dengan kategori 'action' untuk block {selected_block}")
        return

    # --- FIX MASALAH 1: NORMALIZE WEEK_DATE & SELECTED_WEEK ---
    # Memastikan perbandingan tanggal tidak gagal karena jam (00:00:00)
    df_action["week_date"] = pd.to_datetime(df_action["week_date"], errors="coerce").dt.normalize()
    current_week_dt = pd.to_datetime(selected_week).normalize()
    
    # --- FIX MASALAH 3: NORMALISASI STATUS ---
    if "status" in df_action.columns:
        df_action["status"] = df_action["status"].fillna("unknown").astype(str).str.lower().str.strip()
        # Mapping status agar konsisten
        df_action["status"] = df_action["status"].replace({
            "on progress": "progress",
            "in progress": "progress"
        })
    
    if "priority" in df_action.columns:
        df_action["priority"] = df_action["priority"].fillna("Medium").astype(str).str.capitalize()

    if "due_date" in df_action.columns:
        df_action["due_date"] = pd.to_datetime(df_action["due_date"], errors="coerce").dt.normalize()

    # Filter Data Minggu Terpilih (Gunakan pembanding yang sudah dinormalisasi)
    df_now = df_action[df_action["week_date"] == current_week_dt].copy().reset_index(drop=True)

    # 2. TOP SUMMARY
    if not df_now.empty:
        st.markdown(f"📌 Menampilkan **{len(df_now)} action** | Block: **{selected_block}**")

        # 3. KPI SECTION
        open_count = len(df_now[df_now["status"] == "open"])
        progress_count = len(df_now[df_now["status"] == "progress"])
        closed_count = len(df_now[df_now["status"] == "closed"])
        
        overdue_count = 0
        if "due_date" in df_now.columns:
            # Overdue = belum closed dan due_date sudah lewat dari minggu terpilih
            overdue_count = len(df_now[(df_now["due_date"] < current_week_dt) & (df_now["status"] != "closed")])

        c1, c2, c3, c4 = st.columns(4)
        with c1: render_kpi_card("Open Action", open_count)
        with c2: render_kpi_card("In Progress", progress_count)
        with c3: render_kpi_card("Closed", closed_count)
        with c4: render_kpi_card("Overdue", overdue_count)

        # 4. DETAILED TABLE WITH FILTERS
        st.markdown("---")
        st.markdown("### 🎛️ Detailed Action Tracking")

        f1, f2, f3 = st.columns(3)
        with f1: 
            status_opts = ["All"] + sorted(df_now["status"].unique().tolist())
            status_filter = st.selectbox("Filter Status", status_opts)
        with f2: 
            prio_opts = ["All"] + sorted(df_now["priority"].unique().tolist())
            priority_filter = st.selectbox("Filter Priority", prio_opts)
        with f3: 
            pic_opts = ["All"] + sorted(df_now["pic"].dropna().unique().tolist()) if "pic" in df_now.columns else ["All"]
            pic_filter = st.selectbox("Filter PIC", pic_opts)

        # Apply Filters
        display_df = df_now.copy()
        if status_filter != "All": display_df = display_df[display_df["status"] == status_filter]
        if priority_filter != "All": display_df = display_df[display_df["priority"] == priority_filter]
        if pic_filter != "All" and "pic" in display_df.columns: display_df = display_df[pic_filter == display_df["pic"]]

        st.markdown("**📊 Data Action (Colored by Priority)**")
        
        # Format due_date untuk tampilan tabel
        if "due_date" in display_df.columns:
            display_df["DUE_DATE_STR"] = display_df["due_date"].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else "-")
        
        action_cols = ["block", "action_detail", "pic", "status", "priority", "DUE_DATE_STR"]
        final_cols = [c for c in action_cols if c in display_df.columns]

        if not display_df.empty:
            render_issue_table_colored(display_df[final_cols])
        else:
            st.info("Tidak ada data sesuai filter")

        # 5. VISUAL ANALYTICS
        st.markdown("<div style='margin-top:-20px'></div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### 📊 Visual Analytics")
        v1, v2 = st.columns(2)

        with v1:
            st.markdown("##### 📌 Status Distribution")
            s_df = df_now["status"].value_counts().reset_index()
            s_df.columns = ["status", "count"]
            st.plotly_chart(get_pie_chart_status(s_df), use_container_width=True)

        with v2:
            st.markdown("##### 🚨 Priority Breakdown")
            p_df = df_now["priority"].value_counts().reset_index()
            p_df.columns = ["priority", "count"]
            st.plotly_chart(get_bar_chart_priority(p_df), use_container_width=True)
    else:
        st.info(f"Tidak ada data action pada minggu {selected_week}")

    # 6. TREND ANALYSIS (Last 15 Weeks)
    st.markdown("---")
    st.markdown("### 📈 Trend Action (Last 15 Weeks)")

    if not df_action.empty:
        trend_prep = df_action.copy()
        
        # --- FIX MASALAH 2: NORMALIZE UNTUK TREND (Mencegah object/jump) ---
        trend_prep["week_date_only"] = trend_prep["week_date"].dt.normalize()

        all_weeks = sorted(trend_prep["week_date_only"].dropna().unique())[-15:]
        statuses = ["open", "progress", "closed"]
        
        # Create MultiIndex untuk memastikan tidak ada minggu yang bolong di grafik
        full_index = pd.MultiIndex.from_product([all_weeks, statuses], names=["week_date", "status"])
        
        trend_group = (
            trend_prep.groupby(["week_date_only", "status"])
            .size()
            .reindex(full_index, fill_value=0)
            .reset_index(name="count")
        )

        t1, t2, t3 = st.columns(3)
        with t1: st.plotly_chart(safe_bar(trend_group[trend_group["status"] == "open"], "🔴 Open", "#ef4444"), use_container_width=True)
        with t2: st.plotly_chart(safe_bar(trend_group[trend_group["status"] == "progress"], "🟡 Progress", "#f59e0b"), use_container_width=True)
        with t3: st.plotly_chart(safe_bar(trend_group[trend_group["status"] == "closed"], "🟢 Closed", "#10b981"), use_container_width=True)