# Synthetic testing in the MNP

This document answers, with code, the question: do synthetic rules improve the sufficiency of the MNP, and are they worth it?

## The distinction that defines the answer

There are two meanings of "synthetic", with opposite risk profiles.

Synthetic cases are generated test scenarios, each submitted to both engines (Clingo and fallback) with the requirement that they agree. An incorrect synthetic case fails loudly and is reviewed. They are highly valuable, with low risk.

Synthetic rules are LLM-generated normative logic. A plausible but legally wrong rule fails silently and provides false assurance, precisely where the value of the system is verifiability. They do not improve legal sufficiency on their own, and may worsen it. They serve as a drafting accelerator, always subject to human ratification, never as a source of truth.

This module implements the first meaning, which has the highest return and does not depend on a legal expert to deliver value.

## What the generator found

The three hand-written cross-validation scenarios covered only `data_category=health` with `requires_purpose_confirmation=False`. When generating 200 varied cases and running them through both engines, 31 divergences emerged (about 15%), in paths that had never been exercised. Each divergence was a place where the two engines silently disagreed about what the norm says. Reconciliation was guided case by case until there were zero divergences across 35,000 scenarios and seven seeds.

The divergences found and resolved:

Purpose confirmation applied to any data category in the fallback, but only to sensitive data in Clingo. Reconciled: both now scope it by candidacy for sensitive processing.

The fluent `purpose_confirmed` was tied to `consent.holds` in the fallback, whereas in Clingo it is initiated by `grant_consent` and terminated only by `change_purpose`, not by `revoke_consent`. Reconciled: the fallback now mirrors the rule.

The breach rule in Clingo had no time guard and counted even future incidents (a real Event Calculus bug). The fallback used a strict window. Reconciled: both count the breach if it occurred up to `current_time`, never in the future.

Incident-based escalation existed in the fallback but not in Clingo, and the fallback prohibition branch was incorrectly restricted to `health`. Reconciled: incidents escalate in both engines, and prohibition escalates for any sensitive data.

The obligation `obl_confirm_purpose` was derived from purpose violation in Clingo but was missing in the fallback. Reconciled.

None of these would have been caught by hand-written tests without anticipating the exact failing combination. This is the canonical use case for differential testing.

## The three test families

Differential, in `tests/test_synthetic_differential.py`: the reproducible corpus goes through both engines and requires identical decisions. The compared contract is the decision (prohibition, permission, escalation, risk, violated rules, required changes, obligations, consequences) plus the consent state, which is relevant to the decision. Fluent state that is irrelevant to the decision is not part of the contract.

Metamorphic, in the same file: properties that hold without knowing the exact verdict. An event after `current_time` does not change the present decision. Removing the legal-basis requirement never makes the decision stricter. The emergency exception only relaxes. Each property runs on both engines.

On-demand report, in `scripts/divergence_report.py`: runs a large corpus and reports the divergence rate by field, for inspection after changing rules and for generating an auditable number.

## Reproducibility

The generator is deterministic given a seed. The same seed produces the same corpus, which makes the test set versionable and auditable, instead of being non-reproducible randomness. This matters in a governance system: being able to state "this specific set of N cases passed" is part of accountability.

## Open issues (pending normative decisions)

Reconciliation aligned the two engines, but two choices were made as engineering decisions and deserve ratification by a legal expert, not by a programmer.

The events `human_review_approved` and `human_review_rejected` are currently inert in both engines. Only the `human_review_override` flag grants the deviation. Treating approval as granting an override and rejection as revocation would require modeling them as a fluent in ASP (approval initiates, rejection terminates), which is a decision about how the human-review flow interacts with the norm. It is documented and consistent across engines, but still pending.

The temporal convention for breach was fixed as "occurred up to and including `current_time`". The choice between inclusive and strict at the current instant is defensible on both sides and was standardized for consistency, not because of a legal requirement.

These are exactly the kinds of issues where synthetic testing delivers its second value: beyond catching inconsistencies, it makes explicit the normative decisions that were implicit and unagreed. Each one becomes an agenda item for the legal expert, with a concrete case that illustrates it.

## Is it worth it?

For testing and validation, yes, and the return appeared immediately: the infrastructure paid for itself by finding six classes of inconsistencies between the engines and raising confidence from "it passes the three cases I remembered to write" to "it agrees across 35,000 generated scenarios". For rule generation, the verdict remains the same: it is a legitimate drafting accelerator as long as the human-ratification gate remains non-negotiable, because legal sufficiency is fidelity to the text plus accountability, and neither comes from a rule that nobody ratified.
