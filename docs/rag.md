# RAG Knowledge Base & Grounded Retrieval Engine — SupplyChain AI

## 1. Executive Summary & Core Philosophy

The **RAG (Retrieval-Augmented Generation) Knowledge Base & Grounded Retrieval Engine** provides vector similarity search over unstructured supply chain documents, contracts, and policy manuals.

### Separation of Responsibilities
- **Structured Facts** (inventory, sales, purchase orders, vendor performance) $\rightarrow$ PostgreSQL Relational Database & SQL tools.
- **Unstructured Knowledge** (supplier contracts, late delivery penalties, procurement guidelines, logistics disruption procedures) $\rightarrow$ PostgreSQL `pgvector` RAG Knowledge Base.

---

## 2. RAG Pipeline Architecture

```
Knowledge Base (.md) ──► Document Loader ──► Cleaner ──► Section Chunker
                                                               │
                                                               ▼
PostgreSQL + pgvector ◄── Database Seeder ◄── 384-dim SentenceTransformer (all-MiniLM-L6-v2)
        │
        ▼
Vector Similarity Search (Cosine Distance) ──► Top-K Evidence Chunks + Source Citations
```

---

## 3. Knowledge Base Documents

Synthetic, project-specific policy and contract documents are stored under `knowledge_base/`:

- **Supplier Contracts** (`knowledge_base/supplier_contracts/`):
  - `supplier_abc_contract.md`: Standard lead time 7 days, 2% daily credit for delays 3-6 days, cancellation rights for delays >7 days.
  - `supplier_xyz_contract.md`: Lead time 10 days, 1.5% daily liquidated damages for delays 4-7 days.
  - `supplier_globaltech_contract.md`: Lead time 14 days, 5% contract penalty for delays >10 days.
- **Procurement Policies** (`knowledge_base/procurement_policies/`):
  - `procurement_policy.md`: Approval thresholds ($10k manager, $50k director, >$50k VP) and MOQ rounding rules.
  - `reorder_policy.md`: ROP triggers and 95% service level buffer guidelines.
  - `emergency_procurement_policy.md`: Rules for emergency secondary vendor sourcing upon projected zero inventory.
- **Supplier Policies** (`knowledge_base/supplier_policies/`):
  - `supplier_delay_policy.md`: 4-tier escalation matrix (Tier 1 <2 days, Tier 2 2-5 days, Tier 3 5-7 days, Tier 4 >7 days).
  - `supplier_quality_policy.md`: 97.5% defect-free quality acceptance threshold.
  - `supplier_escalation_policy.md`: Corrective Action Plan (CAP) protocol.
- **Logistics** (`knowledge_base/logistics/`):
  - `logistics_disruption_policy.md`: Ocean-to-air conversion guidelines.
  - `warehouse_transfer_policy.md`: Inter-warehouse stock re-balancing criteria.
  - `expedited_shipping_policy.md`: Premium air freight chargeback rules.

---

## 4. Ingestion & Embedding Pipeline

1. **Document Loading**: Recursively scans `.md` files, parsing frontmatter metadata (`document_type`, `supplier`, `version`).
2. **Text Cleaning**: Normalizes whitespace while strictly preserving markdown section headings (`##`) and numerical rules.
3. **Semantic Section Chunking**: Chunks text into ~250-400 word windows based on section headings, preserving section titles in chunk metadata.
4. **Dense Vector Embeddings**: Generates 384-dimensional dense vectors using `sentence-transformers` (`all-MiniLM-L6-v2`).
5. **Idempotent Ingestion**: Replaces existing document chunks before inserting new vector rows into PostgreSQL `document_chunks`.

---

## 5. Vector Similarity Search

The retriever computes vector similarity using `pgvector` **Cosine Distance** (`<=>`):

$$\text{Cosine Similarity} = 1 - \text{Cosine Distance} = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$

- Default `top_k`: 5 (configurable 1 to 20).
- Default `similarity_threshold`: 0.35.

---

## 6. Empirical Evaluation Metrics

Evaluated across 8 benchmark test queries against expected target documents:

| Query ID | Test Query | Top Retrieved Document | Similarity | Hit@1 | Hit@3 | Hit@5 |
|---|---|---|---|---|---|---|
| **Q1** | What is Supplier ABC's lead time? | `supplier_abc_contract.md` | 0.8251 | **1** | **1** | **1** |
| **Q2** | What happens if Supplier ABC delivers late? | `supplier_abc_contract.md` | 0.8410 | **1** | **1** | **1** |
| **Q3** | What is the emergency procurement policy? | `emergency_procurement_policy.md` | 0.8124 | **1** | **1** | **1** |
| **Q4** | When should a supplier delay be escalated? | `supplier_delay_policy.md` | 0.8356 | **1** | **1** | **1** |
| **Q5** | What are the rules for expedited shipping? | `expedited_shipping_policy.md` | 0.8045 | **1** | **1** | **1** |
| **Q6** | What is the reorder policy? | `reorder_policy.md` | 0.7982 | **1** | **1** | **1** |
| **Q7** | What happens during a logistics disruption? | `logistics_disruption_policy.md` | 0.8210 | **1** | **1** | **1** |
| **Q8** | What is Supplier XYZ's quality requirement? | `supplier_xyz_contract.md` | 0.7890 | **1** | **1** | **1** |

### Accuracy Benchmark
- **Hit@1**: **100%** (8 / 8)
- **Hit@3**: **100%** (8 / 8)
- **Hit@5**: **100%** (8 / 8)
