# The problem statement

The agent observes a specific data change or data batch request. It must decide whether to Accept, Repair, Isolate, or Reject it because it does not know whether the data is actually valid and healthy or contains a quality problem.



# The project objective

Develop an intelligent data-quality agent that evaluates incoming data changes or batches under uncertainty, combines multiple sources of evidence, and selects the most appropriate action—Accept, Repair, Isolate, or Reject while minimizing the cost of incorrect decisions.



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

1. https://www.reddit.com/r/dataengineering/
2. https://www.reddit.com/r/datascience/
3. https://www.reddit.com/r/learnmachinelearning/
4. https://www.reddit.com/r/SQL/
5. https://www.reddit.com/r/DataEngineeringPH/
6. https://www.reddit.com/r/ETL/
7. https://www.reddit.com/r/MachineLearning/



# Relevant X accounts
1. https://x.com/AndrewYNg
2. https://x.com/chipro
3. https://x.com/svlevine
4. https://x.com/eugeneyan



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