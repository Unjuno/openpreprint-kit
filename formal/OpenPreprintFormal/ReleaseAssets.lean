/- Formal model: Release asset sets and repository/version identity.

   This is a MODEL of scripts/verify_release.py, scripts/preflight.py and
   scripts/publish_manuscript.py. It is intentionally a small, closed-world
   model over an inductive `Asset` type and is NOT the production Python code.
   Correspondence is checked separately by formal/differential.py using common
   test vectors. No `sorry`, `admit`, or unproven axioms are used. -/
namespace OpenPreprintFormal.ReleaseAssets

/-- The 11 asset kinds recognised by the kit (mirrors verify_release.py). -/
inductive Asset where
  | citation | notes | bibtex | paper | metadata | manifest | sums
  | researchJson | researchTar | tsq | tsr
  deriving DecidableEq, Repr, BEq

/-- A deterministic characteristic-function representation of a set of assets.
    A structure is used (instead of `Asset -> Bool`) so that set equality is
    structurally decidable by the kernel with no Fintype axioms. -/
structure AssetSet where
  citation : Bool
  notes : Bool
  bibtex : Bool
  paper : Bool
  metadata : Bool
  manifest : Bool
  sums : Bool
  researchJson : Bool
  researchTar : Bool
  tsq : Bool
  tsr : Bool
  deriving DecidableEq, Repr, BEq

def emptySet : AssetSet :=
  { citation := false, notes := false, bibtex := false, paper := false,
    metadata := false, manifest := false, sums := false,
    researchJson := false, researchTar := false, tsq := false, tsr := false }

def unionSet (a b : AssetSet) : AssetSet :=
  { citation := a.citation || b.citation, notes := a.notes || b.notes,
    bibtex := a.bibtex || b.bibtex, paper := a.paper || b.paper,
    metadata := a.metadata || b.metadata, manifest := a.manifest || b.manifest,
    sums := a.sums || b.sums, researchJson := a.researchJson || b.researchJson,
    researchTar := a.researchTar || b.researchTar,
    tsq := a.tsq || b.tsq, tsr := a.tsr || b.tsr }

/-- The five always-required payload assets (PAYLOAD_FILES). -/
def payloadSet (research : Bool) : AssetSet :=
  { emptySet with
    citation := true, notes := true, bibtex := true, paper := true, metadata := true,
    researchJson := research, researchTar := research }

/-- The expected bundle: payload + manifest + SHA256SUMS (+ research assets). -/
def expectedSet (research : Bool) : AssetSet :=
  { payloadSet research with manifest := true, sums := true }

/-- Optional RFC 3161 evidence assets. -/
def evidenceSet : AssetSet :=
  { emptySet with tsq := true, tsr := true }

def researchOf (actual : AssetSet) : Bool :=
  actual.researchJson || actual.researchTar

/-- A bundle's asset set is valid iff it equals the expected set, with or
    without the optional timestamp evidence. This mirrors the exact membership
    test in verify_release.verify(). -/
def assetSetValid (actual : AssetSet) : Bool :=
  let research := researchOf actual
  decide (actual = expectedSet research ∨
          actual = unionSet (expectedSet research) evidenceSet)

/-- manifest.json must list exactly the payload (plus research) assets. -/
def manifestMatches (actual manifestFiles : AssetSet) : Bool :=
  decide (manifestFiles = payloadSet (researchOf actual))

/- ------------------------------------------------------------------------- -/
/- Repository and version identity                                            -/
/- ------------------------------------------------------------------------- -/

def isAsciiAlnum (c : Char) : Bool :=
  ('0' <= c && c <= '9') || ('A' <= c && c <= 'Z') || ('a' <= c && c <= 'z')

def isRepoChar (c : Char) : Bool :=
  isAsciiAlnum c || c == '_' || c == '.' || c == '-'

def firstIsAlnum (s : String) : Bool :=
  match s.toList with
  | c :: _ => isAsciiAlnum c
  | [] => false

/-- Simplified model of preflight.validate_repository: OWNER/REPO with
    non-empty alphanumeric-leading parts of bounded length. -/
def repoPartValid (s : String) : Bool :=
  decide (1 <= s.length && s.length <= 100) &&
  firstIsAlnum s && s.toList.all isRepoChar

structure RepoId where
  owner : String
  name : String
  deriving DecidableEq, Repr, BEq

def repoIdValid (r : RepoId) : Bool :=
  repoPartValid r.owner && repoPartValid r.name

/-- A semantic version is a 1..3 component numeric list with at least one
    non-zero component. Numeric components exclude leading zeros by
    construction, matching the production regex. -/
structure Version where
  parts : List Nat
  deriving DecidableEq, Repr, BEq

def versionValid (v : Version) : Bool :=
  decide (1 <= v.parts.length && v.parts.length <= 3 && v.parts.any (fun n => n != 0))

/- ------------------------------------------------------------------------- -/
/- Release acceptance verdict                                                 -/
/- ------------------------------------------------------------------------- -/

def isHex64 (s : String) : Bool :=
  let hex (c : Char) : Bool := ('0' <= c && c <= '9') || ('a' <= c && c <= 'f')
  decide (s.length == 64) && s.toList.all hex

structure Release where
  repo : RepoId
  version : Version
  assets : AssetSet
  manifestFiles : AssetSet
  paperDigest : String
  pinnedPaperDigest : Option String
  deriving DecidableEq, Repr

/-- The full acceptance predicate for a release against an independently
    pinned repository identity and version, stated as a Prop. -/
def releaseAcceptProp (r : Release) (trustedRepo : RepoId) (trustedVersion : Version) : Prop :=
  repoIdValid r.repo = true ∧ r.repo = trustedRepo ∧
  versionValid r.version = true ∧ r.version = trustedVersion ∧
  assetSetValid r.assets = true ∧
  manifestMatches r.assets r.manifestFiles = true ∧
  (match r.pinnedPaperDigest with
   | some p => r.paperDigest = p
   | none => True)

instance releaseAcceptPropDecidable (r : Release) (repo : RepoId) (v : Version) :
    Decidable (releaseAcceptProp r repo v) := by
  unfold releaseAcceptProp
  cases r.pinnedPaperDigest <;> infer_instance

/-- Boolean view used by the differential harness. -/
def releaseAccept (r : Release) (trustedRepo : RepoId) (trustedVersion : Version) : Bool :=
  decide (releaseAcceptProp r trustedRepo trustedVersion)

/- ------------------------------------------------------------------------- -/
/- Kernel-checked theorems                                                    -/
/- ------------------------------------------------------------------------- -/

theorem accept_is_deterministic (a b : Release) (repo : RepoId) (v : Version)
    (h : a = b) : releaseAccept a repo v = releaseAccept b repo v := by
  rw [h]

theorem accept_decomposes (r : Release) (repo : RepoId) (v : Version) :
    releaseAccept r repo v = true ↔ releaseAcceptProp r repo v := by
  simp [releaseAccept]

theorem accept_requires_repo_match (r : Release) (repo : RepoId) (v : Version)
    (h : releaseAccept r repo v = true) : r.repo = repo := by
  have hp : releaseAcceptProp r repo v := by simpa [releaseAccept] using h
  exact hp.2.1

theorem accept_requires_version_match (r : Release) (repo : RepoId) (v : Version)
    (h : releaseAccept r repo v = true) : r.version = v := by
  have hp : releaseAcceptProp r repo v := by simpa [releaseAccept] using h
  exact hp.2.2.2.1

theorem accept_requires_valid_repo (r : Release) (repo : RepoId) (v : Version)
    (h : releaseAccept r repo v = true) : repoIdValid r.repo = true := by
  have hp : releaseAcceptProp r repo v := by simpa [releaseAccept] using h
  exact hp.1

theorem accept_requires_valid_version (r : Release) (repo : RepoId) (v : Version)
    (h : releaseAccept r repo v = true) : versionValid r.version = true := by
  have hp : releaseAcceptProp r repo v := by simpa [releaseAccept] using h
  exact hp.2.2.1

theorem accept_requires_asset_set_valid (r : Release) (repo : RepoId) (v : Version)
    (h : releaseAccept r repo v = true) : assetSetValid r.assets = true := by
  have hp : releaseAcceptProp r repo v := by simpa [releaseAccept] using h
  exact hp.2.2.2.2.1

theorem accept_requires_manifest_match (r : Release) (repo : RepoId) (v : Version)
    (h : releaseAccept r repo v = true) : manifestMatches r.assets r.manifestFiles = true := by
  have hp : releaseAcceptProp r repo v := by simpa [releaseAccept] using h
  exact hp.2.2.2.2.2.1

theorem pinned_valid_digest_implies_binding (r : Release) (repo : RepoId) (v : Version)
    (p : String) (h : releaseAccept r repo v = true)
    (hp : r.pinnedPaperDigest = some p) (hhex : isHex64 p = true) :
    r.paperDigest = p ∧ isHex64 r.paperDigest = true := by
  have hparts : releaseAcceptProp r repo v := by simpa [releaseAccept] using h
  unfold releaseAcceptProp at hparts
  rw [hp] at hparts
  have hbind : r.paperDigest = p := hparts.2.2.2.2.2.2
  constructor
  · exact hbind
  · rw [hbind]
    exact hhex

theorem evidence_only_set_is_accepted (actual : AssetSet) :
    actual = unionSet (expectedSet (researchOf actual)) evidenceSet →
    assetSetValid actual = true := by
  intro h
  unfold assetSetValid
  cases hdec : decide (actual = expectedSet (researchOf actual) ∨
          actual = unionSet (expectedSet (researchOf actual)) evidenceSet) with
  | true => rfl
  | false =>
      have hp : ¬ (actual = expectedSet (researchOf actual) ∨
                actual = unionSet (expectedSet (researchOf actual)) evidenceSet) := by
        simpa using hdec
      exact (hp (Or.inr h)).elim

theorem missing_payload_is_rejected (actual : AssetSet)
    (h : actual.citation = false) : assetSetValid actual = false := by
  have hn1 : ¬ actual = expectedSet (researchOf actual) := by
    intro heq
    have hc := congrArg AssetSet.citation heq
    simp [expectedSet, payloadSet, h] at hc
  have hn2 : ¬ actual = unionSet (expectedSet (researchOf actual)) evidenceSet := by
    intro heq
    have hc := congrArg AssetSet.citation heq
    simp [unionSet, expectedSet, payloadSet, h] at hc
  unfold assetSetValid
  cases hdec : decide (actual = expectedSet (researchOf actual) ∨
          actual = unionSet (expectedSet (researchOf actual)) evidenceSet) with
  | true =>
      have hp : actual = expectedSet (researchOf actual) ∨
                actual = unionSet (expectedSet (researchOf actual)) evidenceSet := by
        simpa using hdec
      cases hp with
      | inl heq => exact (hn1 heq).elim
      | inr heq => exact (hn2 heq).elim
  | false => rfl

theorem extra_unknown_asset_is_rejected (actual : AssetSet)
    (h1 : ¬ actual = expectedSet (researchOf actual))
    (h2 : ¬ actual = unionSet (expectedSet (researchOf actual)) evidenceSet) :
    assetSetValid actual = false := by
  unfold assetSetValid
  cases hdec : decide (actual = expectedSet (researchOf actual) ∨
          actual = unionSet (expectedSet (researchOf actual)) evidenceSet) with
  | true =>
      have hp : actual = expectedSet (researchOf actual) ∨
                actual = unionSet (expectedSet (researchOf actual)) evidenceSet := by
        simpa using hdec
      cases hp with
      | inl heq => exact (h1 heq).elim
      | inr heq => exact (h2 heq).elim
  | false => rfl

end OpenPreprintFormal.ReleaseAssets
