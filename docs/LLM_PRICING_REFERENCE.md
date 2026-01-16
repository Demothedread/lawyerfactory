# LLM Pricing Reference Guide

**LawyerFactory - Bartleby AI Legal Clerk**  
**Last Updated**: October 23, 2025

---

## 📊 Supported Language Models & Pricing

### OpenAI Models

#### **GPT-5** (Default - Flagship Model)
- **Model ID**: `gpt-5`
- **Description**: Most advanced reasoning and legal analysis capabilities
- **Input**: $0.030 per 1K tokens
- **Output**: $0.120 per 1K tokens
- **Context Window**: 128K tokens
- **Best For**: Complex legal reasoning, multi-document analysis, advanced case law research
- **Estimated Cost/Hour**: $3.60 - $7.20 (typical legal workflow)

#### **GPT-5-mini** (Cost-Effective)
- **Model ID**: `gpt-5-mini`
- **Description**: Balanced performance and cost for routine legal tasks
- **Input**: $0.015 per 1K tokens
- **Output**: $0.060 per 1K tokens
- **Context Window**: 128K tokens
- **Best For**: Evidence review, citation extraction, document summarization
- **Estimated Cost/Hour**: $1.80 - $3.60

#### **GPT-5-nano** (Ultra-Efficient)
- **Model ID**: `gpt-5-nano`
- **Description**: Fast, lightweight model for simple tasks
- **Input**: $0.005 per 1K tokens
- **Output**: $0.020 per 1K tokens
- **Context Window**: 64K tokens
- **Best For**: Quick queries, fact extraction, basic research
- **Estimated Cost/Hour**: $0.60 - $1.20

#### **GPT-4o** (Multimodal Vision)
- **Model ID**: `gpt-4o`
- **Description**: Multimodal model with vision capabilities for document images
- **Input**: $0.005 per 1K tokens
- **Output**: $0.015 per 1K tokens
- **Vision Input**: $0.001 per image
- **Context Window**: 128K tokens
- **Best For**: OCR on scanned documents, charts, exhibits, handwritten notes
- **Estimated Cost/Hour**: $0.60 - $1.80

#### **GPT-o1** (Reasoning-Optimized)
- **Model ID**: `gpt-o1`
- **Description**: Enhanced reasoning with chain-of-thought processing
- **Input**: $0.015 per 1K tokens
- **Output**: $0.060 per 1K tokens
- **Context Window**: 128K tokens
- **Best For**: Complex legal arguments, multi-step reasoning, strategy planning
- **Estimated Cost/Hour**: $1.80 - $3.60

#### **GPT-o3** (Advanced Reasoning)
- **Model ID**: `gpt-o3`
- **Description**: Latest reasoning model with improved legal domain performance
- **Input**: $0.010 per 1K tokens
- **Output**: $0.040 per 1K tokens
- **Context Window**: 128K tokens
- **Best For**: Case strategy, complex statutory interpretation, appellate arguments
- **Estimated Cost/Hour**: $1.20 - $2.40

---

### Anthropic Claude Models

#### **Claude 3.5 Sonnet** (Recommended)
- **Model ID**: `claude-3-5-sonnet-20241022`
- **Description**: Excellent legal reasoning with strong citation accuracy
- **Input**: $0.003 per 1K tokens
- **Output**: $0.015 per 1K tokens
- **Context Window**: 200K tokens
- **Best For**: Long-form legal writing, comprehensive case analysis
- **Estimated Cost/Hour**: $0.36 - $1.80

#### **Claude 3 Opus**
- **Model ID**: `claude-3-opus-20240229`
- **Description**: Anthropic's most capable model for complex tasks
- **Input**: $0.015 per 1K tokens
- **Output**: $0.075 per 1K tokens
- **Context Window**: 200K tokens
- **Best For**: High-stakes litigation documents, appellate briefs
- **Estimated Cost/Hour**: $1.80 - $4.50

#### **Claude 3 Haiku** (Fast & Affordable)
- **Model ID**: `claude-3-haiku-20240307`
- **Description**: Fast responses for simple legal queries
- **Input**: $0.00025 per 1K tokens
- **Output**: $0.00125 per 1K tokens
- **Context Window**: 200K tokens
- **Best For**: Quick fact-checking, simple research, drafting assistance
- **Estimated Cost/Hour**: $0.03 - $0.15

---

### GitHub Copilot Models

#### **GitHub Copilot Chat**
- **Model ID**: `github-copilot`
- **Description**: Access to GitHub's multi-model chat interface
- **Pricing**: Included with GitHub Copilot subscription ($10-$19/month)
- **Models Available**:
  - GPT-4 Turbo
  - GPT-4o
  - Claude 3.5 Sonnet
  - Claude 3 Opus
- **Context Window**: Varies by underlying model
- **Best For**: Integrated development environment, code-assisted legal research
- **Estimated Cost**: Fixed monthly fee (unlimited usage within fair use)

---

### Ollama Localhost Models (Free)

#### **Localhost LLM via Ollama**
- **Model ID**: `ollama-localhost`
- **Description**: Run open-source models locally (Llama 3.1, Mistral, etc.)
- **Pricing**: **FREE** (no API costs)
- **Requirements**:
  - Local Ollama installation
  - Hardware: 8GB+ RAM (16GB+ recommended)
  - Disk Space: 4-45GB per model
- **Supported Models**:
  - **Llama 3.1 70B**: Best quality, requires 40GB RAM
  - **Llama 3.1 8B**: Balanced, requires 8GB RAM
  - **Mistral 7B**: Fast, requires 6GB RAM
  - **Phi-3 Mini**: Ultra-light, requires 4GB RAM
- **Context Window**: 8K-128K tokens (model-dependent)
- **Best For**: Privacy-sensitive cases, unlimited usage, offline work
- **Estimated Cost**: $0.00 (electricity costs only)

---

## 💡 Cost Optimization Strategies

### Hybrid Approach (Recommended)
Use different models for different tasks to optimize cost:

1. **Phase A01 (Intake)**: GPT-4o for OCR, GPT-5-nano for metadata extraction
2. **Phase A02 (Research)**: GPT-5 or Claude 3.5 Sonnet for legal research
3. **Phase A03 (Outline)**: GPT-o3 for complex reasoning
4. **Phase B01 (Review)**: GPT-5-mini for validation checks
5. **Phase B02 (Drafting)**: Claude 3.5 Sonnet for long-form writing
6. **Phase C01 (Editing)**: GPT-5-nano for grammar and formatting
7. **Bartleby Chat**: GPT-5-mini or Claude Haiku for interactive assistance

**Estimated Hybrid Cost**: $0.50 - $2.00 per complete case workflow

---

### Local-First Strategy (Privacy-Focused)
1. **Primary**: Ollama Llama 3.1 70B (localhost) - FREE
2. **Fallback**: Claude 3.5 Sonnet (cloud) for complex reasoning
3. **Benefits**: 90% cost reduction, complete data privacy
4. **Trade-off**: Slower responses, requires powerful hardware

---

## 📈 Usage Monitoring

### Track Costs in Real-Time
Bartleby provides cost tracking for each conversation:

```
💰 Session Cost: $0.42
📊 Tokens Used: 14,230 input / 3,450 output
🤖 Model: GPT-5-mini
⏱️ Duration: 8m 32s
```

### Budget Alerts
Set monthly budget limits in Settings:
- **Low**: $10/month (careful usage)
- **Medium**: $50/month (regular usage)
- **High**: $200/month (intensive litigation)
- **Unlimited**: No limits (enterprise)

---

## 🔧 Configuration

### Select LLM in Settings Panel
1. Navigate to **Settings** (⚙️ icon)
2. Select **AI Configuration** tab
3. Choose **LLM Provider**:
   - OpenAI
   - Anthropic
   - GitHub Copilot
   - Ollama (Localhost)
4. Select **Model** from dropdown
5. Optional: Set **Temperature** (0.0-1.0)
6. Optional: Set **Max Tokens** limit

### Environment Variables (Backend)
```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# GitHub Copilot
GITHUB_TOKEN=ghp_...

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:70b
```

---

## 🎯 Model Selection Guide

| Use Case | Recommended Model | Reason |
|----------|------------------|---------|
| Complex legal reasoning | GPT-5 or GPT-o3 | Best logical analysis |
| Long-form writing | Claude 3.5 Sonnet | Superior prose quality |
| Cost-sensitive work | GPT-5-nano or Ollama | Minimal expense |
| OCR/Vision tasks | GPT-4o | Multimodal capabilities |
| Privacy-critical cases | Ollama Localhost | No data leaves premises |
| Interactive chat | GPT-5-mini or Claude Haiku | Fast, affordable responses |
| Research & citations | GPT-5 or Claude Opus | Accurate legal citations |

---

## 📞 Support

For questions about LLM configuration or cost optimization:
- **Documentation**: `/docs/EVIDENCE_PIPELINE_INTEGRATION_GUIDE.md`
- **Settings Panel**: Click ⚙️ icon in app
- **Bartleby Help**: Type `/help models` in chat

---

**Note**: Pricing accurate as of October 2025. Check provider websites for current rates:
- OpenAI: https://openai.com/api/pricing/
- Anthropic: https://www.anthropic.com/pricing
- GitHub Copilot: https://github.com/features/copilot/plans
- Ollama: https://ollama.com/ (free, open-source)
