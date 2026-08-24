# Community Discussion Record

This file records public discussions conducted during the project and how
practitioner feedback affected the design.

A discussion being recorded here does not mean that the feedback was treated
as authoritative. Each response was considered as practitioner input and was
either incorporated, partially incorporated, recorded as future work, or left
without a design change.

| Platform | Community / Account | Link | My First Contribution | Human Answer | My Next Answer | Design Change / Takeaway |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Reddit | r/DataEngineeringPH | https://www.reddit.com/r/DataEngineeringPH/comments/1vmn9gf/when_is_a_dataquality_problem_actually_repairable/ | Asked when a data-quality problem is actually safe to repair automatically, especially for missing values, duplicates, invalid-looking values, formatting problems, and outliers. | A commenter suggested considering why data is missing, referring to MCAR, MAR, and MNAR rather than treating every missing value identically. They also suggested involving a superior when deciding whether missing data can simply be excluded. | — | **Partially accepted.** Missing values should be treated as evidence rather than automatically implying corruption. MCAR/MAR/MNAR modelling itself was left outside the Week 1 scope. |
| Reddit | r/DataEngineeringPH | https://www.reddit.com/r/DataEngineeringPH/comments/1vmn9gf/when_is_a_dataquality_problem_actually_repairable/ | Asked when a data-quality problem is actually safe to repair automatically. | Another commenter suggested being more comfortable automating structural changes such as formatting/casing and being much more cautious when changing a value could alter the underlying business meaning. | — | **Accepted.** Strengthened the distinction between `S3_FORMAT_GLITCH` and `S4_CORRUPTED`. `REPAIR` should generally mean a known, defensible transformation rather than inventing an unknown semantic value. |
| Reddit | r/SQL | https://www.reddit.com/r/SQL/comments/1vmmgdq/what_evidence_do_you_trust_most_when_deciding/ | Asked what evidence practitioners trust most when deciding whether unusual incoming data is actually bad. | No usable response. The post was removed by Reddit's filters. | — | **No design change.** Retained as an attempted research contribution, but no project claim is based on it. |
| Reddit | r/ETL | https://www.reddit.com/r/ETL/comments/1vqj4m9/when_a_batch_of_1000_transactions_has_5_bad_rows/ | Asked whether a batch containing 995 valid transactions and 5 records with missing critical fields should be held entirely or whether the valid records should continue while the problematic records are isolated. | Several responses emphasized that there is no universal answer; the decision depends on the business process, payment product, contractual requirements, reconciliation requirements, and whether records depend on one another. | — | **Accepted as a limitation.** The current cost matrix approximates business consequences, but a production decision policy would need actual domain context. |
| Reddit | r/ETL | https://www.reddit.com/r/ETL/comments/1vqj4m9/when_a_batch_of_1000_transactions_has_5_bad_rows/ | Asked whether 995 valid records should continue while 5 problematic records are held. | One practitioner said they would process what they could while repeatedly raising the bad records with the responsible developer. | I followed up by asking whether this effectively meant processing the valid records while isolating the suspicious ones for evaluation. The commenter agreed and emphasized retaining evidence that the problem had been flagged. | **Accepted as future work.** Exposed a limitation of the current `one batch → one action` model. A future version could support record-level or hierarchical triage. |
| Reddit | r/ETL | https://www.reddit.com/r/ETL/comments/1vqj4m9/when_a_batch_of_1000_transactions_has_5_bad_rows/ | Asked how to handle a mostly-valid payment batch containing a few problematic records. | A commenter emphasized investigating why financial transactions contain null values, involving finance/accounting where appropriate, and producing an error report rather than silently discarding suspicious records. | — | **Accepted conceptually.** Strengthened the meaning of `ISOLATE`: preserve suspicious data, prevent automatic downstream use, and make investigation possible. Also motivates an audit trail. |
| Reddit | r/ETL | https://www.reddit.com/r/ETL/comments/1vqj4m9/when_a_batch_of_1000_transactions_has_5_bad_rows/ | Asked whether a few invalid rows should stop an entire batch. | One practitioner described a system where known erroneous records are dropped and noted that known source-system defects can continue despite repeated tickets. | — | **Partially accepted.** Source history and known failure patterns could become useful evidence in a future version, but they are not modelled in Week 1. |
| Reddit | r/ETL | https://www.reddit.com/r/ETL/comments/1vqj4m9/when_a_batch_of_1000_transactions_has_5_bad_rows/ | Asked whether the entire batch should be held because of five bad transactions. | A commenter suggested first determining whether the records depend on one another. If they are independent, quarantining individual failures may be reasonable; if the batch must reconcile as a whole, the decision changes. They also emphasized accounting for all records rather than silently dropping failures. | — | **Accepted as future work.** The percentage of bad rows alone is insufficient. Batch atomicity, record independence, and reconciliation requirements could become policy context. |
| Reddit | r/DataEngineeringPH | https://www.reddit.com/r/DataEngineeringPH/comments/1vqj5fn/what_is_the_sneakiest_financialtransaction_data/ | Asked for examples of semantic financial-transaction corruption that can pass basic SQL constraints such as types, foreign keys, and non-null checks. | No usable comments were available when this record was prepared. | — | **No design change.** The question remains relevant, but no practitioner claim is derived from this thread. |

## Main Takeaways

The discussions did not produce a universal data-quality policy. Instead, they
exposed several assumptions in the initial design:

1. **An anomaly is evidence, not automatically a hidden state.**
   A missing value, formatting difference, or outlier can have several
   possible explanations.

2. **Repairability depends on semantics.**
   Known structural transformations are generally safer than changing an
   unknown business value.

3. **ISOLATE should preserve evidence.**
   Suspicious data should remain available for investigation rather than being
   silently discarded.

4. **Batch-level decisions are a simplification.**
   Some systems can process valid records while quarantining invalid ones,
   while other systems require the batch to remain atomic.

5. **Business context affects the policy.**
   Reconciliation requirements, downstream dependencies, payment semantics,
   source history, and business cost can change the correct action.

6. **Auditability matters.**
   A production system should retain what failed, why it failed, what action
   was taken, and what was escalated.

## Project Impact Summary

The most important effect of the community research was not adding another
hardcoded rule. It was evidence against relying on hardcoded rules alone.

The discussions supported the project's move toward:

    observed evidence
            ↓
    uncertain hidden state
            ↓
    probabilistic belief
            ↓
    cost-sensitive action

while also exposing capabilities that remain outside the Week 1 implementation,
particularly record-level triage, richer business context, source history,
sequential evidence gathering, and audit trails.
