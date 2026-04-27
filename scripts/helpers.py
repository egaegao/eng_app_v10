import pandas as pd

def add_achievement_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menghitung persentase pencapaian (actual/plan).
    Menangani kasus plan = 0 untuk menghindari division by zero atau nilai inf/NaN.
    """
    result = df.copy()

    # Mengganti angka 0 pada 'plan' dengan NA agar hasil pembagian menjadi NA, bukan 'inf'
    # Kemudian mengisi hasil NA tersebut dengan 0 menggunakan fillna(0)
    result["achievement_pct"] = (
        result["actual"] / result["plan"].replace(0, pd.NA)
    ) * 100

    result["achievement_pct"] = result["achievement_pct"].fillna(0)

    return result


def format_metric_name(metric: str) -> str:
    """
    Memetakan key metric mentah menjadi nama yang lebih rapi untuk tampilan UI/Chart.
    """
    mapping = {
        "overburden": "OB",
        "coal_getting": "Coal Getting",
        "stripping_ratio": "Stripping Ratio",
        "coal_crushing": "Coal Crushing",
        "distance_ob": "Distance OB",
        "distance_cg": "Distance CG",
    }
    return mapping.get(metric, metric)