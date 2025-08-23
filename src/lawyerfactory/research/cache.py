"""
# Script Name: cache.py
# Description: Legal Research Cache Manager for Claims Matrix Phase 3.2 Manages intelligent caching, performance optimization, and cache invalidation
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Research
#   - Group Tags: legal-research
Legal Research Cache Manager for Claims Matrix Phase 3.2
Manages intelligent caching, performance optimization, and cache invalidation
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from enhanced_knowledge_graph import EnhancedKnowledgeGraph

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    TIME_BASED = "time_based"
    USAGE_BASED = "usage_based" 
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata"""
    cache_key: str
    data: Dict[str, Any]
    cache_type: str  # research, definition, case_law
    jurisdiction: str
    expiry_time: datetime
    hit_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    validity_score: float = 1.0


@dataclass
class CachePerformanceMetrics:
    """Cache performance metrics"""
    hit_rate: float = 0.0
    miss_rate: float = 0.0
    total_requests: int = 0
    total_hits: int = 0
    total_misses: int = 0
    average_response_time_ms: float = 0.0
    cache_size_mb: float = 0.0
    eviction_count: int = 0


class LegalResearchCacheManager:
    """Manages caching for legal research results with intelligent invalidation"""
    
    def __init__(self, enhanced_kg: EnhancedKnowledgeGraph, max_cache_size_mb: int = 500):
        self.kg = enhanced_kg
        self.max_cache_size_mb = max_cache_size_mb
        self.max_cache_size_bytes = max_cache_size_mb * 1024 * 1024
        
        # Cache configuration
        self.cache_config = {
            'legal_research_cache': {
                'default_expiry_hours': 24,
                'max_entries': 10000,
                'cleanup_threshold': 0.8
            },
            'definition_cache': {
                'default_expiry_hours': 168,  # 1 week
                'max_entries': 5000,
                'cleanup_threshold': 0.8
            },
            'case_law_cache': {
                'default_expiry_hours': 72,  # 3 days
                'max_entries': 15000,
                'cleanup_threshold': 0.8
            }
        }
        
        # Performance tracking
        self.performance_metrics = {
            'legal_research_cache': CachePerformanceMetrics(),
            'definition_cache': CachePerformanceMetrics(),
            'case_law_cache': CachePerformanceMetrics()
        }
        
        # Background tasks
        self.cleanup_task = None
        self.metrics_task = None
        
        logger.info("Legal Research Cache Manager initialized")
    
    async def start_background_tasks(self):
        """Start background cache maintenance tasks"""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._background_cleanup())
        if self.metrics_task is None:
            self.metrics_task = asyncio.create_task(self._background_metrics_update())
        
        logger.info("Started background cache maintenance tasks")
    
    async def stop_background_tasks(self):
        """Stop background cache maintenance tasks"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            self.cleanup_task = None
        if self.metrics_task:
            self.metrics_task.cancel()
            self.metrics_task = None
        
        logger.info("Stopped background cache maintenance tasks")
    
    async def get_cached_research(self, cache_key: str, jurisdiction: str) -> Optional[Dict[str, Any]]:
        """Get cached research results"""
        return await self._get_cache_entry('legal_research_cache', cache_key, jurisdiction)
    
    async def cache_research_result(self, cache_key: str, jurisdiction: str, 
                                  data: Dict[str, Any], expiry_hours: int = 24) -> bool:
        """Cache research results"""
        return await self._set_cache_entry(
            'legal_research_cache', cache_key, jurisdiction, data, expiry_hours
        )
    
    async def get_cached_definition(self, legal_term: str, jurisdiction: str) -> Optional[Dict[str, Any]]:
        """Get cached legal definition"""
        cache_key = self._generate_definition_key(legal_term, jurisdiction)
        return await self._get_cache_entry('definition_cache', cache_key, jurisdiction)
    
    async def cache_definition(self, legal_term: str, jurisdiction: str, 
                             definition_data: Dict[str, Any], expiry_hours: int = 168) -> bool:
        """Cache legal definition"""
        cache_key = self._generate_definition_key(legal_term, jurisdiction)
        return await self._set_cache_entry(
            'definition_cache', cache_key, jurisdiction, definition_data, expiry_hours
        )
    
    async def get_cached_case_law(self, cause_of_action: str, jurisdiction: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached case law for cause of action"""
        cache_key = self._generate_case_law_key(cause_of_action, jurisdiction)
        cached_result = await self._get_cache_entry('case_law_cache', cache_key, jurisdiction)
        return cached_result.get('cases', []) if cached_result else None
    
    async def cache_case_law(self, cause_of_action: str, jurisdiction: str,
                           cases: List[Dict[str, Any]], expiry_hours: int = 72) -> bool:
        """Cache case law results"""
        cache_key = self._generate_case_law_key(cause_of_action, jurisdiction)
        cache_data = {
            'cause_of_action': cause_of_action,
            'jurisdiction': jurisdiction,
            'cases': cases,
            'cached_at': datetime.now().isoformat()
        }
        return await self._set_cache_entry(
            'case_law_cache', cache_key, jurisdiction, cache_data, expiry_hours
        )
    
    async def _get_cache_entry(self, cache_type: str, cache_key: str, 
                             jurisdiction: str) -> Optional[Dict[str, Any]]:
        """Generic method to get cache entry"""
        try:
            start_time = time.time()
            
            # Query cache from database
            result = self.kg._execute("""
                SELECT result_data, cache_expiry, created_at
                FROM {} 
                WHERE jurisdiction = ? AND search_query = ? 
                AND cache_expiry > datetime('now')
                ORDER BY created_at DESC LIMIT 1
            """.format(cache_type), (jurisdiction, cache_key)).fetchone()
            
            response_time = (time.time() - start_time) * 1000
            
            if result:
                # Cache hit
                self._update_hit_metrics(cache_type, response_time)
                self._update_cache_access(cache_type, cache_key)
                
                result_data, cache_expiry, created_at = result
                return json.loads(result_data)
            else:
                # Cache miss
                self._update_miss_metrics(cache_type, response_time)
                return None
                
        except Exception as e:
            logger.error(f"Cache get failed for {cache_type}/{cache_key}: {e}")
            self._update_miss_metrics(cache_type, 0)
            return None
    
    async def _set_cache_entry(self, cache_type: str, cache_key: str, 
                             jurisdiction: str, data: Dict[str, Any], 
                             expiry_hours: int) -> bool:
        """Generic method to set cache entry"""
        try:
            cache_expiry = datetime.now() + timedelta(hours=expiry_hours)
            data_json = json.dumps(data)
            data_size = len(data_json.encode('utf-8'))
            
            # Check cache size limits
            if not await self._check_cache_capacity(cache_type, data_size):
                await self._evict_cache_entries(cache_type)
            
            # Store in cache table
            if cache_type == 'definition_cache':
                # Special handling for definition cache
                self.kg._execute("""
                    INSERT OR REPLACE INTO definition_cache
                    (jurisdiction, legal_term, definition_text, authority_citation,
                     confidence_score, cache_expiry, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    jurisdiction,
                    data.get('term', cache_key),
                    data_json,
                    data.get('authority_citation', ''),
                    data.get('confidence_score', 0.7),
                    cache_expiry,
                    datetime.now()
                ))
            elif cache_type == 'case_law_cache':
                # Special handling for case law cache
                self.kg._execute("""
                    INSERT OR REPLACE INTO case_law_cache
                    (jurisdiction, cause_of_action, case_citation, case_summary,
                     relevance_score, authority_level, decision_date, cache_expiry, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    jurisdiction,
                    data.get('cause_of_action', ''),
                    cache_key,
                    data_json,
                    data.get('relevance_score', 0.5),
                    data.get('authority_level', 3),
                    data.get('decision_date'),
                    cache_expiry,
                    datetime.now()
                ))
            else:
                # General legal research cache
                self.kg._execute("""
                    INSERT OR REPLACE INTO legal_research_cache
                    (jurisdiction, search_query, api_source, result_data,
                     relevance_score, cache_expiry, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    jurisdiction,
                    cache_key,
                    'integrated_research',
                    data_json,
                    data.get('relevance_score', 0.5),
                    cache_expiry,
                    datetime.now()
                ))
            
            self.kg.conn.commit()
            logger.debug(f"Cached entry: {cache_type}/{cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed for {cache_type}/{cache_key}: {e}")
            return False
    
    def _generate_definition_key(self, legal_term: str, jurisdiction: str) -> str:
        """Generate cache key for legal definition"""
        key_string = f"definition_{legal_term}_{jurisdiction}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _generate_case_law_key(self, cause_of_action: str, jurisdiction: str) -> str:
        """Generate cache key for case law"""
        key_string = f"case_law_{cause_of_action}_{jurisdiction}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _update_hit_metrics(self, cache_type: str, response_time_ms: float):
        """Update cache hit metrics"""
        metrics = self.performance_metrics[cache_type]
        metrics.total_hits += 1
        metrics.total_requests += 1
        
        # Update average response time
        if metrics.average_response_time_ms == 0:
            metrics.average_response_time_ms = response_time_ms
        else:
            metrics.average_response_time_ms = (
                (metrics.average_response_time_ms * (metrics.total_hits - 1) + response_time_ms) 
                / metrics.total_hits
            )
        
        # Update hit rate
        metrics.hit_rate = metrics.total_hits / metrics.total_requests
        metrics.miss_rate = 1.0 - metrics.hit_rate
    
    def _update_miss_metrics(self, cache_type: str, response_time_ms: float):
        """Update cache miss metrics"""
        metrics = self.performance_metrics[cache_type]
        metrics.total_misses += 1
        metrics.total_requests += 1
        
        # Update rates
        metrics.hit_rate = metrics.total_hits / metrics.total_requests
        metrics.miss_rate = metrics.total_misses / metrics.total_requests
    
    def _update_cache_access(self, cache_type: str, cache_key: str):
        """Update cache access tracking"""
        try:
            # This could be used to track access patterns for LRU eviction
            # For now, we'll just log the access
            logger.debug(f"Cache access: {cache_type}/{cache_key}")
        except Exception as e:
            logger.error(f"Failed to update cache access: {e}")
    
    async def _check_cache_capacity(self, cache_type: str, new_entry_size: int) -> bool:
        """Check if cache has capacity for new entry"""
        try:
            # Get current cache size
            current_size = self.kg._execute("""
                SELECT SUM(LENGTH(result_data)) FROM {}
            """.format(cache_type)).fetchone()
            
            current_size_bytes = current_size[0] if current_size and current_size[0] else 0
            config = self.cache_config[cache_type]
            
            # Check size limit
            if (current_size_bytes + new_entry_size) > self.max_cache_size_bytes:
                return False
            
            # Check entry count limit
            entry_count = self.kg._execute("""
                SELECT COUNT(*) FROM {}
            """.format(cache_type)).fetchone()
            
            current_entries = entry_count[0] if entry_count else 0
            if current_entries >= config['max_entries']:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Cache capacity check failed: {e}")
            return True  # Allow cache on error
    
    async def _evict_cache_entries(self, cache_type: str, eviction_count: int = 100):
        """Evict least recently used cache entries"""
        try:
            logger.info(f"Evicting {eviction_count} entries from {cache_type}")
            
            # Get oldest entries to evict
            if cache_type == 'definition_cache':
                self.kg._execute("""
                    DELETE FROM definition_cache WHERE id IN (
                        SELECT id FROM definition_cache 
                        ORDER BY created_at ASC LIMIT ?
                    )
                """, (eviction_count,))
            elif cache_type == 'case_law_cache':
                self.kg._execute("""
                    DELETE FROM case_law_cache WHERE id IN (
                        SELECT id FROM case_law_cache 
                        ORDER BY created_at ASC LIMIT ?
                    )
                """, (eviction_count,))
            else:
                self.kg._execute("""
                    DELETE FROM legal_research_cache WHERE id IN (
                        SELECT id FROM legal_research_cache 
                        ORDER BY created_at ASC LIMIT ?
                    )
                """, (eviction_count,))
            
            self.kg.conn.commit()
            
            # Update eviction metrics
            self.performance_metrics[cache_type].eviction_count += eviction_count
            
            logger.info(f"Evicted {eviction_count} entries from {cache_type}")
            
        except Exception as e:
            logger.error(f"Cache eviction failed for {cache_type}: {e}")
    
    async def invalidate_cache(self, cache_type: str, pattern: str = None, 
                             jurisdiction: str = None) -> int:
        """Invalidate cache entries based on pattern or jurisdiction"""
        try:
            if cache_type not in self.cache_config:
                logger.error(f"Unknown cache type: {cache_type}")
                return 0
            
            # Build WHERE clause based on parameters
            where_conditions = []
            params = []
            
            if jurisdiction:
                where_conditions.append("jurisdiction = ?")
                params.append(jurisdiction)
            
            if pattern:
                if cache_type == 'definition_cache':
                    where_conditions.append("legal_term LIKE ?")
                elif cache_type == 'case_law_cache':
                    where_conditions.append("cause_of_action LIKE ?")
                else:
                    where_conditions.append("search_query LIKE ?")
                params.append(f"%{pattern}%")
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # Execute deletion
            result = self.kg._execute(f"""
                DELETE FROM {cache_type} WHERE {where_clause}
            """, params)
            
            deleted_count = result.rowcount
            self.kg.conn.commit()
            
            logger.info(f"Invalidated {deleted_count} entries from {cache_type}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return 0
    
    async def _background_cleanup(self):
        """Background task for cache cleanup"""
        logger.info("Started background cache cleanup task")
        
        while True:
            try:
                # Clean expired entries
                for cache_type in self.cache_config.keys():
                    expired_count = self.kg._execute(f"""
                        DELETE FROM {cache_type} 
                        WHERE cache_expiry < datetime('now')
                    """).rowcount
                    
                    if expired_count > 0:
                        logger.info(f"Cleaned {expired_count} expired entries from {cache_type}")
                
                self.kg.conn.commit()
                
                # Check cache sizes and evict if necessary
                for cache_type, config in self.cache_config.items():
                    current_size = await self._get_cache_size(cache_type)
                    
                    if current_size['size_mb'] > self.max_cache_size_mb * config['cleanup_threshold']:
                        await self._evict_cache_entries(cache_type, 500)
                
                # Sleep for 1 hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Background cleanup error: {e}")
                await asyncio.sleep(1800)  # Sleep 30 minutes on error
    
    async def _background_metrics_update(self):
        """Background task for updating cache metrics"""
        logger.info("Started background metrics update task")
        
        while True:
            try:
                # Update cache size metrics
                for cache_type in self.cache_config.keys():
                    size_info = await self._get_cache_size(cache_type)
                    self.performance_metrics[cache_type].cache_size_mb = size_info['size_mb']
                
                # Sleep for 15 minutes
                await asyncio.sleep(900)
                
            except Exception as e:
                logger.error(f"Background metrics update error: {e}")
                await asyncio.sleep(1800)
    
    async def _get_cache_size(self, cache_type: str) -> Dict[str, Any]:
        """Get current cache size information"""
        try:
            if cache_type == 'definition_cache':
                result = self.kg._execute("""
                    SELECT COUNT(*), SUM(LENGTH(definition_text))
                    FROM definition_cache
                """).fetchone()
            elif cache_type == 'case_law_cache':
                result = self.kg._execute("""
                    SELECT COUNT(*), SUM(LENGTH(case_summary))
                    FROM case_law_cache
                """).fetchone()
            else:
                result = self.kg._execute("""
                    SELECT COUNT(*), SUM(LENGTH(result_data))
                    FROM legal_research_cache
                """).fetchone()
            
            entry_count, total_size = result if result else (0, 0)
            size_mb = (total_size or 0) / (1024 * 1024)
            
            return {
                'entry_count': entry_count or 0,
                'size_bytes': total_size or 0,
                'size_mb': size_mb
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache size for {cache_type}: {e}")
            return {'entry_count': 0, 'size_bytes': 0, 'size_mb': 0.0}
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        try:
            stats = {
                'total_performance': {
                    'total_requests': sum(m.total_requests for m in self.performance_metrics.values()),
                    'total_hits': sum(m.total_hits for m in self.performance_metrics.values()),
                    'total_misses': sum(m.total_misses for m in self.performance_metrics.values()),
                    'overall_hit_rate': 0.0,
                    'total_evictions': sum(m.eviction_count for m in self.performance_metrics.values())
                },
                'by_cache_type': {}
            }
            
            # Calculate overall hit rate
            if stats['total_performance']['total_requests'] > 0:
                stats['total_performance']['overall_hit_rate'] = (
                    stats['total_performance']['total_hits'] / 
                    stats['total_performance']['total_requests']
                )
            
            # Add per-cache-type statistics
            for cache_type, metrics in self.performance_metrics.items():
                stats['by_cache_type'][cache_type] = asdict(metrics)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e}")
            return {'error': str(e)}
    
    async def optimize_cache_performance(self) -> Dict[str, Any]:
        """Analyze and optimize cache performance"""
        try:
            optimization_results = {
                'actions_taken': [],
                'recommendations': [],
                'performance_impact': {}
            }
            
            # Analyze hit rates and suggest improvements
            for cache_type, metrics in self.performance_metrics.items():
                if metrics.hit_rate < 0.6:  # Below 60% hit rate
                    # Suggest increasing cache size or expiry times
                    config = self.cache_config[cache_type]
                    
                    if metrics.cache_size_mb < self.max_cache_size_mb * 0.5:
                        optimization_results['recommendations'].append(
                            f"Consider increasing {cache_type} size - current hit rate: {metrics.hit_rate:.2%}"
                        )
                    
                    if config['default_expiry_hours'] < 48:
                        optimization_results['recommendations'].append(
                            f"Consider increasing {cache_type} expiry time for better hit rates"
                        )
                
                # Check for excessive evictions
                if metrics.eviction_count > metrics.total_hits * 0.1:
                    optimization_results['recommendations'].append(
                        f"{cache_type} has high eviction rate - consider increasing cache size"
                    )
            
            # Perform automatic optimizations
            await self._auto_optimize_cache()
            optimization_results['actions_taken'].append("Performed automatic cache optimization")
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            return {'error': str(e)}
    
    async def _auto_optimize_cache(self):
        """Perform automatic cache optimizations"""
        try:
            # Clean up very old entries that are rarely accessed
            for cache_type in self.cache_config.keys():
                old_threshold = datetime.now() - timedelta(days=30)
                
                if cache_type == 'definition_cache':
                    # Keep definitions longer since they change less frequently
                    continue
                
                # Remove entries older than 30 days with low relevance
                deleted_count = self.kg._execute(f"""
                    DELETE FROM {cache_type} 
                    WHERE created_at < ? AND relevance_score < 0.3
                """, (old_threshold,)).rowcount
                
                if deleted_count > 0:
                    logger.info(f"Auto-optimized {cache_type}: removed {deleted_count} old low-relevance entries")
            
            self.kg.conn.commit()
            
        except Exception as e:
            logger.error(f"Auto optimization failed: {e}")
    
    async def preload_common_definitions(self, jurisdiction: str, legal_terms: List[str]):
        """Preload commonly used legal definitions"""
        try:
            logger.info(f"Preloading {len(legal_terms)} definitions for {jurisdiction}")
            
            # This would integrate with the legal research system to preload definitions
            # For now, we'll create placeholder entries
            for term in legal_terms:
                cache_key = self._generate_definition_key(term, jurisdiction)
                
                # Check if already cached
                existing = await self.get_cached_definition(term, jurisdiction)
                if existing:
                    continue
                
                # Create placeholder definition entry
                definition_data = {
                    'term': term,
                    'definition': f"Legal definition of {term} - to be populated",
                    'jurisdiction': jurisdiction,
                    'authority_citation': 'To be determined',
                    'confidence_score': 0.5,
                    'preloaded': True
                }
                
                await self.cache_definition(term, jurisdiction, definition_data, 168)
            
            logger.info(f"Preloaded definitions for {jurisdiction}")
            
        except Exception as e:
            logger.error(f"Definition preloading failed: {e}")