import os
import pandas as pd
import streamlit as st

@st.cache_data(show_spinner=False)
def load_excel_data(file):
    """
    Memuat data Excel, melakukan validasi kolom, tipe data, dan pembersihan string.
    Mendukung skema standar operasional, skema khusus fleet, 
    skema unit (unjuk kerja), skema Productivity, skema Hybrid, maupun Action Issue Findings.
    
    Menggunakan @st.cache_data untuk optimasi performa agar file tidak di-load ulang
    setiap kali ada perubahan widget di Streamlit.
    """
    # Ambil nama file untuk deteksi grup
    file_name = file.name if hasattr(file, "name") else os.path.basename(str(file))
    
    # Deteksi grup di awal untuk menentukan skema validasi
    metric_group = detect_metric_group(file_name)

    # =====================================================
    # PATCH: HANDLE ACTION ISSUE FINDINGS (MODUL 10-12)
    # =====================================================
    if metric_group == "aif":
        try:
            # Read all sheets
            issue_df = pd.read_excel(file, sheet_name="issue_log", engine="openpyxl")
            action_df = pd.read_excel(file, sheet_name="action_tracker", engine="openpyxl")
            finding_df = pd.read_excel(file, sheet_name="findings_summary", engine="openpyxl")

            # --- CLEAN ISSUE ---
            issue_df.columns = issue_df.columns.str.strip().str.lower()
            issue_df["week_date"] = pd.to_datetime(issue_df["week_date"], errors="coerce")
            issue_df["metric_group"] = "issue"
            issue_df["source"] = "issue"

            # --- CLEAN ACTION ---
            action_df.columns = action_df.columns.str.strip().str.lower()
            action_df["week_date"] = pd.to_datetime(action_df["week_date"], errors="coerce")
            action_df["metric_group"] = "action"
            action_df["source"] = "action"

            # --- CLEAN FINDING ---
            finding_df.columns = finding_df.columns.str.strip().str.lower()
            finding_df["week_date"] = pd.to_datetime(finding_df["week_date"], errors="coerce")
            finding_df["metric_group"] = "finding"
            finding_df["source"] = "finding"

            # --- Gabungkan (PATCH FINAL) ---
            # Menggunakan concat dengan sort=False agar kolom yang berbeda tidak dipaksa urut abjad
            df_combined = pd.concat(
                [issue_df, action_df, finding_df], 
                ignore_index=True, 
                sort=False
            )

            return df_combined

        except Exception as e:
            raise ValueError(f"Gagal membaca file action_issue_findings: {e}")

    # =====================================================
    # PATCH OPTIMASI: Load dengan engine & dtypes kategori (Untuk non-AIF)
    # =====================================================
    df = pd.read_excel(
        file,
        engine="openpyxl",
        dtype={
            "block": "category",
            "category": "category",
            "type": "category",
            "unit_type": "category",
            "no_lambung": "category"
        }
    )

    # =====================================================
    # PATCH FINAL: HANDLE FLEET SCHEMA (MULTI-SCHEMA & HYBRID)
    # =====================================================
    if metric_group == "fleet":
        # FIX: HYBRID DETECTION (KPI + UNIT)
        has_kpi_cols = all(col in df.columns for col in ["metric", "plan", "actual"])
        has_detail_cols = all(col in df.columns for col in ["loader_id", "loader_type"])
        
        is_plan_actual = has_kpi_cols
        is_hybrid = has_kpi_cols and has_detail_cols

        # SCHEMA 1: PLAN VS ACTUAL (KPI FLEET)
        if is_plan_actual:
            expected_columns_kpi = [
                "date", "week_date", "block",
                "metric", "plan", "actual"
            ]

            missing_cols = [col for col in expected_columns_kpi if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Kolom fleet (plan-actual) tidak lengkap: {missing_cols}")

            # Clean string standar
            for col in ["date", "week_date", "block", "metric"]:
                df[col] = df[col].astype(str).str.strip()

            # Convert date
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["week_date"] = pd.to_datetime(df["week_date"], errors="coerce")

            # Validate date
            if df["date"].isna().any():
                bad_rows = df[df["date"].isna()].index.tolist()
                raise ValueError(f"Kolom 'date' fleet tidak valid pada baris: {bad_rows[:10]}")

            if df["week_date"].isna().any():
                bad_rows = df[df["week_date"].isna()].index.tolist()
                raise ValueError(f"Kolom 'week_date' fleet tidak valid pada baris: {bad_rows[:10]}")

            # Konversi numeric
            df["plan"] = pd.to_numeric(df["plan"], errors="coerce")
            df["actual"] = pd.to_numeric(df["actual"], errors="coerce")

            # Ambil hanya row KPI untuk validasi numeric
            df_kpi = df[
                df["metric"].notna() &
                (df["metric"].astype(str).str.strip() != "") &
                (df["metric"].astype(str).str.lower() != "nan")
            ]

            if not df_kpi.empty:
                if df_kpi["plan"].isna().any():
                    bad_rows = df_kpi[df_kpi["plan"].isna()].index.tolist()
                    raise ValueError(f"Kolom 'plan' fleet tidak valid pada baris: {bad_rows[:10]}")

                if df_kpi["actual"].isna().any():
                    bad_rows = df_kpi[df_kpi["actual"].isna()].index.tolist()
                    raise ValueError(f"Kolom 'actual' fleet tidak valid pada baris: {bad_rows[:10]}")

            if not is_hybrid:
                df["metric_group"] = "fleet"
                return df

        # HANDLE HYBRID ATAU DETAIL ONLY (UNIT-BASED FLEET)
        if is_hybrid or not is_plan_actual:
            expected_columns_detail = [
                "date", "week_date", "block",
                "fleet_type", "loader_type", "loader_id"
            ]
            
            missing_cols_detail = [col for col in expected_columns_detail if col not in df.columns]
            if missing_cols_detail:
                raise ValueError(f"Kolom detail fleet tidak lengkap: {missing_cols_detail}")

            detail_str_cols = ["fleet_type", "loader_type", "loader_id"]
            if "fleet_id" in df.columns:
                detail_str_cols.append("fleet_id")
            if "hauler_type" in df.columns:
                detail_str_cols.append("hauler_type")
            
            for col in detail_str_cols:
                df[col] = df[col].astype(str).str.strip()

            if not is_hybrid:
                for col in ["date", "week_date", "block"]:
                    df[col] = df[col].astype(str).str.strip()
                
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df["week_date"] = pd.to_datetime(df["week_date"], errors="coerce")

                if df["date"].isna().any():
                    bad_rows = df[df["date"].isna()].index.tolist()
                    raise ValueError(f"Kolom 'date' fleet tidak valid pada baris: {bad_rows[:10]}")

            if "hauler_count" in df.columns:
                df["hauler_count"] = pd.to_numeric(df["hauler_count"], errors="coerce")
                if not is_hybrid and df["hauler_count"].isna().any():
                    bad_rows = df[df["hauler_count"].isna()].index.tolist()
                    raise ValueError(f"Kolom 'hauler_count' tidak valid pada baris: {bad_rows[:10]}")

            df["metric_group"] = "fleet"
            return df

    # =====================================================
    # PATCH REVISI: HANDLE UNIT SCHEMA (UNJUK KERJA)
    # =====================================================
    if metric_group == "unit":
        expected = [
            "date", "week_date", "block",
            "category", "type",
            "unit_type", "no_lambung", "hm",
            "pa_plan", "pa_actual",
            "ma_plan", "ma_actual",
            "ua_plan", "ua_actual"
        ]

        missing = [c for c in expected if c not in df.columns]
        if missing:
            raise ValueError(f"Kolom unit tidak lengkap: {missing}")

        # CLEAN STRING DULU
        str_cols = ["block", "category", "type", "unit_type", "no_lambung"]
        for col in str_cols:
            df[col] = df[col].astype(str).str.strip()

        # HANDLE TYPE FALLBACK
        df["type"] = df["type"].replace(["", "nan", "None"], pd.NA)
        df["type"] = df["type"].fillna(df["unit_type"])

        # CONVERT DATE
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["week_date"] = pd.to_datetime(df["week_date"], errors="coerce")

        if df["date"].isna().any():
            bad = df[df["date"].isna()].index.tolist()
            raise ValueError(f"Kolom 'date' unit tidak valid pada baris: {bad[:10]}")

        if df["week_date"].isna().any():
            bad = df[df["week_date"].isna()].index.tolist()
            raise ValueError(f"Kolom 'week_date' unit tidak valid pada baris: {bad[:10]}")

        # NUMERIC CONVERSION
        num_cols = ["hm", "pa_plan", "pa_actual", "ma_plan", "ma_actual", "ua_plan", "ua_actual"]
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # PATCH: HANDLE OPTIONAL EWH COLUMNS
        ewh_cols = ["ewh_plan", "ewh_actual"]
        for col in ewh_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 🚀 FINAL PERFORMANCE PATCH (WAJIB - UNIT ONLY)
        df["week_date_norm"] = df["week_date"].dt.normalize()
        df["date_norm"] = df["date"].dt.normalize()
        df["category_clean"] = df["category"].astype(str)
        df["type_clean"] = df["type"].astype(str)
        df["unit_type_clean"] = df["unit_type"].astype(str)
        df["no_lambung_clean"] = df["no_lambung"].astype(str)
        df["unit_key"] = df["unit_type_clean"] + " - " + df["no_lambung_clean"]

        cat_cols_optimized = ["block", "category_clean", "type_clean", "unit_type_clean", "no_lambung_clean"]
        for col in cat_cols_optimized:
            df[col] = df[col].astype("category")

        df = df.sort_values(["block", "week_date_norm", "category_clean"])
        df["metric_group"] = "unit"
        return df

    # =====================================================
    # PATCH: HANDLE PRODUCTIVITY SCHEMA (MODUL 6)
    # =====================================================
    if metric_group == "productivity":
        expected = [
            "date", "week_date", "block",
            "category", "type", "unit_type", "no_lambung",
            "plan", "actual", "unit"
        ]

        missing = [c for c in expected if c not in df.columns]
        if missing:
            raise ValueError(f"Kolom productivity tidak lengkap: {missing}")

        str_cols = ["block", "category", "type", "unit_type", "no_lambung", "unit"]
        for col in str_cols:
            df[col] = df[col].astype(str).str.strip()

        df["type"] = df["type"].replace(["", "nan", "None"], pd.NA)
        df["type"] = df["type"].fillna(df["unit_type"])

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["week_date"] = pd.to_datetime(df["week_date"], errors="coerce")

        if df["date"].isna().any():
            bad = df[df["date"].isna()].index.tolist()
            raise ValueError(f"Kolom 'date' productivity tidak valid pada baris: {bad[:10]}")

        df["plan"] = pd.to_numeric(df["plan"], errors="coerce")
        df["actual"] = pd.to_numeric(df["actual"], errors="coerce")

        df["week_date_norm"] = df["week_date"].dt.normalize()
        df["date_norm"] = df["date"].dt.normalize()
        df["category_clean"] = df["category"].astype(str)
        df["type_clean"] = df["type"].astype(str)
        df["unit_type_clean"] = df["unit_type"].astype(str)
        df["no_lambung_clean"] = df["no_lambung"].astype(str)
        df["unit_key"] = df["unit_type_clean"] + " - " + df["no_lambung_clean"]

        cat_cols_optimized = ["block", "category_clean", "type_clean", "unit_type_clean", "no_lambung_clean"]
        for col in cat_cols_optimized:
            df[col] = df[col].astype("category")

        df = df.sort_values(["block", "week_date_norm", "category_clean"])
        df["metric_group"] = "productivity"
        return df

    # =====================================================
    # PATCH: HANDLE INVENTORY SCHEMA (MODUL 8)
    # =====================================================
    if metric_group == "inventory":
        expected = ["week_date", "block", "metric", "actual", "unit"]
        missing = [c for c in expected if c not in df.columns]
        if missing:
            raise ValueError(f"Kolom inventory tidak lengkap: {missing}")

        for col in ["block", "metric", "unit"]:
            df[col] = df[col].astype(str).str.strip()

        df["week_date"] = pd.to_datetime(df["week_date"], errors="coerce")
        df["actual"] = pd.to_numeric(df["actual"], errors="coerce")

        df["metric_group"] = "inventory"
        return df

    # =====================================================
    # ORIGINAL LOGIC: OPERATIONAL SCHEMA (Produksi, Hauling, Fuel, etc.)
    # =====================================================
    expected_columns = [
        "date", "week_date", "block", "metric",
        "plan", "actual", "unit",
    ]

    missing_cols = [col for col in expected_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Kolom tidak lengkap: {missing_cols}")

    for col in ["date", "week_date", "block", "metric", "unit"]:
        df[col] = df[col].astype(str).str.strip()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["week_date"] = pd.to_datetime(df["week_date"], errors="coerce")

    if df["date"].isna().any():
        bad_rows = df[df["date"].isna()].index.tolist()
        raise ValueError(f"Kolom 'date' format tidak valid pada baris: {bad_rows[:10]}")

    df["plan"] = pd.to_numeric(df["plan"], errors="coerce")
    df["actual"] = pd.to_numeric(df["actual"], errors="coerce")

    df_kpi = df[
        df["metric"].notna() & 
        (df["metric"].astype(str).str.strip() != "") & 
        (df["metric"].astype(str).str.lower() != "nan")
    ]

    if not df_kpi.empty:
        if df_kpi["plan"].isna().any():
            bad_rows = df_kpi[df_kpi["plan"].isna()].index.tolist()
            raise ValueError(f"Kolom 'plan' tidak valid pada baris: {bad_rows[:10]}")

    if "metric_group" not in df.columns:
        df["metric_group"] = metric_group
    else:
        df["metric_group"] = df["metric_group"].astype(str).str.strip()
        mask_empty = df["metric_group"].isin(["", "nan", "None"])
        if mask_empty.any():
            df.loc[mask_empty, "metric_group"] = metric_group

    return df

def detect_metric_group(file_name: str) -> str:
    """
    Mendeteksi grup metrik berdasarkan nama file.
    """
    name = file_name.lower()

    if "action_issue_findings" in name:
        return "aif"
    elif "produksi" in name:
        return "produksi"
    elif "hauling" in name:
        return "hauling"
    elif "fuel" in name:
        return "fuel"
    elif "weather" in name:
        return "weather"
    elif "fleet" in name:
        return "fleet"
    elif "productivity" in name or "produkt" in name or "pty" in name:
        return "productivity"
    elif "unit" in name or "unjuk" in name:
        return "unit"
    elif "inventory" in name:
        return "inventory"
    else:
        return "unknown"