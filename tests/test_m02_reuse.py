"""Area D reuse semantics: cache layers, keys, the poisoning shield and quarantine.

These are the tests for the frozen contract in
planning/modules/M02-PROJECT-OS-PRODUCTION-GRAPH.md sections 8 to 12. The shape of
every test is the same: state what a hit is allowed to mean, then try to take more
than that and require a refusal that names itself.
"""

from __future__ import annotations

import unittest

from tests import m02_kernel_support as k
from iris_project_os.build import BuildState, BuildStep, WorkDisposition
from iris_project_os.errors import BuildError, SchemaValidationError
from iris_project_os.identity import EntityKind, ExternalRef
from iris_project_os.reuse import (
    CACHE_KEY_SCHEMA,
    CacheCheck,
    CacheEntry,
    CacheKey,
    CacheLayer,
    CacheTrust,
    CompatibilityKind,
    CompatibilityRef,
    ContextFingerprint,
    ContextSource,
    OriginClass,
    PoisonCheck,
    Qualification,
    QuarantineLedger,
    QuarantineRule,
    ReuseClass,
    ReuseReceipt,
    ReuseRejection,
    admit_reuse,
    evict,
    eviction_rank,
)
from iris_project_os.snapshots import RetentionReason
from iris_project_os.versions import ComponentVersion, canonical_json, content_digest
from iris_quality.contracts import QualityClass

PRODUCER = k.CACHE_PRODUCER
EVALUATOR = k.CACHE_EVALUATOR
NOW = k.CACHE_NOW


class CacheLayerVocabulary(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = k.bound()

    def test_six_layers_are_named_and_ordered_by_trust(self) -> None:
        self.assertEqual(
            [(layer.label, layer.value) for layer in CacheLayer],
            [
                ("L0", "PLANNING"),
                ("L1", "CONTEXT"),
                ("L2", "WARM_STATE"),
                ("L3", "INTERMEDIATE"),
                ("L4", "FINAL"),
                ("L5", "EVIDENCE"),
            ],
        )
        warm = CacheLayer.WARM_STATE
        self.assertTrue(warm.is_ephemeral)
        self.assertFalse(warm.may_satisfy_a_production_output)
        self.assertFalse(warm.requires_receipt)
        self.assertTrue(CacheLayer.FINAL.may_satisfy_a_production_output)
        self.assertTrue(CacheLayer.EVIDENCE.requires_receipt)

    def test_a_layer_only_admits_the_classes_that_mean_the_same_thing_on_it(self) -> None:
        for layer in CacheLayer:
            for claimed in ReuseClass:
                if claimed in layer.admits_classes:
                    continue
                with self.subTest(layer=layer.label, claimed=claimed.value):
                    with self.assertRaises(BuildError):
                        k.cache_entry(self.graph, "render.logo", layer=layer, reuse_class=claimed, observed_digest=None)

    def test_warm_state_holds_no_result_and_no_quality_claim(self) -> None:
        with self.assertRaises(BuildError):
            k.cache_entry(
                self.graph, "render.logo", layer=CacheLayer.WARM_STATE, reuse_class=ReuseClass.WARM_REUSE
            )
        warm = k.cache_entry(
            self.graph,
            "render.logo",
            layer=CacheLayer.WARM_STATE,
            reuse_class=ReuseClass.WARM_REUSE,
            observed_digest=None,
            quality_class=None,
        )
        self.assertIsNone(warm.observed_digest)
        self.assertIsNone(warm.quality_class)

    def test_a_result_layer_must_point_at_bytes_and_evidence_at_an_evaluator(self) -> None:
        with self.assertRaises(BuildError):
            k.cache_entry(self.graph, "render.logo", observed_digest=None)
        with self.assertRaises(BuildError):
            k.cache_entry(
                self.graph, "render.logo", layer=CacheLayer.EVIDENCE, reuse_class=ReuseClass.QUALIFIED_REUSE, evaluator=None
            )


class ContextAndKeyAxes(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = k.bound()
        self.context = k.cache_context()

    def test_the_context_fingerprint_is_computed_from_its_parts(self) -> None:
        self.assertEqual(self.context.components, tuple(sorted(self.context.components, key=lambda i: i.text)))
        forged = {**self.context.to_payload(), "fingerprint": k.digest("forged")}
        with self.assertRaises(SchemaValidationError):
            ContextFingerprint(**forged)
        asserted = {**self.context.to_payload(), "components": [self.context.components[0].to_payload()]}
        with self.assertRaises(SchemaValidationError):
            ContextFingerprint(**asserted)

    def test_a_different_model_is_a_different_context_not_a_different_result(self) -> None:
        moved = k.cache_context(model=ComponentVersion("provider.model", "2026-02"))
        self.assertNotEqual(self.context.fingerprint, moved.fingerprint)
        self.assertEqual(self.context.compatibility_digest, moved.compatibility_digest)
        self.assertTrue(self.context.differs_from(moved))

    def test_two_sources_cannot_claim_the_same_ordinal(self) -> None:
        with self.assertRaises(SchemaValidationError):
            k.cache_context(
                sources=(
                    ContextSource(ref=ExternalRef(EntityKind.HIVE_CONTEXT, "brief.front"), ordinal=0),
                    ContextSource(ref=ExternalRef(EntityKind.HIVE_CONTEXT, "brief.style"), ordinal=0),
                )
            )

    def test_a_key_addresses_the_whole_claim_and_reports_what_moved(self) -> None:
        built = k.reuse_request(self.graph, "render.logo").key
        self.assertTrue(built.schema_matches(CACHE_KEY_SCHEMA))
        self.assertFalse(built.schema_matches("iris-cache-key-v0"))
        self.assertIs(built.external_ref.kind, EntityKind.CACHE_KEY)
        other = k.CacheKey.of(
            "render.logo",
            build_fingerprint=k.digest("another-build"),
            context=self.context,
            layer=CacheLayer.FINAL,
        )
        self.assertNotEqual(built.address, other.address)
        moved = built.differs_from(other)
        self.assertEqual(len(moved), 2, moved)

    def test_a_key_refuses_axes_it_never_declared(self) -> None:
        built = k.reuse_request(self.graph, "render.logo").key
        with self.assertRaises(SchemaValidationError):
            CacheKey.from_payload({**built.to_payload(), "unknown_axis": 1})
        with self.assertRaises(SchemaValidationError):
            CacheKey.from_payload({name: value for name, value in built.to_payload().items() if name != "layer"})

    def test_an_entry_rehashes_its_own_closure(self) -> None:
        entry = k.cache_entry(self.graph, "render.logo")
        self.assertEqual(entry.closure_digest, content_digest(list(entry.dependency_closure)))
        with self.assertRaises(BuildError):
            k.cache_entry(self.graph, "render.logo", closure_digest=k.digest("claimed-complete"))


class PoisoningShield(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = k.bound()

    @staticmethod
    def with_key(entry, **over):
        payload = entry.to_payload()
        payload["key"] = {**payload["key"], **over}
        return CacheEntry.from_payload(payload)

    def admit(self, entry, request=None, **over):
        outcome = admit_reuse(entry, request or k.reuse_request(self.graph, "render.logo"), trust=k.cache_trust(), **over)
        return outcome

    def test_admission_is_explained_and_rebuilds_itself(self) -> None:
        granted = self.admit(k.cache_entry(self.graph, "render.logo"))
        self.assertIsInstance(granted, ReuseReceipt)
        self.assertIs(granted.reuse_class, ReuseClass.EXACT_REUSE)
        self.assertTrue(granted.is_exact and granted.satisfies_output)
        self.assertTrue(granted.satisfies("render.logo", granted.result_digest))
        self.assertFalse(granted.satisfies("deliver.web", granted.result_digest))
        self.assertGreater(len(granted.reason), 20)
        self.assertEqual(granted.environment_verdict, "IDENTICAL")
        self.assertIs(granted.trust_rule.kind, EntityKind.POLICY)
        self.assertEqual(ReuseReceipt.from_payload(granted.to_payload()).digest(), granted.digest())

    def test_a_receipt_that_claims_bytes_it_did_not_admit_is_refused(self) -> None:
        entry = k.cache_entry(self.graph, "render.logo")
        with self.assertRaises(BuildError):
            ReuseReceipt(
                **{
                    **self.admit(entry).to_payload(),
                    "observed_digest": k.digest("other-bytes"),
                }
            )

    def test_an_admission_with_no_reason_is_not_an_admission(self) -> None:
        payload = self.admit(k.cache_entry(self.graph, "render.logo")).to_payload()
        with self.assertRaises(BuildError):
            ReuseReceipt(**{**payload, "reason": "   "})

    def test_every_shield_question_refuses_on_its_own(self) -> None:
        request = k.reuse_request(self.graph, "render.logo")
        cleared = k.reuse_request(
            self.graph,
            "render.logo",
            rights_digest=k.digest("rights.granted"),
            provenance_digest=k.digest("provenance.owned"),
        )
        cases = (
            (
                PoisonCheck.PRODUCER_ADMISSION,
                k.cache_entry(self.graph, "render.logo", producer=ComponentVersion("m02.render", "9.9.9")),
                request,
            ),
            (
                PoisonCheck.KEY_SCHEMA,
                self.with_key(k.cache_entry(self.graph, "render.logo"), schema_version="iris-cache-key-v0"),
                request,
            ),
            (PoisonCheck.KEY_SCHEMA, k.cache_entry(self.graph, "render.logo", layer=CacheLayer.FINAL), request),
            (
                PoisonCheck.DIGEST_VERIFICATION,
                k.cache_entry(self.graph, "render.logo", observed_digest=k.digest("stored-something-else")),
                request,
            ),
            (
                PoisonCheck.CLOSURE_COMPLETENESS,
                self.with_key(
                    k.cache_entry(self.graph, "render.logo"),
                    build_fingerprint=k.digest("another-build"),
                ),
                request,
            ),
            (
                PoisonCheck.QUALIFICATION_EXPIRY,
                k.cache_entry(self.graph, "render.logo", qualification=k.cache_qualification(expires_at_ms=NOW)),
                request,
            ),
            (
                PoisonCheck.QUALIFICATION_EXPIRY,
                k.cache_entry(self.graph, "render.logo", qualification=Qualification(refs=())),
                request,
            ),
            (
                PoisonCheck.RIGHTS_PROVENANCE_DRIFT,
                k.cache_entry(self.graph, "render.logo", rights_digest=k.digest("rights.revoked")),
                cleared,
            ),
            (
                PoisonCheck.RIGHTS_PROVENANCE_DRIFT,
                k.cache_entry(
                    self.graph,
                    "render.logo",
                    rights_digest=k.digest("rights.granted"),
                    provenance_digest=None,
                ),
                cleared,
            ),
            (
                PoisonCheck.EVIDENCE_QUALIFICATION,
                k.cache_entry(self.graph, "render.logo", quality_class=QualityClass.REVIEW),
                k.reuse_request(self.graph, "render.logo", required_quality_class=QualityClass.MASTER),
            ),
            (
                PoisonCheck.EVIDENCE_QUALIFICATION,
                k.cache_entry(self.graph, "render.logo", evaluator=ComponentVersion("m02.judge", "1.0.0")),
                k.reuse_request(
                    self.graph,
                    "render.logo",
                    required_quality_class=QualityClass.MASTER,
                    qualified_evaluators=(ComponentVersion("m02.judge", "9.9.9"),),
                ),
            ),
            (
                PoisonCheck.WRITE_TRUST,
                k.cache_entry(self.graph, "render.logo", writer_origin=OriginClass.LOCAL_EXPERIMENT),
                request,
            ),
            (PoisonCheck.CROSS_PROJECT_IDENTITY, k.cache_entry(self.graph, "render.logo", project_id="other"), request),
            (
                PoisonCheck.PRODUCER_ADMISSION,
                k.cache_entry(self.graph, "render.logo", reuse_class=ReuseClass.NO_REUSE),
                request,
            ),
        )
        self.assertEqual({check for check, _, _ in cases}, set(PoisonCheck), "every question has a case")
        for wanted, entry, wanted_request in cases:
            with self.subTest(check=wanted.value):
                outcome = self.admit(entry, wanted_request)
                self.assertIsInstance(outcome, ReuseRejection, f"{wanted.value} was admitted: {outcome}")
                self.assertIn(wanted, outcome.refused_by, outcome.text)
                self.assertEqual(len(outcome.checks), len(PoisonCheck))
                refused = [check for check in outcome.checks if not check.passed]
                self.assertTrue(any(check.name is wanted for check in refused))

    def test_a_hit_may_not_be_taken_across_layers(self) -> None:
        final = k.cache_entry(self.graph, "render.logo", layer=CacheLayer.FINAL)
        outcome = self.admit(final, k.reuse_request(self.graph, "render.logo"))
        self.assertIsInstance(outcome, ReuseRejection)
        self.assertIn(PoisonCheck.KEY_SCHEMA, outcome.refused_by)
        self.assertTrue(any("layer" in check.detail for check in outcome.checks if not check.passed))

    def test_a_hit_may_not_be_taken_from_a_different_build_fingerprint(self) -> None:
        stale = k.cache_entry(self.graph, "render.logo")
        moved = k.reuse_request(self.graph, "render.logo")
        payload = stale.to_payload()
        payload["key"] = {
            **payload["key"],
            "build_fingerprint": k.digest("the-node-built-from-other-bytes"),
        }
        poisoned = CacheEntry.from_payload(payload)
        outcome = self.admit(poisoned, moved)
        self.assertIsInstance(outcome, ReuseRejection)
        self.assertIn(PoisonCheck.CLOSURE_COMPLETENESS, outcome.refused_by)
        self.assertIn(PoisonCheck.KEY_SCHEMA, outcome.refused_by)

    def test_no_reuse_is_refused_as_a_producer_declaration(self) -> None:
        refused = k.cache_entry(self.graph, "render.logo", reuse_class=ReuseClass.NO_REUSE)
        outcome = self.admit(refused)
        self.assertIsInstance(outcome, ReuseRejection)
        self.assertIn(PoisonCheck.PRODUCER_ADMISSION, outcome.refused_by)

    def test_a_partial_hit_never_finishes_a_node(self) -> None:
        partial = k.cache_entry(self.graph, "render.logo", reuse_class=ReuseClass.PARTIAL_REUSE)
        granted = self.admit(partial)
        self.assertIsInstance(granted, ReuseReceipt)
        self.assertFalse(granted.satisfies_output)
        with self.assertRaises(BuildError):
            BuildStep(
                node_id="render.logo",
                state=BuildState.CACHED_ELIGIBLE,
                disposition=WorkDisposition.REUSE,
                reasons=("a partial hit was counted as the whole answer",),
                key=granted.key,
                receipt=granted,
            )

    def test_a_refusal_answers_all_nine_questions(self) -> None:
        outcome = self.admit(k.cache_entry(self.graph, "render.logo", project_id="other"))
        self.assertIsInstance(outcome, ReuseRejection)
        self.assertEqual({check.name for check in outcome.checks}, set(PoisonCheck))
        for check in outcome.checks:
            with self.subTest(check=check.name.value):
                self.assertIsInstance(check, CacheCheck)
                self.assertTrue(check.detail.strip())


class TrustAndClearance(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = k.bound()

    def test_read_trust_is_not_write_trust(self) -> None:
        policy = CacheTrust(
            allowed_producers=(PRODUCER,),
            readers=(OriginClass.LOCAL_EXPERIMENT, OriginClass.TRUSTED_WORKER),
        )
        self.assertTrue(policy.may_read(OriginClass.LOCAL_EXPERIMENT))
        self.assertFalse(policy.may_write(OriginClass.LOCAL_EXPERIMENT))
        experiment = k.cache_entry(self.graph, "render.logo", writer_origin=OriginClass.LOCAL_EXPERIMENT)
        outcome = admit_reuse(experiment, k.reuse_request(self.graph, "render.logo"), trust=policy)
        self.assertIsInstance(outcome, ReuseRejection)
        self.assertIn(PoisonCheck.WRITE_TRUST, outcome.refused_by)
        self.assertNotIn(PoisonCheck.PRODUCER_ADMISSION, outcome.refused_by)

    def test_cross_project_needs_a_rights_grant(self) -> None:
        foreign = k.cache_entry(self.graph, "render.logo", project_id="other")
        request = k.reuse_request(self.graph, "render.logo")
        refused = admit_reuse(foreign, request, trust=k.cache_trust())
        self.assertIsInstance(refused, ReuseRejection)
        self.assertIn(PoisonCheck.CROSS_PROJECT_IDENTITY, refused.refused_by)
        permissive = CacheTrust(allowed_producers=(PRODUCER,), allow_cross_project=True)
        cleared = admit_reuse(
            foreign,
            request,
            trust=permissive,
            rights_grant_ref=ExternalRef(EntityKind.RIGHTS, "grant.cross"),
        )
        self.assertIsInstance(cleared, ReuseReceipt, cleared.reason)

    def test_protected_identity_needs_its_own_clearance(self) -> None:
        permissive = CacheTrust(allowed_producers=(PRODUCER,), allow_cross_project=True)
        face = k.cache_entry(
            self.graph, "render.logo", project_id="other", identity_refs=(ExternalRef(EntityKind.PROVENANCE, "person.42"),)
        )
        request = k.reuse_request(self.graph, "render.logo", protected_identity=True)
        grant = ExternalRef(EntityKind.RIGHTS, "grant.cross")
        refused = admit_reuse(face, request, trust=permissive, rights_grant_ref=grant)
        self.assertIsInstance(refused, ReuseRejection)
        self.assertIn(PoisonCheck.CROSS_PROJECT_IDENTITY, refused.refused_by)
        cleared = admit_reuse(
            face,
            request,
            trust=permissive,
            rights_grant_ref=grant,
            identity_clearance_ref=ExternalRef(EntityKind.POLICY, "clearance.persona"),
        )
        self.assertIsInstance(cleared, ReuseReceipt, cleared.reason)


class EvidenceAuthority(unittest.TestCase):
    """M01 owns the quality ladder; a cache entry may not re-score it."""

    def setUp(self) -> None:
        self.graph = k.bound()

    def ladder(self, cached, required):
        return admit_reuse(
            k.cache_entry(self.graph, "render.logo", quality_class=cached, evaluator=EVALUATOR),
            k.reuse_request(
                self.graph,
                "render.logo",
                required_quality_class=required,
                qualified_evaluators=(EVALUATOR,),
            ),
            trust=k.cache_trust(),
        )

    def test_a_lower_class_never_satisfies_a_higher_gate(self) -> None:
        for required, cached, admitted in (
            (QualityClass.MASTER, QualityClass.MASTER, True),
            (QualityClass.ARCHIVAL_MASTER, QualityClass.MASTER, False),
            (QualityClass.PREVIEW, QualityClass.MASTER, True),
        ):
            with self.subTest(required=required.value, cached=cached.value):
                outcome = self.ladder(cached, required)
                refused = PoisonCheck.EVIDENCE_QUALIFICATION in getattr(outcome, "refused_by", ())
                self.assertEqual(not refused, admitted)

    def test_a_class_without_an_evaluator_backing_it_is_not_evidence(self) -> None:
        outcome = admit_reuse(
            k.cache_entry(self.graph, "render.logo", quality_class=QualityClass.MASTER, evaluator=None),
            k.reuse_request(
                self.graph,
                "render.logo",
                required_quality_class=QualityClass.MASTER,
                qualified_evaluators=(EVALUATOR,),
            ),
            trust=k.cache_trust(),
        )
        self.assertIsInstance(outcome, ReuseRejection)
        self.assertIn(PoisonCheck.EVIDENCE_QUALIFICATION, outcome.refused_by)

    def test_an_invented_quality_class_is_a_schema_error_not_a_refusal(self) -> None:
        with self.assertRaises(SchemaValidationError):
            k.cache_entry(self.graph, "render.logo", quality_class="GOOD_ENOUGH")


class QuarantineAndEviction(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = k.bound()

    def test_a_quarantine_rule_blocks_the_entry_it_named(self) -> None:
        entry = k.cache_entry(self.graph, "render.logo")
        ledger = QuarantineLedger(
            rules=(QuarantineRule(rule_id=k.new_id(), value=entry.key.address, scope="key", reason="poisoned"),),
            now_ms=NOW,
        )
        self.assertTrue(ledger.blocking(entry))
        outcome = admit_reuse(entry, k.reuse_request(self.graph, "render.logo"), trust=k.cache_trust(), quarantine=ledger)
        self.assertIsInstance(outcome, ReuseRejection)
        self.assertIn(PoisonCheck.PRODUCER_ADMISSION, outcome.refused_by)

    def test_a_rule_widened_from_an_entry_blocks_its_producer_too(self) -> None:
        entry = k.cache_entry(self.graph, "render.logo")
        widened = QuarantineLedger(rules=(), now_ms=NOW).widened(entry, "poisoned by a stale closure")
        self.assertTrue(widened.blocking(entry))
        self.assertTrue(
            any(rule.scope != "key" for rule in widened.rules),
            [rule.scope for rule in widened.rules],
        )
        other_node = k.cache_entry(self.graph, "deliver.web")
        blocked = admit_reuse(
            other_node,
            k.reuse_request(self.graph, "deliver.web"),
            trust=k.cache_trust(),
            quarantine=widened,
        )
        self.assertIsInstance(blocked, ReuseRejection, "the same producer wrote both entries")

    def test_expired_rules_stop_blocking_once_the_clock_passes_them(self) -> None:
        entry = k.cache_entry(self.graph, "render.logo")
        ledger = QuarantineLedger(
            rules=(
                QuarantineRule(
                    rule_id=k.new_id(),
                    value=entry.key.address,
                    scope="key",
                    expires_at_ms=NOW + 10,
                    reason="under review",
                ),
            ),
            now_ms=NOW,
        )
        self.assertTrue(ledger.blocking(entry))
        self.assertFalse(ledger.advanced(NOW + 11).blocking(entry))

    def test_eviction_drops_the_cheapest_first_and_never_the_protected(self) -> None:
        warm = k.cache_entry(
            self.graph,
            "render.logo",
            layer=CacheLayer.WARM_STATE,
            reuse_class=ReuseClass.WARM_REUSE,
            observed_digest=None,
            quality_class=None,
        )
        final = k.cache_entry(self.graph, "deliver.web", layer=CacheLayer.FINAL)
        protected = k.cache_entry(self.graph, "render.logo", retained_for=(RetentionReason.RIGHTS_OR_PROVENANCE_REQUIRED,))
        self.assertEqual(eviction_rank(protected), -1)
        self.assertLess(eviction_rank(warm), eviction_rank(final))
        dropped = evict((warm, final, protected), keep=1)
        self.assertNotIn(protected.entry_id, [item.entry_id for item in dropped])
        self.assertEqual(len(dropped), 1)


class SerializationDiscipline(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = k.bound()

    def test_every_reuse_record_round_trips_and_stays_immutable(self) -> None:
        receipt = k.admitted_receipt(self.graph, "render.logo")
        entry = k.cache_entry(self.graph, "render.logo")
        rejection = admit_reuse(
            k.cache_entry(self.graph, "render.logo", project_id="other"),
            k.reuse_request(self.graph, "render.logo"),
            trust=k.cache_trust(),
        )
        for record in (
            k.cache_context(),
            entry.key,
            entry,
            k.reuse_request(self.graph, "render.logo"),
            receipt,
            rejection,
            CacheTrust(allowed_producers=(PRODUCER,)),
            CompatibilityRef(kind=CompatibilityKind.PROVIDER, provider_id="p", opaque_digest=k.digest("p")),
        ):
            with self.subTest(record=type(record).__name__):
                payload = record.to_payload()
                rebuilt = type(record).from_payload(payload)
                self.assertEqual(rebuilt, record)
                self.assertEqual(canonical_json(rebuilt.to_payload()), canonical_json(payload))
                self.assertEqual(rebuilt.digest(), record.digest())

    def test_identity_is_not_part_of_the_address_that_finds_a_hit(self) -> None:
        first = k.cache_entry(self.graph, "render.logo")
        second = k.cache_entry(self.graph, "render.logo")
        self.assertNotEqual(first.entry_id, second.entry_id)
        self.assertEqual(first.key.address, second.key.address)
        self.assertEqual(first.qualification.address, second.qualification.address)

    def test_an_entry_describes_itself_without_losing_its_axes(self) -> None:
        entry = k.cache_entry(self.graph, "render.logo")
        self.assertIn(entry.key.layer.value, entry.text)
        self.assertIn(entry.result_digest[:12], entry.text)
        self.assertIsInstance(entry.is_protected, bool)
        self.assertFalse(entry.is_protected)
        self.assertTrue(entry.dependency_closure)


if __name__ == "__main__":
    unittest.main()
