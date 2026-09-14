"""Descarga datos públicos y conserva su procedencia. No necesita credenciales."""

from pathlib import Path
import json, hashlib, requests, concurrent.futures

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
RAW.mkdir(parents=True, exist_ok=True)
manifest = {}


def fetch(name, url, headers=None):
    p = RAW / name
    if not p.exists():
        r = requests.get(url, headers=headers, timeout=45)
        r.raise_for_status()
        p.write_bytes(r.content)
    manifest[name] = {"url": url, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    return p


def main():
    fetch("dsfs_bundesliga_history.pdf", "https://www.dsfs.de/wp-content/uploads/2024/01/Bundesliga_Geschichte_Tabellen.pdf")
    fetch(
        "germany.csv",
        "https://raw.githubusercontent.com/jalapic/engsoccerdata/master/data-raw/germany.csv",
    )
    fetch(
        "clubelo_archive.csv",
        "https://raw.githubusercontent.com/xgabora/Club-Football-Match-Data/main/data/EloRatings.csv",
    )
    matches = json.loads(
        fetch(
            "leverkusen_matches_statsbomb.json",
            "https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/9/281.json",
        ).read_text()
    )

    def events(m):
        mid = m["match_id"]
        p = fetch(
            f"events/{mid}.json",
            f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{mid}.json",
        )
        return p

    (RAW / "events").mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:
        list(e.map(events, matches))
    # Códigos del proveedor World Football Elo Ratings.
    groups = {
        "A": ["MX", "ZA", "KR", "CZ"],
        "B": ["CA", "CH", "QA", "BA"],
        "C": ["BR", "MA", "HT", "SQ"],
        "D": ["US", "PY", "AU", "TR"],
        "E": ["DE", "CW", "CI", "EC"],
        "F": ["NL", "JP", "SE", "TN"],
        "G": ["BE", "EG", "IR", "NZ"],
        "H": ["ES", "CV", "SA", "UY"],
        "I": ["FR", "SN", "IQ", "NO"],
        "J": ["AR", "DZ", "AT", "JO"],
        "K": ["PT", "CD", "UZ", "CO"],
        "L": ["EN", "HR", "GH", "PA"],
    }
    (ROOT / "data/groups_2026.json").write_text(json.dumps(groups, indent=2))
    names = {
        s.split("\t")[0]: s.split("\t")[1]
        for s in fetch("elo_teams.tsv", "https://www.eloratings.net/en.teams.tsv")
        .read_text()
        .splitlines()
    }
    codes = set(sum(groups.values(), [])) | {"CM", "AO", "LY", "SZ", "MU"}

    def country(code):
        name = {
            "CW": "Curacao",
            "CI": "Ivory_Coast",
            "CD": "DR_Congo",
            "SZ": "Eswatini",
            "TR": "Turkey",
        }.get(code, names[code].replace(" ", "_"))
        fetch(f"national/{code}.tsv", f"https://www.eloratings.net/{name}.tsv")

    (RAW / "national").mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:
        list(e.map(country, sorted(codes)))
    (ROOT / "data/sources.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False)
    )
    print(f"{len(manifest)} archivos registrados")


if __name__ == "__main__":
    main()
