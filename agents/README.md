# KaibanJS Agent System

Agentic task management system with 8 specialized AI agents.

## 🤖 Agents

### Cloud Agents (Anthropic Claude Sonnet 4.5)
- **Felix** (Feature Architect) - Analyzes new features and breaks them down
- **Quinn** (Quality Inspector) - Reviews code quality and best practices

### Cloud Agents (OpenAI GPT-4)
- **Miguel** (Migration Architect) - Plans complex system migrations

### Local Agents (Ollama Llama 3.1)
- **Marcus** (Maintenance Specialist) - Identifies technical debt
- **Betty** (Bug Hunter) - Analyzes bugs and traces root causes
- **Eliza** (Estimation Engine) - Calculates story points
- **Tessa** (Test Engineer) - Generates test scenarios
- **Diana** (Documentation Writer) - Creates technical documentation

## 📁 Directory Structure

```
backend/agents/
├── configs/          # Agent configurations
│   └── agents.ts     # KaibanJS Agent instances
├── types/            # TypeScript type definitions
│   └── AgentTypes.ts # Agent roles and configs
├── workflows/        # Workflow definitions
│   └── featureAnalysis.ts  # Example workflow
├── tools/            # Agent tools (future)
├── index.ts          # Main entry point
├── package.json      # Dependencies
├── tsconfig.json     # TypeScript config
└── .env.example      # Environment template
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
cd backend/agents
cp .env.example .env
# Edit .env with your API keys
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Setup Ollama (for local agents)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull llama3.1:8b

# Verify it's running
ollama list
```

### 4. Build TypeScript

```bash
npm run build
```

### 5. Test the System

```bash
node dist/index.js
```

## 🔧 Development

### Run in Development Mode

```bash
npm run dev
```

### Build for Production

```bash
npm run build
npm start
```

## 📋 Example Workflow

The **Feature Analysis Workflow** demonstrates agent collaboration:

1. **Feature Architect** analyzes requirements
2. **Quality Inspector** reviews the analysis
3. **Estimation Engine** calculates story points
4. **Test Engineer** defines test scenarios
5. **Documentation Writer** creates specifications

```typescript
import { analyzeFeature } from './backend/agents';

const result = await analyzeFeature('Add user authentication with OAuth2 support');
console.log(result);
```

## 🔗 Integration with FastAPI

Week 5 Day 4 (Thursday) we'll create FastAPI endpoints:

```python
# backend/app/api/agents.py
@router.post("/analyze-feature")
async def analyze_feature(request: FeatureRequest):
    # Call KaibanJS agents via subprocess or API
    result = await call_agents(request.description)
    return result
```

## 📚 Next Steps

- **Tuesday**: Define all 8 agent types with detailed configurations
- **Wednesday**: Create KaibanBoard configuration and task assignment logic
- **Thursday**: Integrate with FastAPI backend (Celery + Redis)
- **Friday**: Write tests and complete documentation

## 🎯 Success Metrics

- ✅ 8 agents defined with roles and backgrounds
- ✅ Feature analysis workflow operational
- ✅ TypeScript compilation successful
- ⏳ Integration with FastAPI (Week 5 Day 4)
- ⏳ Task queue setup (Week 5 Day 4)

## 📖 Resources

- [KaibanJS GitHub](https://github.com/zeeneddie/kaibanjs)
- [KaibanJS Documentation](https://docs.kaibanjs.com)
- [Fasenplan](../../fasenplan.md) - Complete project planning
