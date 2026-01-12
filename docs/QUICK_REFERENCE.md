# Quick Reference: Routes Registration & File Locations

**Quick Access Guide** | October 20, 2025

---

## 🎯 One-Minute Summary

### What Does "Register Flask Routes" Mean?
**Connect HTTP URLs to Python functions so frontend can call backend code.**

### Where Are Backend Files?
```
/Users/jreback/Projects/LawyerFactory/src/lawyerfactory/
├── api/evidence_queue_api.py        ← Routes (REST endpoints)
├── storage/core/evidence_queue.py   ← Logic (processing)
├── config/case_types.py              ← Config (case types)
└── phases/phaseB01_review/ui/api_app_main.py  ← Main Flask app
```

### Are There Duplicate Files?
**No problematic duplicates.** You have:
- `EvidenceUpload.jsx` (generic) + `EvidenceUploadQueue.jsx` (specialized) = Intentional, different purposes
- `shotlist.py` (core) + `api/shot_list.py` (API wrapper) = Intentional, good architecture
- Similar pattern throughout = Follows proper separation of concerns

---

## 🔧 How to Register Routes (3 Steps)

### Step 1: Open Main Flask App
```
File: /Users/jreback/Projects/LawyerFactory/src/lawyerfactory/
      phases/phaseB01_review/ui/api_app_main.py
```

### Step 2: Add Import
```python
# Near top of file, with other imports
from lawyerfactory.api.evidence_queue_api import register_evidence_queue_routes
```

### Step 3: Call Registration Function
```python
# After app = Flask(__name__), add:
register_evidence_queue_routes(app)
```

### That's it! ✅

Routes are now active:
- `GET  /api/evidence/queue/status/<case_id>`
- `POST /api/evidence/queue/upload/<case_id>`
- `POST /api/evidence/queue/start/<case_id>`
- `GET  /api/evidence/queue/filter/<case_id>`
- `GET  /api/evidence/queue/stats/<case_id>`
- etc.

---

## 📍 File Location Quick Reference

### Evidence Pipeline Backend Files

| Component | File | Location |
|-----------|------|----------|
| **API Routes** | `evidence_queue_api.py` | `src/lawyerfactory/api/` |
| **Queue Logic** | `evidence_queue.py` | `src/lawyerfactory/storage/core/` |
| **Case Types** | `case_types.py` | `src/lawyerfactory/config/` |
| **Flask App** | `api_app_main.py` | `src/lawyerfactory/phases/phaseB01_review/ui/` |

### Evidence Pipeline Frontend Files

| Component | File | Location |
|-----------|------|----------|
| **Upload Queue UI** | `EvidenceUploadQueue.jsx` | `apps/ui/react-app/src/components/ui/` |
| **Evidence Table UI** | `EvidenceTable.jsx` | `apps/ui/react-app/src/components/ui/` |
| **Shot List UI** | `ShotList.jsx` | `apps/ui/react-app/src/components/ui/` |
| **Claims Matrix UI** | `ClaimsMatrix.jsx` | `apps/ui/react-app/src/components/ui/` |

---

## 🔄 Data Flow (High Level)

```
User uploads evidence
         ↓
EvidenceUploadQueue.jsx
         ↓
POST /api/evidence/queue/upload/CASE-001
         ↓
evidence_queue_api.py (route handler)
         ↓
evidence_queue.py (processes queue)
         ↓
case_types.py (classifies evidence)
         ↓
Database stores: primary vs secondary + type + confidence
         ↓
Frontend polls GET /api/evidence/queue/status/CASE-001
         ↓
EvidenceTable.jsx renders hierarchical view
```

---

## 🤔 FAQ

### Q: Why two upload components?
**A:** Different purposes:
- `EvidenceUpload`: Generic file storage (any file, any phase)
- `EvidenceUploadQueue`: Evidence classification (legal cases only, real-time processing)

Keep both.

### Q: Why separate `shotlist.py` and `api/shot_list.py`?
**A:** Separation of concerns:
- `evidence/shotlist.py`: Core logic (extract facts, manage shots)
- `api/shot_list.py`: REST API (HTTP endpoints, request handling)

This is good design. The API layer wraps the core logic.

### Q: What happens if I don't register routes?
**A:** Frontend gets `404 Not Found` when trying to call the endpoints. Routes won't exist.

### Q: Where do I add the registration call?
**A:** In `api_app_main.py`, right after `app = Flask(__name__)` and other initial setup.

### Q: What backend files do I need to copy?
**A:** All already exist in the codebase:
- ✅ `evidence_queue_api.py`
- ✅ `evidence_queue.py`
- ✅ `case_types.py`

Just need to register them.

---

## ✅ Pre-Integration Checklist

### Backend
- [ ] Locate `api_app_main.py`
- [ ] Find line where `app = Flask(__name__)` is defined
- [ ] Add import: `from lawyerfactory.api.evidence_queue_api import register_evidence_queue_routes`
- [ ] Add call: `register_evidence_queue_routes(app)`
- [ ] Restart Flask server
- [ ] Verify no errors in logs

### Frontend
- [ ] `EvidenceUploadQueue.jsx` ready to use
- [ ] `EvidenceTable.jsx` ready to use
- [ ] `ShotList.jsx` ready to use
- [ ] `ClaimsMatrix.jsx` ready to use
- [ ] No frontend changes needed (already implemented)

### Testing
- [ ] curl test: `GET http://localhost:5000/api/evidence/queue/status/TEST-001`
- [ ] Check response: Should not be 404
- [ ] Frontend upload: Try uploading evidence
- [ ] Verify queue shows items
- [ ] Verify classifications appear

---

## 🚀 Next Steps After Registration

1. **Test upload endpoint**
   ```bash
   curl -X POST http://localhost:5000/api/evidence/queue/upload/CASE-001 \
     -F "files=@test.pdf" \
     -F "case_type=autonomous_vehicle"
   ```

2. **Check queue status**
   ```bash
   curl http://localhost:5000/api/evidence/queue/status/CASE-001
   ```

3. **Filter by classification**
   ```bash
   curl "http://localhost:5000/api/evidence/queue/filter/CASE-001?evidence_class=primary"
   ```

4. **Get statistics**
   ```bash
   curl http://localhost:5000/api/evidence/queue/stats/CASE-001
   ```

---

## 📚 Related Documentation

- **FLASK_ROUTES_EXPLAINED.md** - Deep dive into route registration
- **BACKEND_FILES_LOCATION_DUPLICATES.md** - Full file analysis
- **EVIDENCE_PIPELINE_INTEGRATION_GUIDE.md** - Component integration guide
- **EVIDENCE_PROCESSING_PIPELINE.md** - Architecture overview

---

**Print this page for quick reference!**

Version 1.0 | Status: Ready | Last Updated: October 20, 2025
