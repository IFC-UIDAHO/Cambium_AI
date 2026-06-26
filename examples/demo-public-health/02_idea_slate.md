# 02 Idea Slate — Community Wastewater Surveillance for Infectious Disease Early Warning (FICTIONAL DEMO)
*Agent: Ideation-Facilitator | Date: demo | Input: 01_rfp_brief.md, G1 approval*

> G1 decision (Director, Dr. Priya Sundaram, demo): **pursue**. CBO partner confirmed: fictional
> Riverside Community Health Promoters (RCHP) have agreed in principle; formal MOU in preparation.
> Sites selected: four rural package-plant systems in fictional Millbrook County (pop. ~18,000).

## Three candidate approaches

### Idea A — Passive Moore-Swab Sampling + ddPCR Quantification with SMS Alert System (fit 9/10)
Deploy passive Moore swabs at each of the four site inlet points; collect weekly, extract, and
quantify target pathogens (initially influenza A + norovirus GII) by droplet digital PCR (ddPCR).
Automated threshold logic triggers an SMS/WhatsApp bulletin to RCHP community health workers when
signal exceeds a 2-week rolling baseline by >1.5 SD. Community health workers relay actionable
guidance (testing location, hand-hygiene messaging) via their existing network.
- Pros: proven low-cost passive sampler; ddPCR quantifies accurately at low concentrations;
  SMS alert fits existing CBO infrastructure; interpretable threshold logic builds trust.
- Cons: weekly cadence may miss fast-rising outbreaks; need local health-worker training.
- Equity note: no internet connection assumed for households; alert pathway goes through CBO, not
  directly to residents.
- Lab method gap: requires validation of swab elution protocol for low-flow (< 50 L/min) systems —
  planned for months 1–4.

### Idea B — Automated Refrigerated Composite Sampler + qPCR (fit 7/10)
Install automated 24-hour composite samplers at each site; analyse by standard qPCR.
- Pros: higher temporal resolution (daily composites possible); widely published method.
- Cons: composite samplers cost ~$8 K each × 4 sites = ~$32 K equipment alone; maintenance burden
  on rural sites; qPCR less sensitive than ddPCR at low concentrations common in small systems.
- Budget impact: likely exceeds $210 K without reducing site count to 2.

### Idea C — Grab Sampling + Metagenomic Sequencing (fit 5/10)
Collect grab samples twice weekly; perform shotgun metagenomic sequencing for broad pathogen
surveillance.
- Pros: pathogen-agnostic; could detect novel or unexpected pathogens.
- Cons: 2–5 day turnaround prohibits early-warning use case; cost per sample ($400–800) limits
  frequency; bioinformatics pipeline requires expertise not currently on team; 30-month timeline
  insufficient to validate and deploy.

## Recommendation
**Idea A** — Moore-swab / ddPCR / SMS pipeline is the strongest fit: low cost, actionable output
for the CBO, validated sensitivity at low concentrations, and achievable within budget and timeline.
Build in a month-4 protocol-validation milestone as a go/no-go checkpoint before full deployment.

**G2 decision needed: which idea advances?**
