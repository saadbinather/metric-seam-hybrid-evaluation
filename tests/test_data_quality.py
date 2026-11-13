import json
from pathlib import Path


DATA = Path(__file__).parents[1] / "data/peerread_iclr2017_v6"


def rows():
    return {r["paper_id"]: r for r in (json.loads(x) for x in (DATA / "development_pairs.jsonl").read_text().splitlines())}


def test_all_eight_source_backed_pairs_are_complete_and_independent():
    expected = {
        "312": ("3.65", "3.46%"), "709": ("1.3 BLEU", "1.3"),
        "617": ("1.7x", "1.7x"), "309": ("880%", "54%"),
        "785": ("1/25", "1/25"), "596": ("5.7%", "5.7%"),
        "388": ("71.0%", "75.9%"), "552": ("5,000", "5,000"),
    }
    got = rows()
    assert set(got) == set(expected)
    for paper_id, (claim_marker, focal) in expected.items():
        pair = got[paper_id]["pair"]
        assert claim_marker in pair["claim_text"]
        assert pair["evidence_independent"] is True
        assert focal in pair["claim_text"] or focal in pair["evidence_text"]
        assert pair["claim_start"] < pair["claim_end"]
        assert pair["evidence_start"] < pair["evidence_end"]
        assert pair["claim_text"] != pair["evidence_text"] or paper_id == "785"


def test_decimal_ratio_and_duplicate_repairs():
    got = rows()
    assert "3.65" in got["312"]["pair"]["claim_text"]
    assert got["785"]["pair"]["claim_text"].count("1/25") == 1
    assert got["785"]["pair"]["claim_text"] != got["785"]["pair"]["evidence_text"]
    raw785 = json.loads((Path(__file__).parents[1] / "data/peerread_iclr2017_v5/raw/785.pdf.json").read_text())
    assert got["785"]["pair"]["evidence_text"] not in raw785["metadata"]["abstractText"]
    assert got["709"]["pair"]["evidence_start"] > len(json.loads((Path(__file__).parents[1] / "data/peerread_iclr2017_v5/raw/709.pdf.json").read_text())["metadata"]["abstractText"])


def test_relevance_repairs_for_unrelated_cases():
    got = rows()
    assert "asynchronous" in got["617"]["pair"]["evidence_text"]
    assert "FB15k" in got["596"]["pair"]["evidence_text"]
    assert "SQuAD" in got["388"]["pair"]["evidence_text"]
    assert "memory" in got["552"]["pair"]["evidence_text"].lower()

