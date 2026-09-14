"""Ejecutar desde la raíz con uv run python src/analyze.py."""

from pathlib import Path
import json, math
import numpy as np, pandas as pd
from scipy.stats import poisson, nbinom, skellam
from models import goal_rates, probabilities, group_sim, summarize, interval

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
OUT = ROOT / "outputs"
PROC = ROOT / "data/processed"
for p in [OUT, PROC, OUT / "figures"]:
    p.mkdir(exist_ok=True, parents=True)
SEED = 14643
N = 10000
ALIAS = {
    "Bayern Munchen": "Bayern Munich",
    "FC Bayern Munchen": "Bayern Munich",
    "Bayer Leverkusen": "Leverkusen",
    "RasenBallsport Leipzig": "RB Leipzig",
    "Borussia Dortmund": "Dortmund",
    "Eintracht Frankfurt": "Ein Frankfurt",
    "Frankfurter SG Eintracht": "Ein Frankfurt",
    "1. FC Koln": "FC Koln",
    "Bor. Monchengladbach": "MGladbach",
    "Borussia Monchengladbach": "MGladbach",
    "1. FSV Mainz 05": "Mainz",
    "1. FC Union Berlin": "Union Berlin",
    "VfB Stuttgart": "Stuttgart",
    "SC Freiburg": "Freiburg",
    "FC Augsburg": "Augsburg",
    "VfL Bochum": "Bochum",
    "VfL Wolfsburg": "Wolfsburg",
    "SV Darmstadt 98": "Darmstadt",
    "1. FC Heidenheim": "Heidenheim",
    "1899 Hoffenheim": "Hoffenheim",
}


def historical():
    df = pd.read_csv(RAW / "germany.csv")
    df = df[(df.tier == 1) & df.Season.between(1963, 2023)].copy()
    df["home"] = df.home.replace(ALIAS)
    df["visitor"] = df.visitor.replace(ALIAS)
    champions = []
    for season, ms in df.groupby("Season"):
        clubs = sorted(set(ms.home) | set(ms.visitor))
        rows = []
        for club in clubs:
            h = ms[ms.home == club]
            a = ms[ms.visitor == club]
            w = int((h.hgoal > h.vgoal).sum() + (a.vgoal > a.hgoal).sum())
            d = int((h.hgoal == h.vgoal).sum() + (a.vgoal == a.hgoal).sum())
            l = len(h) + len(a) - w - d
            gf = int(h.hgoal.sum() + a.vgoal.sum())
            ga = int(h.vgoal.sum() + a.hgoal.sum())
            rows.append(
                dict(
                    team=club,
                    played=len(h) + len(a),
                    wins=w,
                    draws=d,
                    losses=l,
                    gf=gf,
                    ga=ga,
                    points=(2 if season < 1995 else 3) * w + d,
                    gd=gf - ga,
                )
            )
        champ = max(
            rows,
            key=lambda x: (
                x["points"],
                x["gf"] / max(1, x["ga"]) if season < 1969 else x["gd"],
                x["gf"],
            ),
        )
        if season == 1991:
            # La fuente de partidos conserva 340 de los 380 cruces de esta campaña.
            # Registro completo contrastado con DSFS y Sportschau (38 jornadas).
            assert len(ms) == 340
            champ = dict(
                team="Stuttgart",
                played=38,
                wins=21,
                draws=10,
                losses=7,
                gf=62,
                ga=32,
                points=52,
                gd=30,
            )
        else:
            assert len(ms) == (240 if season in [1963, 1964] else 306), (
                season,
                len(ms),
            )
        champions.append({"end_year": int(season + 1), **champ})
    ch = pd.DataFrame(champions)
    ch[ch.end_year <= 2023].to_csv(PROC / "champions_1964_2023.csv", index=False)
    hist = ch[ch.end_year <= 2023]
    recent = hist[hist.end_year >= 2005]
    assert len(hist) == 60 and (hist.team == "Bayern Munich").sum() == 32
    assert len(recent) == 19 and (recent.team == "Bayern Munich").sum() == 15
    fits = []
    for name, sub in [
        ("Todos", hist),
        ("Bayern", hist[hist.team == "Bayern Munich"]),
        ("Otros", hist[hist.team != "Bayern Munich"]),
    ]:
        mu = float(sub.losses.mean())
        var = float(sub.losses.var(ddof=1))
        rate = sub.losses.sum() / sub.played.sum()
        row = {
            "group": name,
            "n": len(sub),
            "mean": mu,
            "variance": var,
            "p_zero": math.exp(-mu),
            "p_zero_34": math.exp(-34 * rate),
            "empirical_zero": float((sub.losses == 0).mean()),
        }
        if var > mu:
            r = mu * mu / (var - mu)
            p = r / (r + mu)
            row.update(nb_r=r, nb_p_zero=float(nbinom.pmf(0, r, p)))
        fits.append(row)
    return (
        df,
        ch,
        {"non_bayern_all": 28 / 60, "non_bayern_recent": 4 / 19, "fits": fits},
    )
