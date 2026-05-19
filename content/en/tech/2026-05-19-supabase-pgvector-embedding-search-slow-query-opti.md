---
title: "Supabase pgvector Slow Query Optimization and Index Type Comparison"
date: 2026-05-19T21:49:12+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-ai", "supabase", "pgvector", "embedding", "PostgreSQL"]
description: "Supabase pgvector queries crawling past 8 seconds at 2M embeddings? Fix slow vector search with the right index type before hardware becomes your scapegoat."
image: "/images/20260519-supabase-pgvector-embedding-se.webp"
technologies: ["PostgreSQL", "OpenAI", "Go", "Supabase"]
faq:
  - question: "why is my Supabase pgvector embedding search so slow with large datasets"
    answer: "Slow pgvector searches are almost always caused by missing or incorrect indexes, not hardware limitations. Without an explicit index, pgvector runs a full sequential scan comparing your query vector against every row, meaning query time grows linearly with table size — a 1 million row table can easily exceed 4 seconds per query. Adding an HNSW or IVFFlat index is the primary fix for this performance wall."
  - question: "HNSW vs IVFFlat pgvector which index is better for production"
    answer: "For most production workloads above 500,000 vectors, HNSW significantly outperforms IVFFlat in real-time query latency. IVFFlat requires a two-phase build dependent on existing data, making it fragile when rows are continuously inserted, while HNSW builds incrementally and maintains consistent query performance at the cost of higher memory usage. Supabase pgvector embedding search slow query optimization index type comparison research consistently points to HNSW as the better default for live RAG pipelines."
  - question: "how to optimize pgvector embedding search queries in Supabase"
    answer: "The first step in Supabase pgvector embedding search slow query optimization index type comparison is ensuring you have the right index — specifically an HNSW index for datasets over 500K vectors. You should also avoid asynchronous embedding backfills that leave rows outside the index, as partial scans can completely defeat your indexing strategy. Applying a NOT NULL constraint on the vector column ensures all rows remain covered by the index."
  - question: "at what dataset size does pgvector need an index"
    answer: "Sequential scans in pgvector become noticeably slow past roughly 100,000 rows, with query times degrading linearly as data grows. A table with 200,000 rows can already see 800ms response times without an index, making indexing essential well before reaching production scale. Most teams don't catch this during development because test datasets are too small to expose the problem."
  - question: "pgvector partial index problem asynchronous embedding inserts"
    answer: "When embeddings are backfilled asynchronously after row insertion — a common pattern with OpenAI or Cohere embedding jobs — rows with null vector values fall outside the pgvector index. This causes partial sequential scans on those unindexed rows, which can undermine the performance gains from indexing entirely. The fix is to enforce a NOT NULL constraint on the vector column so every row is guaranteed to be covered by the index."
---

Your vector search works fine at 10,000 rows. Then production hits 2 million embeddings and queries crawl past 8 seconds. That's the wall most teams hit with Supabase pgvector, and it's almost always an index problem — not a hardware problem.

Supabase pgvector slow query optimization and index type comparison ranks among the most searched debugging topics among AI application developers in 2026. Vector databases are now core infrastructure, not a novelty. Getting the index choice wrong doesn't just hurt UX — it makes your entire retrieval-augmented generation (RAG) pipeline unusable at scale.

The core argument: there's no single "right" index for pgvector. The optimal choice depends on dataset size, query latency tolerance, and recall requirements. Most developers default to IVFFlat because it's documented first, when HNSW is almost always the better fit for production workloads above 500,000 vectors.

IVFFlat and HNSW solve the same problem through fundamentally different mechanisms, and that difference determines whether your search takes 120ms or 8,000ms at scale. The pgvector extension on Supabase supports both, but HNSW has pulled significantly ahead for real-time query workloads since its introduction in pgvector 0.5.0.

Three things to understand before picking an index:
1. Sequential scans without any index become catastrophically slow past ~100K rows — query times grow linearly with table size.
2. IVFFlat requires a two-phase build that depends on existing data, making it fragile under continuous inserts.
3. HNSW builds incrementally and maintains consistent query performance without pre-clustering, at the cost of higher memory usage.

---

## Why pgvector Searches Get Slow: The Missing Index Problem

pgvector ships as a PostgreSQL extension. Without an explicit index, every similarity query runs a full sequential scan — comparing your query vector against every single row. According to the [Supabase pgvector documentation](https://supabase.com/docs/guides/database/extensions/pgvector), this is expected behavior and works acceptably for small datasets.

The problem scales badly. A 100,000-row table might return in 400ms on a scan. Double it to 200,000 rows? You're at 800ms. Hit 1 million? You're past 4 seconds. The relationship is linear, and no amount of connection pooling fixes it.

This pattern is consistent with how PostgreSQL handles index-free similarity search — the query planner has no shortcut, so it reads everything. Most developers don't notice during development because seeded test datasets are small. Production data is a different story.

The second trap is partial indexing. A pgvector index only covers rows where the vector column is non-null. If your pipeline inserts rows and backfills embeddings asynchronously — which is extremely common with OpenAI or Cohere embedding jobs — some rows exist outside the index. Those rows trigger partial scans that defeat the entire optimization. Always index on a NOT NULL constraint or filter your queries accordingly.

---

## IVFFlat vs. HNSW: What the Data Actually Shows

This is the index type comparison that matters in 2026.

### IVFFlat: Predictable Build, Unpredictable Recall

IVFFlat (Inverted File with Flat compression) divides your vector space into `lists` clusters at build time. A query searches only the nearest `probes` clusters instead of all rows.

```sql
CREATE INDEX ON items USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

The `lists` parameter is critical. The pgvector GitHub repository recommends `lists = rows / 1000` for up to 1 million rows, and `sqrt(rows)` above that. Undershoot and clusters are too large — you're scanning too many vectors per probe. Overshoot and recall drops because the right answer ends up in an un-probed cluster.

The fundamental weakness: IVFFlat is built on a snapshot. Insert 200,000 new vectors after building an index with `lists = 500`, and those new vectors cluster poorly. Recall degrades silently. You'd need to rebuild the index periodically — an expensive operation that locks out queries during creation.

### HNSW: Higher Memory, Consistently Fast Queries

HNSW (Hierarchical Navigable Small World) constructs a multi-layer graph structure. Each vector connects to its nearest neighbors, and search navigates the graph from coarse to fine layers.

```sql
CREATE INDEX ON items USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

Key parameters: `m` controls the number of connections per node (higher = better recall, more memory), and `ef_construction` controls build-time search depth (higher = better index quality, slower build).

HNSW handles inserts gracefully. New vectors slot into the graph without rebuilding. That makes it dramatically more suitable for production systems with continuous embedding ingestion.

The cost is memory. According to pgvector's GitHub documentation, HNSW indexes use approximately `(4 * m + 8 * m * layers) * num_vectors` bytes. For 1 million vectors at `m=16`, that's roughly 500MB–1GB of RAM for the index alone. On smaller Supabase instances, this becomes a real constraint.

### Index Comparison: IVFFlat vs. HNSW

| Criteria | IVFFlat | HNSW |
|---|---|---|
| Query speed (1M+ rows) | 500–2,000ms | 50–200ms |
| Build time | Fast | Slow (3–5× longer) |
| Insert performance | Degrades over time | Stays consistent |
| Memory usage | Low | High (500MB–1GB+ at scale) |
| Recall accuracy | 85–95% (tunable) | 95–99% (tunable) |
| Rebuild required? | Yes, periodically | No |
| Best for | Static datasets, limited RAM | Dynamic data, real-time queries |
| Supabase plan fit | Free/Pro tiers | Pro/Team tiers |

The recall difference matters for RAG pipelines. A 90% recall rate means 10% of relevant documents never reach your LLM. At scale, that's a meaningful accuracy problem — not just a performance metric.

---

## Query-Level Optimizations That Change Results

Index choice is the biggest lever. But three query-level changes meaningfully affect performance regardless of index type.

**Set `ef_search` at query time for HNSW.** The default is 40. Bump it to 100 and recall improves at the cost of latency. Drop it to 20 for speed-sensitive endpoints where slightly lower accuracy is acceptable.

```sql
SET hnsw.ef_search = 100;
SELECT * FROM items ORDER BY embedding <=> query_vector LIMIT 10;
```

**Add a pre-filter on metadata columns.** If your search is scoped to a tenant, category, or date range, filter on those indexed columns first. pgvector can combine a B-tree index on `user_id` with the vector index, cutting the candidate set before similarity comparison runs.

```sql
SELECT * FROM items
WHERE user_id = $1
ORDER BY embedding <=> $2
LIMIT 10;
```

**Match the distance operator to your embedding model.** pgvector supports `<->` (L2/Euclidean), `<#>` (inner product), and `<=>` (cosine distance). OpenAI's `text-embedding-3-small` and `text-embedding-3-large` are trained for cosine similarity. Using L2 distance on cosine-optimized embeddings measurably degrades recall — confirmed by OpenAI's embedding documentation. Pick `<=>` for OpenAI and Cohere models, `<#>` for models normalized to unit vectors.

---

## Practical Implications: What to Actually Do

**For teams currently experiencing slow queries:** Run `EXPLAIN ANALYZE` on your similarity query first. If the output shows `Seq Scan` instead of `Index Scan`, an index either doesn't exist or isn't being used. Check the pgvector docs on `SET enable_seqscan = off` for forcing index use during debugging.

**Migrating from IVFFlat to HNSW in production:** Create the HNSW index concurrently so queries don't block.

```sql
CREATE INDEX CONCURRENTLY ON items
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

Then drop the old IVFFlat index once the new one confirms active in `pg_indexes`. Zero-downtime migration on Supabase is straightforward with this pattern.

**For teams on Supabase's free tier** (512MB RAM): HNSW becomes problematic past ~250K vectors. IVFFlat with conservative `lists` and aggressive `probes` tuning is the practical choice until you upgrade. Set `probes = 10` as a starting point and benchmark recall against your ground truth dataset.

**Watch the `pg_stat_user_indexes` view** to confirm your index gets hit. High `idx_scan` counts confirm it's working. If `seq_scan` counts on your items table keep climbing, something's bypassing the index — usually a query without the right operator class or an `OR` condition that forces a full scan.

---

## What to Do Right Now

The decision tree for 2026 is straightforward:

- **Under 100K rows:** Skip the index, use sequential scan, revisit when latency crosses 200ms.
- **100K–500K rows, static data:** IVFFlat with tuned `lists` and `probes` values.
- **500K+ rows, any inserts:** HNSW with `m=16`, `ef_construction=64`, and RAM provisioned accordingly.
- **All cases:** Match distance operator to embedding model, pre-filter on metadata columns, and monitor with `EXPLAIN ANALYZE`.

This approach can fail when memory constraints are underestimated. Teams that provision HNSW on underpowered instances often see Postgres thrashing swap — which produces latency worse than a sequential scan. Size your RAM before you size your index.

Looking at the next 6–12 months: pgvector's roadmap on GitHub points toward improved HNSW build parallelism and better memory management. Supabase's infrastructure team has signaled interest in managed vector index compression via scalar quantization, which could cut HNSW memory usage by 4× — making it viable on smaller plans and largely obsoleting IVFFlat for new deployments.

The open question worth tracking: whether Supabase will surface index health and recall metrics directly in the dashboard, removing the need for manual `pg_stat` queries.

Slow vector search is rarely a hardware problem. Check the index type first.

---

> **Key Takeaways**
> - Sequential scans scale linearly — past 100K rows, they become unusable without an index.
> - IVFFlat works for static datasets and RAM-constrained environments; HNSW wins for dynamic data and real-time queries above 500K vectors.
> - Recall matters as much as speed: a 90% recall rate means 10% of relevant documents never reach your LLM.
> - Match your distance operator to your embedding model — using L2 on cosine-optimized embeddings degrades results measurably.
> - Pre-filter on metadata columns and tune `ef_search` at query time to get the most out of HNSW without over-provisioning.
> - Monitor `pg_stat_user_indexes` to confirm your index is actually being used in production.

---

*Hitting a specific recall vs. latency trade-off in your pgvector setup? Drop your schema details in the comments — real numbers make for better analysis.*

## References

1. [pgvector: Embeddings and vector similarity | Supabase Docs](https://supabase.com/docs/guides/database/extensions/pgvector)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
