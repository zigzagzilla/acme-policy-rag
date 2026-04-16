# Evaluation Results (Retrieval-Only Mode)

**Date**: 2026-04-16  
**Mode**: Retrieval-only — no LLM calls; evaluates the ChromaDB retrieval stage  
**Embedding model**: all-MiniLM-L6-v2  
**Vector store**: ChromaDB (local, cosine similarity)  
**Top-k**: 5

> **Note**: This report covers retrieval-stage metrics only. For end-to-end answer
> quality (groundedness, citation accuracy) re-run without `--retrieval-only` once
> the OpenRouter daily API rate limit has reset.

---

## Summary Metrics

| Metric | Value |
|--------|-------|
| Questions evaluated | 30 |
| **Key-fact Recall** | **88.6%** |
| **Source Recall** | **100.0%** |
| Retrieval Latency p50 | 37 ms |
| Retrieval Latency p95 | 72 ms |

---

## Metric Definitions

- **Key-fact Recall**: Fraction of pre-defined `key_facts` strings found (case-insensitive) in the concatenated text of all top-k retrieved chunks. Measures whether the retrieval step surfaces the relevant information before LLM generation.
- **Source Recall**: Whether at least one chunk was successfully retrieved (sanity check; expected 100% for in-scope questions).
- **Retrieval Latency**: Wall-clock time for query embedding + ChromaDB cosine search. Excludes LLM generation time.

---

## Results by Topic

### Benefits

| ID | Question | Key-fact Recall | Found/Total | Latency | Top Sources |
|----|----------|-----------------|-------------|---------|-------------|
| Q18 | What percentage of medical insurance premiums does Acme... | 100% | 4/4 | 38ms | Employee Benefits Policy, Business Travel Policy |
| Q19 | How much does the company match for 401(k) contribution... | 100% | 4/4 | 35ms | Employee Benefits Policy, Employee Benefits Policy |
| Q20 | How many weeks of paid parental leave does the primary ... | 100% | 4/4 | 34ms | Employee Benefits Policy, Paid Time Off (PTO) Policy |
| Q21 | What is the annual learning and development stipend per... | 100% | 4/4 | 34ms | Employee Benefits Policy, Paid Time Off (PTO) Policy |

### Code of Conduct

| ID | Question | Key-fact Recall | Found/Total | Latency | Top Sources |
|----|----------|-----------------|-------------|---------|-------------|
| Q22 | What is the anonymous ethics hotline number for reporti... | 100% | 4/4 | 37ms | Code of Conduct, Data Privacy Policy |
| Q23 | What happens to employees who retaliate against someone... | 100% | 3/3 | 45ms | Code of Conduct, Information Security Policy |

### Data Privacy

| ID | Question | Key-fact Recall | Found/Total | Latency | Top Sources |
|----|----------|-----------------|-------------|---------|-------------|
| Q30 | How long does Acme Corp retain employee HR records afte... | 75% | 3/4 | 37ms | Data Privacy Policy, Data Privacy Policy |

### Expenses

| ID | Question | Key-fact Recall | Found/Total | Latency | Top Sources |
|----|----------|-----------------|-------------|---------|-------------|
| Q08 | What is the maximum reimbursable hotel rate for domesti... | 67% | 2/3 | 46ms | Business Travel Policy, Expense Reimbursement Policy |
| Q09 | What is the daily meal allowance for domestic business ... | 75% | 3/4 | 37ms | Business Travel Policy, Expense Reimbursement Policy |
| Q10 | Within how many days must expenses be submitted for rei... | 100% | 3/3 | 36ms | Expense Reimbursement Policy, Expense Reimbursement Policy |
| Q11 | What expense approval is required for purchases over $2... | 75% | 3/4 | 44ms | Expense Reimbursement Policy, Expense Reimbursement Policy |

### Holidays

| ID | Question | Key-fact Recall | Found/Total | Latency | Top Sources |
|----|----------|-----------------|-------------|---------|-------------|
| Q05 | How many paid company holidays does Acme Corp offer in ... | 25% | 1/4 | 39ms | Company Holiday Calendar, Company Holiday Calendar |
| Q06 | When is Juneteenth observed in 2024? | 100% | 3/3 | 38ms | Company Holiday Calendar, Company Holiday Calendar |
| Q07 | How many floating holidays do employees receive per yea... | 100% | 3/3 | 45ms | Company Holiday Calendar, Company Holiday Calendar |

### Onboarding

| ID | Question | Key-fact Recall | Found/Total | Latency | Top Sources |
|----|----------|-----------------|-------------|---------|-------------|
| Q24 | Within how many days must new employees complete benefi... | 100% | 4/4 | 32ms | Employee Onboarding Guide, Employee Benefits Policy |
| Q25 | What mandatory training must be completed within 30 day... | 100% | 4/4 | 38ms | Employee Onboarding Guide, Employee Onboarding Guide |

### PTO

| ID | Question | Key-fact Recall | Found/Total | Latency | Top Sources |
|----|----------|-----------------|-------------|---------|-------------|
| Q01 | How many PTO days do employees receive in their first y... | 33% | 1/3 | 143ms | Paid Time Off (PTO) Policy, Paid Time Off (PTO) Policy |
| Q02 | How many days of PTO can employees carry over to the ne... | 100% | 3/3 | 55ms | Paid Time Off (PTO) Policy, Paid Time Off (PTO) Policy |
| Q03 | How far in advance do I need to request more than two w... | 100% | 2/2 | 72ms | Paid Time Off (PTO) Policy, Paid Time Off (PTO) Policy |
| Q04 | How many days of bereavement leave are provided for an ... | 100% | 5/5 | 40ms | Paid Time Off (PTO) Policy, Employee Benefits Policy |

### Performance

| ID | Question | Key-fact Recall | Found/Total | Latency | Top Sources |
|----|----------|-----------------|-------------|---------|-------------|
| Q28 | When does the annual performance review cycle take plac... | 67% | 2/3 | 36ms | Performance Review Policy, Performance Review Policy |
| Q29 | What merit increase percentage is given to employees ra... | 67% | 2/3 | 34ms | Performance Review Policy, Performance Review Policy |

### Remote Work

| ID | Question | Key-fact Recall | Found/Total | Latency | Top Sources |
|----|----------|-----------------|-------------|---------|-------------|
| Q12 | How many days per week must hybrid employees be on-site... | 100% | 4/4 | 35ms | Remote Work Policy, Employee Onboarding Guide |
| Q13 | What is the home office setup stipend for full-time rem... | 100% | 4/4 | 34ms | Remote Work Policy, Expense Reimbursement Policy |
| Q14 | What are the core hours that remote employees must be a... | 100% | 3/3 | 37ms | Remote Work Policy, Remote Work Policy |

### Security

| ID | Question | Key-fact Recall | Found/Total | Latency | Top Sources |
|----|----------|-----------------|-------------|---------|-------------|
| Q15 | What is the minimum password length required by the sec... | 100% | 3/3 | 44ms | Information Security Policy, Employee Onboarding Guide |
| Q16 | When must a security incident be reported after discove... | 100% | 3/3 | 40ms | Information Security Policy, Information Security Policy |
| Q17 | Is multi-factor authentication required for remote acce... | 100% | 4/4 | 31ms | Information Security Policy, Information Security Policy |

### Travel

| ID | Question | Key-fact Recall | Found/Total | Latency | Top Sources |
|----|----------|-----------------|-------------|---------|-------------|
| Q26 | What class of airfare is allowed for domestic flights? | 100% | 3/3 | 37ms | Business Travel Policy, Expense Reimbursement Policy |
| Q27 | What is the IRS mileage reimbursement rate for personal... | 75% | 3/4 | 37ms | Business Travel Policy, Employee Benefits Policy |
