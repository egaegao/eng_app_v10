import streamlit as st

def apply_app_style():
    st.markdown(
        """
        <style>
        /* 1. Layout Configuration */
        .main {
            padding-top: 0.5rem;
        }

        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
        }

        /* 2. Sticky Header Styling */
        .sticky-header {
            position: sticky;
            top: 0;
            background: white;
            z-index: 999;
            padding-top: 0.2rem;
            padding-bottom: 0.8rem;
            border-bottom: 1px solid #e9edf3;
            margin-bottom: 1rem;
        }

        /* 3. DataFrame Styling */
        div[data-testid="stDataFrame"] {
            border: 1px solid #e9edf3;
            border-radius: 12px;
            overflow: hidden;
        }

        /* 4. Modern Button Navigation Styling (FINAL VERSION) */
        
        /* BASE BUTTON - General Box Styling */
        button {
            border-radius: 10px !important;
            height: 60px !important;
            line-height: 1.2 !important;
            transition: all 0.2s ease !important;
            margin-bottom: 0.5rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        /* FORCE TEXT INSIDE BUTTON (Targeting p and span) */
        button p {
            font-weight: 800 !important;
            font-size: 15px !important;
            margin: 0 !important;
        }

        button span {
            font-weight: 800 !important;
        }

        /* PRIMARY (ACTIVE TAB) - More Intense Bold & Larger */
        button[kind="primary"] {
            background-color: #2563eb !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
        }

        button[kind="primary"] p {
            font-weight: 900 !important; /* Sangat Tebal untuk Tab Aktif */
            font-size: 16px !important; /* Sedikit lebih besar */
            color: white !important;
        }

        /* SECONDARY (NON-ACTIVE TAB) */
        button[kind="secondary"] {
            background-color: #f9fafb !important;
            color: #374151 !important;
            border: 1px solid #e5e7eb !important;
        }

        /* HOVER EFFECT */
        button[kind="secondary"]:hover {
            border: 1px solid #2563eb !important;
            color: #2563eb !important;
            background-color: #eef2ff !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05) !important;
        }

        button[kind="secondary"]:hover p {
            color: #2563eb !important;
        }

        /* ACTIVE CLICK FEEDBACK */
        button:active {
            transform: scale(0.98) !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )