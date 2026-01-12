# 🤖 Bartleby AI Legal Clerk - Implementation Guide

**LawyerFactory - Intelligent Chatbot Assistant**  
**Version**: 1.0.0  
**Last Updated**: October 23, 2025

---

## 📋 Overview

Bartleby is an AI-powered legal clerk assistant integrated into LawyerFactory. Unlike the literary character who "would prefer not to," this Bartleby is proactive, helpful, and capable of intelligently assisting with legal research, document modification, and case analysis.

### **Key Capabilities**

✅ **Natural Language Understanding**: Ask questions in plain English about your case  
✅ **Vector Store Integration**: Semantic search across all evidence and documents  
✅ **Document Modification**: Edit skeletal outlines, evidence tables, and research parameters  
✅ **Context Awareness**: Understands current phase, case state, and workflow status  
✅ **Multi-LLM Support**: Works with OpenAI, Anthropic, GitHub Copilot, and Ollama  
✅ **Cost Tracking**: Real-time API usage monitoring and budget alerts  
✅ **Action Execution**: Proactively suggests and executes document improvements  

---

## 🏗️ Architecture

### **Frontend Components**

```
BartlebyChatbot.jsx
├── Message History UI
├── Input Field with Commands
├── Context Attachment System
├── Action Button Rendering
├── Cost Display
└── Soviet Industrial Styling
```

### **Backend Components**

```
bartleby_handler.py
├── LLM Client Manager
│   ├── OpenAI Integration
│   ├── Anthropic Integration
│   ├── GitHub Copilot Integration
│   └── Ollama Local Integration
├── Context Builder
│   ├── Skeletal Outline
│   ├── Evidence Table Data
│   ├── Phase Statuses
│   └── Vector Store Access
├── Action Executor
│   ├── Modify Outline
│   ├── Update Evidence
│   ├── Adjust Research
│   └── Search Vectors
└── Cost Calculator
```

### **Data Flow**

```
User Input
    ↓
BartlebyChatbot Component
    ↓
backendService.sendChatMessage()
    ↓
Flask /api/chat/message endpoint
    ↓
BartlebyChatHandler.send_message()
    ↓
LLM API (OpenAI/Anthropic/Ollama)
    ↓
Response + Actions
    ↓
Action Execution (if needed)
    ↓
Updated UI State
```

---

## 🚀 Quick Start

### **1. Install Dependencies**

```bash
# Install Python dependencies
pip install openai anthropic

# Or add to requirements.txt
echo "openai>=1.0.0" >> requirements.txt
echo "anthropic>=0.18.0" >> requirements.txt
pip install -r requirements.txt
```

### **2. Configure API Keys**

```bash
# Add to your .env file
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...  # Optional for GitHub Copilot
OLLAMA_BASE_URL=http://localhost:11434  # Optional for Ollama
```

### **3. Register Chat Routes in Flask**

```python
# In apps/api/server.py or your main Flask app

from src.lawyerfactory.chat.bartleby_handler import BartlebyChatHandler, register_chat_routes
from src.lawyerfactory.storage.vectors.enhanced_vector_store import EnhancedVectorStoreManager

# Initialize components
vector_store = EnhancedVectorStoreManager()
chat_handler = BartlebyChatHandler(vector_store_manager=vector_store)

# Register routes
register_chat_routes(app, chat_handler)
```

### **4. Enable in Frontend**

Bartleby is automatically enabled when `settings.bartlebyEnabled` is `true` (default).

To manually toggle:

```javascript
// In App.jsx settings
settings: {
  bartlebyEnabled: true,  // Enable/disable chatbot
  bartlebyPosition: 'right',  // left, right, bottom
  bartlebyAutoOpen: false,  // Auto-open on page load
}
```

### **5. Start Using Bartleby**

1. Click the floating ⚖️ button in the bottom-right corner
2. Type your question or command
3. Bartleby responds with context-aware answers
4. Execute suggested actions with one click

---

## 💬 Usage Examples

### **Basic Questions**

```
You: "How many pieces of evidence do I have?"
Bartleby: "You currently have 14 evidence items loaded (9 PRIMARY, 5 SECONDARY)."

You: "What's the status of Phase A02?"
Bartleby: "Phase A02 (Legal Research) is currently in progress. 
Research has been completed for 3 out of 5 claims."

You: "Find all evidence related to contract breach"
Bartleby: [Searches vector store and displays results]
```

### **Document Modification**

```
You: "Add a new section to the skeletal outline for damages calculation"
Bartleby: "I can add a section titled 'IV. Damages Calculation' to your skeletal 
outline. This would include subsections for:
- Economic damages
- Punitive damages
- Interest calculations

Would you like me to proceed?"
[Action Button: Add Section]
```

### **Evidence Management**

```
You: "Add a column to the evidence table for 'Authenticity Status'"
Bartleby: "I'll add a new column 'Authenticity Status' to the evidence table with 
possible values: Authenticated, Pending, Challenged. This will help track evidence 
admissibility."
[Action Button: Add Column]
```

### **Research Assistance**

```
You: "Expand research to include California state law on punitive damages"
Bartleby: "I'll adjust the research parameters for Phase A02 to include:
- California Civil Code § 3294 (punitive damages)
- Recent California Supreme Court decisions
- Appellate court precedents from last 5 years

This will add approximately 15-20 additional sources."
[Action Button: Expand Research]
```

---

## 🎛️ Slash Commands

Bartleby supports quick commands for common tasks:

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show available commands | `/help` |
| `/clear` | Clear chat history | `/clear` |
| `/context` | Show attached context | `/context` |
| `/outline` | Display skeletal outline | `/outline` |
| `/evidence` | Show evidence summary | `/evidence` |
| `/research` | View research status | `/research` |
| `/cost` | Display usage costs | `/cost` |
| `/models` | List available LLMs | `/models` |

---

## ⚙️ Configuration

### **LLM Selection**

Change the active LLM model in Settings (⚙️ icon):

1. **LLM Provider**: OpenAI, Anthropic, GitHub Copilot, Ollama
2. **Model**: Select from available models (see pricing guide)
3. **Temperature**: 0.0 (precise) to 1.0 (creative)
4. **Max Tokens**: Response length limit (default: 4096)

### **Cost Management**

Set budget alerts in Settings:

- **Monthly Budget**: $10, $50, $200, or Unlimited
- **Track Usage**: Enable real-time cost tracking
- **Show Estimates**: Display cost per message

### **Personality Settings**

Adjust Bartleby's communication style:

- **Professional**: Formal legal terminology (default)
- **Casual**: Conversational tone
- **Formal**: Strict appellate court style

---

## 🔍 Context Attachment

Attach additional context to your messages for better responses:

1. Click the **Menu** icon (☰) in Bartleby header
2. Select **Quick Actions**
3. Choose context to attach:
   - **Outline**: Skeletal outline structure
   - **Evidence**: Evidence table data
   - **Phase Status**: Current workflow phase

Attached context appears as chips below the input field.

---

## 🛠️ Advanced Features

### **Action Execution**

Bartleby can suggest and execute structured actions:

```javascript
// Example action returned by Bartleby
{
  "type": "modify_outline",
  "label": "Add Damages Section",
  "data": {
    "section_title": "IV. Damages Calculation",
    "subsections": [
      "Economic Damages",
      "Punitive Damages",
      "Interest Calculations"
    ],
    "insert_after": "III. Liability Analysis"
  }
}
```

Click the action button to execute automatically.

### **Vector Store Search**

Semantic search across all case evidence:

```
You: "Find documents mentioning the December 2023 incident"
```

Bartleby searches the enhanced vector store and returns:
- Relevant evidence items
- Similarity scores
- Source documents
- Linked claims

### **Real-Time Collaboration**

Bartleby maintains awareness of:
- Current case ID
- Active phase workflow
- Recent document uploads
- Phase completion status
- Agent activity

This enables contextual responses like:
```
Bartleby: "I see you just completed Phase A01. Would you like me to 
summarize the extracted facts before moving to research?"
```

---

## 📊 Cost Tracking

Bartleby provides transparent cost tracking:

### **Session Costs**

Displayed at bottom of chat:
```
💰 Session: $0.42 • Model: GPT-5-mini
```

### **Detailed Breakdown**

Use `/cost` command:
```
💰 Usage Costs:
- Session: $0.4230
- Total: $12.45
- Model: gpt-5-mini
- Provider: openai

Token Usage:
- Input: 14,230 tokens ($0.21)
- Output: 3,450 tokens ($0.21)
```

### **Budget Alerts**

Receive notifications when approaching monthly budget:
- 50% threshold: Warning toast
- 80% threshold: Alert modal
- 100% threshold: Chat disabled (configurable)

---

## 🔒 Privacy & Security

### **Data Handling**

- **Local Context**: Case data stays in your LawyerFactory instance
- **API Calls**: Only sent to selected LLM provider
- **No Training**: Your data is NOT used to train provider models
- **Localhost Option**: Use Ollama for complete data privacy

### **Ollama Local Setup**

For maximum privacy, run LLMs locally:

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull a model (e.g., Llama 3.1 70B)
ollama pull llama3.1:70b

# Start Ollama server
ollama serve
```

Then select **Ollama** provider in Settings with model `llama3.1:70b`.

**Benefits**:
- ✅ $0.00 API costs
- ✅ Complete data privacy
- ✅ No internet required
- ✅ Unlimited usage

**Requirements**:
- 40GB RAM for llama3.1:70b
- 8GB RAM for llama3.1:8b (smaller model)
- GPU optional but recommended

---

## 🐛 Troubleshooting

### **Bartleby Not Responding**

1. Check API keys in `.env` file
2. Verify Flask server is running (`http://localhost:5000`)
3. Check browser console for errors
4. Confirm `bartlebyEnabled: true` in settings

### **High API Costs**

1. Switch to more affordable model (GPT-5-nano, Claude Haiku)
2. Lower `maxTokens` in settings
3. Use Ollama localhost (free)
4. Set monthly budget limit

### **Action Execution Fails**

1. Verify case ID is set (`currentCaseId`)
2. Check Flask logs for backend errors
3. Ensure vector store is initialized
4. Confirm permissions for document modification

### **Slow Responses**

1. Use faster models (GPT-5-nano, GPT-4o)
2. Reduce context attachment (fewer evidence items)
3. Lower `maxTokens` setting
4. Check internet connection (if using cloud LLMs)

---

## 📖 API Reference

### **Frontend API**

```javascript
// Send chat message
await backendService.sendChatMessage({
  message: "Your question here",
  caseId: currentCaseId,
  context: { outline, evidence, phases },
  settings: { model, provider, temperature }
});

// Modify outline
await backendService.modifyOutlineViaChat(caseId, modifications);

// Update evidence
await backendService.updateEvidenceViaChat(caseId, evidenceUpdate);

// Adjust research
await backendService.adjustResearchViaChat(caseId, researchParams);

// Search vectors
await backendService.searchVectorStore(caseId, query, filters);
```

### **Backend API**

```python
# Initialize handler
chat_handler = BartlebyChatHandler(
    vector_store_manager=vector_store,
    evidence_table=evidence_api
)

# Send message
response = await chat_handler.send_message(
    message="User question",
    context=ChatContext(...),
    settings={"model": "gpt-5", ...}
)

# Execute action
result = await chat_handler.execute_action(
    action={"type": "modify_outline", "data": {...}},
    case_id="case123"
)
```

---

## 🎯 Best Practices

### **Effective Prompting**

**Good**:
```
"Find all evidence from January 2024 related to the breach of contract claim 
and summarize the key facts."
```

**Better**:
```
"Search evidence table for documents dated January 1-31, 2024 with 
evidence_type='CONTRACT' and extract facts supporting the breach claim."
```

### **Context Attachment**

Always attach relevant context for complex questions:
1. Attach **Outline** when asking about document structure
2. Attach **Evidence** when researching facts
3. Attach **Phase Status** when asking about workflow progress

### **Action Review**

Before executing suggested actions:
1. Read the explanation carefully
2. Verify the proposed changes
3. Consider downstream effects
4. Use confirmation modals for major changes

### **Cost Optimization**

1. **Start small**: Use GPT-5-nano for simple queries
2. **Escalate as needed**: Switch to GPT-5 for complex reasoning
3. **Batch questions**: Ask multiple related questions together
4. **Use localhost**: Ollama for unlimited free queries

---

## 🔄 Integration with Workflow Phases

Bartleby integrates with all 7 workflow phases:

| Phase | Bartleby Capabilities |
|-------|----------------------|
| **A01 (Intake)** | Evidence upload assistance, fact extraction review |
| **A02 (Research)** | Research parameter adjustment, authority search |
| **A03 (Outline)** | Skeletal outline modification, claim addition |
| **B01 (Review)** | Validation assistance, fact-checking |
| **B02 (Drafting)** | Citation review, argument suggestions |
| **C01 (Editing)** | Grammar checks, formatting improvements |
| **C02 (Orchestration)** | Workflow coordination, phase summaries |

---

## 📚 Related Documentation

- **LLM Pricing Reference**: `/docs/LLM_PRICING_REFERENCE.md`
- **Vector Store Guide**: `/docs/EVIDENCE_PIPELINE_INTEGRATION_GUIDE.md`
- **System Architecture**: `/docs/VISUAL_ARCHITECTURE.md`
- **User Guide**: `/USER_GUIDE.md`

---

## 🆘 Support

For questions or issues with Bartleby:

1. Type `/help` in the chat for quick reference
2. Check this documentation for detailed guidance
3. Review Flask server logs for backend errors
4. Verify API keys and environment configuration

---

**Note**: Bartleby is designed to assist, not replace, legal professionals. Always review AI-generated suggestions before implementing them in legal documents.

**"I would prefer to help."** - Bartleby, AI Legal Clerk
