import logging
from pathlib import Path
import json
import uuid
import re
from typing import List, Dict, Any, Optional

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import dependencies with fallbacks
try:
    from pysqlcipher3 import dbapi2 as sqlite3
except ImportError:
    import sqlite3
    logger.warning("pysqlcipher3 not available, using standard sqlite3")

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    logger.warning("sentence-transformers or numpy not available, semantic search disabled")

try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    logger.warning("spaCy not available, NER disabled")


class KnowledgeGraph:
    """
    SQLite-based encrypted knowledge graph database handler.
    """
    
    def __init__(self, db_path: str = 'knowledge_graph.db', key: str = ''):
        """Initialize an encrypted SQLCipher database."""
        self.db_path = Path(db_path)
        self.key = key
        self.conn = sqlite3.connect(str(self.db_path))
        
        try:
            self._configure_encryption()
            self._initialize_schema()
            
            # Initialize embedder for semantic search if available
            if HAS_EMBEDDINGS:
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            else:
                self.embedder = None
                
            logger.info("Knowledge graph database initialized at %s", self.db_path)
        except Exception as e:
            logger.exception("Failed to initialize knowledge graph: %s", e)
            raise

    def _configure_encryption(self):
        """Configure database encryption if key provided."""
        if self.key:
            try:
                cursor = self.conn.cursor()
                cursor.execute(f"PRAGMA key = '{self.key}';")
                cursor.close()
                self.conn.commit()
            except Exception as e:
                logger.exception("Failed to configure encryption: %s", e)
                raise

    def _initialize_schema(self):
        """Create tables and indexes as defined in the knowledge_graph_schema."""
        sql = """
        -- Entities table
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            canonical_name TEXT,
            description TEXT,
            source_text TEXT,
            context_window TEXT,
            confidence REAL DEFAULT 1.0,
            extraction_method TEXT DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            legal_attributes TEXT,
            embeddings BLOB,
            verified BOOLEAN DEFAULT FALSE,
            verification_source TEXT
        );
        
        -- Relationships table
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_entity TEXT NOT NULL,
            to_entity TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            extraction_method TEXT DEFAULT 'manual',
            verified BOOLEAN DEFAULT FALSE,
            supporting_text TEXT,
            temporal_context TEXT,
            legal_significance TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_entity) REFERENCES entities (id),
            FOREIGN KEY (to_entity) REFERENCES entities (id)
        );
        
        -- Document sources table
        CREATE TABLE IF NOT EXISTS document_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT NOT NULL,
            document_id TEXT NOT NULL,
            page_number INTEGER,
            char_start INTEGER,
            char_end INTEGER,
            FOREIGN KEY (entity_id) REFERENCES entities (id)
        );
        
        -- Observations table
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            entity_id TEXT,
            relationship_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            observation_type TEXT DEFAULT 'system',
            FOREIGN KEY (entity_id) REFERENCES entities (id),
            FOREIGN KEY (relationship_id) REFERENCES relationships (id)
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
        CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
        CREATE INDEX IF NOT EXISTS idx_relationships_from ON relationships(from_entity);
        CREATE INDEX IF NOT EXISTS idx_relationships_to ON relationships(to_entity);
        CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type);
        CREATE INDEX IF NOT EXISTS idx_document_sources_entity ON document_sources(entity_id);
        CREATE INDEX IF NOT EXISTS idx_document_sources_document ON document_sources(document_id);
        """
        
        try:
            cursor = self.conn.cursor()
            cursor.executescript(sql)
            cursor.close()
            self.conn.commit()
        except Exception as e:
            logger.exception("Failed to initialize schema: %s", e)
            raise

    def _execute(self, query: str, params: tuple = ()):
        """Execute a SQL command and commit the transaction."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return cursor
        except Exception as e:
            logger.exception("Failed to execute query: %s", e)
            raise

    def _fetchall(self, query: str, params: tuple = ()):
        """Execute a query and return all rows."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            logger.exception("Failed to fetch all: %s", e)
            return []

    def _fetchone(self, query: str, params: tuple = ()):
        """Execute a query and return a single row."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except Exception as e:
            logger.exception("Failed to fetch one: %s", e)
            return None

    def semantic_search(self, query: str, top_k: int = 5):
        """Perform semantic search on entity embeddings."""
        if not self.embedder:
            logger.warning("Semantic search not available - embeddings disabled")
            return []
            
        try:
            q_emb = self.embedder.encode([query])[0]
            rows = self._fetchall("SELECT id, type, name, embeddings FROM entities WHERE embeddings IS NOT NULL")
            sims = []
            
            for eid, etype, name, emb_blob in rows:
                emb = np.frombuffer(emb_blob, dtype=np.float32)
                score = np.dot(q_emb, emb) / (np.linalg.norm(q_emb) * np.linalg.norm(emb))
                sims.append((score, eid, etype, name))
                
            sims.sort(reverse=True, key=lambda x: x[0])
            return [{"id": eid, "type": etype, "name": name, "score": float(score)} 
                   for score, eid, etype, name in sims[:top_k]]
        except Exception as e:
            logger.exception("Semantic search failed for query '%s': %s", query, e)
            return []

    def query_entities(self, entity_type: Optional[str] = None, name: Optional[str] = None):
        """Retrieve entities filtered by type and/or name."""
        try:
            sql = "SELECT * FROM entities"
            params = []
            
            if entity_type and name:
                sql += " WHERE type = ? AND name LIKE ?"
                params = [entity_type, f"%{name}%"]
            elif entity_type:
                sql += " WHERE type = ?"
                params = [entity_type]
            elif name:
                sql += " WHERE name LIKE ?"
                params = [f"%{name}%"]
                
            rows = self._fetchall(sql, tuple(params))
            return [dict(id=r[0], type=r[1], name=r[2], source_text=r[5]) for r in rows]
        except Exception as e:
            logger.exception("Query entities failed: %s", e)
            return []

    def get_case_facts(self, document_id: str):
        """Retrieve all entities associated with a document and their relationships."""
        try:
            srcs = self._fetchall("SELECT entity_id FROM document_sources WHERE document_id = ?", (document_id,))
            entity_ids = {row[0] for row in srcs}
            entities = []
            
            for eid in entity_ids:
                ent = self._fetchone("SELECT * FROM entities WHERE id = ?", (eid,))
                if ent:
                    entities.append(dict(id=ent[0], type=ent[1], name=ent[2], source_text=ent[5]))
                    
            rels = self._fetchall("SELECT * FROM relationships WHERE supporting_text = ?", (document_id,))
            relationships = [{"id": r[0], "from": r[1], "to": r[2], "type": r[3]} for r in rels]
            
            return {"entities": entities, "relationships": relationships}
        except Exception as e:
            logger.exception("Get case facts failed for document '%s': %s", document_id, e)
            return {}

    def close(self):
        """Close the database connection."""
        try:
            self.conn.close()
        except Exception as e:
            logger.exception("Failed to close database connection: %s", e)


class DocumentIngestionPipeline:
    """Handles document processing for multiple file formats."""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        
        # Initialize spaCy NLP if available
        if HAS_SPACY:
            try:
                self.nlp = spacy.load("en_core_web_lg")
            except OSError:
                logger.warning("en_core_web_lg model not found, NER disabled")
                self.nlp = None
        else:
            self.nlp = None

    def ingest(self, file_path: str):
        """Main ingestion method for processing documents."""
        ext = Path(file_path).suffix.lower()
        document_id = Path(file_path).name
        logger.info("Ingesting document %s of type %s", document_id, ext)
        
        try:
            # Extract text based on file type
            if ext == '.pdf':
                text = self._extract_pdf(file_path)
            elif ext in ('.docx', '.doc'):
                text = self._extract_docx(file_path)
            elif ext in ('.txt', '.md'):
                text = self._extract_txt(file_path)
            elif ext in ('.eml', '.msg'):
                text = self._extract_email(file_path)
            elif ext == '.csv':
                text = self._extract_csv(file_path)
            else:
                logger.error("Unsupported file type: %s", ext)
                return
                
            # Perform NER and extract entities
            entities = self._perform_ner(text)
            
            # Generate embeddings if available
            if self.kg.embedder and entities:
                texts = [ent['text'] for ent in entities]
                embeddings = self.kg.embedder.encode(texts)
            else:
                embeddings = [None] * len(entities)
                
            # Insert entities into database
            for ent, emb in zip(entities, embeddings):
                emb_blob = emb.tobytes() if emb is not None else None
                self.kg._execute(
                    "INSERT OR IGNORE INTO entities(id, type, name, source_text, embeddings) VALUES (?, ?, ?, ?, ?)",
                    (ent['id'], ent['label'], ent['text'], text, emb_blob)
                )
                self.kg._execute(
                    "INSERT INTO document_sources(entity_id, document_id) VALUES (?, ?)",
                    (ent['id'], document_id)
                )
                
            # Map relationships
            self._map_relationships(entities, document_id)
            logger.info("Completed ingestion for document %s", document_id)
            
        except Exception as e:
            logger.exception("Ingestion failed for document %s: %s", document_id, e)

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF with OCR fallback."""
        try:
            import pdfplumber
            import pytesseract
            from pdf2image import convert_from_path
            
            text = ''
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                        
            # OCR fallback if no text extracted
            if not text.strip():
                logger.info("No text found, using OCR for %s", file_path)
                for img in convert_from_path(file_path):
                    text += pytesseract.image_to_string(img)
                    
            return text
        except ImportError:
            logger.error("PDF processing libraries not available")
            return ""
        except Exception as e:
            logger.exception("PDF extraction failed for %s: %s", file_path, e)
            return ""

    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX files."""
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(file_path)
            return '\n'.join([para.text for para in doc.paragraphs])
        except ImportError:
            logger.error("python-docx library not available")
            return ""
        except Exception as e:
            logger.exception("DOCX extraction failed for %s: %s", file_path, e)
            return ""

    def _extract_txt(self, file_path: str) -> str:
        """Extract text from TXT files with encoding detection."""
        try:
            import chardet
            raw = Path(file_path).read_bytes()
            encoding = chardet.detect(raw)['encoding'] or 'utf-8'
            return raw.decode(encoding, errors='ignore')
        except ImportError:
            # Fallback without chardet
            try:
                return Path(file_path).read_text(encoding='utf-8')
            except UnicodeDecodeError:
                return Path(file_path).read_text(encoding='latin1', errors='ignore')
        except Exception as e:
            logger.exception("TXT extraction failed for %s: %s", file_path, e)
            return ""

    def _extract_email(self, file_path: str) -> str:
        """Extract text from email files."""
        try:
            from email.parser import BytesParser
            from email import policy
            
            with open(file_path, 'rb') as f:
                msg = BytesParser(policy=policy.default).parse(f)
            body = msg.get_body(preferencelist=('plain',))
            return body.get_content() if body else ""
        except Exception as e:
            logger.exception("Email extraction failed for %s: %s", file_path, e)
            return ""

    def _extract_csv(self, file_path: str) -> str:
        """Extract text from CSV files."""
        try:
            import csv
            rows = []
            with open(file_path, newline='', encoding='utf-8') as f:
                for row in csv.reader(f):
                    rows.append(' '.join(row))
            return '\n'.join(rows)
        except Exception as e:
            logger.exception("CSV extraction failed for %s: %s", file_path, e)
            return ""

    def _perform_ner(self, text: str) -> List[Dict[str, str]]:
        """Perform Named Entity Recognition using spaCy and custom patterns."""
        entities = []
        
        try:
            # spaCy NER
            if self.nlp:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ in {"PERSON", "ORG", "DATE", "MONEY", "GPE"}:
                        entities.append({
                            "id": str(uuid.uuid4()),
                            "label": ent.label_,
                            "text": ent.text
                        })
            
            # Custom legal entity patterns
            # Case numbers
            for match in re.finditer(r"Case(?: No\.?\s*)?\d+", text, re.IGNORECASE):
                entities.append({
                    "id": str(uuid.uuid4()),
                    "label": "CASE_NUMBER",
                    "text": match.group()
                })
                
            # Statutes and regulations
            for match in re.finditer(r"§\s*\d+[A-Za-z0-9\-]*", text):
                entities.append({
                    "id": str(uuid.uuid4()),
                    "label": "STATUTE",
                    "text": match.group()
                })
                
        except Exception as e:
            logger.exception("NER failed: %s", e)
            
        return entities

    def _map_relationships(self, entities: List[Dict], document_id: str):
        """Create co-occurrence relationships between sequential entities."""
        try:
            for i in range(len(entities) - 1):
                from_id = entities[i]['id']
                to_id = entities[i + 1]['id']
                self.kg._execute(
                    "INSERT INTO relationships(from_entity, to_entity, relationship_type, supporting_text) VALUES (?, ?, ?, ?)",
                    (from_id, to_id, 'co_occurrence', document_id)
                )
        except Exception as e:
            logger.exception("Failed to map relationships for document %s: %s", document_id, e)


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Initialize, ingest, or query the encrypted knowledge graph.")
    parser.add_argument("--db", default="knowledge_graph.db", help="Path to the encrypted database file.")
    parser.add_argument("--key", default="", help="Encryption key for the database.")
    parser.add_argument("--ingest-dir", help="Directory of documents to ingest")
    parser.add_argument("--query-type", help="Entity type to query")
    parser.add_argument("--query-name", help="Entity name substring to query")
    parser.add_argument("--case-facts", help="Document ID to retrieve case facts")
    args = parser.parse_args()

    kg = KnowledgeGraph(db_path=args.db, key=args.key)

    try:
        if args.ingest_dir:
            pipeline = DocumentIngestionPipeline(kg)
            ingest_path = Path(args.ingest_dir)
            
            if ingest_path.is_dir():
                for file_path in ingest_path.rglob("*.*"):
                    if file_path.is_file():
                        pipeline.ingest(str(file_path))
            else:
                pipeline.ingest(str(ingest_path))
                
            logger.info("Completed ingestion for %s", args.ingest_dir)
            
        elif args.query_type or args.query_name:
            results = kg.query_entities(entity_type=args.query_type, name=args.query_name)
            logger.info("Query results: %s", results)
            
        elif args.case_facts:
            facts = kg.get_case_facts(args.case_facts)
            logger.info("Case facts for %s: %s", args.case_facts, facts)
            
        else:
            count_result = kg._fetchone("SELECT COUNT(*) FROM entities")
            count = count_result[0] if count_result else 0
            logger.info("Existing entities count: %d", count)
            
    except Exception as e:
        logger.exception("Operation failed: %s", e)
    finally:
        kg.close()
