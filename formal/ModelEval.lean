/- Evaluate the Lean models on the shared differential vectors.
   Output format: <case-id>\t<model-verdict>\t<expected-verdict>
   Used by differential.py to compare against production Python. -/
import OpenPreprintFormal.GeneratedVectors
import OpenPreprintFormal.ReleaseAssets
import OpenPreprintFormal.StateTransition
import OpenPreprintFormal.EvidenceBinding

open OpenPreprintFormal
open ReleaseAssets StateTransition EvidenceBinding

namespace OpenPreprintFormal.ModelEval

def bstr (b : Bool) : String := if b then "true" else "false"

def phaseStr : Phase -> String
  | Phase.draft => "draft"
  | Phase.verified => "verified"
  | Phase.published => "published"

def run : IO Unit := do
  for (cid, r, repo, ver, exp) in GeneratedVectors.releaseCases do
    let got := releaseAccept r repo ver
    IO.println s!"{cid}\t{bstr got}\t{bstr exp}"
  for (cid, ctx, view, exp) in GeneratedVectors.stateCases do
    let got := (advance initial ctx view).phase
    IO.println s!"{cid}\t{phaseStr got}\t{phaseStr exp}"
  for (cid, d1, s1, d2, s2, exp) in GeneratedVectors.evidenceCases do
    let got := decide (receiptDigest d1 s1 = receiptDigest d2 s2)
    IO.println s!"{cid}\t{bstr got}\t{bstr exp}"
  for (cid, rc, exp) in GeneratedVectors.claimCases do
    let got := decide ((parseClaims rc).isSome = true)
    IO.println s!"{cid}\t{bstr got}\t{bstr exp}"

#eval run

end OpenPreprintFormal.ModelEval
