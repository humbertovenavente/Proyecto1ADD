"""Modelos de marcadores y clasificación usados en ambos estudios."""

from functools import lru_cache
import numpy as np
from scipy.optimize import brentq
from scipy.stats import skellam, beta


@lru_cache(maxsize=4096)
def goal_rates(delta: float, total: float = 2.7):
    """Invierte el Elo esperado E=P(G)+P(E)/2 para dos Poisson independientes."""
    expected = 1 / (1 + 10 ** (-delta / 400))

    def residual(t):
        a = (total / 2) * np.exp(t)
        b = (total / 2) * np.exp(-t)
        return skellam.sf(0, a, b) + 0.5 * skellam.pmf(0, a, b) - expected

    t = brentq(residual, -8, 8)
    return (total / 2) * np.exp(t), (total / 2) * np.exp(-t)


def probabilities(delta, total=2.7):
    a, b = goal_rates(float(delta), float(total))
    return np.array([skellam.sf(0, a, b), skellam.pmf(0, a, b), skellam.cdf(-1, a, b)])


def interval(k, n, alpha=0.05):
    if not n:
        return [None, None]
    return [
        0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1)),
        1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k)),
    ]


def summarize(mask):
    k = int(np.sum(mask))
    n = len(mask)
    return {"successes": k, "n": n, "p": k / n if n else None, "ci95": interval(k, n)}


def rank_table(scores, head_to_head=True, rng=None):
    """Puntos; minitabla H2H (Mundial); DG; GF; sorteo residual explícito.

    scores[i,j] son los goles de i contra j, sumados en ida y vuelta.
    match_points se entrega aparte para no confundir agregado con resultados.
    """
    goals, points = scores
    n = len(goals)
    gf = goals.sum(axis=1)
    gd = gf - goals.sum(axis=0)
    pts = points.sum(axis=1)
    tie = np.zeros(n) if rng is None else rng.random(n)
    keys = []
    for i in range(n):
        tied = np.flatnonzero(pts == pts[i])
        hpts = points[i, tied].sum()
        hgd = goals[i, tied].sum() - goals[tied, i].sum()
        hgf = goals[i, tied].sum()
        key = (
            (pts[i], hpts, hgd, hgf, gd[i], gf[i], tie[i])
            if head_to_head
            else (pts[i], gd[i], gf[i], hpts, hgd, hgf, tie[i])
        )
        keys.append(key)
    return sorted(range(n), key=lambda i: keys[i], reverse=True), pts, gd, gf


def group_sim(
    teams, ratings, n, rng, double=False, forced_cv=False, total=2.7, home_adv=0
):
    """Simula marcadores y devuelve clasificación y resultados sin usar datos futuros."""
    m = len(teams)
    g = np.zeros((n, m, m), dtype=np.int16)
    pt = np.zeros_like(g)
    fixtures = []
    draw_prob = 1.0
    for i in range(m):
        for j in range(i + 1, m):
            for home, away in [(i, j), (j, i)] if double else [(i, j)]:
                delta = ratings[teams[home]] - ratings[teams[away]] + home_adv
                a, b = goal_rates(float(delta), float(total))
                x = rng.poisson(a, n)
                y = rng.poisson(b, n)
                if forced_cv and "CV" in [teams[home], teams[away]]:
                    # Marcador condicionado a empate: P(k,k) proporcional a Poisson(a,k)Poisson(b,k).
                    from scipy.stats import poisson

                    ks = np.arange(25)
                    w = poisson.pmf(ks, a) * poisson.pmf(ks, b)
                    draw_prob *= w.sum()
                    w /= w.sum()
                    x = rng.choice(ks, size=n, p=w)
                    y = x.copy()
                g[:, home, away] += x
                g[:, away, home] += y
                pt[:, home, away] += 3 * (x > y) + (x == y)
                pt[:, away, home] += 3 * (y > x) + (x == y)
                fixtures.append((teams[home], teams[away], x, y))
    order = np.zeros((n, m), dtype=int)
    stats = np.zeros((n, m, 3), dtype=int)
    for k in range(n):
        o, p, d, f = rank_table((g[k], pt[k]), head_to_head=not double, rng=rng)
        order[k] = o
        stats[k] = np.stack([p, d, f], axis=1)
    return {
        "teams": teams,
        "order": order,
        "stats": stats,
        "fixtures": fixtures,
        "p_three_draws": draw_prob,
    }
