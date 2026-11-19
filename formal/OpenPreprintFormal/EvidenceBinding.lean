/- Formal model: observation record / signature / evidence mutual binding.

   Models scripts/observation.py receipt_digest() and verify_public() and
   scripts/verify_evidence.py. This is a MODEL, not production Python.
   Cryptographic strength (SHA-256 collision resistance, Ed25519 unforgeability)
   is NOT assumed or proved; it is explicitly OUT OF MODEL. What is proved here
   is structural binding: which values are included in the receipt envelope,
   that identity/hash/claim fields are cross-checked, and that over-claiming is
   rejected by construction. No sorry/admit/axioms. -/
namespace OpenPreprintFormal.EvidenceBinding

/-- An idealised injective digest wrapper. The real SHA-256 is OUT OF MODEL;
    modelling the digest as an injective wrapper lets us prove byte-binding
    WITHOUT assuming collision resistance. -/
structure Digest (α : Type) where
  value : α
  deriving DecidableEq, Repr

def digest {α : Type} (a : α) : Digest α := { value := a }

theorem digest_injective {α : Type} {a b : α} (h : digest a = digest b) : a = b := by
  cases h
  rfl

def DOMAIN : String := "OpenPreprintKit-ObservationReceipt-v1"

/-- Domain-separated receipt envelope. Mirrors observation.receipt_digest(),
    which hashes DOMAIN || len(data) || data || len(sig) || sig. -/
structure ReceiptEnvelope where
  domain : String
  dataLen : Nat
  data : List Char
  sigLen : Nat
  sig : List Char
  deriving DecidableEq, Repr

def receiptEnvelope (data sig : List Char) : ReceiptEnvelope :=
  { domain := DOMAIN, dataLen := data.length, data := data,
    sigLen := sig.length, sig := sig }

def receiptDigest (data sig : List Char) : Digest ReceiptEnvelope :=
  digest (receiptEnvelope data sig)

theorem envelope_binds_signature (data s1 s2 : List Char)
    (h : receiptEnvelope data s1 = receiptEnvelope data s2) : s1 = s2 := by
  exact congrArg ReceiptEnvelope.sig h

theorem envelope_binds_data (d1 d2 sig : List Char)
    (h : receiptEnvelope d1 sig = receiptEnvelope d2 sig) : d1 = d2 := by
  exact congrArg ReceiptEnvelope.data h

/-- A receipt digest over (data, sig) cannot be reused for a different pair. -/
theorem receipt_digest_is_binding (d1 s1 d2 s2 : List Char)
    (h : receiptDigest d1 s1 = receiptDigest d2 s2) : d1 = d2 ∧ s1 = s2 := by
  have henv : receiptEnvelope d1 s1 = receiptEnvelope d2 s2 := digest_injective h
  constructor
  · exact congrArg ReceiptEnvelope.data henv
  · exact congrArg ReceiptEnvelope.sig henv

theorem envelope_lengths_are_bound (d1 s1 d2 s2 : List Char)
    (h : receiptEnvelope d1 s1 = receiptEnvelope d2 s2) :
    d1.length = d2.length ∧ s1.length = s2.length := by
  constructor
  · exact congrArg ReceiptEnvelope.dataLen h
  · exact congrArg ReceiptEnvelope.sigLen h

/- ------------------------------------------------------------------------- -/
/- Bounded observation claims                                                 -/
/- ------------------------------------------------------------------------- -/

inductive PublicClaim where
  | witnessAssertsAnonymousRetrieval
  deriving DecidableEq, Repr

inductive FirstPublicationClaim where
  | notProven
  deriving DecidableEq, Repr

inductive AuthorshipClaim where
  | notProven
  deriving DecidableEq, Repr

inductive ClockClaim where
  | selfReportedNotTrusted
  deriving DecidableEq, Repr

structure BoundedClaims where
  accessClaim : PublicClaim
  first : FirstPublicationClaim
  authorship : AuthorshipClaim
  clock : ClockClaim
  anonymousHttps : Bool
  timestampVerified : Bool
  deriving DecidableEq, Repr

structure RawClaims where
  publicAvailability : String
  firstPublication : String
  authorship : String
  witnessClock : String
  anonymousHttps : Bool
  timestampVerified : Bool
  deriving DecidableEq, Repr

/-- Parsing accepts ONLY the bounded vocabulary; an overclaim such as
    FIRST_PUBLICATION_PROVEN has no constructor and is impossible here. -/
def parseClaims (r : RawClaims) : Option BoundedClaims :=
  if r.publicAvailability == "WITNESS_ASSERTS_ANONYMOUS_RETRIEVAL" &&
     r.firstPublication == "NOT_PROVEN" &&
     r.authorship == "NOT_PROVEN" &&
     r.witnessClock == "SELF_REPORTED_NOT_A_TRUSTED_TIMESTAMP" &&
     r.anonymousHttps && r.timestampVerified then
    some { accessClaim := PublicClaim.witnessAssertsAnonymousRetrieval,
           first := FirstPublicationClaim.notProven,
           authorship := AuthorshipClaim.notProven,
           clock := ClockClaim.selfReportedNotTrusted,
           anonymousHttps := true, timestampVerified := true }
  else none

theorem parsed_claims_are_bounded (r : RawClaims) (c : BoundedClaims)
    (h : parseClaims r = some c) :
    c.first = FirstPublicationClaim.notProven ∧
    c.authorship = AuthorshipClaim.notProven ∧
    c.clock = ClockClaim.selfReportedNotTrusted ∧
    c.accessClaim = PublicClaim.witnessAssertsAnonymousRetrieval := by
  unfold parseClaims at h
  by_cases hc : r.publicAvailability == "WITNESS_ASSERTS_ANONYMOUS_RETRIEVAL" &&
     r.firstPublication == "NOT_PROVEN" &&
     r.authorship == "NOT_PROVEN" &&
     r.witnessClock == "SELF_REPORTED_NOT_A_TRUSTED_TIMESTAMP" &&
     r.anonymousHttps && r.timestampVerified
  · simp [hc] at h
    cases h
    simp
  · simp [hc] at h

theorem overclaim_is_rejected (first : String)
    (h : (first != "NOT_PROVEN") = true) :
    parseClaims { publicAvailability := "WITNESS_ASSERTS_ANONYMOUS_RETRIEVAL",
                  firstPublication := first, authorship := "NOT_PROVEN",
                  witnessClock := "SELF_REPORTED_NOT_A_TRUSTED_TIMESTAMP",
                  anonymousHttps := true, timestampVerified := true } = none := by
  unfold parseClaims
  by_cases hf : first = "NOT_PROVEN"
  · simp [hf] at h
  · simp [hf]

/- ------------------------------------------------------------------------- -/
/- Observation verification and identity binding                              -/
/- ------------------------------------------------------------------------- -/

structure ObsRecord where
  repository : String
  version : String
  manifestDigest : Digest (List Char)
  paperDigest : Digest (List Char)
  claims : BoundedClaims
  deriving DecidableEq, Repr

structure ObsEvidence where
  record : ObsRecord
  recordBytes : List Char
  signature : List Char
  actualManifestBytes : List Char
  actualPaperBytes : List Char
  timestampManifestBytes : List Char
  deriving DecidableEq, Repr

/-- Minimal abstract signature model: accept only the model signature of the
    EXACT record bytes under the pinned key. Ed25519 is OUT OF MODEL. -/
def modelSign (key : String) (data : List Char) : List Char := key.toList ++ data

def signatureValid (key : String) (data sig : List Char) : Bool :=
  decide (sig = modelSign key data)

def obsVerify (e : ObsEvidence) (key : String)
    (expectedRepo expectedVersion : String) : Prop :=
  signatureValid key e.recordBytes e.signature = true ∧
  e.record.repository = expectedRepo ∧
  e.record.version = expectedVersion ∧
  e.record.manifestDigest = digest e.actualManifestBytes ∧
  e.record.paperDigest = digest e.actualPaperBytes ∧
  e.record.manifestDigest = digest e.timestampManifestBytes

theorem verify_implies_identity_bind (e : ObsEvidence) (key repo ver : String)
    (h : obsVerify e key repo ver) :
    e.record.repository = repo ∧ e.record.version = ver := by
  exact ⟨h.2.1, h.2.2.1⟩

theorem verify_implies_content_bind (e : ObsEvidence) (key repo ver : String)
    (h : obsVerify e key repo ver) :
    e.record.manifestDigest = digest e.actualManifestBytes ∧
    e.record.paperDigest = digest e.actualPaperBytes := by
  exact ⟨h.2.2.2.1, h.2.2.2.2.1⟩

theorem verify_implies_timestamp_bind (e : ObsEvidence) (key repo ver : String)
    (h : obsVerify e key repo ver) :
    e.record.manifestDigest = digest e.timestampManifestBytes := by
  exact h.2.2.2.2.2

theorem verify_implies_signature_over_record (e : ObsEvidence) (key repo ver : String)
    (h : obsVerify e key repo ver) :
    signatureValid key e.recordBytes e.signature = true := by
  exact h.1

/-- A substituted timestamp (from a different version) is rejected. -/
theorem substituted_timestamp_rejected (e : ObsEvidence) (key repo ver : String)
    (hsub : (e.timestampManifestBytes != e.record.manifestDigest.value) = true) :
    ¬ obsVerify e key repo ver := by
  intro h
  have heq : e.record.manifestDigest = digest e.timestampManifestBytes := h.2.2.2.2.2
  have hbytes : e.record.manifestDigest.value = e.timestampManifestBytes :=
    congrArg Digest.value heq
  simp [hbytes] at hsub

end OpenPreprintFormal.EvidenceBinding


