# 🚀 Bartleby Quick Setup Guide

**Get started with Bartleby AI Legal Clerk in 5 minutes**

---

## Step 1: Install Python Dependencies

```bash
cd /Users/jreback/Projects/LawyerFactory

# Install required packages
pip install openai anthropic

# Or add to requirements.txt and install
echo "openai>=1.0.0" >> requirements.txt
echo "anthropic>=0.18.0" >> requirements.txt
pip install -r requirements.txt
```

---

## Step 2: Configure API Keys

Create or edit `.env` file:

```bash
# In project root
nano .env
```

Add your API keys:

```bash
# Required for OpenAI (GPT-5, GPT-4o, etc.)
OPENAI_API_KEY=sk-proj-...your-key-here...

# Optional: For Anthropic Claude models
ANTHROPIC_API_KEY=sk-ant-...your-key-here...

# Optional: For GitHub Copilot integration
GITHUB_TOKEN=ghp_...your-token-here...

# Optional: For Ollama local models
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Step 3: Register Chat Routes in Flask

Edit `apps/api/server.py`:

```python
# Add these imports at the top
from src.lawyerfactory.chat.bartleby_handler import (
    BartlebyChatHandler,
    register_chat_routes
)
from src.lawyerfactory.storage.vectors.enhanced_vector_store import (
    EnhancedVectorStoreManager
)

# After creating your Flask app, add this:
# (Around line 50-100, after app = Flask(__name__))

# Initialize vector store
vector_store = EnhancedVectorStoreManager()

# Initialize Bartleby chat handler
chat_handler = BartlebyChatHandler(
    vector_store_manager=vector_store,
    evidence_table=None  # Add your evidence table instance if available
)

# Register chat routes
register_chat_routes(app, chat_handler)

print("✅ Bartleby chat routes registered")
```

---

## Step 4: Start the Application

```bash
# Terminal 1: Start Flask backend
cd /Users/jreback/Projects/LawyerFactory
python apps/api/server.py

# Terminal 2: Start React frontend
cd apps/ui/react-app
npm run dev
```

---

## Step 5: Open Bartleby

1. Navigate to http://localhost:3000
2. Look for the floating ⚖️ button in bottom-right corner
3. Click to open Bartleby
4. Try a test message:

```
"How many evidence items do I have?"
```

---

## ✅ Verification Checklist

- [ ] Python dependencies installed (`pip list | grep -E "openai|anthropic"`)
- [ ] API keys configured in `.env` file
- [ ] Chat routes registered in Flask server
- [ ] Flask server running on port 5000
- [ ] React app running on port 3000
- [ ] Bartleby button appears in UI
- [ ] Chat window opens when clicked
- [ ] Test message receives response

---

## 🎯 Test Commands

Try these in Bartleby to verify functionality:

```
/help              # Show available commands
/models            # List available LLM models
/cost              # Show current costs (should be $0.00)
/evidence          # Show evidence summary
/outline           # Display skeletal outline
```

---

## 🐛 Troubleshooting

### Bartleby button not appearing?

Check `apps/ui/react-app/src/App.jsx` settings:

```javascript
bartlebyEnabled: true,  // Make sure this is true
```

### "API key not configured" error?

Verify your `.env` file:

```bash
cat .env | grep OPENAI_API_KEY
```

Should show your key. If not, add it and restart Flask server.

### Chat not responding?

1. Check Flask server logs for errors
2. Verify backend is running: `curl http://localhost:5000/health`
3. Check browser console for JavaScript errors
4. Ensure CORS is configured in Flask app

### High costs immediately?

You're probably using GPT-5 (flagship model). Switch to cheaper model:

1. Click ⚙️ Settings icon
2. Go to "AI Configuration"
3. Change model to "GPT-5-nano" or "Claude Haiku"
4. Save settings

---

## 💡 Quick Tips

**Cost-Effective Usage**:
- Start with GPT-5-nano ($0.005/1K input)
- Use Claude Haiku for longer responses ($0.00025/1K)
- Install Ollama for $0 costs

**Better Responses**:
- Attach context (click Menu ☰ → Quick Actions)
- Be specific in your questions
- Use slash commands for quick info

**Privacy**:
- Use Ollama localhost for sensitive cases
- Data never used for training (OpenAI policy)
- Consider self-hosted models for maximum security

---

## 📚 Next Steps

1. **Read the full guide**: `/docs/BARTLEBY_GUIDE.md`
2. **Check pricing**: `/docs/LLM_PRICING_REFERENCE.md`
3. **Review implementation**: `/BARTLEBY_IMPLEMENTATION_COMPLETE.md`

---

**Ready to go! Bartleby is at your service. ⚖️**

*"I would prefer to help."*
