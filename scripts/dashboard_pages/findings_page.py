import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# =================================================================
# UI HELPERS & STYLING (Standardized for Enterprise Look)
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
        # Menggunakan format tanggal yang konsisten untuk label
        df["week_label"] = pd.to_datetime(df["week_date_only"]).dt.strftime("%d-%b")

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
    """Tabel utama dengan Row Coloring & Limit 200 Row untuk Performa"""
    
    # PATCH WAJIB: Limit table rendering agar UI tetap instant
    df = df.head(200)
    
    def get_row_style(row):
        status = str(row.get("status", "")).lower()
        if status == "open":
            return 'background-color: #fee2e2;' # Merah muda
        elif status == "progress":
            return 'background-color: #fef3c7;' # Kuning muda
        elif status == "closed":
            return 'background-color: #dcfce7;' # Hijau muda
        return ''

    cols = [c for c in df.columns]
    header_labels = [c.replace('_', ' ').upper() for c in cols]
    
    header_html = "".join([f"<th style='padding:12px 8px; text-align:center; position:sticky; top:0; background:#1e293b; color:white; z-index:10;'>{label}</th>" for label in header_labels])

    rows_html = ""
    for _, row in df.iterrows():
        style = get_row_style(row)
        cells = "".join([f"<td style='padding:10px 8px; border-bottom:1px solid #e5e7eb; text-align:center;'>{'' if pd.isna(row[c]) or str(row[c]) == 'nan' else row[c]}</td>" for c in cols])
        rows_html += f"<tr style='{style}'>{cells}</tr>"

    html_content = f"""
    <div style="
        overflow-y:auto; 
        max-height:450px; 
        border:1px solid #e5e7eb; 
        border-radius:10px; 
        font-family:'Inter', sans-serif;
    ">
        <table style="width:100%; border-collapse:collapse; font-size:13px; min-width:1000px;">
            <thead>
                <tr style="font-weight:700;">
                    {header_html}
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
    components.html(html_content, height=470)

# =================================================================
# CACHEABLE VISUALS (OPTIONAL PATCH)
# =================================================================

@st.cache_data(show_spinner=False)
def build_findings_pie(cat_dist):
    fig = px.pie(cat_dist, names="category", values="count", hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel)
    return style_chart(fig)

@st.cache_data(show_spinner=False)
def build_findings_bar(status_analytics):
    fig = px.bar(
        status_analytics,
        x="status",
        y="count",
        text="count",
        color="status",
        color_discrete_map={
            "open": "#ef4444",
            "progress": "#f59e0b",
            "closed": "#10b981",
            "unknown": "#9ca3af"
        }
    )
    return style_chart(fig)

# =================================================================
# MAIN FINDINGS PAGE FUNCTION
# =================================================================

def show_findings_page(df, selected_block, selected_week):
    st.markdown("## 📋 Findings Summary")

    if df is None or df.empty:
        st.warning("Tidak ada data findings")
        return

    df = df.copy()

    # ==============================
    # 1. PREPROCESSING & CLEANING
    # ==============================
    # Handle column naming mismatch
    if "category" not in df.columns and "issue_category" in df.columns:
        df["category"] = df["issue_category"]

    # Filter Group (Hanya ambil data finding)
    df_find = df[df["metric_group"] == "finding"].copy()

    if df_find.empty:
        st.info(f"Tidak ada data findings untuk block {selected_block}")
        return

    # PATCH WAJIB 1: Normalize week_date agar tidak ada mismatch jam (00:00:00)
    df_find["week_date"] = pd.to_datetime(df_find["week_date"], errors="coerce").dt.normalize()
    
    # Ambil data minggu terpilih dengan normalisasi juga
    current_week_dt = pd.to_datetime(selected_week).normalize()
    df_now = df_find[df_find["week_date"] == current_week_dt].copy().reset_index(drop=True)

    if df_now.empty:
        st.info(f"Tidak ada findings pada minggu {selected_week}")
        return

    # PATCH WAJIB 3: Clean & Map status agar KPI Konsisten
    if "status" in df_now.columns:
        df_now["status"] = df_now["status"].fillna("unknown").astype(str).str.strip().str.lower()
        # Mapping status varian ke standar 'progress'
        df_now["status"] = df_now["status"].replace({
            "in progress": "progress",
            "on progress": "progress"
        })
    else:
        df_now["status"] = "unknown"

    # Format Date for Table Display
    df_now["week_date_display"] = df_now["week_date"].dt.date
    if "due_date" in df_now.columns:
        df_now["due_date"] = pd.to_datetime(df_now["due_date"], errors="coerce").dt.date

    # ==============================
    # 2. TOP SUMMARY & KPI
    # ==============================
    st.markdown(f"📌 Menampilkan **{len(df_now)} findings** | Block: **{selected_block}**")

    total_findings = len(df_now)
    open_count = len(df_now[df_now["status"] == "open"])
    progress_count = len(df_now[df_now["status"] == "progress"])
    closed_count = len(df_now[df_now["status"] == "closed"])

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_kpi_card("Total Findings", total_findings)
    with c2: render_kpi_card("Open", open_count)
    with c3: render_kpi_card("Progress", progress_count)
    with c4: render_kpi_card("Closed", closed_count)

    # ==============================
    # 3. DETAILED TABLE & FILTERS
    # ==============================
    st.markdown("---")
    st.markdown("### 🎛️ Detailed Findings Tracking")

    key_prefix = f"find_{str(selected_block).lower().replace(' ', '_')}"

    f1, f2, f3 = st.columns(3)
    with f1:
        status_opts = ["All"] + sorted(df_now["status"].unique().tolist())
        status_filter = st.selectbox("Filter Status", status_opts, key=f"{key_prefix}_status")

    with f2:
        cat_opts = ["All"] + sorted(df_now["category"].dropna().unique().tolist()) if "category" in df_now.columns else ["All"]
        category_filter = st.selectbox("Filter Category", cat_opts, key=f"{key_prefix}_cat")

    with f3:
        pic_opts = ["All"] + sorted(df_now["pic"].dropna().unique().tolist()) if "pic" in df_now.columns else ["All"]
        pic_filter = st.selectbox("Filter PIC", pic_opts, key=f"{key_prefix}_pic")

    display_df = df_now.copy()

    # Apply Filters
    if status_filter != "All":
        display_df = display_df[display_df["status"] == status_filter]
    
    if category_filter != "All" and "category" in display_df.columns:
        display_df = display_df[display_df["category"] == category_filter]

    if pic_filter != "All" and "pic" in display_df.columns:
        display_df = display_df[display_df["pic"] == pic_filter]

    if not display_df.empty and "detail_temuan" in display_df.columns:
        display_df = display_df.dropna(subset=["detail_temuan"])

    st.markdown("**📊 Data Findings (Colored by Status)**")

    finding_cols = [
        "week_date_display", "block", "category", "detail_temuan",
        "status", "due_date", "pic", "action_plan", "remarks"
    ]

    final_cols = [c for c in finding_cols if c in display_df.columns]
    
    render_df = display_df[final_cols].copy()
    if "week_date_display" in render_df.columns:
        render_df = render_df.rename(columns={"week_date_display": "week_date"})

    if not render_df.empty:
        render_issue_table_colored(render_df)
    else:
        st.info("Tidak ada data sesuai filter")

    # ==============================
    # 4. VISUAL ANALYTICS
    # ==============================
    st.markdown("<div style='margin-top:-20px'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📊 Visual Analytics")

    v1, v2 = st.columns(2)

    with v1:
        st.markdown("##### 📌 Category Distribution")
        if "category" in df_now.columns and not df_now["category"].dropna().empty:
            cat_dist = df_now["category"].value_counts().reset_index()
            cat_dist.columns = ["category", "count"]
            st.plotly_chart(build_findings_pie(cat_dist), use_container_width=True)
        else:
            st.info("Data kategori tidak tersedia")

    with v2:
        st.markdown("##### 📌 Status Breakdown")
        if "status" in df_now.columns and not df_now["status"].empty:
            status_analytics = df_now["status"].value_counts().reset_index()
            status_analytics.columns = ["status", "count"]
            st.plotly_chart(build_findings_bar(status_analytics), use_container_width=True)
        else:
            st.info("Data status tidak tersedia")

    # ==============================
    # 5. TREND BY CATEGORY (Dynamic Rows)
    # ==============================
    st.markdown("---")
    st.markdown("### 📈 Trend Findings by Category (Last 15 Weeks)")

    if not df_find.empty:
        trend_prep = df_find.copy()
        
        # PATCH WAJIB 2: Gunakan normalize agar sorting trend stabil secara kronologis
        trend_prep["week_date_only"] = trend_prep["week_date"].dt.normalize()
        
        all_weeks = sorted(trend_prep["week_date_only"].dropna().unique())[-15:]
        
        if "category" in trend_prep.columns:
            categories = sorted(trend_prep["category"].dropna().unique().tolist())
        else:
            categories = []
        
        if categories:
            colors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"]
            
            for i in range(0, len(categories), 3):
                t_cols = st.columns(3)
                for j in range(3):
                    if i + j < len(categories):
                        cat_name = categories[i+j]
                        cat_color = colors[(i+j) % len(colors)]
                        
                        cat_trend = (
                            trend_prep[trend_prep["category"] == cat_name]
                            .groupby("week_date_only")
                            .size()
                            .reindex(all_weeks, fill_value=0)
                            .reset_index(name="count")
                        )
                        
                        with t_cols[j]:
                            st.plotly_chart(safe_bar(cat_trend, f"📊 {cat_name}", cat_color), use_container_width=True)
        else:
            st.info("Kategori tidak ditemukan untuk trend.")
    else:
        st.info("Tidak ada data untuk menampilkan trend.")