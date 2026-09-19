import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
from models import probabilities, goal_rates, group_sim, rank_table, interval


def test_elo_expected_score_and_symmetry():
    for delta in [-800, -200, 0, 200, 800]:
        w, d, l = probabilities(delta)
        assert np.isclose(w + d + l, 1)
        assert np.isclose(w + 0.5 * d, 1 / (1 + 10 ** (-delta / 400)))
        assert np.allclose([w, d, l], probabilities(-delta)[::-1])


def test_fixture_counts_and_points():
    r = group_sim(
        ["CV", "CM", "AO", "LY", "SZ", "MU"],
        dict.fromkeys(["CV", "CM", "AO", "LY", "SZ", "MU"], 1500),
        8,
        np.random.default_rng(1),
        double=True,
    )
    assert len(r["fixtures"]) == 30
    assert all(len(set(row)) == 6 for row in r["order"])
    for t in r["teams"]:
        assert sum(t in f[:2] for f in r["fixtures"]) == 10


def test_conditioned_draws():
    r = group_sim(
        ["ES", "CV", "SA", "UY"],
        dict.fromkeys(["ES", "CV", "SA", "UY"], 1600),
        20,
        np.random.default_rng(1),
        forced_cv=True,
    )
    assert (r["stats"][:, 1, 0] == 3).all()
    assert (r["stats"][:, 1, 1] == 0).all()
    for a, b, x, y in r["fixtures"]:
        if "CV" in [a, b]:
            assert (x == y).all()


def test_head_to_head_priority():
    # Los dos equipos empatados a puntos se ordenan por su duelo directo.
    g = np.array([[0, 1, 0], [0, 0, 4], [1, 0, 0]])
    p = np.array([[0, 3, 0], [0, 0, 3], [3, 0, 0]])
    order, _, _, _ = rank_table((g, p), True, np.random.default_rng(1))
    assert order == [1, 0, 2]  # empate triple: diferencia de goles en minitabla


def test_zero_success_interval_not_zero():
    assert interval(0, 10000)[1] > 0


def test_historical_correction_and_country_codes():
    from analyze import historical, ROOT
    import json

    _, c, _ = historical()
    s = c[c.end_year == 1992].iloc[0]
    assert s.team == "Stuttgart" and s.played == 38 and s.losses == 7
    groups = json.loads((ROOT / "data/groups_2026.json").read_text())
    assert groups["C"] == ["BR", "MA", "HT", "SQ"]
    assert len(set(sum(groups.values(), []))) == 48


def test_saved_event_audit():
    import pandas as pd

    root = Path(__file__).resolve().parents[1]
    a = pd.read_csv(root / "data/processed/leverkusen_85min_audit.csv")
    assert len(a) == 34 and a.rescued.sum() == 4
    assert (a.final_lev >= a.final_opp).all()
    r = pd.read_csv(root / "data/processed/rescues.csv")
    assert (r.deficit == 1).all() and ((r.q > 0) & (r.q < 1)).all()
    assert (r.final_whistle > r.state_minute).all()


def test_team_names_join_across_outputs():
    # Las salidas de eventos y las de Elo comparten los nombres de ClubElo.
    import pandas as pd

    proc = Path(__file__).resolve().parents[1] / "data/processed"
    p = pd.read_csv(proc / "leverkusen_probabilities.csv")
    for name in ["rescues.csv", "leverkusen_85min_audit.csv", "leverkusen_goals.csv"]:
        t = pd.read_csv(proc / name)
        assert set(t.opponent) <= set(p.opponent), (name, set(t.opponent) - set(p.opponent))
    r = pd.read_csv(proc / "rescues.csv")
    assert len(r.merge(p, on=["date", "opponent"])) == len(r) == 4
