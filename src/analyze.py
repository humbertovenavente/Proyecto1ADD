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


def leverkusen(df, ch):
    # Filtra por bloques: no conserva todo el archivo Elo en memoria.
    elo = pd.concat(
        [chunk[(chunk.country == "GER") & (chunk.date == "2023-08-15")]
         for chunk in pd.read_csv(RAW / "clubelo_archive.csv", chunksize=20000)],
        ignore_index=True,
    )
    actual = df[df.Season == 2023]
    clubs = sorted(actual.home.unique())
    cut = "2023-08-15"
    er = (
        elo[(elo.country == "GER") & (elo.date == cut) & elo.club.isin(clubs)]
        .copy()
        .sort_values("elo", ascending=False)
    )
    assert len(er) == 18
    er.to_csv(PROC / "bundesliga_elo_2023_08_15.csv", index=False)
    ratings = er.set_index("club").elo.to_dict()
    train = df[df.Season.between(2018, 2022)]
    total = float((train.hgoal + train.vgoal).mean())
    hfa = 60.0
    fixtures = actual[
        (actual.home == "Leverkusen") | (actual.visitor == "Leverkusen")
    ].sort_values("Date")
    rows = []
    for m in fixtures.itertuples():
        home = m.home == "Leverkusen"
        opp = m.visitor if home else m.home
        delta = ratings["Leverkusen"] - ratings[opp] + (hfa if home else -hfa)
        pw, pd_, pl = probabilities(delta, total)
        rows.append(
            {
                "date": m.Date,
                "opponent": opp,
                "home": home,
                "elo_delta": delta,
                "p_win": pw,
                "p_draw": pd_,
                "p_loss": pl,
                "p_unbeaten": pw + pd_,
            }
        )
    f = pd.DataFrame(rows)
    f.to_csv(PROC / "leverkusen_probabilities.csv", index=False)
    pb = float(f[f.opponent == "Bayern Munich"].p_unbeaten.prod())
    po = float(f[f.opponent != "Bayern Munich"].p_unbeaten.prod())
    p = pb * po
    rng = np.random.default_rng(SEED)
    u = rng.random((N, 34))
    loss = (u > f.p_unbeaten.to_numpy()).sum(axis=1)
    win = (u < f.p_win.to_numpy()).sum(axis=1)
    draw = 34 - win - loss
    pd.DataFrame(
        {
            "season": np.arange(1, N + 1),
            "wins": win,
            "draws": draw,
            "losses": loss,
            "points": 3 * win + draw,
        }
    ).to_csv(OUT / "leverkusen_10000.csv", index=False)
    # Reconstrucción cronológica de goles de los 34 partidos, incluidos autogoles.
    matches = json.loads((RAW / "leverkusen_matches_statsbomb.json").read_text())
    goals = []
    audit = []
    rescues = []
    for m in sorted(matches, key=lambda z: z["match_date"]):
        hn = m["home_team"]["home_team_name"]
        an = m["away_team"]["away_team_name"]
        levhome = hn == "Bayer Leverkusen"
        ours = 0
        theirs = 0
        at85 = None
        late = []
        state_start = 85.0
        qstate = None
        events = json.loads((RAW / f"events/{m['match_id']}.json").read_text())
        for e in events:
            typ = e["type"]["name"]
            goal = e.get("shot", {}).get("outcome", {}).get("name") == "Goal"
            if not goal and typ != "Own Goal Against":
                continue
            islev = e["team"]["name"] == "Bayer Leverkusen"
            islev = (not islev) if typ == "Own Goal Against" else islev
            minute = e["minute"] + e["second"] / 60
            # El agregado de minutos de StatsBomb reinicia segunda parte en 45.
            if e["period"] == 2 and minute >= 85 and at85 is None:
                at85 = (ours, theirs)
            before = (ours, theirs)
            if e["period"] == 2 and minute >= 85 and qstate is None:
                if ours < theirs:
                    qstate = (ours, theirs)
                elif not islev and theirs + 1 > ours:
                    qstate = (ours, theirs + 1)
                    state_start = minute
            if islev:
                ours += 1
            else:
                theirs += 1
            goals.append(
                {
                    "match_id": m["match_id"],
                    "date": m["match_date"],
                    "opponent": an if levhome else hn,
                    "period": e["period"],
                    "minute": e["minute"],
                    "second": e["second"],
                    "leverkusen_goal": islev,
                    "player": e.get("player", {}).get("name", "Autogol"),
                    "score_lev": ours,
                    "score_opp": theirs,
                }
            )
            if (
                e["period"] == 2
                and minute >= 85
                and islev
                and before[0] < before[1]
                and ours >= theirs
            ):
                late.append(goals[-1])
        if at85 is None:
            at85 = (ours, theirs)
        expected = (
            (m["home_score"], m["away_score"])
            if levhome
            else (m["away_score"], m["home_score"])
        )
        assert (ours, theirs) == expected, (m["match_id"], ours, theirs, expected)
        audit.append(
            {
                "date": m["match_date"],
                "opponent": an if levhome else hn,
                "score85_lev": at85[0],
                "score85_opp": at85[1],
                "final_lev": ours,
                "final_opp": theirs,
                "rescued": bool(late),
            }
        )
        if late:
            l = late[0]
            rate_ours = float(train.hgoal.mean() if levhome else train.vgoal.mean())
            rate_opp = float(train.vgoal.mean() if levhome else train.hgoal.mean())
            # Tasas históricas liga antes de 2023/24, estado al 85 y 5 min de añadido supuestos.
            end_second = max(
                e["minute"] + e["second"] / 60 for e in events if e["period"] == 2
            )
            deficit = qstate[1] - qstate[0]
            remaining = end_second - state_start
            q = float(
                skellam.sf(
                    deficit - 1, rate_ours * remaining / 90, rate_opp * remaining / 90
                )
            )
            rescues.append(
                {
                    "date": m["match_date"],
                    "opponent": an if levhome else hn,
                    "at85": f"{at85[0]}-{at85[1]}",
                    "minute": f"{l['minute']}:{l['second']:02d}",
                    "player": l["player"],
                    "final": f"{ours}-{theirs}",
                    "q": q,
                    "home": levhome,
                    "deficit": deficit,
                    "state_minute": state_start,
                    "state_score": f"{qstate[0]}-{qstate[1]}",
                    "remaining": remaining,
                    "final_whistle": end_second,
                }
            )
    pd.DataFrame(goals).to_csv(PROC / "leverkusen_goals.csv", index=False)
    pd.DataFrame(audit).to_csv(PROC / "leverkusen_85min_audit.csv", index=False)
    pd.DataFrame(rescues).to_csv(PROC / "rescues.csv", index=False)
    Q = float(np.prod([r["q"] for r in rescues]))
    sensitivity = []
    for extra in [0, 3, 5, 8]:
        qs = []
        for r in rescues:
            a = train.hgoal.mean() if r["home"] else train.vgoal.mean()
            b = train.vgoal.mean() if r["home"] else train.hgoal.mean()
            qs.append(
                skellam.sf(
                    r["deficit"] - 1,
                    a * max(0.1, 90 + extra - r["state_minute"]) / 90,
                    b * max(0.1, 90 + extra - r["state_minute"]) / 90,
                )
            )
        sensitivity.append(
            {
                "added_minutes": extra,
                "Q": float(np.prod(qs)),
                "adjusted": p * float(np.prod(qs)),
            }
        )
    elo_sens = []
    for h in [0, 60, 100]:
        for boost in [0, 100, 200]:
            vals = [
                probabilities(
                    ratings["Leverkusen"]
                    + boost
                    - ratings[r.opponent]
                    + (h if r.home else -h),
                    total,
                )[:2].sum()
                for r in f.itertuples()
            ]
            elo_sens.append(
                {"hfa": h, "leverkusen_elo_boost": boost, "p": float(np.prod(vals))}
            )
    return {
        "elo_date": cut,
        "total_goals": total,
        "hfa": hfa,
        "p_bayern2": pb,
        "p_other32": po,
        "p_unbeaten": p,
        "simulation": summarize(loss == 0),
        "expected_unbeaten_10000": N * p,
        "mean_losses": float(loss.mean()),
        "rescues": rescues,
        "Q": Q,
        "inverse_Q": 1 / Q,
        "adjusted": p * Q,
        "late_sensitivity": sensitivity,
        "elo_sensitivity": elo_sens,
    }


def national_ratings(codes, cut):
    rows = []
    for code in codes:
        path = RAW / f"national/{code}.tsv"
        valid = []
        for line in path.read_text().splitlines():
            f = line.split("\t")
            if len(f) < 13:
                continue
            date = "-".join(f[:3])
            if date < cut and f[0].isdigit() and code in f[3:5]:
                idx = 10 if f[3] == code else 11
                try:
                    valid.append((date, int(f[idx])))
                except ValueError:
                    pass
        assert valid, code
        date, elo = valid[-1]
        rows.append({"code": code, "elo": elo, "last_match": date, "cutoff": cut})
    frame = pd.DataFrame(rows)
    frame.to_csv(PROC / f"national_elo_{cut}.csv", index=False)
    return frame.set_index("code").elo.to_dict()


def qualify_world(groups, ratings, n, rng, forced=False, total=2.7):
    # Mantiene solo los terceros y el grupo H, sin acumular doce torneos completos.
    keys = list(groups)
    third_rows = []
    h = None
    for key, teams in groups.items():
        sim = group_sim(teams, ratings, n, rng, forced_cv=forced and key == "H", total=total)
        third_rows.append(sim["stats"][np.arange(n), sim["order"][:, 2]].copy())
        if key == "H":
            h = sim
        del sim
    ci = h["teams"].index("CV")
    pos = np.argmax(h["order"] == ci, axis=1) + 1
    thirds = np.stack(third_rows, axis=1)
    del third_rows
    hi = keys.index("H")
    tie = rng.random((n, 12))
    accepted = np.zeros(n, dtype=bool)
    for j in range(n):
        rank = sorted(range(12), key=lambda k: (*thirds[j, k], tie[j, k]), reverse=True)
        accepted[j] = hi in rank[:8]
    qualified = (pos <= 2) | ((pos == 3) & accepted)
    uruguay = None
    for a, b, x, y in h["fixtures"]:
        if {a, b} == {"UY", "ES"}:
            uruguay = x >= y if a == "UY" else y >= x
    return {
        "position": pos,
        "qualified": qualified,
        "third_ok": accepted,
        "uruguay_not_lose": uruguay,
        "p_three_draws": h["p_three_draws"],
    }


def cape_verde():
    groups = json.loads((ROOT / "data/groups_2026.json").read_text())
    codes = sorted(set(sum(groups.values(), [])))
    qual = ["CV", "CM", "AO", "LY", "SZ", "MU"]
    r0 = national_ratings(qual, "2023-11-15")
    r1 = national_ratings(codes, "2026-06-11")
    rng = np.random.default_rng(SEED + 1)
    q = group_sim(qual, r0, N, rng, double=True, home_adv=100)
    direct = q["order"][:, 0] == 0
    a = qualify_world(groups, r1, N, rng)
    b = qualify_world(groups, r1, N, rng, forced=True)
    rows = []
    for code in ["AR", "EG", "CH", "EN", "ES"]:
        pw, pd_, pl = probabilities(r1["CV"] - r1[code])
        rows.append(
            {
                "opponent": code,
                "elo": r1[code],
                "p_win": float(pw),
                "p_draw": float(pd_),
                "p_advance": float(pw + pd_),
            }
        )
    route = float(np.prod([x["p_advance"] for x in rows[1:]]))
    full = route * rows[0]["p_advance"]
    pd.DataFrame(rows).to_csv(PROC / "cape_verde_knockouts.csv", index=False)
    pd.DataFrame(
        {
            "trial": np.arange(1, N + 1),
            "direct_qualification": direct,
            "group_position": a["position"],
            "advance": a["qualified"],
            "three_draws_position": b["position"],
            "three_draws_advance": b["qualified"],
        }
    ).to_csv(OUT / "cape_verde_10000.csv", index=False)
    scenarios = {
        "grupo_sin_condicionar": summarize(a["qualified"]),
        "tres_empates": summarize(b["qualified"]),
        "uruguay_no_pierde_sin_condicionar_empates": summarize(
            a["qualified"][a["uruguay_not_lose"]]
        ),
        "tres_empates_y_uruguay_no_pierde": summarize(
            b["qualified"][b["uruguay_not_lose"]]
        ),
        "tres_empates_y_tercero": summarize(b["qualified"][b["position"] == 3]),
    }
    pthird = [float(np.mean(b["position"] == i)) for i in range(1, 5)]
    # Réplica independiente del recorrido eliminatorio para comparar con el producto.
    ko = (rng.random((N, 4)) < np.array([x["p_advance"] for x in rows[1:]])).all(axis=1)
    return {
        "qualifying": summarize(direct),
        "qualifying_elo": r0,
        "world_elo": r1,
        "scenarios": scenarios,
        "p_three_draws": b["p_three_draws"],
        "positions_three_draws": pthird,
        "knockouts": rows,
        "title_given_pass_argentina": route,
        "title_from_argentina": full,
        "title_from_group_fixed_route": a["qualified"].mean() * full,
        "title_from_qualifiers_fixed_route": direct.mean()
        * a["qualified"].mean()
        * full,
        "knockout_mc": summarize(ko),
        "total_goals_assumption": 2.7,
        "n": N,
    }


def charts(df, ch, r):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 150,
            "savefig.bbox": "tight",
        }
    )
    red = "#B62835"
    blue = "#176B9A"
    gray = "#7B858D"

    def save(name):
        plt.tight_layout()
        plt.savefig(OUT / f"figures/{name}.png", dpi=200)
        plt.savefig(OUT / f"figures/{name}.svg")
        plt.close()

    h = ch[ch.end_year <= 2023]
    counts = h.team.value_counts()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(
        counts.index[::-1],
        counts.values[::-1],
        color=[red if x == "Bayern Munich" else gray for x in counts.index[::-1]],
    )
    ax.set_xlabel("Títulos entre 1964 y 2023")
    save("champions")
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.scatter(
        h.end_year,
        np.zeros(len(h)),
        c=[red if x == "Bayern Munich" else blue for x in h.team],
        s=80,
    )
    ax.set_yticks([])
    ax.set_xlabel("Año de finalización de temporada")
    ax.set_title("Rojo: Bayern Múnich    Azul: otros campeones")
    save("timeline")
    f = pd.read_csv(PROC / "bundesliga_elo_2023_08_15.csv")
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(
        f.club[::-1],
        f.elo[::-1],
        color=[red if x == "Leverkusen" else gray for x in f.club[::-1]],
    )
    ax.set_xlim(1400, 2000)
    ax.set_xlabel("Elo al 15 de agosto de 2023")
    save("elo")
    sim = pd.read_csv(OUT / "leverkusen_10000.csv")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.hist(
        sim.losses,
        bins=np.arange(-0.5, sim.losses.max() + 1.5),
        color=red,
        edgecolor="white",
    )
    ax.set_xlabel("Derrotas en 34 partidos")
    ax.set_ylabel("Temporadas simuladas")
    ax.set_title(f"10 000 temporadas · {int((sim.losses == 0).sum())} invictas")
    save("montecarlo")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(14)
    for fit, c in zip(r["history"]["fits"], [gray, red, blue]):
        ax.plot(x, poisson.pmf(x, fit["mean"]), marker="o", label=fit["group"], color=c)
    ax.set_xlabel("Derrotas del campeón")
    ax.set_ylabel("Probabilidad Poisson")
    ax.legend()
    save("poisson")
    fig, ax = plt.subplots(figsize=(9, 4))
    rr = r["leverkusen"]["rescues"]
    ax.barh([x["opponent"] for x in rr], [100 * x["q"] for x in rr], color=red)
    ax.set_xlabel("Probabilidad de rescate desde el minuto 85 (%)")
    save("rescues")
    cv = r["cape_verde"]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    labels = [
        "Clasificación\ndirecta",
        "Avanzar\ndel grupo",
        "Avanzar con\ntres empates",
        "Avanzar siendo\ntercero y 3 empates",
    ]
    vals = [
        cv["qualifying"]["p"],
        cv["scenarios"]["grupo_sin_condicionar"]["p"],
        cv["scenarios"]["tres_empates"]["p"],
        cv["scenarios"]["tres_empates_y_tercero"]["p"],
    ]
    ax.bar(labels, np.array(vals) * 100, color=blue)
    ax.set_ylabel("Probabilidad (%)")
    ax.set_ylim(0, 100)
    save("cape_scenarios")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ko = cv["knockouts"]
    ax.bar([x["opponent"] for x in ko], [100 * x["p_advance"] for x in ko], color=blue)
    ax.set_ylabel("Victoria o empate en 90 minutos (%)")
    ax.set_ylim(0, 100)
    save("knockouts")
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(
        ["Egipto", "Suiza", "Inglaterra", "España"],
        100 * np.cumprod([x["p_advance"] for x in ko[1:]]),
        marker="o",
        color=blue,
    )
    ax.set_yscale("log")
    ax.set_ylabel("Probabilidad acumulada (%) · escala log")
    save("route")


def main():
    df, ch, h = historical()
    r = {
        "seed": SEED,
        "n": N,
        "history": h,
        "leverkusen": leverkusen(df, ch),
        "cape_verde": cape_verde(),
    }
    (OUT / "results.json").write_text(json.dumps(r, indent=2, ensure_ascii=False))
    charts(df, ch, r)
    print(json.dumps(r, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
