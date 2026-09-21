"""IRIS-WO-0006 synthetic brief profiles: six domains, one kernel.

Each profile below is assembled only from :mod:`iris_intent` primitives: preserved raw sources,
statements with an authority and a provenance capsule, constraints with a predicate and a scope,
freedom zones, protected anchors and open questions. Nothing here imports a provider SDK, and
nothing in the kernel learns a word of any domain's vocabulary — the six briefs differ only in the
semantic paths they address and the channel set they scope to.

That asymmetry is the proof. A logo brief and a narration brief reach the same slice, fingerprint,
conflict-detection and readiness calls, and if the kernel needed a pixel, a mesh, a camera or a
text-to-image field to hold one of them, one of these six would not compile.

Like :mod:`examples.m01_synthetic_profiles` and :mod:`examples.m02_synthetic_profiles`, this module
is a fixture, not a feature: the kernel must stay importable with this directory deleted, and no
production code may import it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from iris_intent.ambiguity import (
    AmbiguityConsequence,
    AmbiguityKind,
    AmbiguityRecord,
    FreedomZone,
    OpenQuestion,
)
from iris_intent.authority import AuthorityLevel
from iris_intent.briefs import BriefRevision, RevisionKind, intent_model_for
from iris_intent.conflicts import detect_conflicts
from iris_intent.constraints import (
    AntiReference,
    Condition,
    Constraint,
    ConstraintBundle,
    ConstraintPolarity,
    ConstraintScope,
    ConstraintStrength,
    CrossModalLink,
    ProtectedAnchor,
    ToleranceEnvelope,
)
from iris_intent.fingerprints import fingerprint_revision
from iris_intent.freshness import (
    DerivedArtifactKind,
    DerivedIntentDependency,
    FreshnessDimension,
    assess_freshness,
)
from iris_intent.identity import (
    VERSIONED_REF_KINDS,
    RefKind,
    SemanticRef,
    SourceKind,
    ceiling_for,
)
from iris_intent.intent import (
    IntentAuthorityRef,
    IntentModel,
    IntentOrigin,
    IntentStatement,
    ModalChannel,
    StatementKind,
)
from iris_intent.overrides import OverrideLedger
from iris_intent.predicates import PredicateCall, PredicateRegistry, PredicateSignature
from iris_intent.readiness import assess_release_readiness
from iris_intent.reuse import evaluate_reuse, passport_for
from iris_intent.slicing import (
    MinimumSufficientSemanticSlice,
    SemanticSliceRequest,
    slice_intent,
)
from iris_intent.sources import (
    AnchorSpan,
    DerivationKind,
    ProvenanceCapsule,
    RawInputRef,
    SourceAnchor,
)
from iris_intent.versions import content_digest

__all__ = ["BRIEFS", "BriefProfile", "profile_for", "profiles_by_channel", "run_kernel"]


def digest(seed: Any) -> str:
    return content_digest(seed)


def ref(kind: str, ident: str, version: str | None = None) -> SemanticRef:
    pinned = version or ("v1" if _versioned(kind) else None)
    return SemanticRef(kind=kind, ref_id=ident, version=pinned, content_digest=digest(ident))


def _versioned(kind: str) -> bool:
    try:
        member = RefKind(kind)
    except ValueError:
        return False
    return member in VERSIONED_REF_KINDS


REVISION_7 = ref(RefKind.REVISION.value, "rev.7")

HUMAN = IntentAuthorityRef(
    authority=AuthorityLevel.HUMAN_OWNER.value,
    basis="REVISION",
    granted_by=REVISION_7,
    rationale="owner revision 7",
)
STAFF = IntentAuthorityRef(authority=AuthorityLevel.PROJECT_RECORD.value, basis="PROJECT_RECORD")
INFER = IntentAuthorityRef(authority=AuthorityLevel.MODEL_INFERRED.value, basis="PROJECT_RECORD")

_CEILING_BY_ORIGIN = {
    IntentOrigin.EXPLICIT.value: HUMAN,
    IntentOrigin.DERIVED.value: STAFF,
    IntentOrigin.INFERRED.value: INFER,
    # A default is not an inference: the kernel floors DEFAULTED at project record because someone
    # has to stand behind the value the brief never stated.
    IntentOrigin.DEFAULTED.value: STAFF,
}


def source(source_id: str, kind: str = SourceKind.HUMAN_MESSAGE.value) -> RawInputRef:
    """A preserved input at the authority its kind can actually carry.

    The ceiling comes from the kind rather than from a wish: a project record that claims human
    standing is the forgery this module exists to make impossible to write.
    """

    return RawInputRef(
        source_id=source_id,
        kind=kind,
        authority=ceiling_for(kind).value,
        content_digest=digest(source_id),
        language="en",
    )


def capsule(
    capsule_id: str,
    item: RawInputRef,
    *,
    derivation: str = DerivationKind.PARAPHRASED.value,
    quote: str | None = None,
) -> ProvenanceCapsule:
    anchors = ()
    if quote is not None:
        anchors = (
            SourceAnchor(
                anchor_id=f"an.{capsule_id}",
                source_id=item.source_id,
                quote_digest=digest(quote),
                language="en",
                span=AnchorSpan(start=0, end=len(quote)),
            ),
        )
    return ProvenanceCapsule(
        capsule_id=capsule_id,
        derivation=derivation,
        source_refs=(item.source_ref,),
        anchors=anchors,
    )


def say(
    ident: str,
    path: str,
    kind: str,
    assertion: str,
    item: RawInputRef,
    *,
    origin: str = IntentOrigin.EXPLICIT.value,
    modality: str | None = None,
    mandatory: bool = False,
    ancestors: Sequence[str] = (),
) -> IntentStatement:
    return IntentStatement(
        statement_id=ident,
        semantic_path=path,
        kind=kind,
        assertion=assertion,
        origin=origin,
        authority=_CEILING_BY_ORIGIN[origin],
        modality=modality or ModalChannel.UNSPECIFIED.value,
        value={"state": "on"},
        mandatory=mandatory,
        source_statement_ids=tuple(ancestors),
        provenance=capsule(
            f"cap.{ident}", item, quote=assertion if origin == IntentOrigin.EXPLICIT.value else None
        ),
    )


def rule(
    ident: str,
    path: str,
    predicate: str,
    *,
    polarity: str = ConstraintPolarity.REQUIRE.value,
    strength: str = ConstraintStrength.HARD.value,
    channels: Sequence[str],
    arguments: Mapping[str, Any] | None = None,
    mandatory: bool = False,
    conditions: Iterable[Condition] = (),
    tolerances: Iterable[ToleranceEnvelope] = (),
    anti_references: Iterable[AntiReference] = (),
    protected_anchors: Iterable[ProtectedAnchor] = (),
    cross_modal_links: Iterable[CrossModalLink] = (),
    excluded_paths: Sequence[str] = (),
) -> Constraint:
    return Constraint(
        constraint_id=ident,
        semantic_path=path,
        predicate=PredicateCall(
            predicate_id=predicate, version="v1", arguments=dict(arguments or {})
        ),
        polarity=polarity,
        strength=strength,
        scope=ConstraintScope(
            subject_paths=(path,), modalities=tuple(channels), excluded_paths=tuple(excluded_paths)
        ),
        authority=STAFF,
        conditions=tuple(conditions),
        tolerances=tuple(tolerances),
        anti_references=tuple(anti_references),
        protected_anchors=tuple(protected_anchors),
        cross_modal_links=tuple(cross_modal_links),
        mandatory=mandatory,
        modality=channels[0],
        provenance=capsule(
            f"cap.{ident}",
            source(f"src.{ident}", SourceKind.PROJECT_RECORD.value),
            derivation=DerivationKind.PARAPHRASED.value,
        ),
    )


def measure(
    metric_id: str,
    comparison: str,
    *,
    unit: str,
    target: float | None = None,
    lower: float | None = None,
    upper: float | None = None,
    ident: str | None = None,
) -> ToleranceEnvelope:
    return ToleranceEnvelope(
        measure=ident or f"tol.{metric_id}",
        comparison=comparison,
        unit=unit,
        metric_ref=ref(RefKind.SOURCE.value, f"metric.{metric_id}"),
        target=target,
        lower=lower,
        upper=upper,
    )


def pin(
    ident: str,
    path: str,
    kind: str,
    *,
    statements: Sequence[str] = (),
    consequence: str = "BLOCKING",
) -> ProtectedAnchor:
    return ProtectedAnchor(
        anchor_id=ident,
        semantic_path=path,
        anchor_kind=kind,
        statement_refs=tuple(ref(RefKind.STATEMENT.value, name) for name in statements),
        must_survive_translation=True,
        minimum_authority=AuthorityLevel.HUMAN_OWNER.value,
        loss_consequence=consequence,
    )


def freedom(
    ident: str,
    label: str,
    free: Sequence[str],
    fixed: Sequence[str],
    *,
    latitude: str = "OPEN_WITHIN_BOUNDS",
) -> FreedomZone:
    return FreedomZone(
        zone_id=ident,
        label=label,
        free_paths=tuple(free),
        fixed_paths=tuple(fixed),
        latitude=latitude,
        rationale="the brief states the outcome and leaves the means to the maker",
        granted_by=REVISION_7,
    )


def ask(ident: str, text: str, paths: Sequence[str], *, blocking: bool = False) -> OpenQuestion:
    return OpenQuestion(
        question_id=ident,
        text=text,
        consequence=(
            AmbiguityConsequence.BLOCKING.value
            if blocking
            else AmbiguityConsequence.COST_CRITICAL.value
        ),
        status="OPEN",
        semantic_paths=tuple(paths),
        blocking=blocking,
        addressed_to="owner",
    )


def unclear(
    ident: str,
    path: str,
    kind: str,
    question: str,
    statements: Sequence[str],
    *,
    consequence: str = AmbiguityConsequence.COST_CRITICAL.value,
    readings: Sequence[str] = (),
) -> AmbiguityRecord:
    return AmbiguityRecord(
        ambiguity_id=ident,
        kind=kind,
        consequence=consequence,
        semantic_paths=(path,),
        question=question,
        candidate_readings=tuple(readings),
        affected_statement_ids=tuple(statements),
        requires_human=True,
    )


@dataclass(frozen=True)
class BriefProfile:
    """One domain's admitted brief, assembled entirely from kernel records.

    ``channels`` and ``paths`` are the only things a reader may expect to differ between profiles:
    every other field is the same type, produced by the same calls.
    """

    profile_id: str
    label: str
    revision: BriefRevision
    model: IntentModel
    bundle: ConstraintBundle
    channels: tuple[str, ...]
    paths: tuple[str, ...]
    registry: PredicateRegistry
    zones: tuple[FreedomZone, ...] = ()
    questions: tuple[OpenQuestion, ...] = ()
    ambiguities: tuple[AmbiguityRecord, ...] = ()
    predicates: tuple[str, ...] = ()


def registry_for(paths: Sequence[str], predicates: Sequence[str]) -> PredicateRegistry:
    """A domain's own vocabulary, admitted through the extension route the contract names.

    Nothing here is shared between profiles on purpose: a predicate that means one thing to a logo
    brief and another to a narration brief is two predicates, and a common registry would be the
    place that error became invisible.
    """

    return PredicateRegistry(
        PredicateSignature(
            predicate_id=name,
            version="v1",
            semantic_path=paths[0],
            trust="CORE",
            interpretation=f"{name} as this brief defines it",
        )
        for name in predicates
    )


def build(
    profile_id: str,
    label: str,
    statements: Sequence[IntentStatement],
    sources: Sequence[RawInputRef],
    constraints: Sequence[Constraint],
    channels: Sequence[str],
    paths: Sequence[str],
    *,
    zones: Sequence[FreedomZone] = (),
    questions: Sequence[OpenQuestion] = (),
    ambiguities: Sequence[AmbiguityRecord] = (),
    predicates: Sequence[str] = (),
    number: int = 7,
) -> BriefProfile:
    """Admit a revision, compile its model, then seal the bundle that cites it.

    The order is the kernel's, not a style choice: a bundle names the revision it was admitted
    against, so nothing here can be assembled in one expression.
    """

    revision = BriefRevision(
        revision_id=f"rev.{profile_id}.{number}",
        brief_id=f"brief.{profile_id}",
        revision_number=number,
        kind=RevisionKind.CORRECTION.value,
        status="ADMITTED",
        statements=tuple(statements),
        sources=tuple(sources),
        predecessor_revision_id=f"rev.{profile_id}.{number - 1}" if number > 1 else None,
        ancestor_revision_ids=tuple(f"rev.{profile_id}.{index}" for index in range(1, number)),
        created_by=REVISION_7,
        admitted_by=REVISION_7,
        label=profile_id,
    )
    registry = registry_for(paths, predicates)
    bundle = ConstraintBundle(
        bundle_id=f"bundle.{profile_id}",
        brief_id=revision.brief_id,
        revision_id=revision.revision_id,
        version="v1",
        constraints=tuple(constraints),
    ).admit(registry=registry, admitted_by=revision.revision_ref)
    return BriefProfile(
        profile_id=profile_id,
        label=label,
        revision=revision,
        model=intent_model_for(revision, model_id=f"model.{profile_id}"),
        bundle=bundle,
        channels=tuple(channels),
        paths=tuple(paths),
        registry=registry,
        zones=tuple(zones),
        questions=tuple(questions),
        ambiguities=tuple(ambiguities),
        predicates=tuple(predicates),
    )


# --- 1. logo / brand / web --------------------------------------------------

LOGO_BRIEF = source("src.logo.brief", SourceKind.HUMAN_DOCUMENT.value)

LOGO_PROFILE = build(
    "logo-brand-web",
    "Brand mark for a launch landing page",
    (
        say(
            "st.logo.wordmark",
            "brief.visual.logo",
            StatementKind.IDENTITY.value,
            "the mark is the client's existing wordmark, recoloured only",
            LOGO_BRIEF,
            modality=ModalChannel.IMAGE.value,
            mandatory=True,
        ),
        say(
            "st.logo.palette",
            "brief.visual.palette",
            StatementKind.STYLE.value,
            "use only the two documented brand colours",
            LOGO_BRIEF,
            origin=IntentOrigin.DERIVED.value,
            ancestors=("st.logo.wordmark",),
        ),
        say(
            "st.hero.promise",
            "brief.web.hero",
            StatementKind.OUTCOME.value,
            "one sentence a first-time visitor repeats back",
            LOGO_BRIEF,
        ),
        say(
            "st.icon.grid",
            "brief.visual.icon",
            StatementKind.CONSTRAINT_SEMANTICS.value,
            "the favicon is the mark's first letter on the same grid",
            LOGO_BRIEF,
            origin=IntentOrigin.INFERRED.value,
            ancestors=("st.logo.wordmark",),
            modality=ModalChannel.IMAGE.value,
        ),
    ),
    (LOGO_BRIEF,),
    (
        rule(
            "cn.logo.present",
            "brief.visual.logo",
            "shows_logo",
            channels=(ModalChannel.IMAGE.value,),
            mandatory=True,
            protected_anchors=(pin("an.logo.mark", "brief.visual.logo", "BRAND", statements=("st.logo.wordmark",)),),
        ),
        rule(
            "cn.logo.min-size",
            "brief.visual.logo",
            "fits_canvas",
            channels=(ModalChannel.IMAGE.value,),
            tolerances=(measure("logo.legibility", "GTE", unit="PX", target=24.0),),
        ),
        rule(
            "cn.logo.no-substituted-font",
            "brief.visual.logo",
            "keeps_palette",
            polarity=ConstraintPolarity.FORBID.value,
            channels=(ModalChannel.TEXT.value,),
            anti_references=(
                AntiReference(
                    anti_ref_id="ar.logo.stock-font",
                    anchor_ref=ref(RefKind.ANCHOR.value, "an.logo.mark"),
                    facets=("typography",),
                    modality=ModalChannel.TEXT.value,
                    severity_hint="MAJOR",
                    rationale="a substituted face is a different mark wearing the same colours",
                ),
            ),
        ),
        rule(
            "cn.hero.promise-length",
            "brief.web.hero",
            "fits_canvas",
            strength=ConstraintStrength.SOFT.value,
            channels=(ModalChannel.TEXT.value, ModalChannel.INTERFACE.value),
            tolerances=(measure("hero.word_count", "LTE", unit="WORDS", target=14.0),),
        ),
    ),
    (ModalChannel.IMAGE.value, ModalChannel.BRAND.value),
    ("brief.visual.logo", "brief.visual.icon", "brief.web.hero"),
    zones=(freedom("zone.logo.grid", "Grid and optical spacing are the designer's", ("brief.visual.grid",), ("brief.visual.logo",)),),
    questions=(ask("q.logo.file", "Which master file is the mark's source of truth?", ("brief.visual.logo",)),),
    ambiguities=(
        unclear(
            "am.logo.mark",
            "brief.visual.logo",
            AmbiguityKind.TERM_OVERLOAD.value,
            "Does 'the mark' mean the wordmark or the monogram?",
            ("st.logo.wordmark",),
            readings=("wordmark", "monogram"),
        ),
    ),
    predicates=("shows_logo", "keeps_palette", "fits_canvas"),
)


# --- 2. product photography -------------------------------------------------

PHOTO_BRIEF = source("src.photo.brief")

PHOTO_PROFILE = build(
    "product-photography",
    "Catalogue photography for a hardware line",
    (
        say(
            "st.photo.subject",
            "brief.visual.product",
            StatementKind.SUBJECT.value,
            "every SKU shown exactly as shipped, no posed props",
            PHOTO_BRIEF,
            modality=ModalChannel.IMAGE.value,
            mandatory=True,
        ),
        say(
            "st.photo.light",
            "brief.visual.lighting",
            StatementKind.DIRECTION.value,
            "soft key from the upper left, no coloured rim",
            PHOTO_BRIEF,
        ),
        say(
            "st.photo.surface",
            "brief.visual.surface",
            StatementKind.CONSTRAINT_SEMANTICS.value,
            "reflections show the room as a single even gradient",
            PHOTO_BRIEF,
            origin=IntentOrigin.DEFAULTED.value,
        ),
    ),
    (PHOTO_BRIEF,),
    (
        rule(
            "cn.photo.subject",
            "brief.visual.product",
            "shows_product",
            channels=(ModalChannel.IMAGE.value,),
            mandatory=True,
            protected_anchors=(pin("an.photo.as-shipped", "brief.visual.product", "CANON", statements=("st.photo.subject",)),),
        ),
        rule(
            "cn.photo.no-prop",
            "brief.visual.product",
            "shows_product",
            polarity=ConstraintPolarity.FORBID.value,
            channels=(ModalChannel.IMAGE.value,),
            excluded_paths=("brief.visual.styling",),
        ),
        rule(
            "cn.photo.key-soft",
            "brief.visual.lighting",
            "keeps_lighting",
            strength=ConstraintStrength.SOFT.value,
            channels=(ModalChannel.IMAGE.value,),
            tolerances=(measure("photo.rim_contrast", "LTE", unit="EV", target=0.5),),
        ),
    ),
    (ModalChannel.IMAGE.value,),
    ("brief.visual.product", "brief.visual.lighting"),
    zones=(freedom("zone.photo.styling", "Support surfaces and shadows are the photographer's", ("brief.visual.styling",), ("brief.visual.product",)),),
    questions=(ask("q.photo.backdrop", "Seamless white or the textured set the last campaign used?", ("brief.visual.styling",)),),
    predicates=("shows_product", "keeps_lighting", "holds_surface"),
)


# --- 3. isometric 3D / game asset ------------------------------------------

ASSET_BRIEF = source("src.asset.brief", SourceKind.CANON_RECORD.value)

ASSET_PROFILE = build(
    "isometric-game-asset",
    "Isometric building set for a strategy title",
    (
        say(
            "st.asset.projection",
            "brief.geometry.building",
            StatementKind.CONSTRAINT_SEMANTICS.value,
            "the set reads as one projection at any zoom the editor offers",
            ASSET_BRIEF,
            modality=ModalChannel.GEOMETRY.value,
            mandatory=True,
        ),
        say(
            "st.asset.tri-budget",
            "brief.geometry.budget",
            StatementKind.TEMPORAL.value,
            "each building stays inside the shared triangle ceiling",
            ASSET_BRIEF,
            origin=IntentOrigin.DERIVED.value,
            ancestors=("st.asset.projection",),
        ),
        say(
            "st.asset.atlas",
            "brief.material.palette",
            StatementKind.STYLE.value,
            "one atlas across the set so the scene draws in one batch",
            ASSET_BRIEF,
        ),
    ),
    (ASSET_BRIEF,),
    (
        rule(
            "cn.asset.projection",
            "brief.geometry.building",
            "keeps_projection",
            channels=(ModalChannel.GEOMETRY.value,),
            mandatory=True,
            protected_anchors=(pin("an.asset.projection", "brief.geometry.building", "CANON", statements=("st.asset.projection",)),),
        ),
        rule(
            "cn.asset.tri-ceiling",
            "brief.geometry.budget",
            "stays_within",
            channels=(ModalChannel.GEOMETRY.value,),
            tolerances=(measure("asset.triangle_count", "LTE", unit="COUNT", target=9000.0),),
        ),
        rule(
            "cn.asset.one-atlas",
            "brief.material.palette",
            "shares_atlas",
            strength=ConstraintStrength.GUARDED.value,
            channels=(ModalChannel.MATERIAL.value,),
        ),
    ),
    (ModalChannel.GEOMETRY.value, ModalChannel.MATERIAL.value),
    ("brief.geometry.building", "brief.material.palette"),
    zones=(freedom("zone.asset.silhouette", "Rooflines and signage are the artist's", ("brief.geometry.silhouette",), ("brief.geometry.building",)),),
    questions=(ask("q.asset.atlas", "One 2K atlas or two 1K atlases for the mobile target?", ("brief.material.palette",)),),
    predicates=("keeps_projection", "stays_within", "shares_atlas"),
)


# --- 4. film / commercial / multi-shot --------------------------------------

FILM_BRIEF = source("src.film.brief", SourceKind.HUMAN_DOCUMENT.value)

FILM_PROFILE = build(
    "film-commercial",
    "Thirty-second spot cut from three shots",
    (
        say(
            "st.film.beat",
            "brief.video.beat",
            StatementKind.TEMPORAL.value,
            "the reveal lands at the fifteen second mark",
            FILM_BRIEF,
            modality=ModalChannel.VIDEO.value,
            mandatory=True,
        ),
        say(
            "st.film.open",
            "brief.video.shot_open",
            StatementKind.DIRECTION.value,
            "the opening holds one continuous move, no cut inside it",
            FILM_BRIEF,
        ),
        say(
            "st.film.close",
            "brief.video.shot_close",
            StatementKind.OUTCOME.value,
            "the closing frame carries the mark and nothing else",
            FILM_BRIEF,
            origin=IntentOrigin.DERIVED.value,
            ancestors=("st.film.open",),
        ),
        say(
            "st.film.mood",
            "brief.audio.tone",
            StatementKind.DIRECTION.value,
            "the mix stays under the voice until the last three seconds",
            FILM_BRIEF,
            modality=ModalChannel.AUDIO.value,
            origin=IntentOrigin.INFERRED.value,
            ancestors=("st.film.beat",),
        ),
    ),
    (FILM_BRIEF,),
    (
        rule(
            "cn.film.beat",
            "brief.video.beat",
            "lands_at",
            channels=(ModalChannel.VIDEO.value,),
            mandatory=True,
            tolerances=(measure("film.timeline_offset", "BETWEEN", unit="S", lower=14.0, upper=16.0),),
            protected_anchors=(pin("an.film.beat", "brief.video.beat", "STORY", statements=("st.film.beat",)),),
        ),
        rule(
            "cn.film.open-one-move",
            "brief.video.shot_open",
            "holds_shot",
            channels=(ModalChannel.VIDEO.value, ModalChannel.MOTION.value),
            conditions=(Condition(context_key="cut.count", operator="EQ", values=("1",)),),
        ),
        rule(
            "cn.film.close-mark",
            "brief.video.shot_close",
            "holds_shot",
            channels=(ModalChannel.IMAGE.value, ModalChannel.VIDEO.value),
            cross_modal_links=(
                CrossModalLink(
                    link_id="link.film.mark",
                    channels=(ModalChannel.VIDEO.value, ModalChannel.IMAGE.value),
                    semantic_paths=("brief.video.shot_close", "brief.visual.logo"),
                    consistency="STRICT",
                    reference_channel=ModalChannel.IMAGE.value,
                ),
            ),
        ),
        rule(
            "cn.film.mix-under",
            "brief.audio.tone",
            "keeps_mix_below",
            strength=ConstraintStrength.SOFT.value,
            channels=(ModalChannel.AUDIO.value,),
            tolerances=(measure("film.level", "LTE", unit="DB", target=-12.0),),
        ),
    ),
    (ModalChannel.VIDEO.value, ModalChannel.MOTION.value, ModalChannel.AUDIO.value),
    ("brief.video.shot_open", "brief.video.shot_product", "brief.video.shot_close"),
    zones=(freedom("zone.film.camera", "Lens choice and camera moves are the DP's", ("brief.video.camera",), ("brief.video.beat",)),),
    questions=(ask("q.film.licence", "Is the licensed track cleared for the broadcast territory?", ("brief.audio.music",)),),
    ambiguities=(
        unclear(
            "am.film.beat",
            "brief.video.beat",
            AmbiguityKind.UNBOUNDED_TOLERANCE.value,
            "Does 'the reveal' name a shot or a graphic event?",
            ("st.film.beat",),
        ),
    ),
    predicates=("holds_shot", "lands_at", "keeps_mix_below"),
)


# --- 5. corporate spokesperson / digital human ------------------------------

PERSONA_BRIEF = source("src.persona.brief", SourceKind.GOVERNED_POLICY.value)

PERSONA_PROFILE = build(
    "spokesperson-digital-human",
    "A persistent on-screen spokesperson across campaigns",
    (
        say(
            "st.persona.identity",
            "brief.identity.persona",
            StatementKind.IDENTITY.value,
            "the same licensed person appears in every cut, never a composite of two",
            PERSONA_BRIEF,
            modality=ModalChannel.VIDEO.value,
            mandatory=True,
        ),
        say(
            "st.persona.voice",
            "brief.speech.persona",
            StatementKind.MODALITY.value,
            "the delivery is the approved reading, not an improvised one",
            PERSONA_BRIEF,
            modality=ModalChannel.SPEECH.value,
            mandatory=True,
        ),
        say(
            "st.persona.disclosure",
            "brief.rights.disclosure",
            StatementKind.CANON.value,
            "synthetic movement is disclosed wherever the spot runs",
            PERSONA_BRIEF,
            origin=IntentOrigin.DERIVED.value,
            ancestors=("st.persona.identity",),
        ),
    ),
    (PERSONA_BRIEF,),
    (
        rule(
            "cn.persona.identity",
            "brief.identity.persona",
            "keeps_identity",
            channels=(ModalChannel.VIDEO.value,),
            mandatory=True,
            protected_anchors=(pin("an.persona.face", "brief.identity.persona", "IDENTITY", statements=("st.persona.identity",)),),
        ),
        rule(
            "cn.persona.voice",
            "brief.speech.persona",
            "matches_voice",
            channels=(ModalChannel.SPEECH.value,),
            mandatory=True,
            cross_modal_links=(
                CrossModalLink(
                    link_id="link.persona.identity",
                    channels=(ModalChannel.SPEECH.value, ModalChannel.VIDEO.value),
                    semantic_paths=("brief.speech.persona", "brief.identity.persona"),
                    consistency="STRICT",
                    reference_channel=ModalChannel.SPEECH.value,
                ),
            ),
        ),
        rule(
            "cn.persona.undeclared-synthesis",
            "brief.rights.disclosure",
            "discloses_synthesis",
            polarity=ConstraintPolarity.FORBID.value,
            strength=ConstraintStrength.GUARDED.value,
            channels=(ModalChannel.VIDEO.value, ModalChannel.SPEECH.value),
        ),
    ),
    (ModalChannel.VIDEO.value, ModalChannel.SPEECH.value, ModalChannel.BRAND.value),
    ("brief.identity.persona", "brief.speech.persona", "brief.video.persona"),
    zones=(freedom("zone.persona.wardrobe", "Wardrobe and set dressing rotate per campaign", ("brief.visual.wardrobe",), ("brief.identity.persona",)),),
    questions=(
        ask(
            "q.persona.consent",
            "Does the talent's licence cover derivative synthetic movement for this territory?",
            ("brief.rights.disclosure",),
            blocking=True,
        ),
    ),
    predicates=("keeps_identity", "matches_voice", "discloses_synthesis"),
)


# --- 6. voice / narration / music -------------------------------------------

AUDIO_BRIEF = source("src.audio.brief")

AUDIO_PROFILE = build(
    "voice-narration-music",
    "Narration and bed for an explainer",
    (
        say(
            "st.audio.script",
            "brief.speech.narration",
            StatementKind.CONSTRAINT_SEMANTICS.value,
            "the read follows the approved script word for word",
            AUDIO_BRIEF,
            modality=ModalChannel.SPEECH.value,
            mandatory=True,
        ),
        say(
            "st.audio.bed",
            "brief.music.bed",
            StatementKind.DIRECTION.value,
            "the bed is instrumental and stays behind the voice",
            AUDIO_BRIEF,
        ),
        say(
            "st.audio.length",
            "brief.speech.length",
            StatementKind.TEMPORAL.value,
            "the read finishes inside the picture's thirty seconds",
            AUDIO_BRIEF,
            origin=IntentOrigin.DERIVED.value,
            ancestors=("st.audio.script",),
        ),
    ),
    (AUDIO_BRIEF,),
    (
        rule(
            "cn.audio.script",
            "brief.speech.narration",
            "follows_script",
            channels=(ModalChannel.SPEECH.value,),
            mandatory=True,
            protected_anchors=(pin("an.audio.script", "brief.speech.narration", "VOICE", statements=("st.audio.script",)),),
        ),
        rule(
            "cn.audio.no-lyrics",
            "brief.music.bed",
            "stays_behind_voice",
            polarity=ConstraintPolarity.FORBID.value,
            channels=(ModalChannel.MUSIC.value,),
        ),
        rule(
            "cn.audio.runtime",
            "brief.speech.length",
            "fits_runtime",
            channels=(ModalChannel.SPEECH.value,),
            tolerances=(measure("audio.duration", "LTE", unit="S", target=30.0),),
        ),
    ),
    (ModalChannel.SPEECH.value, ModalChannel.MUSIC.value, ModalChannel.TEXT.value),
    ("brief.speech.narration", "brief.music.bed"),
    zones=(freedom("zone.audio.arrangement", "Arrangement and instrumentation are the composer's", ("brief.music.arrangement",), ("brief.music.bed",)),),
    questions=(ask("q.audio.reader", "Has a reader been cast, or is the voice still open?", ("brief.speech.narration",)),),
    predicates=("follows_script", "stays_behind_voice", "fits_runtime"),
)


BRIEFS: tuple[BriefProfile, ...] = (
    LOGO_PROFILE,
    PHOTO_PROFILE,
    ASSET_PROFILE,
    FILM_PROFILE,
    PERSONA_PROFILE,
    AUDIO_PROFILE,
)

PROFILES: Mapping[str, BriefProfile] = {item.profile_id: item for item in BRIEFS}


def profile_for(name: str) -> BriefProfile:
    """Look a profile up by short name, with or without its ``profile.`` prefix."""

    key = name.split(".", 1)[1] if name.startswith("profile.") else name
    try:
        return PROFILES[key]
    except KeyError as error:
        raise KeyError(f"unknown synthetic brief {name!r}; choose from {sorted(PROFILES)}") from error


def profiles_by_channel(channel: str) -> tuple[BriefProfile, ...]:
    """Every profile that speaks through one channel, which is how a consumer checks coverage."""

    label = channel.strip().upper()
    return tuple(item for item in BRIEFS if label in item.channels)


def readiness_inputs(profile: BriefProfile, fingerprint_item: Any) -> dict[str, Any]:
    """The seven §28 families, each fed by the record that actually owns its answer.

    A report is only as good as the families it assessed, and ``ready`` refuses to be true while
    one is missing, so this has to build the real inputs rather than omit them: the artifact's
    declared dependencies, the upstream state observed for them, and the reuse decision a compiled
    contract set would be carried over on.
    """

    dependencies = (
        DerivedIntentDependency(
            dependency_id=f"dep.{profile.profile_id}.source",
            derived_ref=fingerprint_item.model_ref,
            derived_kind=DerivedArtifactKind.CONTRACT_SET.value,
            upstream_ref=profile.revision.sources[0].source_ref,
            dimension=FreshnessDimension.SOURCE_REVISION.value,
            invalidates=FreshnessDimension.SOURCE_REVISION.staleness_scope.value,
            match_on=("DIGEST",),
            last_known_digest=profile.revision.sources[0].content_digest,
            valid_through_revision=profile.revision.revision_number,
            partial=True,
            affected_paths=profile.paths[:1],
            rationale="the contract set was compiled from the preserved brief text",
        ),
        DerivedIntentDependency(
            dependency_id=f"dep.{profile.profile_id}.model",
            derived_ref=fingerprint_item.model_ref,
            derived_kind=DerivedArtifactKind.CONTRACT_SET.value,
            upstream_ref=fingerprint_item.model_ref,
            dimension=FreshnessDimension.SEMANTIC_MODEL.value,
            invalidates=FreshnessDimension.SEMANTIC_MODEL.staleness_scope.value,
            match_on=("DIGEST",),
            last_known_digest=fingerprint_item.semantic_digest,
            valid_through_revision=profile.revision.revision_number,
            partial=True,
            affected_paths=profile.paths[:1],
            rationale="the contract set carries the intent model it was sliced from",
        ),
    )
    observed = {
        item.upstream_ref.text: {"digest": item.last_known_digest} for item in dependencies
    }
    vector = assess_freshness(
        vector_id=f"fv.{profile.profile_id}",
        brief_ref=profile.revision.brief_ref,
        revision_ref=profile.revision.revision_ref,
        subject_ref=fingerprint_item.model_ref,
        dependencies=dependencies,
        upstream=observed,
        revision_ordinal=profile.revision.revision_number,
    )
    passport = passport_for(
        fingerprint_item,
        passport_id=f"pp.{profile.profile_id}",
        brief_ref=profile.revision.brief_ref,
        revision_ref=profile.revision.revision_ref,
        dependencies=dependencies,
        rationale="the compiled contract set, and the two inputs its reuse turns on",
    )
    assessment = evaluate_reuse(
        passport,
        assessment_id=f"ra.{profile.profile_id}",
        vector_id=f"rv.{profile.profile_id}",
        semantic_digest=fingerprint_item.semantic_digest,
        profile_ref=fingerprint_item.profile_ref,
        upstream=observed,
        revision_ordinal=profile.revision.revision_number,
    )
    return {
        "ledger": OverrideLedger(
            ledger_id=f"ledger.{profile.profile_id}",
            brief_ref=profile.revision.brief_ref,
            revision_ref=profile.revision.revision_ref,
        ),
        "dependencies": dependencies,
        "freshness": vector,
        "assessments": (assessment,),
    }


def audit_slice(profile: BriefProfile) -> MinimumSufficientSemanticSlice:
    """The same closure asked for a different reason: provenance in, rules out.

    Two purposes over one profile is the cheapest proof that the slice follows the request rather
    than the domain: every profile answers both, and nothing here reads a profile id.
    """

    return slice_intent(
        profile.model,
        profile.bundle,
        SemanticSliceRequest(
            request_id=f"audit.{profile.profile_id}",
            consumer_ref=ref(RefKind.PROVENANCE.value, f"audit.{profile.profile_id}"),
            purpose="AUDIT",
            paths=profile.paths[:1],
            revision_ref=profile.revision.revision_ref,
        ),
    )


def run_kernel(profile: BriefProfile) -> dict[str, Any]:
    """Push one profile through the calls every profile must survive, and return the artifacts.

    A single function with no ``if profile_id ==`` branch is the point: six domains, one code path,
    and whatever the kernel produces is what a test or a document can cite.
    """

    request = SemanticSliceRequest(
        request_id=f"req.{profile.profile_id}",
        consumer_ref=ref(RefKind.CONTRACT_SET.value, f"contracts.{profile.profile_id}"),
        purpose="COMPILE_QUALITY",
        paths=profile.paths[:1],
        revision_ref=profile.revision.revision_ref,
        # The same consumer context for all six domains: one cut of the deliverable. A conditional
        # rule binds here and a conditional rule elsewhere stays out of the slice, which is the
        # only way this table can show that conditionality is real rather than decorative.
        context={"cut.count": "1"},
    )
    fingerprint_item = fingerprint_revision(profile.revision)
    conflicts = detect_conflicts(
        bundle=profile.bundle,
        revision_ref=profile.revision.revision_ref,
        rule_classes={
            item.constraint_id: f"{profile.profile_id}.rule" for item in profile.bundle.constraints
        },
        conflict_prefix=f"cnf.{profile.profile_id}",
    )
    return {
        "slice": slice_intent(profile.model, profile.bundle, request),
        "fingerprint": fingerprint_item,
        "conflicts": conflicts,
        "readiness": assess_release_readiness(
            report_id=f"rr.{profile.profile_id}",
            revision=profile.revision,
            conflicts=conflicts,
            questions=profile.questions,
            **readiness_inputs(profile, fingerprint_item),
        ),
    }


if __name__ == "__main__":  # pragma: no cover - a readable dump for whoever checks this by hand
    for item in BRIEFS:
        artifacts = run_kernel(item)
        report = artifacts["readiness"]
        print(
            f"{item.profile_id:30s} channels={','.join(item.channels):34s} "
            f"statements={len(item.revision.statements)} constraints={len(item.bundle.constraints)} "
            f"slice={len(artifacts['slice'].statement_ids)}/{len(artifacts['slice'].constraints)} "
            f"conflicts={len(artifacts['conflicts'])} "
            f"families={len(report.assessed_families)} ready={report.ready} "
            f"blockers={list(report.blocking_families)} "
            f"digest={artifacts['fingerprint'].semantic_digest[:12]}"
        )
