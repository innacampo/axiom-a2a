# **AXIOM: Automated X-reference Intelligence & Outcomes for Menopause**

### **An Evidence-Based Multi-Agent Orchestrator Connecting the Silos of Midlife Women's Health via Google ADK and Model Context Protocol (MCP)**

## **1\. Executive Summary & Inspiration: Sarah's Story**

Sarah is 47\. Over an 18-month window, she consulted four independent medical specialists:

1. A **cardiologist** flagged elevated LDL cholesterol and borderline hypertension, recommending statin therapy.  
2. An **orthopedist** diagnosed and began treating a painful "frozen shoulder" (adhesive capsulitis) with physical therapy and steroid injections.  
3. Her **primary care physician (GP)** prescribed an SSRI to manage sudden onset anxiety and sleep fragmentation.  
4. Her **gynecologist** noted irregular menstrual cycles, offering a brief: *"That is just perimenopause. It is normal."*

Four board-certified physicians. Four distinct diagnostic codes. Four separate treatment pathways. **Not a single clinician connected them.** This medical disconnect did not happen because clinical evidence was missing. It happened because medicine operates in highly isolated specialty silos, and no accessible, point-of-care tool exists to cross-reference multi-system symptoms back to a single endocrine driver.  
Every one of Sarah’s symptoms is a classic physiological manifestation of systemic estrogen decline. Estrogen receptors are densely populated in vascular endothelium, joint synovial fluid, the central nervous system, and reproductive tissues. Yet, clinicians treating midlife women in 2026 are frequently constrained by time, cognitive overload, and specialty-specific guidelines. They are often working from baseline clinical training completed decades prior, rather than the latest cross-disciplinary meta-analyses.  
**AXIOM (Automated X-reference Intelligence & Outcomes for Menopause)** was built to break down these silos. AXIOM is an evidence-based clinical co-pilot designed to help individuals, families, and point-of-care clinicians hold complex medical presentations together in one unified conversation. AXIOM is an **A2A (Agent-to-Agent) \+ MCP system**. It utilizes a decoupled architecture where a high-level Python ADK Host Agent orchestrates overall clinical reasoning, task routing, and user privacy, while communicating via the **Model Context Protocol (MCP)** to downstream, specialized tool agents that manage vector retrieval and real-time medical registry verification.

## **2\. The Problem: The Neuroendocrine Fragmentation Gap**

By 2030, an estimated 1.2 billion women worldwide will be actively navigating perimenopause or menopause \[1\]. This transition can last up to a decade, during which estrogen fluctuation and eventual depletion fundamentally alter multi-organ physiology. The medical evidence linking endocrine decline to cardiovascular disease, musculoskeletal deterioration, psychiatric vulnerability, and metabolic dysfunction is extensive, yet scattered across tens of thousands of peer-reviewed papers.  
Standard Search Engines and general-purpose LLM architectures fail to resolve this problem at the point of care:

* **Generative Hallucinations:** Broad LLMs hallucinate medical associations or cite non-existent publications, making them dangerous for clinical reasoning.  
* **Semantic Similarity Limits (Standard RAG):** Standard Retrieval-Augmented Generation (RAG) relies purely on cosine similarity of text embeddings. In medicine, a highly cited, outlier case report from 2012 can easily outscore a 2025 double-blind randomized controlled trial (RCT) on raw semantic distance, leading to poor clinical ground truth.  
* **The Retraction & Trust Problem:** Thousands of papers are corrected, flagged with expressions of concern, or retracted every year. Surfacing retracted or unverified research creates an immediate patient safety risk.  
* **Data Privacy Concerns (PHI):** Traditional cloud-based AI systems risk exposing Protected Health Information (PHI) when querying public search engines or unencrypted third-party model APIs.

AXIOM addresses these infrastructure limitations directly. It is a local-first, trust-verified clinical agent that bridges medical silos, tracks and ranks scientific evidence, and synthesizes complex symptom patterns securely on-device.

## **3\. System Architecture & The Orchestration Loop**

AXIOM’s architecture separates the high-level cognitive orchestration (the **Host Agent**) from the low-level data and tool execution layers (the **MCP Client**). The system is built around a strictly governed, state-driven loop:  
![][image1]    \+--------------------------------------------------------------------------+  
    |                             NEXT.JS UI                                   |  
    |               (Real-time Streaming & Audit Trace Rendering)             |  
    \+------------------------------------+-------------------------------------+  
                                         |  
                       SSE (Server-Sent Events) Stream  
                                         |  
    \+------------------------------------+-------------------------------------+  
    |                           FASTAPI GATEWAY                                |  
    |                     (Session State & SSE Routers)                        |  
    \+------------------------------------+-------------------------------------+  
                                         |  
                                  Internal Call  
                                         |  
    \+------------------------------------+-------------------------------------+  
    |                       ADK AGENT ORCHESTRATOR                             |  
    |          (Gemini-2.0-Flash / Vertex AI / Safe Concept Extractor)         |  
    \+------------------------------------+-------------------------------------+  
                                         |  
                             Model Context Protocol (MCP)  
                                         |  
    \+------------------------------------+-------------------------------------+  
    |                         AXIOM MCP SERVER                                 |  
    |                       (Python / FastMCP)                                 |  
    \+---------------+--------------------+------------------+------------------+  
                    |                                       |  
          \[query\_evidence\]                         \[search\_pubmed\]  
          \[ingest\_to\_chroma\]                       \[check\_retractions\]  
                    |                                       |  
    \+---------------+--------------------+      \+----------+-------------------+  
    |           LOCAL CHROMADB                   |       NCBI ENTREZ API        |  
    |  (sqlite / all-MiniLM-L6-v2 Embeddings)   |    (Live PubMed / Retractions)  
    \+--------------------------------------------+------------------------------+

The Orchestration Flow

1. **Perceive:** The AXIOM Host Agent receives a multi-specialty clinical presentation along with a user-defined confidence threshold.  
2. **Plan & Protect (The PHI Gate):** Before any external tool call, the agent filters raw clinical text, stripping names, MRNs, or specific dates. It extracts and abstracts raw symptoms into high-level, standardized pathophysiological concepts (e.g., transmuting "Sarah, a 47-year-old female with shoulder pain and high cholesterol" into *"perimenopause, hypercholesterolemia, adhesive capsulitis"*).  
3. **Act (Step-Wise Tool Invocation):**  
   * The agent invokes the local vector store via query\_evidence to retrieve pre-seeded, high-quality local literature.  
   * If local confidence or semantic match falls below the user's defined threshold, the agent transitions to a live PubMed fallback via search\_pubmed or ingest\_to\_chroma.  
4. **Observe & Score:** Retrieved documents are parsed, checked for active retractions via check\_retractions, and run through AXIOM's custom **Composite Scoring Engine**.  
5. **Iterate:** If the top-scoring literature fails to meet the confidence threshold, the agent automatically reformulates its query (e.g., dynamically prepending terms like "systematic review" or "clinical trial") and re-runs the loop up to a predefined MAX\_RETRIES limit.  
6. **Synthesize:** Once stopping conditions are satisfied, the agent synthesizes a highly structured, citable clinical explanation grounded strictly within the retrieved literature.

## **4\. Technical Implementation & The Math Behind the Engine**

### **A. The Core ADK Host Agent**

The orchestration layer is built using the **Google Agent Development Kit (ADK)**. Below is the implementation of the primary cognitive routing layer, demonstrating strict environment isolation, PHI gating, and tool integration.

### **B. The Composite Evidence Scoring Algorithm**

To prevent outdated, low-tier, or biased studies from polluting clinical recommendations, AXIOM implements a mathematical scoring system directly into the retrieval pipeline.

For each retrieved paper $i$, AXIOM calculates a **Composite Score ($S\_i$)**:

$$S\_i \= \\text{Similarity}\_i \\times \\text{Hierarchy}\_i \\times \\text{Recency}\_i \\times \\text{Safety}\_i$$

#### **1\. Semantic Similarity ($\\text{Similarity}\_i$)**

Calculated as the cosine similarity between the query embedding vector $q$ and the document abstract embedding vector $d\_i$ generated locally using the all-MiniLM-L6-v2 Sentence Transformer model:

$$\\text{Similarity}\_i \= \\frac{q \\cdot d\_i}{\\|q\\| \\|d\_i\\|}$$

#### **2\. Study-Type Hierarchy Boost ($\\text{Hierarchy}\_i$)**

We map study designs to a strict, evidence-based weight scale. This ensures that meta-analyses and systematic reviews are naturally promoted above descriptive case reports:

$$\\text{Hierarchy}\_i \= 1.0 \+ \\text{Weight}\_{\\text{design}}$$  
Where:

* **Systematic Review / Meta-Analysis:** $+0.50$  
* **Randomized Controlled Trial (RCT):** $+0.40$  
* **Cohort / Observational Study:** $+0.25$  
* **Case Series / Case Report:** $+0.00$  
* **Editorial / Expert Opinion:** $-0.15$

#### **3\. Exponential Recency Decay ($\\text{Recency}\_i$)**

Medical evidence depreciates in value over time as new discoveries alter standard guidelines. We model this depreciation utilizing an exponential decay function:

$$\\text{Recency}\_i \= e^{-\\lambda (t\_{\\text{current}} \- t\_{\\text{pub}, i})}$$  
Where $t\_{\\text{current}} \- t\_{\\text{pub}, i}$ represents the age of the study in years, and $\\lambda$ is a decay coefficient set to $0.05$ (corresponding to a half-life of approximately 14 years). This guarantees that a 2026 study receives a natural boost over an otherwise identical study published in 2012\.

#### **4\. Safety Multiplier ($\\text{Safety}\_i$)**

This is a binary and scalar safety switch dependent on retraction status:

$$\\text{Safety}\_i \= \\begin{cases} 0.0 & \\text{if Retracted} \\\\ 0.5 & \\text{if Expression of Concern} \\\\ 1.0 & \\text{if Clear of Flags} \\end{cases}$$  
Any paper flagged as retracted by our live PubMed check is permanently zeroed out and omitted from downstream LLM context windows, protecting patient safety.

### **C. The AXIOM FastMCP Server**

The MCP server hosts our data and tools using the Python-native FastMCP framework. It maintains the local vector store (using SQLite to persist ChromaDB embeddings) and links to the NCBI Entrez API.

\#\# 5\. Production Deployment & Cloud Readiness

To ensure the project is enterprise-grade, highly deployable, and optimized for production environments, AXIOM is fully containerized and configured for rapid hosting on \*\*Google Cloud Run\*\*. 

\#\#\# A. Core Challenge Resolved: Local Embedding Cold-Starts  
A common architectural flaw in containerized AI deployments is downloading heavy machine learning model weights at container startup. This results in severe cold-start times (often up to 45 seconds of idle latency as the container fetches model weights from public hubs like HuggingFace). 

To solve this, AXIOM’s production \`Dockerfile\` \*\*pre-bakes\*\* the Sentence Transformer model weights directly into the container filesystem layer during the Docker build stage. This decreases cold-start latency to under 2 seconds.

\#\#\# B. Automated Cloud Run Deployment Script  
The accompanying deployment script automates Cloud Build compilation and spins up a managed instance on Google Cloud Run with single-command simplicity.

\---

\#\# 7\. Key Accomplishments & Lessons Learned

Developing AXIOM throughout this capstone project surfaced several critical clinical AI insights:

1\. \*\*Medical Evidence is a Trust Problem, Not a Search Problem:\*\* Standard semantic search algorithms do not understand scientific rigor. The creation of AXIOM’s \*\*Composite Scoring Module\*\* successfully encoded decades of evidence-based medical hierarchies directly into the retrieval ranking algorithm, demonstrating that raw cosine similarity is an insufficient metric for clinical application.  
2\. \*\*Retraction Checking is a Non-Negotiable Safety Safeguard:\*\* Generative AI platforms that ingest unchecked medical datasets risk citing falsified, flawed, or retracted papers. Building the automated \`check\_retractions\` pipeline directly into the core MCP server established a strong safety guardrail that protects patient-centric care.  
3\. \*\*Orchestration Dictates Usability:\*\* The development of the Google ADK Host Agent highlighted that while toolsets are vital, the orchestration model is what determines whether a clinician or family member can safely act on the returned results. Explicit instruction design—forcing the agent to parse patient files, extract clean concepts, run safety checks, and frame uncertainty—matters just as much as database speed.

[image1]: <data:image/png;base64,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>