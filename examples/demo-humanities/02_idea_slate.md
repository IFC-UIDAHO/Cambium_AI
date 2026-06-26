# 02 Idea Slate — Voices of the Press: 19th-Century Newspaper Corpus Study (FICTIONAL DEMO)
*Agent: Ideation-Facilitator | Date: demo | Input: 01_rfp_brief.md, G1 approval*

> G1 decision (Director, Prof. Celeste Armand, demo): **pursue**, contingent on confirming historian
> co-PI (Dr. Tariq Oyelaran, History Dept, verbally agreed) and clearing redistribution rights
> (British Newspaper Archive terms confirmed: research use permitted, no bulk redistribution).

## Research question chosen
**"How did representations of working-class labour shift across the British regional press between
1840 and 1900, and did industrialising vs. agricultural counties differ systematically?"**

Anchor: the language of "the labourer" — what roles, morality, and agency are ascribed in print —
as a lens on class formation and the provincial press's political economy.

## Three candidate approaches

### Idea A — Diachronic Word-Embedding Shift Analysis (fit 9/10)
Train decade-by-decade word2vec models on the full corpus; track semantic drift of target terms
("labourer", "strike", "wages", "factory") using cosine-distance neighbours. Qualitatively
validate drift by close-reading the highest-shifting passages.
- Pros: state-of-practice for diachronic semantics; produces interpretable nearest-neighbour tables;
  directly answers the "how did representations shift" question; clean open-code story.
- Cons: requires OCR cleaning upfront; embedding models sensitive to corpus size per decade — sparse
  early decades need care.
- Data: ~1.2 M pages from fictional BNA research extract (verified above).

### Idea B — Latent Dirichlet Allocation Topic Modelling per Region (fit 7/10)
Fit an LDA model per county-group (industrialising vs. agricultural); compare topic proportions and
keyword loadings over time.
- Pros: exposes thematic structure rather than single-term drift; good comparative angle.
- Cons: topic coherence harder to interpret for non-NLP reviewers; less direct link to the
  "labour language" question; tuning K (number of topics) adds a researcher-degrees-of-freedom risk.

### Idea C — Named-Entity + Sentiment Pipeline (fit 6/10)
Extract person/organisation references near labour keywords; classify sentiment (positive/negative
framing of labour actors) using a fine-tuned period lexicon.
- Pros: produces actor-level framing data; potentially high public interest.
- Cons: period sentiment lexicon does not exist — would require 6+ months to build; high risk of
  anachronistic sentiment scoring; 24-month timeline is tight.

## Recommendation
**Idea A** — diachronic embedding shift is the strongest fit for the research question, the funder's
integration criterion, and the timeline. Supplement with a targeted frequency count of key terms by
region (a lightweight version of Idea B's comparative angle) to anchor the close-reading selections.

**G2 decision needed: which idea advances?**
