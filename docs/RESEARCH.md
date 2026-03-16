# Research Context — MHG POS Tagging

Academic context for the planned publication. This doc captures the research landscape so that Related Work sections and framing decisions have a traceable basis.

## Research Question

**Which model tags Middle High German POS best?** Until now, there was no way to answer this objectively. There are trained taggers (TreeTagger ~91%, spaCy MHG model) and a gold-standard corpus (ReM), but no benchmark that enables head-to-head comparison on the same data with the same metrics. This project builds that benchmark — technology-agnostic, so any tagger (frontier LLMs like Gemini 3.1 Pro or Claude Opus 4.6, encoder models, classical taggers) can compete on equal ground.

## Research Gap

The gap is not "MHG POS tagging is unsolved" — it's that **results aren't comparable**. Schulz & Ketschik (2019) report ~91% with TreeTagger, but on their own train/test split. The MHDBDB Gemini skill reports ~100% on normalized texts, but on MHDBDB data, not ReM. Without a shared ground truth and evaluation protocol, these numbers mean nothing relative to each other.

## Existing MHG POS Taggers

| Tagger | Type | Tagset | Accuracy | Reference |
|--------|------|--------|----------|-----------|
| TreeTagger + MHG params | Classical (HMM/decision tree) | HiTS | ~91% | Schulz & Ketschik 2019 |
| spaCy v3 MHG model | Neural (tok2vec+tagger) | HiTS | — | MHDBDB project, GitHub |
| Gemini 3.1 Pro (MHDBDB skill) | Frontier LLM | MHDBDB 19-tag | ~100% on normalized | Unpublished, sibling project |

Key reference: Schulz, Sarah & Ketschik, Nora (2019). "From 0 to 10 million annotated words: part-of-speech tagging for Middle High German." *Language Resources and Evaluation* 53, 693–712.

## HiTS Tagset & ReM Corpus

- **HiTS:** Dipper, S.; Donhauser, K.; Klein, T.; Linde, S.; Müller, S.; Wegera, K.-P. (2013). "HiTS: ein Tagset für historische Sprachstufen des Deutschen." *JLCL* 28(1), 85–137.
- **ReM:** Roussel, A.; Klein, T.; Dipper, S.; Wegera, K.-P.; Wich-Reif, C. (2024). Referenzkorpus Mittelhochdeutsch (1050–1350), Version 2.1. ISLRN 937-948-254-174-0.
- **HiNTS:** Variant for Middle Low German, derived from HiTS. Barteld et al. (2015).

## LLMs for Historical Language POS Tagging

Emerging field — no work on MHG specifically, but close analogues:

| Paper | Language | Models | Finding |
|-------|----------|--------|---------|
| Schöffel et al. 2025 | Old Occitan | Open-source LLMs | Critical limitations with orthographic/syntactic variability |
| Vidal-Gorène et al. 2026 | Armenian, Georgian, Greek, Syriac | GPT-4, Mistral | Competitive few-shot/zero-shot performance |
| Riemenschneider & Frank 2023 | Ancient Greek | RoBERTa, T5 | Domain-adapted encoder models effective |
| Volk et al. 2024 | Early New High German | GPT-4, Gemini | Translation, not POS — but tests LLMs on historical German |

Full references:
- Schöffel, M. et al. (2025). "Modern Models, Medieval Texts: A POS Tagging Study of Old Occitan." *NLP4DH 2025*, 334–349.
- Vidal-Gorène, C. et al. (2026). "Under-resourced studies of under-resourced languages." *LoResLM@EACL 2026*. arXiv 2602.15753.
- Riemenschneider, F. & Frank, A. (2023). "Exploring Large Language Models for Classical Philology." *ACL 2023*.
- Volk, M. et al. (2024). "LLM-based Translation Across 500 Years." *KONVENS 2024*.

## Historical German NLP — Broader Context

- **GHisBERT:** Beck & Köllner (2023). BERT trained on OHG+MHG+ENHG+NHG. *LChange@ACL 2023*. Available on HuggingFace.
- **Normalization:** Bollmann (2019). "A Large-Scale Comparison of Historical Text Normalization Systems." *NAACL 2019*.
- **Evaluation:** Ortmann, Roussel & Dipper (2019). "Evaluating Off-the-Shelf NLP Tools for German." *KONVENS 2019*.
- **Topological fields:** Ortmann & Dipper (2020). Automatic identification in historical German. *LaTeCH-CLfL 2020*.

## Shared Tasks / Benchmarks for Historical Languages

| Task | Language | Venue | Relevance |
|------|----------|-------|-----------|
| EvaLatin 2020/2022/2024 | Latin | LT4HALA | POS + lemmatization benchmark, cross-genre |
| EvaHan 2022/2024 | Ancient Chinese | LT4HALA | Historical language NLP shared task |
| LT4HALA Workshop | Multiple | LREC/COLING | Main venue for historical language NLP |
| NLP4DH Workshop | Multiple | Various | DH-focused NLP |

**None for MHG.** This is the gap we fill.

## Our Contribution

1. **First MHG POS tagging benchmark with validated ground truth** — the ReM→HiTS→MHDBDB pipeline makes objective head-to-head comparison possible for the first time
2. **Technology-agnostic:** same interface and metrics for frontier LLMs, encoder models, classical taggers — models come and go, the benchmark stays
3. **Tagset bridge:** HiTS (73 tags) → MHDBDB (19 tags) mapping, empirically validated against full ReM v2.1 (2.58M tokens)
4. **Reproducible:** Pipeline code + documented methodology. ReM is freely available (CC BY-SA 4.0).

## Paper Framing

The core narrative: "We built the ground truth pipeline that makes comparison possible, then used it to compare." The specific models tested (currently Gemini 3.1 Pro, Claude Opus 4.6, ...) are examples — the contribution is the infrastructure, the results are the demonstration.

Decision on exact framing deferred until we have results.
