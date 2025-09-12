<?php

namespace App\Services;

use App\Models\DataSource;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

class QueryCacheService
{
    private const DEFAULT_TTL = 3600; // 1 hour
    private const MAX_CACHE_SIZE = 10000; // Max rows to cache
    private const CACHE_PREFIX = 'query_cache:';

    public function getCachedQuery(DataSource $dataSource, string $sql): ?array
    {
        $cacheKey = $this->generateCacheKey($dataSource, $sql);
        
        try {
            $cached = Cache::get($cacheKey);
            
            if ($cached) {
                Log::info("Query cache hit", [
                    'data_source_id' => $dataSource->id,
                    'cache_key' => $cacheKey
                ]);
                
                return [
                    'success' => true,
                    'results' => $cached['results'],
                    'row_count' => $cached['row_count'],
                    'execution_time_ms' => 0, // Cached, no execution time
                    'cached' => true,
                    'cached_at' => $cached['cached_at']
                ];
            }
            
            return null;
            
        } catch (\Exception $e) {
            Log::warning("Failed to retrieve from query cache", [
                'error' => $e->getMessage(),
                'cache_key' => $cacheKey
            ]);
            
            return null;
        }
    }

    public function cacheQuery(DataSource $dataSource, string $sql, array $results, int $executionTime): bool
    {
        // Don't cache large result sets or queries that took too long
        if (count($results) > self::MAX_CACHE_SIZE || $executionTime > 30000) {
            return false;
        }

        // Don't cache empty results
        if (empty($results)) {
            return false;
        }

        $cacheKey = $this->generateCacheKey($dataSource, $sql);
        $ttl = $this->calculateTTL($sql, $executionTime);
        
        $cacheData = [
            'results' => $results,
            'row_count' => count($results),
            'execution_time_ms' => $executionTime,
            'cached_at' => now()->toISOString(),
            'data_source_id' => $dataSource->id,
            'sql_hash' => md5($sql)
        ];

        try {
            $success = Cache::put($cacheKey, $cacheData, $ttl);
            
            if ($success) {
                Log::info("Query cached successfully", [
                    'data_source_id' => $dataSource->id,
                    'cache_key' => $cacheKey,
                    'ttl' => $ttl,
                    'row_count' => count($results)
                ]);
            }
            
            return $success;
            
        } catch (\Exception $e) {
            Log::error("Failed to cache query", [
                'error' => $e->getMessage(),
                'cache_key' => $cacheKey,
                'data_source_id' => $dataSource->id
            ]);
            
            return false;
        }
    }

    public function invalidateDataSourceCache(DataSource $dataSource): bool
    {
        try {
            $pattern = self::CACHE_PREFIX . $dataSource->id . ':*';
            $keys = Cache::getStore()->getRedis()->keys($pattern);
            
            if (!empty($keys)) {
                Cache::getStore()->getRedis()->del($keys);
                
                Log::info("Invalidated cache for data source", [
                    'data_source_id' => $dataSource->id,
                    'keys_cleared' => count($keys)
                ]);
            }
            
            return true;
            
        } catch (\Exception $e) {
            Log::error("Failed to invalidate data source cache", [
                'error' => $e->getMessage(),
                'data_source_id' => $dataSource->id
            ]);
            
            return false;
        }
    }

    public function invalidateTableCache(DataSource $dataSource, string $tableName): bool
    {
        try {
            $pattern = self::CACHE_PREFIX . $dataSource->id . ':*' . strtolower($tableName) . '*';
            $keys = Cache::getStore()->getRedis()->keys($pattern);
            
            if (!empty($keys)) {
                Cache::getStore()->getRedis()->del($keys);
                
                Log::info("Invalidated table cache", [
                    'data_source_id' => $dataSource->id,
                    'table_name' => $tableName,
                    'keys_cleared' => count($keys)
                ]);
            }
            
            return true;
            
        } catch (\Exception $e) {
            Log::error("Failed to invalidate table cache", [
                'error' => $e->getMessage(),
                'data_source_id' => $dataSource->id,
                'table_name' => $tableName
            ]);
            
            return false;
        }
    }

    public function getCacheStats(DataSource $dataSource): array
    {
        try {
            $pattern = self::CACHE_PREFIX . $dataSource->id . ':*';
            $keys = Cache::getStore()->getRedis()->keys($pattern);
            
            $totalSize = 0;
            $oldestCache = null;
            $newestCache = null;
            
            foreach ($keys as $key) {
                $data = Cache::get(str_replace(self::CACHE_PREFIX, '', $key));
                if ($data && isset($data['cached_at'])) {
                    $cachedAt = \Carbon\Carbon::parse($data['cached_at']);
                    
                    if (!$oldestCache || $cachedAt->lt($oldestCache)) {
                        $oldestCache = $cachedAt;
                    }
                    
                    if (!$newestCache || $cachedAt->gt($newestCache)) {
                        $newestCache = $cachedAt;
                    }
                    
                    $totalSize += $data['row_count'] ?? 0;
                }
            }
            
            return [
                'total_cached_queries' => count($keys),
                'total_cached_rows' => $totalSize,
                'oldest_cache' => $oldestCache?->toISOString(),
                'newest_cache' => $newestCache?->toISOString(),
                'data_source_id' => $dataSource->id
            ];
            
        } catch (\Exception $e) {
            Log::error("Failed to get cache stats", [
                'error' => $e->getMessage(),
                'data_source_id' => $dataSource->id
            ]);
            
            return [
                'total_cached_queries' => 0,
                'total_cached_rows' => 0,
                'error' => $e->getMessage()
            ];
        }
    }

    public function clearAllCache(): bool
    {
        try {
            $pattern = self::CACHE_PREFIX . '*';
            $keys = Cache::getStore()->getRedis()->keys($pattern);
            
            if (!empty($keys)) {
                Cache::getStore()->getRedis()->del($keys);
                
                Log::info("Cleared all query cache", [
                    'keys_cleared' => count($keys)
                ]);
            }
            
            return true;
            
        } catch (\Exception $e) {
            Log::error("Failed to clear all cache", [
                'error' => $e->getMessage()
            ]);
            
            return false;
        }
    }

    private function generateCacheKey(DataSource $dataSource, string $sql): string
    {
        // Normalize SQL for consistent caching
        $normalizedSql = $this->normalizeSql($sql);
        $sqlHash = md5($normalizedSql);
        
        return self::CACHE_PREFIX . $dataSource->id . ':' . $sqlHash;
    }

    private function normalizeSql(string $sql): string
    {
        // Remove extra whitespace and normalize case
        $normalized = trim(preg_replace('/\s+/', ' ', $sql));
        $normalized = strtolower($normalized);
        
        // Remove trailing semicolon
        $normalized = rtrim($normalized, ';');
        
        return $normalized;
    }

    private function calculateTTL(string $sql, int $executionTime): int
    {
        // Base TTL
        $ttl = self::DEFAULT_TTL;
        
        // Longer TTL for expensive queries
        if ($executionTime > 5000) { // 5+ seconds
            $ttl *= 3; // 3 hours
        } elseif ($executionTime > 1000) { // 1+ seconds
            $ttl *= 2; // 2 hours
        }
        
        // Shorter TTL for queries that might change frequently
        $mutableKeywords = ['count', 'sum', 'avg', 'max', 'min', 'recent', 'today', 'latest'];
        
        foreach ($mutableKeywords as $keyword) {
            if (str_contains(strtolower($sql), $keyword)) {
                $ttl = min($ttl, 1800); // Max 30 minutes for potentially changing data
                break;
            }
        }
        
        // Never cache for more than 6 hours
        return min($ttl, 21600);
    }

    public function shouldCache(string $sql): bool
    {
        // Don't cache non-SELECT queries
        if (!str_starts_with(trim(strtoupper($sql)), 'SELECT')) {
            return false;
        }
        
        // Don't cache queries with random functions
        $nonCacheablePatterns = [
            '/\bRAND\b/i',
            '/\bRANDOM\b/i', 
            '/\bNOW\b/i',
            '/\bCURRENT_TIMESTAMP\b/i',
            '/\bCURRENT_TIME\b/i',
            '/\bCURRENT_DATE\b/i'
        ];
        
        foreach ($nonCacheablePatterns as $pattern) {
            if (preg_match($pattern, $sql)) {
                return false;
            }
        }
        
        return true;
    }
}