/- Formal model: pre-publication verification and state-transition safety.

   Models scripts/preflight.py (GitHub read-only gates) and the publication
   state machine in scripts/publish_manuscript.py / first_paper_publish.py.
   This is a MODEL, not production Python. No sorry/admit/axioms. -/
namespace OpenPreprintFormal.StateTransition

/-- Publication lifecycle phase. -/
inductive Phase where
  | draft | verified | published
  deriving DecidableEq, Repr, BEq

/-- The immutable identity that preflight binds to. -/
structure PublishContext where
  repository : String
  version : String
  commit : String
  deriving DecidableEq, Repr, BEq

/-- The subset of the GitHub API view that preflight reads. -/
structure RepoView where
  isPublic : Bool
  immutableEnabled : Bool
  headSha : String
  releaseTagExists : Bool
  tagRefExists : Bool
  deriving DecidableEq, Repr, BEq

structure PubState where
  phase : Phase
  checked : Option PublishContext
  deriving DecidableEq, Repr, BEq

def phaseRank : Phase -> Nat
  | Phase.draft => 0
  | Phase.verified => 1
  | Phase.published => 2

/-- Version validity: a version token beginning with 'v' that is not an
    all-zero draft. Full regex validation remains a production-only detail. -/
def versionTokenValid (v : String) : Bool :=
  decide (1 < v.length && v != "v0" && v != "v0.0" && v != "v0.0.0") &&
  (match v.toList with | 'v' :: _ => true | _ => false)

def commitValid (c : String) : Bool :=
  decide (c.length == 40) && c.toList.all (fun ch =>
    ('0' <= ch && ch <= '9') || ('a' <= ch && ch <= 'f'))

/-- The exact read-only gates checked by preflight.preflight(): public repo,
    immutable releases enabled, default-branch HEAD equals the pinned commit,
    and both the Release tag and the git tag ref are absent. -/
def preflightOk (view : RepoView) (ctx : PublishContext) : Bool :=
  versionTokenValid ctx.version && commitValid ctx.commit &&
  view.isPublic && view.immutableEnabled &&
  decide (view.headSha = ctx.commit) &&
  !view.releaseTagExists && !view.tagRefExists

def initial : PubState := { phase := Phase.draft, checked := none }

/-- The only state transition. A draft becomes verified only after all
    preflight gates pass. A verified state becomes published only when the SAME
    context is re-validated against the current view (defeating a forced branch
    update or a competing tag created after verification). Published is
    terminal: no transition mutates it. -/
def advance (s : PubState) (ctx : PublishContext) (view : RepoView) : PubState :=
  match s.phase with
  | Phase.draft =>
      if preflightOk view ctx then { phase := Phase.verified, checked := some ctx } else s
  | Phase.verified =>
      match s.checked with
      | some c0 =>
          if c0 = ctx && preflightOk view ctx then
            { phase := Phase.published, checked := some ctx }
          else s
      | none => s
  | Phase.published => s

/- ------------------------------------------------------------------------- -/
/- Kernel-checked theorems                                                    -/
/- ------------------------------------------------------------------------- -/

theorem published_is_terminal (s : PubState) (ctx : PublishContext) (view : RepoView)
    (h : s.phase = Phase.published) : advance s ctx view = s := by
  cases s with
  | mk phase checked =>
      cases phase
      · simp at h
      · simp at h
      · rfl

theorem published_requires_prior_verification (s : PubState) (ctx : PublishContext)
    (view : RepoView) (hprev : (s.phase != Phase.published) = true)
    (h : (advance s ctx view).phase = Phase.published) :
    s.phase = Phase.verified ∧ s.checked = some ctx := by
  cases s with
  | mk phase checked =>
      cases phase
      · by_cases hpf : preflightOk view ctx
        · simp [advance, hpf] at h
        · simp [advance, hpf] at h
      · cases checked with
        | none => simp [advance] at h
        | some c0 =>
            by_cases heq : c0 = ctx
            · by_cases hpf : preflightOk view ctx
              · simp [advance, heq, hpf] at h ⊢
              · simp [advance, heq, hpf] at h
            · by_cases hpf : preflightOk view ctx
              · simp [advance, heq, hpf] at h
              · simp [advance, heq, hpf] at h
      · have hf : (Phase.published != Phase.published) = false := rfl
        rw [hf] at hprev
        contradiction

theorem preflight_failure_keeps_draft (ctx : PublishContext) (view : RepoView)
    (hpf : preflightOk view ctx = false) : advance initial ctx view = initial := by
  simp [initial, advance, hpf]

theorem forced_update_blocks_publish (ctx : PublishContext) (view : RepoView)
    (hhead : ¬ view.headSha = ctx.commit) :
    advance { phase := Phase.verified, checked := some ctx } ctx view =
      { phase := Phase.verified, checked := some ctx } := by
  have hpf : preflightOk view ctx = false := by
    simp [preflightOk, hhead]
  simp [advance, hpf]

theorem occupied_tag_blocks_verification (ctx : PublishContext) (view : RepoView)
    (htag : view.releaseTagExists = true ∨ view.tagRefExists = true) :
    advance initial ctx view = initial := by
  have hpf : preflightOk view ctx = false := by
    cases htag with
    | inl h => simp [preflightOk, h]
    | inr h => simp [preflightOk, h]
  simp [initial, advance, hpf]

theorem nonpublic_or_nonimmutable_blocked (ctx : PublishContext) (view : RepoView)
    (h : view.isPublic = false ∨ view.immutableEnabled = false) :
    advance initial ctx view = initial := by
  have hpf : preflightOk view ctx = false := by
    cases h with
    | inl hb => simp [preflightOk, hb]
    | inr hb => simp [preflightOk, hb]
  simp [initial, advance, hpf]

theorem phase_never_regresses (s : PubState) (ctx : PublishContext) (view : RepoView) :
    phaseRank s.phase <= phaseRank (advance s ctx view).phase := by
  cases s with
  | mk phase checked =>
      cases phase
      · simp [phaseRank]
      · cases checked with
        | none => simp [advance, phaseRank]
        | some c0 =>
            by_cases hc : c0 = ctx <;> by_cases hpf : preflightOk view ctx <;>
            simp [advance, phaseRank, hc, hpf]
      · simp [advance, phaseRank]

theorem advance_is_deterministic (s : PubState) (a b : PublishContext) (v : RepoView)
    (h : a = b) : advance s a v = advance s b v := by
  rw [h]

end OpenPreprintFormal.StateTransition
