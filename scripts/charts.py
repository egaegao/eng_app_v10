import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

@st.cache_data(show_spinner=False)
def bar_plan_vs_actual(df, metric):
    """
    Menampilkan perbandingan Plan vs Actual dalam bentuk Bar Chart Grouped.
    Menggunakan dekorator cache untuk mempercepat render.
    """
    d = df[df["metric"] == metric]

    summary = d.groupby("metric").agg({
        "plan": "sum",
        "actual": "sum"
    }).reset_index()

    fig = go.Figure()

    fig.add_bar(
        x=summary["metric"],
        y=summary["plan"],
        name="Plan",
        marker_color="gray"
    )

    fig.add_bar(
        x=summary["metric"],
        y=summary["actual"],
        name="Actual",
        marker_color="blue"
    )

    fig.update_layout(
        title=f"Plan vs Actual - {metric}",
        barmode='group',
        xaxis_title="Metric",
        yaxis_title="Value",
        legend_title="Legend",
        hovermode="x unified"
    )

    return fig


@st.cache_data(show_spinner=False)
def trend_daily(df, metric):
    """
    Menampilkan tren harian Plan vs Actual menggunakan Line Chart.
    """
    d = df[df["metric"] == metric]

    fig = px.line(
        d,
        x="date",
        y=["plan", "actual"],
        color_discrete_map={
            "plan": "gray",
            "actual": "blue"
        },
        markers=True
    )

    fig.update_layout(
        title=f"Trend Daily - {metric}",
        xaxis_title="Tanggal",
        yaxis_title="Value",
        legend_title="Type",
        hovermode="x unified"
    )
    
    return fig


@st.cache_data(show_spinner=False)
def trend_weekly(df, metric):
    """
    Menampilkan tren mingguan Plan vs Actual. 
    Data dikelompokkan (aggregated) berdasarkan week_date.
    """
    d = df[df["metric"] == metric]

    # Melakukan agregasi mingguan
    d_weekly = d.groupby("week_date").agg({
        "plan": "sum",
        "actual": "sum"
    }).reset_index()

    fig = px.line(
        d_weekly,
        x="week_date",
        y=["plan", "actual"],
        color_discrete_map={
            "plan": "gray",
            "actual": "blue"
        },
        markers=True
    )

    fig.update_layout(
        title=f"Trend Weekly - {metric}",
        xaxis_title="Minggu Ke-",
        yaxis_title="Total Value",
        legend_title="Type",
        hovermode="x unified"
    )
    
    return fig