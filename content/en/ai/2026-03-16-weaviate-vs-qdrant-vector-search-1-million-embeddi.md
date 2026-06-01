---
title: "Weaviate vs Qdrant: 1M Embeddings Single Node Benchmark"
date: 2026-03-16T20:00:51+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "weaviate", "qdrant", "vector", "Kubernetes"]
description: "Weaviate vs Qdrant at 1M embeddings on a single node: see where production latency diverges and which wins your inference pipeline in 2025."
image: "/images/20260316-weaviate-vs-qdrant-vector-sear.webp"
technologies: ["Kubernetes", "AWS", "GraphQL", "OpenAI", "Rust"]
faq:
  - question: "weaviate vs qdrant vector search 1 million embeddings single node benchmark latency 2025 which is faster"
    answer: "Based on 2025 community benchmarks, Qdrant achieves p99 latency under 10ms at high concurrency, outperforming Weaviate by roughly 2-3x in raw throughput at 1 million embeddings on a single node. This performance gap is largely attributed to Qdrant's Rust-based architecture versus Weaviate's Go implementation."
  - question: "qdrant vs weaviate memory usage 1 million embeddings"
    answer: "Qdrant has a significant memory efficiency advantage, with scalar quantization and product quantization support capable of reducing RAM usage by 4-8x on large datasets. One million 1536-dimensional vectors typically requires around 6GB of RAM, making single-node deployments feasible on a standard cloud instance like an AWS m5.2xlarge."
  - question: "should I use weaviate or qdrant for RAG pipeline production 2025"
    answer: "Qdrant is the better choice if raw query latency and memory efficiency are your primary concerns, while Weaviate is preferable for teams that want built-in vectorizer integrations like text2vec-openai and text2vec-cohere to reduce pipeline complexity. The right decision ultimately depends on your specific query patterns, filter requirements, and whether you're optimizing for speed or faster time-to-ship."
  - question: "weaviate vs qdrant vector search 1 million embeddings single node benchmark latency 2025 cost comparison"
    answer: "A single-node deployment running 1 million embeddings can run on approximately a $200/month VPS or an AWS m5.2xlarge, making the database choice a significant long-term infrastructure decision. Teams that pick the wrong database at this scale risk production latency issues that can translate into roughly $40,000 per year in unnecessary infrastructure costs when scaling up."
  - question: "why is qdrant faster than weaviate vector search"
    answer: "Qdrant was built from the ground up in Rust with low latency as its primary design constraint, while Weaviate originated as a knowledge graph in 2019 and evolved into a vector search engine written in Go. The Rust vs. Go architectural difference, combined with Qdrant's advanced quantization options, accounts for most of the measurable performance delta in benchmark testing."
---

Picking the wrong vector database at scale doesn't just slow your queries — it tanks your entire inference pipeline. At 1 million embeddings on a single node, the performance gap between Weaviate and Qdrant stops being theoretical and starts showing up in production latency.

This comparison matters more in early 2026 than it did a year ago. AI application teams are no longer prototyping. They're running semantic search, RAG pipelines, and recommendation engines at production scale — on cost-constrained, single-node deployments. The database choice made at week two of a project is now a $40k/year infrastructure decision.

The core argument: Qdrant wins on raw latency at high throughput, but Weaviate's integrated ML ecosystem closes the gap for teams that need more than fast nearest-neighbor lookup.

**What this covers:**
- Qdrant consistently delivers lower p99 latency at 1M vectors under concurrent load
- Weaviate's HNSW implementation and memory footprint differ meaningfully from Qdrant's
- Rust vs. Go architecture explains most of the performance delta
- The right choice depends on your query patterns, not just the headline benchmark number

---

> **Key Takeaways**
> - At 1 million embeddings on a single node, Qdrant achieves p99 latency under 10ms at high concurrency, outperforming Weaviate by roughly 2–3x in raw throughput benchmarks from 2025 community testing.
> - Weaviate's built-in vectorizer modules (text2vec-openai, text2vec-cohere) reduce pipeline complexity, making it faster to ship for teams not optimizing for bare-metal query speed.
> - Memory efficiency differs significantly: Qdrant's scalar quantization and product quantization support can cut RAM usage by 4–8x on large datasets, per Qdrant's official documentation.
> - Neither database is universally faster — query filters, vector dimensions, and dataset characteristics all shift benchmark outcomes by meaningful margins.

---

## Why Single-Node Benchmarks Became the Critical Test

Distributed vector database deployments are expensive. Most production AI features — internal semantic search, document retrieval for RAG, product recommendation engines at mid-scale — don't need a Kubernetes cluster with 10 nodes. They need one well-tuned machine that can handle 50–200 concurrent queries without falling over.

That's why the single-node benchmark at 1 million embeddings became the standard test. One million 1536-dimensional vectors (a common output from OpenAI's `text-embedding-3-small`) fits in roughly 6GB of RAM. That's a single m5.2xlarge on AWS, or a $200/month VPS.

Weaviate launched in 2019 as a "knowledge graph" with vector capabilities bolted on, then pivoted hard toward pure vector search around 2021–2022. Qdrant, founded in 2021, was built from day one as a Rust-based vector search engine with latency as the primary design constraint. That architectural history still shows up in benchmarks today.

The 2025 community benchmark by Aditya Ghadge on Medium tested both databases on identical hardware — 32GB RAM, 8-core CPU — with 1 million 768-dimensional vectors. Qdrant hit roughly 4ms average query latency at 10 concurrent requests. Weaviate came in at roughly 9ms under the same conditions. At 50 concurrent requests, the gap widened.

---

## Raw Latency: Qdrant's Rust Advantage Is Real

Qdrant is written in Rust. Weaviate is written in Go. This isn't trivia — it's the primary explanation for the latency delta.

Rust's memory model eliminates garbage collection pauses. Go's GC is good, but under sustained concurrent load, you'll see occasional latency spikes that Rust simply doesn't produce. In benchmark tests documented on Reddit's r/vectordatabase community, Qdrant showed tighter p99 distribution — meaning fewer outlier slow queries. That matters for user-facing features where one bad query poisons the UX.

Specific numbers from community testing:

| Metric | Qdrant | Weaviate |
|---|---|---|
| Avg latency (10 concurrent) | ~4ms | ~9ms |
| p99 latency (10 concurrent) | ~12ms | ~28ms |
| Avg latency (50 concurrent) | ~8ms | ~22ms |
| Memory at 1M vectors (768d) | ~4.5GB | ~7.2GB |
| Index build time (1M vectors) | ~8 min | ~12 min |
| Recall@10 (HNSW defaults) | 0.97 | 0.95 |

*Source: Aditya Ghadge, Medium (2025); r/vectordatabase community benchmark (2025). Hardware: 32GB RAM, 8-core CPU.*

Qdrant wins on every speed metric. But look at the recall numbers — they're close. Weaviate's HNSW implementation isn't sloppy; it's competitive on accuracy.

## Memory Efficiency: Quantization Makes a Bigger Difference Than You'd Expect

At 1 million vectors, memory becomes the binding constraint before CPU does. Qdrant ships with native support for scalar quantization (SQ8) and product quantization (PQ), configurable per collection. According to Qdrant's official documentation, SQ8 alone cuts memory by roughly 4x with less than 1% recall degradation on most datasets.

Weaviate added PQ support in version 1.23, released mid-2024, but community benchmarks suggest Qdrant's quantization implementation is more mature and easier to configure. Running 1.5M+ vectors on a single 16GB node? Qdrant's memory headroom becomes a practical advantage, not an academic one.

This approach can fail when your dataset has unusual vector distributions — certain domain-specific embeddings degrade more sharply under quantization than general-purpose benchmarks suggest. Test quantization on your actual data before committing.

## Weaviate's Filtering and Schema: Slower Queries, Faster Development

Qdrant is faster at pure ANN search. Weaviate is faster at getting a working system into production.

Weaviate's native support for filtered vector search combines metadata filters with ANN using an ACORN algorithm that performs better than naive pre-filtering in many scenarios. The TensorBlue 2025 comparison notes that Weaviate handles high-selectivity filters — retrieving less than 1% of the dataset — more gracefully than Qdrant's current filtering implementation, which can degrade toward brute-force behavior in extreme cases.

Weaviate's built-in schema, REST and GraphQL APIs, and first-class vectorizer integrations also mean a developer can go from zero to working semantic search in an afternoon without writing glue code. That's a real productivity difference when shipping speed matters.

But this isn't always the answer. Teams with simple ANN lookup and minimal filtering don't need that integrated overhead. They're paying a latency tax for features they won't use.

## When to Use Each

**Qdrant:**
- **Pros**: Lower latency at high concurrency, better memory efficiency with quantization, simpler ops model, excellent Rust SDK
- **Cons**: Less integrated ML ecosystem, filtering edge cases at extreme selectivity, limited GraphQL support
- **Best for**: Latency-sensitive production apps, single-node deployments near memory limits, teams comfortable managing vectorization externally

**Weaviate:**
- **Pros**: Native vectorizer modules, strong filtered search, active development velocity, solid multi-tenancy support
- **Cons**: Higher baseline memory usage, Go GC introduces p99 variance, slower raw ANN throughput
- **Best for**: Teams building RAG pipelines that need schema and search in one system, metadata-heavy datasets, rapid prototyping at scale

The trade-off isn't binary. Simple ANN lookup with minimal filtering? Qdrant's advantage is clear and consistent. Hybrid searches — filtering by user_id, date range, and content category simultaneously — and Weaviate's integrated approach starts closing the gap.

---

## Matching the Database to Your Query Pattern

**Scenario 1 — High-throughput RAG retrieval:** A team running an LLM assistant firing 100 concurrent retrieval queries per second against 1M document chunks should default to Qdrant. The latency advantage compounds at scale, and retrieval speed is the bottleneck in the inference chain.

**Scenario 2 — Multi-tenant SaaS search:** A B2B product with per-customer data isolation needs strong multi-tenancy and metadata filtering. Weaviate's multi-tenancy support, generally available since v1.20, and filtered search make it the more practical pick — even with the latency trade-off.

**Scenario 3 — Memory-constrained single node:** Running 2M+ vectors on a 16GB machine? Use Qdrant with SQ8 quantization. Weaviate's higher base memory footprint makes this configuration risky without careful tuning.

**What to watch over the next six months:**

- Weaviate's ongoing work on their async query engine, referenced in their public roadmap as of Q1 2026, could close the concurrency latency gap
- Qdrant v1.9+ introduced sparse vector support for hybrid BM25 + dense search, directly targeting Weaviate's filtering advantage
- Both databases are improving their WASM and edge deployment stories, which matters as vector search moves into browser and edge runtime contexts

---

## Where This Lands

The 2025 benchmark data tells a consistent story:

- **Qdrant leads on raw speed**: roughly 2–3x lower p99 latency under concurrent load
- **Weaviate leads on integration depth**: built-in vectorizers and filtering make complex pipelines easier to manage
- **Memory efficiency favors Qdrant** at scale, especially with quantization enabled
- **Recall quality is comparable** — this isn't a precision trade-off decision

Over the next 6–12 months, expect Qdrant to keep pushing on filtering quality and Weaviate to keep narrowing the raw throughput gap. The two databases are converging on feature parity from opposite directions. Industry reports suggest this competitive pressure is accelerating both roadmaps faster than either team originally projected.

So the practical move is this: profile your actual query patterns before committing. Run a 24-hour load test against a representative dataset. Benchmark latency at *your* concurrency level, not someone else's. That number tells you more than any community benchmark.

Your current concurrency load at 1M vectors is probably the single number that decides this choice.

## References

1. [r/vectordatabase on Reddit: I benchmarked Qdrant vs Milvus vs Weaviate vs PInecone](https://www.reddit.com/r/vectordatabase/comments/1kwaqx1/i_benchmarked_qdrant_vs_milvus_vs_weaviate_vs/)
2. [Choosing Your First Vector DB: Real-World Benchmarks of Qdrant & Weaviate | by Aditya Ghadge | Mediu](https://medium.com/@adityaghadge99/choosing-your-first-vector-db-real-world-benchmarks-of-qdrant-weaviate-5f914cbf2586)
3. [Vector Database Comparison 2025: Pinecone vs Weaviate vs Qdrant vs Milvus vs FAISS | Complete Guide](https://tensorblue.com/blog/vector-database-comparison-pinecone-weaviate-qdrant-milvus-2025)


---

*Photo by [Hoi An and Da Nang Photographer](https://unsplash.com/@hoianphotographer) on [Unsplash](https://unsplash.com/photos/people-working-at-computers-in-a-modern-office-space-Voj5EHsWguc)*
