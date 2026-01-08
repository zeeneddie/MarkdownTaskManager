# LLM Configuration - All Local Ollama Models

**Last Updated:** 2025-11-13

## Agent → Model Mapping

Alle 10 agents gebruiken nu lokale Ollama modellen voor volledige privacy en geen API kosten.

### Code Specialists (qwen2.5-coder:7b)
Deze agents werken met code en hebben gespecialiseerde code kennis nodig:

1. **Felix** (Feature Architect) → `qwen2.5-coder:7b`
   - Architecture decisions
   - Tech stack selection
   - Feature decomposition

2. **Marcus** (Maintenance Specialist) → `qwen2.5-coder:7b`
   - Code refactoring
   - Technical debt analysis
   - Code quality improvements

3. **Quinn** (Quality Inspector) → `qwen2.5-coder:7b`
   - Code reviews
   - Best practices validation
   - Quality metrics

4. **Tessa** (Test Engineer) → `qwen2.5-coder:7b`
   - Test strategy
   - Test code generation
   - Coverage analysis

### Reasoning Specialists (deepseek-r1:latest)
Deze agents doen complexe reasoning en planning:

5. **Eliza** (Estimation Engine) → `deepseek-r1:latest`
   - Effort estimation
   - Complexity analysis
   - Resource planning

6. **Miguel** (Migration Architect) → `deepseek-r1:latest`
   - Migration planning
   - Risk analysis
   - Technology transitions

7. **Peter** (Product Owner) → `deepseek-r1:latest`
   - Business case analysis
   - ROI calculation
   - Strategic thinking

### Debugging Specialist (codellama:latest)
8. **Betty** (Bug Hunter) → `codellama:latest`
   - Root cause analysis
   - Stack trace parsing
   - Debug strategies

### Documentation Specialist (mistral:latest)
9. **Diana** (Documentation Writer) → `mistral:latest`
   - Technical writing
   - Documentation generation
   - README files

### Planning Specialist (qwen2.5:7b)
10. **Paul** (Project Lead) → `qwen2.5:7b`
    - Sprint planning
    - Project management
    - Resource allocation

## Model Characteristics

### qwen2.5-coder:7b (4.7 GB)
- **Specialty:** Code generation, analysis, architecture
- **Speed:** Fast
- **Use case:** All code-related tasks
- **Agents:** Felix, Marcus, Quinn, Tessa (4 agents)

### deepseek-r1:latest (5.2 GB)
- **Specialty:** Complex reasoning, planning, analysis
- **Speed:** Medium (thorough reasoning)
- **Use case:** Strategic decisions, estimations
- **Agents:** Eliza, Miguel, Peter (3 agents)

### codellama:latest (3.8 GB)
- **Specialty:** Code understanding, debugging
- **Speed:** Fast
- **Use case:** Bug analysis, root cause finding
- **Agents:** Betty (1 agent)

### mistral:latest (4.4 GB)
- **Specialty:** Natural language, documentation
- **Speed:** Fast
- **Use case:** Writing, documentation
- **Agents:** Diana (1 agent)

### qwen2.5:7b (4.7 GB)
- **Specialty:** General purpose, planning
- **Speed:** Fast
- **Use case:** Project planning, management
- **Agents:** Paul (1 agent)

## Timeout Configuration

**Default Timeout:** 30 minutes (1800 seconds)

**Important:** Timeouts are **soft limits** - alleen waarschuwingen, geen automatisch afbreken!

**Warning Schedule:**
- ⏰ 5 minutes: First notification
- ⏰ 10 minutes: Second notification
- ⏰ 20 minutes: Third notification
- ⏰ 30 minutes: Fourth notification

**User Control:**
- Alleen de gebruiker bepaalt wanneer een proces wordt afgebroken
- Logs geven progress updates
- Geen automatische kills

## Benefits van All-Local Setup

✅ **Privacy:** Alle data blijft lokaal
✅ **Kosten:** Geen API kosten
✅ **Snelheid:** Directe access, geen netwerk latency
✅ **Offline:** Werkt zonder internet
✅ **Controle:** Volledige controle over modellen
✅ **Schaalbaarheid:** Onbeperkt gebruik

## Resource Usage

**Total Disk Space:** ~24 GB voor alle 5 modellen
**RAM Usage:** ~4-8 GB per actieve agent (afhankelijk van model)
**GPU:** Optional maar recommended voor snelheid

## Testing

Alle agents zijn getest en werken met lokale Ollama modellen.

Test met:
```bash
curl -X POST http://localhost:8000/api/workflows/analyze \
  -H "Content-Type: application/json" \
  -d '{"description": "Add user authentication"}'
```

## Future Considerations

- **Model Updates:** Ollama models kunnen geüpdatet worden met `ollama pull <model>`
- **Custom Models:** Eigen fine-tuned modellen kunnen toegevoegd worden
- **Hybrid Setup:** Indien gewenst kunnen specifieke agents naar cloud teruggeschakeld worden
- **Performance Tuning:** Model parameters (temperature, top_p) kunnen per agent aangepast worden

---

**Status:** ✅ All 10 agents configured with local Ollama models
**Last Tested:** 2025-11-13
**Performance:** Excellent with available models
