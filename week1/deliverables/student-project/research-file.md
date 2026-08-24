# Research File — Data Quality Triage Agent

## 1. Problem Statement

The agent observes an incoming data batch and information that can be derived
from that batch, such as validation failures, formatting anomalies, missing
values, and distribution changes.

At ingestion time, the true underlying health of the batch is not directly
known. An unusual batch may be genuinely corrupted, but it may also represent
a legitimate change in the underlying data or a recoverable formatting issue.

The agent must therefore reason under uncertainty and choose one of four
actions:

- ACCEPT
- REPAIR
- ISOLATE
- REJECT

The central problem is not simply detecting whether an anomaly exists. It is
deciding what to do when the available evidence can have multiple possible
explanations and different mistakes have different costs.


## 2. Project Objective

The objective is to design, implement, and evaluate a cost-sensitive
data-quality triage agent that reasons under uncertainty.

The current implementation:

1. extracts observable evidence from an incoming batch,
2. represents the unknown data-health condition using four latent states,
3. uses an LLM to estimate how compatible the observed evidence is with each
   state,
4. applies Bayesian inference to combine those likelihood estimates with prior
   beliefs,
5. maintains a probability distribution over the possible states for the
   current decision,
6. calculates the expected cost of each available action, and
7. chooses the action with the lowest expected cost.

The project is intentionally a small experimental simulator rather than a
production data-quality platform.

The priors, cost matrix, dataset, and test cases are experimental assumptions
created for the Week 1 project. They should not be interpreted as measured
production probabilities or business costs.


## 3. Current Hidden States

The current experiment models four possible underlying states.

### S1_HEALTHY

The batch is fundamentally valid and safe.

Minor inconsistencies may exist, but they do not represent a meaningful data
quality problem.

### S2_BENIGN_DRIFT

The data is valid, but the distribution or representation has legitimately
changed.

Examples could include changes in transaction amounts, traffic patterns, or
other real-world changes that make the batch look unusual without making it
incorrect.

### S3_FORMAT_GLITCH

The underlying data is still meaningful, but its representation has changed in
a recoverable way.

Examples include:

- date-format changes,
- additional whitespace,
- casing differences,
- serialization inconsistencies.

### S4_CORRUPTED

The batch contains potentially unsafe semantic problems.

Examples include:

- impossible values,
- missing critical information,
- invalid transaction semantics,
- severe corruption that should not silently reach downstream systems.


## 4. Current Actions

### ACCEPT

Allow the batch to continue through the pipeline.

### REPAIR

Apply a known correction and continue processing.

The project currently treats this as a possible action but does not attempt
arbitrary generative correction of unknown business values.

### ISOLATE

Prevent the batch from continuing automatically and hold it for further
investigation or human review.

This is particularly useful when the evidence is ambiguous.

### REJECT

Stop the batch from proceeding because the expected risk of using it is too
high.


## 5. Technical Terms Investigated

### Core concepts

- Data Quality Assessment
- Data Profiling
- Data Validation
- Data Anomaly Detection
- Decision Making Under Uncertainty
- Bayesian Inference
- Prior Probability
- Likelihood
- Posterior Probability
- Cost-Sensitive Decision Making
- Expected Loss / Expected Cost

### Agent and action concepts

- Data Repair / Automated Data Cleaning
- Human-in-the-Loop Data Quality
- Active Sensing
- Active Learning
- Decision Policy
- Belief State

### Supporting concepts

- Data Quality Rules
- Schema Validation
- Statistical Distribution Shift
- Data Drift
- Out-of-Distribution Detection
- Data Contracts
- Data Observability
- Dead-Letter / Quarantine Patterns

### Concepts considered but not fully implemented

- POMDPs (Partially Observable Markov Decision Processes)
- Information-gain-based evidence gathering
- Sequential evidence acquisition
- Learned/calibrated likelihood models

These concepts are relevant to the broader problem, but the current Week 1
implementation should not be described as a complete POMDP or active-learning
system.


## 6. Initial Search Questions

The research started with broad questions about what makes a data batch
healthy or problematic.

### Understanding the data

- What is data quality?
- What structure does incoming data have?
- What schemas and constraints normally exist?
- What relationships or dependencies can exist between fields?
- How do validation requirements differ between different types of data
  systems?

### Detecting quality problems

- What dimensions or metrics determine whether data is healthy?
- What characteristics indicate good data quality?
- What characteristics indicate a potential quality issue?
- Which issues are serious enough to reject?
- Which issues can potentially be repaired?

### Changes in incoming data

- What kinds of changes can occur in an incoming batch?
- Which changes represent real-world drift rather than errors?
- Which operations or transformations are inherently risky?
- How can a system distinguish a representation change from semantic
  corruption?

### Operational response

- What should happen when a data-quality problem is detected?
- When should a pipeline continue?
- When should data be repaired?
- When should data be quarantined?
- When should processing stop completely?


## 7. Reddit Communities Investigated

The following communities were identified while looking for practitioners who
work with data pipelines, validation, databases, ML systems, and production
engineering.

### r/dataengineering

https://www.reddit.com/r/dataengineering/

Primary community considered for production data engineering, ETL/ELT,
pipeline reliability, and data-quality checks.

### r/datascience

https://www.reddit.com/r/datascience/

Relevant for understanding downstream consequences of poor-quality data.

### r/ETL

https://www.reddit.com/r/ETL/

Relevant to ingestion pipelines, batch failures, partial failures, and
remediation strategies.

### r/SQL

https://www.reddit.com/r/SQL/

Considered for database constraints, validation, and practical data issues.

### r/database

https://www.reddit.com/r/database/

Relevant to integrity constraints, schemas, and database correctness.

### r/MachineLearning

https://www.reddit.com/r/MachineLearning/

Relevant to data drift, ML-data validation, distribution changes, and
production ML systems.

### r/learnmachinelearning

https://www.reddit.com/r/learnmachinelearning/

Explored mainly for broader ML/data-quality discussions.

### r/ExperiencedDevs

https://www.reddit.com/r/ExperiencedDevs/

Considered for engineering perspectives on incident response, automation,
escalation, and operational trade-offs.

### r/DataEngineeringPH

https://www.reddit.com/r/DataEngineeringPH/

Used for discussion about data-quality repairability and practical data
engineering decisions.


## 8. Relevant X Accounts Identified During Research

These accounts were identified as potentially useful sources around data
systems, ML systems, data infrastructure, observability, or engineering
operations.

- Chip Huyen (@chipro)  
  https://x.com/chipro

- Eugene Yan (@eugeneyan)  
  https://x.com/eugeneyan

- Barr Moses (@BarrMoses_MC)  
  https://x.com/BarrMoses_MC

- Prukalpa Sankar (@prukalpa)  
  https://x.com/prukalpa

- Wes McKinney (@wesmckinn)  
  https://x.com/wesmckinn

- Shinji Kim (@shinjikim)  
  https://x.com/shinjikim

- Gergely Orosz (@GergelyOrosz)  
  https://x.com/GergelyOrosz

- Gwen Shapira (@gwenshap)  
  https://x.com/gwenshap

Being listed here means the account was identified as relevant to the research
area. It does not mean that the person reviewed, participated in, or endorsed
this project.

### X contributions made for this project

TODO: Add links to the actual X posts/replies made as part of the Week 1
research requirement.

- X contribution 1: [ADD LINK]
- X contribution 2: [ADD LINK]
- X contribution 3: [ADD LINK, IF APPLICABLE]


## 9. Foundational References Verified So Far

### 9.1 Data Validation for Machine Learning

Eric Breck, Neoklis Polyzotis, Sudip Roy, Steven Whang, and Martin Zinkevich.

"Data Validation for Machine Learning", SysML 2019.

Link:

https://research.google/pubs/data-validation-for-machine-learning/

Why it is relevant:

The paper discusses data validation in production machine-learning pipelines,
including detecting unexpected patterns and data problems before they affect
downstream systems.

It provides useful background for thinking about automated evidence generation
and validation before downstream processing.


### 9.2 The Data Linter

Nick Hynes, D. Sculley, and Michael Terry.

"The Data Linter: Lightweight Automated Sanity Checking for ML Data Sets",
NIPS Workshop on ML Systems, 2017.

Link:

https://research.google/pubs/the-data-linter-lightweight-automated-sanity-checking-for-ml-data-sets/

Why it is relevant:

The work investigates automatically inspecting datasets for potential
problems and suggesting transformations.

It helped motivate the distinction between detecting suspicious data and
deciding what corrective action, if any, should follow.


### 9.3 Automating Large-Scale Data Quality Verification

Sebastian Schelter, Dustin Lange, Philipp Schmidt, Meltem Celikel,
Felix Biessmann, and Andreas Grafberger.

"Automating Large-Scale Data Quality Verification", Proceedings of the VLDB
Endowment, 2018.

Paper:

[ADD VERIFIED PAPER LINK]

Related Deequ repository:

https://github.com/awslabs/deequ

Why it is relevant:

The work describes automated data-quality verification at scale using
declarative constraints and data-quality metrics.

The associated Deequ project provides a concrete example of treating
data-quality checks similarly to tests over datasets.


### 9.4 Additional verified source

TODO: Read and verify one additional paper, article, repository, or dataset.

Title:

[ADD]

Authors:

[ADD]

Link:

[ADD]

Why it is relevant:

[ADD AFTER READING]


### 9.5 Additional verified source

TODO: Read and verify one additional paper, article, repository, or dataset.

Title:

[ADD]

Authors:

[ADD]

Link:

[ADD]

Why it is relevant:

[ADD AFTER READING]


## 10. Questions I Want the Research to Answer

### Hidden state

When a batch arrives, what exactly is unknown?

- Is the batch genuinely wrong?
- Is an unusual value actually an error or a legitimate rare event?
- Is the batch representative of a legitimate change in the underlying
  process?
- Is a detected anomaly caused by a pipeline problem or by a real-world
  change?
- Is the data still fit for its intended downstream purpose?

### Evidence

What evidence should materially change the agent's belief?

Possible evidence includes:

- schema violations,
- business-rule violations,
- missing values,
- formatting changes,
- statistical distributions,
- previous batches,
- historical failure patterns,
- source reliability,
- relationships between fields,
- relationships with other datasets,
- deployment/change history,
- domain knowledge.

A major unresolved question is how to combine evidence when several of these
signals disagree.

### Repairability

When is automated repair actually safe?

Questions include:

- Is the repair only changing representation?
- Does the transformation change the underlying business meaning?
- Is the correct value known deterministically?
- Could an attempted repair corrupt otherwise valid data?
- Should unknown semantic values ever be automatically imputed?
- When should a human make the decision instead?

### Decision scope

Should ACCEPT, REPAIR, ISOLATE, and REJECT always apply to an entire batch?

For example, if 995 out of 1,000 transactions are valid and five are
problematic, should the system:

- reject all 1,000,
- accept all 1,000,
- process 995 and isolate five,
- or choose based on transaction/data semantics?

The current Week 1 simulator makes a batch-level decision. Row-level partial
acceptance is an important possible extension.

### Uncertainty and escalation

- At what confidence should the agent act automatically?
- When should ambiguity lead to isolation?
- What new evidence should the agent request or accept?
- Can a new clue change an ISOLATE decision into ACCEPT, REPAIR, or REJECT?
- How should the current posterior become the prior when additional evidence
  about the same batch arrives?

These questions motivate a possible sequential belief-update mechanism.


## 11. Community Questions Asked

These are actual public research contributions made while investigating the
problem.


### 11.1 When is a data-quality problem actually repairable?

Community: r/DataEngineeringPH

Post:

https://www.reddit.com/r/DataEngineeringPH/comments/1vmn9gf/when_is_a_dataquality_problem_actually_repairable/

Research goal:

Understand the boundary between a transformation that can safely be automated
and one that requires human/domain judgment.

What I learned:

Useful discussion suggested a distinction between structural/representation
changes and changes to unknown business meaning.

This supports treating formatting, casing, and known serialization problems as
stronger candidates for REPAIR while being more conservative about unknown
semantic values.

Another useful point raised in the discussion was that missing data cannot
always be treated uniformly; why the value is missing can matter.

Detailed responses and resulting design changes are recorded separately in
`discussion-record.md`.


### 11.2 What evidence do you trust most when deciding whether unusual data is actually bad?

Community: r/SQL

Post:

https://www.reddit.com/r/SQL/comments/1vmmgdq/what_evidence_do_you_trust_most_when_deciding/

Outcome:

The post was removed by Reddit's filters.

No usable practitioner responses were obtained, so no design conclusion is
being attributed to this discussion.

The unsuccessful contribution is retained in the research record rather than
being omitted.


### 11.3 When a batch of 1,000 transactions has 5 bad rows, what should actually happen?

Community: r/ETL

Post:

https://www.reddit.com/r/ETL/comments/1vqj4m9/when_a_batch_of_1000_transactions_has_5_bad_rows/

Research goal:

Understand whether a small number of problematic records should cause an
entire incoming batch to be rejected.

What I learned:

Responses were situational rather than unanimous.

One useful perspective was that systems can continue processing valid records
while flagging or isolating problematic records when the pipeline permits it.

Another perspective emphasized that financial/transactional data may require
additional investigation rather than treating every invalid record as an
ordinary ingestion failure.

This exposed a limitation of the current simulator: ACCEPT, REPAIR, ISOLATE,
and REJECT currently apply to the entire batch rather than individual records.

Detailed comments and resulting design implications are recorded in
`discussion-record.md`.


### 11.4 What is the sneakiest financial-transaction data problem you have seen?

Community: r/DataEngineeringPH

Post:

https://www.reddit.com/r/DataEngineeringPH/comments/1vqj5fn/what_is_the_sneakiest_financialtransaction_data/

Research goal:

Identify semantic data-quality failures that can pass simple schema,
type, range, and non-null validation.

Status:

[ADD FINAL STATUS AFTER REVIEWING ALL RESPONSES]

Useful findings:

[ADD ONLY WHAT ACTUAL RESPONSES SUPPORT]

Design/test change:

[ADD IF A RESPONSE ACTUALLY CHANGED THE PROJECT]

If no useful response was received, record:

"No usable response was received, so this contribution did not result in a
design change."


## 12. Important Findings From Human Discussion

The discussions so far have not produced a universal rule for data-quality
triage. That itself is useful.

Three themes emerged.


### 12.1 Repairability depends on semantics

Formatting and representation problems can often be corrected safely when the
transformation is known and deterministic.

Changing an unknown business value is substantially riskier because the
system may not know the intended value.

This reinforces the distinction between FORMAT_GLITCH and CORRUPTED in the
current state model.


### 12.2 Missing or invalid data does not automatically determine an action

A null or invalid field is evidence of a problem, but the appropriate response
depends on the field, its cause, downstream use, and whether the correct value
can be recovered.

This argues against simple rules such as:

    if null exists -> reject


### 12.3 Batch-level rejection is not always the only operational choice

Some pipelines can process valid records while quarantining bad records.

The current project intentionally remains batch-level for Week 1, but
record-level isolation is a meaningful extension and limitation to document.


## 13. Initial Agent Design and What Changed

### 13.1 Initial approach

The first implementation used handcrafted rules to estimate likelihoods.

For example, particular validation flags were mapped to fixed likelihood
values for HEALTHY, BENIGN_DRIFT, FORMAT_GLITCH, and CORRUPTED.

On the initial synthetic test data, the rules aligned too closely with the
way the data had been generated.

The result was unrealistically strong classification performance.

This indicated that the experiment was testing whether the code could recover
rules that were effectively already encoded in the dataset rather than testing
reasoning under meaningful uncertainty.


### 13.2 Introducing overlapping evidence

The test dataset was changed so that the same observed feature could appear
under more than one hidden state.

For example:

- a healthy batch could contain small imperfections,
- benign drift could coexist with formatting changes,
- format problems could resemble corruption,
- corruption did not always need to contain every obvious critical signal.

With the more ambiguous 40-case dataset, the handcrafted inference model
achieved:

- 60.0% overall state-classification accuracy,
- 57.8% macro F1,
- 100% recall for corrupted batches.

This exposed genuine failure cases rather than perfect classification.


### 13.3 LLM-assisted likelihood estimation

The handcrafted likelihood function was then replaced with an LLM call.

The LLM receives extracted evidence and estimates:

    P(Evidence | State)

for each of the four hidden states.

The LLM does NOT make the final action decision.

Python still performs the Bayesian update:

    P(State | Evidence)
        proportional to
    P(Evidence | State) × P(State)

The resulting posterior is then passed to the same deterministic
expected-cost policy.

On the same 40 simulated test batches, this version produced:

- 87.5% overall state-classification accuracy,
- 83.8% macro F1,
- 100% corrupted-state recall,
- 62.5% corrupted-state precision,
- ₹68,800 total simulated decision cost.

The simulated cost was:

- 98.6% lower than the naive ACCEPT-all baseline,
- 86.3% lower than the strict reject-on-any-signal baseline.

These results are specific to the simulated dataset, priors, cost matrix, and
cached LLM responses. They are not production performance claims.


## 14. Important Failure Patterns Observed

The final LLM-assisted experiment made five incorrect state predictions.


### 14.1 False corruption alarms

Two healthy batches were classified as corrupted.

The policy selected ISOLATE rather than blindly rejecting them.

This suggests that the decision layer can reduce the impact of an incorrect
state prediction when uncertainty remains.


### 14.2 Drift/corruption confusion

One benign-drift case was classified as corrupted.

The posterior confidence was relatively low and the policy selected ISOLATE.

This is a useful example where additional evidence could potentially change
the decision.


### 14.3 Subtle drift under-detection

Two benign-drift cases were classified as healthy.

Benign drift was the weakest state in the experiment:

    Recall = 50%

This may result from ambiguous evidence, LLM inference, or the manually chosen
prior assigning 75% probability to HEALTHY.

The experiment does not currently separate these possible causes.


## 15. AI Assistance Used During the Project

AI tools were used as assistants during research and implementation.

Examples include:

- brainstorming terminology and research directions,
- explaining Bayesian inference and calibration concepts,
- reviewing the initial simulator,
- identifying that perfect metrics were probably caused by overly separable
  synthetic cases,
- helping redesign the dataset with overlapping evidence,
- debugging Python/module/API integration problems,
- helping structure evaluation metrics,
- suggesting failure-analysis questions,
- assisting with LLM API integration.

AI output was not treated as automatically correct.

Technical claims, references, experimental outputs, and implementation changes
were checked against code, experiment results, external sources, or human
discussion where possible.


## 16. Important AI / LLM Errors and Limitations

### 16.1 Overly clean initial experiment

The initial implementation produced approximately perfect precision and
recall.

Rather than treating this as evidence that the agent worked perfectly, the
test design was questioned.

The synthetic cases and handcrafted likelihood rules were too closely aligned.

The test data was therefore redesigned to create overlapping evidence.


### 16.2 LLM likelihoods are estimates, not measured probabilities

The current LLM outputs values interpreted as:

    P(Evidence | State)

These values are model judgments.

They have not been learned or calibrated from a large historical dataset of
labeled production batches.

The project should therefore refer to them as "LLM-estimated likelihoods"
rather than empirically measured likelihoods.


### 16.3 LLM responses were not perfectly reproducible

The same evidence could produce somewhat different likelihood estimates across
separate calls, even when temperature was set to zero.

For the final 40-case benchmark, the first successful LLM likelihood result
for each batch was cached.

Subsequent experiment runs reuse those cached values.


### 16.4 Output-token exhaustion

Some LLM API calls spent their output budget on model reasoning and returned
no final text response:

    stop_reason = max_tokens

This initially caused the experiment to terminate.

The implementation was changed to:

- increase the output-token allowance,
- validate that a usable response was returned,
- retry failed calls up to three times,
- cache every successful response immediately.

This became an engineering lesson of the experiment: once an LLM is part of an
agent, inference reliability must also be handled by deterministic surrounding
software.


### 16.5 AI-suggested references require verification

Some references were originally identified through AI-assisted research.

They should not automatically enter the final preprint.

Only sources that can be independently located, inspected, and shown to be
relevant should be included.


## 17. Current Limitations

The current experiment has several important limitations.

1. The 40 test batches are simulated rather than production data.

2. The class distribution was deliberately designed for experimentation.

3. The prior probabilities are manually assumed.

4. The cost matrix is manually specified and represents experimental business
   costs rather than measured financial impact.

5. The evidence extractor still contains handcrafted thresholds such as the
   amount threshold and median-amount surge threshold.

6. LLM likelihood estimates are not empirically calibrated.

7. Only one LLM configuration is used in the final cached experiment.

8. Decisions currently operate on an entire batch.

9. The current agent does not automatically acquire additional evidence.

10. A posterior is currently computed for a batch, but a full persistent
    multi-step belief board has not yet been implemented.

These limitations should remain visible in the preprint rather than being
hidden.


## 18. Next Research Question

The most useful next question is no longer simply:

    Can the agent classify a batch?

The experiment suggests a more interesting question:

    Can the agent revise a decision when new evidence arrives?

For an ambiguous batch, the desired sequence is:

    initial prior
        ↓
    observed batch evidence
        ↓
    LLM-estimated likelihood
        ↓
    Bayesian posterior
        ↓
    initial action
        ↓
    new evidence / human clue
        ↓
    updated likelihood
        ↓
    previous posterior becomes new prior
        ↓
    updated posterior
        ↓
    updated action

This would allow the project to demonstrate belief revision rather than only
one-shot classification.

It is a candidate next step, not a capability that should be claimed for the
current completed experiment.


## 19. Research Integrity Notes

This project is an educational Week 1 experiment.

The following distinctions should be maintained in all later documentation:

- simulated cost is not real financial savings,
- LLM-estimated likelihood is not a calibrated empirical likelihood,
- synthetic test accuracy is not production accuracy,
- a useful Reddit comment is practitioner feedback, not scientific evidence,
- an AI-generated suggestion is not a verified reference,
- a cached benchmark improves reproducibility but does not remove model
  uncertainty,
- the current system is a small Bayesian decision agent, not a complete
  production data-quality platform.

The goal of the project is to demonstrate and evaluate a concrete decision
process under uncertainty, including where that process fails.


## 20. Links to Project Artifacts

### Repository

Project repository:

[ADD GITHUB REPOSITORY LINK]


### Experiment

Experiment results:

[ADD REPOSITORY LINK TO results/]

Test dataset:

[ADD REPOSITORY LINK TO TEST DATA]

LLM likelihood cache:

[ADD REPOSITORY LINK IF THIS FILE IS INTENDED TO BE PUBLIC]


### Research and decision records

Discussion record:

[ADD LINK AFTER CREATED]

Probability decision record:

[ADD LINK AFTER CREATED]

Review record:

[ADD LINK AFTER CREATED]


### Preprint

Preprint source:

[ADD LINK AFTER CREATED]

Final preprint PDF:

[ADD LINK AFTER CREATED]


### Public discussion

Reddit — Repairability:

https://www.reddit.com/r/DataEngineeringPH/comments/1vmn9gf/when_is_a_dataquality_problem_actually_repairable/

Reddit — Evidence:

https://www.reddit.com/r/SQL/comments/1vmmgdq/what_evidence_do_you_trust_most_when_deciding/

Reddit — Partial batch failure:

https://www.reddit.com/r/ETL/comments/1vqj4m9/when_a_batch_of_1000_transactions_has_5_bad_rows/

Reddit — Transaction-data failures:

https://www.reddit.com/r/DataEngineeringPH/comments/1vqj5fn/what_is_the_sneakiest_financialtransaction_data/


### Final social posts

LinkedIn post:

[ADD LINK AFTER PUBLISHED]

X thread:

[ADD LINK AFTER PUBLISHED]
