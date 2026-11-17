#!/usr/bin/env python3
"""Single source of truth for Python<->Lean differential test vectors.

Running this file writes vectors.json (consumed by differential.py) and
GeneratedVectors.lean (imported by ModelEval.lean), so both sides use the
SAME vectors. These vectors are abstract test data, not production evidence.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A = "a" * 64
B = "b" * 64

# Asset name order: citation, notes, bibtex, paper, metadata, manifest, sums,
# researchJson, researchTar, tsq, tsr
ASSET_ORDER = [
    "citation", "notes", "bibtex", "paper", "metadata", "manifest", "sums",
    "researchJson", "researchTar", "tsq", "tsr",
]
PAYLOAD = ["citation", "notes", "bibtex", "paper", "metadata"]
EXPECTED = PAYLOAD + ["manifest", "sums"]
EVIDENCE = ["tsq", "tsr"]
RESEARCH = ["researchJson", "researchTar"]


def aset(names):
    return {n: n in names for n in ASSET_ORDER}


def rel(assets, manifest, paper=A, pinned=A, owner="Unjuno", name="paper", version=(1,)):
    return {
        "repo": {"owner": owner, "name": name},
        "version": list(version),
        "assets": aset(assets),
        "manifestFiles": aset(manifest),
        "paperDigest": paper,
        "pinnedPaperDigest": pinned,
    }


GOOD_REPO = {"owner": "Unjuno", "name": "paper"}
GOOD_VER = [1]

release_cases = [
    # id, release, trusted repo, trusted version, expected accept
    ["RA-01", rel(EXPECTED, PAYLOAD), GOOD_REPO, GOOD_VER, True],
    ["RA-02", rel(EXPECTED + EVIDENCE, PAYLOAD), GOOD_REPO, GOOD_VER, True],
    ["RA-03", rel(EXPECTED + RESEARCH, PAYLOAD + RESEARCH), GOOD_REPO, GOOD_VER, True],
    ["RA-04", rel(EXPECTED + RESEARCH + EVIDENCE, PAYLOAD + RESEARCH), GOOD_REPO, GOOD_VER, True],
    ["RA-05", rel(EXPECTED, PAYLOAD + ["manifest"]), GOOD_REPO, GOOD_VER, False],  # manifest overdeclared
    ["RA-06", rel([x for x in EXPECTED if x != "paper"], PAYLOAD), GOOD_REPO, GOOD_VER, False],  # missing paper
    ["RA-07", rel(EXPECTED + ["extra"], PAYLOAD), GOOD_REPO, GOOD_VER, False],  # unknown asset modeled via sums? see note
    ["RA-08", rel(EXPECTED, PAYLOAD, paper=B), GOOD_REPO, GOOD_VER, False],  # digest mismatch
    ["RA-09", rel(EXPECTED, PAYLOAD), {"owner": "Other", "name": "paper"}, GOOD_VER, False],  # repo mismatch
    ["RA-10", rel(EXPECTED, PAYLOAD), GOOD_REPO, [0], False],  # version mismatch / zero
    ["RA-11", rel(EXPECTED, PAYLOAD, pinned=None), GOOD_REPO, GOOD_VER, True],  # no pin -> allowed
]

# RA-07 cannot be expressed with the fixed 11-field AssetSet (no "extra" field).
# Model it as a research flag mismatch instead: research file present in assets
# but not in manifest => manifestMatches false.
release_cases[6] = ["RA-07", rel(EXPECTED + RESEARCH, PAYLOAD), GOOD_REPO, GOOD_VER, False]


def view(isPublic=True, immutable=True, head="0" * 40, tag=False, ref=False):
    return {
        "isPublic": isPublic, "immutableEnabled": immutable, "headSha": head,
        "releaseTagExists": tag, "tagRefExists": ref,
    }


COMMIT = "0" * 40
state_cases = [
    # id, context, view, expected phase
    # id, context, view, start phase, checked context, expected phase
    ["ST-01", {"repository": "Unjuno/paper", "version": "v1", "commit": COMMIT}, view(), "draft", "none", "verified"],
    ["ST-02", {"repository": "Unjuno/paper", "version": "v1", "commit": COMMIT}, view(isPublic=False), "draft", "none", "draft"],
    ["ST-03", {"repository": "Unjuno/paper", "version": "v1", "commit": COMMIT}, view(immutable=False), "draft", "none", "draft"],
    ["ST-04", {"repository": "Unjuno/paper", "version": "v1", "commit": COMMIT}, view(head="1" * 40), "draft", "none", "draft"],
    ["ST-05", {"repository": "Unjuno/paper", "version": "v1", "commit": COMMIT}, view(tag=True), "draft", "none", "draft"],
    ["ST-06", {"repository": "Unjuno/paper", "version": "v1", "commit": COMMIT}, view(ref=True), "draft", "none", "draft"],
    ["ST-07", {"repository": "Unjuno/paper", "version": "v0", "commit": COMMIT}, view(), "draft", "none", "draft"],
    ["ST-08", {"repository": "Unjuno/paper", "version": "v2", "commit": "z" * 40}, view(), "draft", "none", "draft"],
    # verified -> published / terminal / forced-update coverage (was missing)
    ["ST-09", {"repository": "Unjuno/paper", "version": "v1", "commit": COMMIT}, view(), "verified", "self", "published"],
    ["ST-10", {"repository": "Unjuno/paper", "version": "v1", "commit": COMMIT}, view(head="1" * 40), "verified", "self", "verified"],
    ["ST-11", {"repository": "Unjuno/paper", "version": "v1", "commit": COMMIT}, view(), "published", "self", "published"],
    ["ST-12", {"repository": "Unjuno/paper", "version": "v1", "commit": COMMIT}, view(), "verified", "other", "verified"],
    ["ST-13", {"repository": "Unjuno/paper", "version": "v1", "commit": COMMIT}, view(), "verified", "none", "verified"],
]

evidence_cases = [
    # id, data1, sig1, data2, sig2, expected digests equal
    ["EB-01", "statement", "sig", "statement", "sig", True],
    ["EB-02", "statement", "sig", "statement", "OTHER", False],
    ["EB-03", "statement", "sig", "ALTERED", "sig", False],
    ["EB-04", "a" * 100, "sig", "a" * 100, "sig", True],
    ["EB-05", "a", "b", "b", "a", False],
    ["EB-06", "\u2603", "s", "\u2603", "s", True],
]

claim_cases = [
    # id, raw claims, expected parse accepted
    ["CL-01", {"publicAvailability": "WITNESS_ASSERTS_ANONYMOUS_RETRIEVAL",
               "firstPublication": "NOT_PROVEN", "authorship": "NOT_PROVEN",
               "witnessClock": "SELF_REPORTED_NOT_A_TRUSTED_TIMESTAMP",
               "anonymousHttps": True, "timestampVerified": True}, True],
    ["CL-02", {"publicAvailability": "WITNESS_ASSERTS_ANONYMOUS_RETRIEVAL",
               "firstPublication": "FIRST_PUBLICATION_PROVEN", "authorship": "NOT_PROVEN",
               "witnessClock": "SELF_REPORTED_NOT_A_TRUSTED_TIMESTAMP",
               "anonymousHttps": True, "timestampVerified": True}, False],
    ["CL-03", {"publicAvailability": "WITNESS_ASSERTS_ANONYMOUS_RETRIEVAL",
               "firstPublication": "NOT_PROVEN", "authorship": "NOT_PROVEN",
               "witnessClock": "SELF_REPORTED_NOT_A_TRUSTED_TIMESTAMP",
               "anonymousHttps": True, "timestampVerified": False}, False],
]

VECTORS = {
    "release_assets": release_cases,
    "state_transition": state_cases,
    "evidence_binding": evidence_cases,
    "claims": claim_cases,
}


def lean_str(s):
    return json.dumps(s, ensure_ascii=False)


def lean_bool(b):
    return "true" if b else "false"


def lean_aset(d):
    return "{" + ", ".join(f"{k} := {lean_bool(d[k])}" for k in ASSET_ORDER) + "}"


def lean_repo(r):
    return f'{{ owner := {lean_str(r["owner"])}, name := {lean_str(r["name"])} }}'


def lean_ver(v):
    return "{" + "parts := [" + ", ".join(str(x) for x in v) + "] }"


def lean_opt(p):
    return "none" if p is None else f"some {lean_str(p)}"


def lean_char_list(s):
    # Represent as a Lean String.toList expression using escaped string.
    return f'({lean_str(s)}).toList'


def generate():
    (HERE / "vectors.json").write_text(
        json.dumps(VECTORS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "/- AUTO-GENERATED by vectors.py from vectors.json. Do not edit by hand. -/",
        "import OpenPreprintFormal.ReleaseAssets",
        "import OpenPreprintFormal.StateTransition",
        "import OpenPreprintFormal.EvidenceBinding",
        "namespace OpenPreprintFormal.GeneratedVectors",
        "",
    ]
    lines.append("open ReleaseAssets StateTransition EvidenceBinding")
    lines.append("")
    lines.append("def releaseCases : List (String × Release × RepoId × Version × Bool) := [")
    for cid, r, repo, ver, exp in release_cases:
        release = (
            f'{{ repo := {lean_repo(r["repo"])}, version := {lean_ver(r["version"])}, '
            f'assets := {lean_aset(r["assets"])}, manifestFiles := {lean_aset(r["manifestFiles"])}, '
            f'paperDigest := {lean_str(r["paperDigest"])}, pinnedPaperDigest := {lean_opt(r["pinnedPaperDigest"])} }}'
        )
        lines.append(f'  ({lean_str(cid)}, {release}, {lean_repo(repo)}, {lean_ver(ver)}, {lean_bool(exp)}),')
    lines.append("]")
    lines.append("")

    lines.append("def stateCases : List (String × PubState × PublishContext × RepoView × Phase) := [")
    for cid, ctx, v, start, checked, exp in state_cases:
        c = (f'{{ repository := {lean_str(ctx["repository"])}, version := {lean_str(ctx["version"])}, '
             f'commit := {lean_str(ctx["commit"])} }}')
        rv = (f'{{ isPublic := {lean_bool(v["isPublic"])}, immutableEnabled := {lean_bool(v["immutableEnabled"])}, '
              f'headSha := {lean_str(v["headSha"])}, releaseTagExists := {lean_bool(v["releaseTagExists"])}, '
              f'tagRefExists := {lean_bool(v["tagRefExists"])} }}')
        if checked == "self":
            ck = f"some {c}"
        elif checked == "other":
            other = (f'{{ repository := {lean_str(ctx["repository"])}, version := "v9", '
                     f'commit := {lean_str(ctx["commit"])} }}')
            ck = f"some {other}"
        else:
            ck = "none"
        st = f'{{ phase := Phase.{start}, checked := {ck} }}'
        lines.append(f'  ({lean_str(cid)}, {st}, {c}, {rv}, Phase.{exp}),')
    lines.append("]")
    lines.append("")

    lines.append("def evidenceCases : List (String × List Char × List Char × List Char × List Char × Bool) := [")
    for cid, d1, s1, d2, s2, exp in evidence_cases:
        lines.append(f'  ({lean_str(cid)}, {lean_char_list(d1)}, {lean_char_list(s1)}, '
                     f'{lean_char_list(d2)}, {lean_char_list(s2)}, {lean_bool(exp)}),')
    lines.append("]")
    lines.append("")

    lines.append("def claimCases : List (String × RawClaims × Bool) := [")
    for cid, rc, exp in claim_cases:
        r = (f'{{ publicAvailability := {lean_str(rc["publicAvailability"])}, '
             f'firstPublication := {lean_str(rc["firstPublication"])}, '
             f'authorship := {lean_str(rc["authorship"])}, '
             f'witnessClock := {lean_str(rc["witnessClock"])}, '
             f'anonymousHttps := {lean_bool(rc["anonymousHttps"])}, '
             f'timestampVerified := {lean_bool(rc["timestampVerified"])} }}')
        lines.append(f'  ({lean_str(cid)}, {r}, {lean_bool(exp)}),')
    lines.append("]")
    lines.append("")
    lines.append("end OpenPreprintFormal.GeneratedVectors")
    target = HERE / "OpenPreprintFormal" / "GeneratedVectors.lean"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    generate()
    print(f"wrote {HERE / 'vectors.json'} and {HERE / 'OpenPreprintFormal' / 'GeneratedVectors.lean'}")
