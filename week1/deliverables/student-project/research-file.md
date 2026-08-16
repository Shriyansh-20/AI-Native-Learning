# The problem statement

The agent observes an incoming data batch and its validation metadata. It must select Accept, Repair, Isolate, or Reject because the true underlying health and semantic validity of the data cannot be directly observed at ingestion time.

# The project objective

To design, implement, and evaluate an autonomous, cost-sensitive decision agent for data quality triage. The agent models the latent data health state as a probability distribution over concrete possible worlds, gathers evidence based on information gain, and chooses actions that minimize total expected business loss (balancing pipeline downtime, human reviewer overload, and downstream silent data corruption).



# Technical terms

## Core — must understand
1. Data Quality Assessment
2. Data Profiling
3. Data Validation
4. Data Anomaly Detection
5. Decision Making Under Uncertainty
6. POMDP (Partially Observable Markov Decision Process)
7. Cost-Sensitive Decision Making

## Action/agent layer
8. Data Repair / Automated Data Cleaning
9. Active Sensing / Active Learning
10. Human-in-the-Loop Data Quality

## Supporting concepts
11. Data Quality Rules
12. Out-of-Distribution (OOD) Detection



# Search queries

1. What is data quality?
2. What is the structure of the data being stored?
   - What schema/constraints exist?
   - What relationships or dependencies exist?
   - Does the structure differ significantly across database types?
3. What metrics/dimensions determine whether data is healthy or problematic?
   - What characteristics indicate good data quality?
   - What characteristics indicate a potential quality issue?
   - Which issues are serious enough to reject versus potentially repair?
4. What operations/changes can happen to the data?
   - What kinds of changes can occur?
   - What constraints exist on those changes?
   - Are some operations inherently riskier than others?
5. What happens when a data-quality issue is detected?



# Five to ten verified Reddit communities

1. https://www.reddit.com/r/dataengineering/ -> Primary community of data engineers managing production ETL/ELT pipelines, circuit breakers, and data downtime incidents.
2. https://www.reddit.com/r/datascience/ -> Analytics practitioners who experience the downstream business costs of corrupted data.
3. https://www.reddit.com/r/learnmachinelearning/
4. https://www.reddit.com/r/SQL/ -> Good for basic sql related doubts 
5. https://www.reddit.com/r/DataEngineeringPH/ -> Students discussing doubts 
6. https://www.reddit.com/r/ETL/ -> Pipeline developers working on batch ingestion failures and automated remediation patterns.
7. https://www.reddit.com/r/MachineLearning/. -> ML researchers and engineers dealing with feature store validation, silent training-data poisoning, and drift detection.
8. https://www.reddit.com/r/ExperiencedDevs/ -> Senior engineering leaders discussing human escalation fatigue, paging costs, and automated triage policies.
9. https://www.reddit.com/r/database/ -> Database administrators focused on schema evolution, integrity constraints, and ACID durability.



# Relevant X accounts
1. https://x.com/chipro -> Author of *Designing Machine Learning Systems*; expert on real-time streaming data architectures.
2. https://x.com/eugeneyan -> Applied ML lead; writes extensively on operational ML patterns and data evaluation.
3. https://x.com/BarrMoses_MC -> CEO of Monte Carlo Data; established Data Observability.
4. https://x.com/prukalpa -> Co-founder of Atlan; active metadata, lineage, and governance.
5. https://x.com/wesmckinn -> Creator of Pandas / Apache Arrow; expert on tabular data representations.
6. https://x.com/shinjikim -> Founder of Select Star; metadata and lineage tracking.
7. https://x.com/GergelyOrosz -> Author of The Pragmatic Engineer; writes on incident triage and on-call costs.
8. https://x.com/gwenshap -> Distributed streaming systems and real-time validation.



# Key Foundational References & Papers
1. **Breck et al. (Google MLSys)**: *"Data Validation for Machine Learning"* (Introduces TensorFlow Data Validation / TFDV at petabyte scale).
2. **Hynes et al. (MLSys)**: *"Data Linter: Lightweight Automated Sanity Checking for Data Science"*.
3. **Schelter et al. (VLDB)**: *"Automating Large-Scale Data Quality Verification"* (AWS Deequ framework).
4. **SARC-DQ (arXiv:2607.26313, 2026)**: *"Runtime Data-Quality Gating for Agentic AI Silent Semantic Failures"*.
5. **Sanderson (O'Reilly)**: *"Practical Data Contracts: Scalable Data Quality at the Source"*.



# Questions that you want to answer


## Hidden state
What do we not know when a data batch arrives?

1. Is the data genuinely wrong?
2. Is an unusual value actually an error or a legitimate rare event?
3. Is the batch representative of the underlying process?
4. Is the source itself trustworthy?
5. Is the data still fit for its intended purpose?
6. Is the detected anomaly caused by a data problem or a genuine change in the real world?


## Evidence
What evidence should change our belief?

1. Historical data?
2. Schema?
3. Business rules?
4. Data-quality dimensions?
5. Previous batches?
6. Source reliability?
7. Relationships with other datasets?
8. Statistical distribution?
9. Human/domain knowledge?


## Questions for Community Discussions

- What is the most insidious data corruption you've seen that passed all schema and non-null checks?
- How do you distinguish benign real-world shifts (e.g., Black Friday traffic) from upstream pipeline bugs?

- Which validation signals give the highest information gain (e.g., column-level lineage vs. statistical divergence vs. producer runtime)?
- How reliably can automated profiling catch encoding/format shifts without false alarms?


## Actions
When should the agent:

1. Accept: Does this push data directly to production or to a staging area?

2. Repair: Is repair deterministic (rule-based imposer) or generative/probabilistic (imputation model)? Could a repair inadvertently corrupt valid data?

3. Isolate: Where does isolated data go, and who/what is alerted? Does this trigger human-in-the-loop review?

4. Reject: What downstream pipeline processes fail when a batch is rejected?


## Errors
What is worse?

1. What is the business cost of a False Accept (passing bad data to downstream applications)?

2. What is the business cost of a False Reject (stopping a valid business pipeline unnecessarily)?

3. How do you quantify the cost of a False Repair (corrupting valid data under the assumption that it was broken)?