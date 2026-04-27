import streamlit as st


def show_home_page():
    st.subheader("Welcome")
    st.write(
        """
        Ini adalah dashboard operasional tambang berbasis data harian dan weekly report.

        Tahap awal dashboard ini akan fokus ke:
        - Produksi Utama
        - OB
        - Coal Getting
        - Stripping Ratio
        - Coal Crushing
        - Distance OB
        - Distance CG
        """
    )