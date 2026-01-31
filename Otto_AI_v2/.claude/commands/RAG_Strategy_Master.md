# Analyze RAG Strategy

Analyze this project and recommend a RAG strategy. Work in phases, completing each before proceeding.

**Reference:** Consult `.claude/commands/rag-strategy-rubric.md` for strategy details and scoring criteria.

$ARGUMENTS

---

## PHASE 1: DISCOVER

**Goal:** Map the project structure and read key files.

```bash
# Run these commands
find . -maxdepth 3 -name "*.md" -o -name "README*" 2>/dev/null | head -10
find . -type f \( -name "*.py" -o -name "*.ts" \) -not -path "*/node_modules/*" 2>/dev/null | head -20
grep -rl "embed\|vector\|chunk\|retriev" --include="*.py" --include="*.ts" . 2>/dev/null | head -5
```

**Read:** README, main source files, any existing RAG code.

**Output a summary:**
```
PROJECT: [name]
PURPOSE: [1 sentence]
LANGUAGE: [Python/TypeScript]
FRAMEWORK: [if any]
EXISTING_RAG: [Yes/No - brief description]
```

**checkpoint:** Say "Phase 1 complete. Proceeding to Phase 2." before continuing.

---

## PHASE 2: PROFILE

**Goal:** Answer these questions from what you learned.

```yaml
DOMAIN: [Healthcare|Legal|Finance|Tech|General]
DOCUMENTS:
  types: [PDF|Markdown|Code|Mixed]
  length: [Short <500w|Medium|Long >2000w]
  count: [estimate]
  has_relationships: [Yes|No]
QUERIES:
  complexity: [Simple|Multi-faceted|Multi-hop]
  typical_length: [Brief|Detailed]
CONSTRAINTS:
  latency: [<500ms|<1s|Flexible]
  accuracy: [Critical|High|Baseline]
  cost: [Minimize|Moderate|Quality-first]
TRAINING_DATA: [Yes - count|No]
```

**checkpoint:** Say "Phase 2 complete. Proceeding to Phase 3." before continuing.

---

## PHASE 3: EVALUATE

**Goal:** Score the top strategies for this project.

**First:** Read `.claude/commands/rag-strategy-rubric.md` for scoring criteria.

**Then:** Score each relevant strategy (1-5):
- 5 = Perfect fit
- 3 = Acceptable  
- 1 = Poor fit

### Ingestion Strategies

| Strategy | Fit | Rationale |
|----------|-----|-----------|
| Context-Aware Chunking | /5 | [why] |
| Contextual Retrieval | /5 | [why] |
| Late Chunking | /5 | [why] |
| Parent-Child Chunks | /5 | [why] |

### Query Strategies

| Strategy | Fit | Rationale |
|----------|-----|-----------|
| Re-ranking | /5 | [why] |
| Hybrid Search | /5 | [why] |
| Query Expansion | /5 | [why] |
| Multi-Query | /5 | [why] |
| Agentic RAG | /5 | [why] |
| Self-Reflective | /5 | [why] |

**checkpoint:** Say "Phase 3 complete. Proceeding to Phase 4." before continuing.

---

## PHASE 4: RECOMMEND

**Goal:** Select the strategy combination.

**Decision logic:**
- Long docs + context loss → Contextual Retrieval
- Need precision → Re-ranking
- Brief queries → Query Expansion  
- Varied query types → Agentic RAG
- Default baseline → Context-Aware Chunking + Re-ranking

**Output:**
```
RECOMMENDED INGESTION: [strategy]
RECOMMENDED QUERY: [strategy or combination]
RATIONALE: [2-3 sentences]
```

**checkpoint:** Say "Phase 4 complete. Proceeding to Phase 5." before continuing.

---

## PHASE 5: SPECIFY

**Goal:** Generate implementation specification.

Create a file `rag-strategy-spec.md` with:

1. **Architecture diagram** (ASCII)
2. **Dependencies** (pip/npm install commands)
3. **Configuration** (env vars)
4. **Code for each selected strategy** (complete, working)
5. **Database schema** (if needed)
6. **Implementation checklist**

Use patterns from: https://github.com/coleam00/ottomator-agents/tree/main/all-rag-strategies

**Save the file** and present it.

---

## EXECUTION RULES

1. **Complete each phase fully** before proceeding
2. **Say the checkpoint phrase** after each phase
3. **If uncertain**, state what's unclear and make a reasonable assumption
4. **Code must be complete** - no pseudocode or placeholders
5. **Match project's existing style** in code examples
