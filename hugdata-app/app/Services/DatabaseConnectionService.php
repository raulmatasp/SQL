<?php

namespace App\Services;

use App\Models\DataSource;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Config;
use PDO;
use PDOException;
use Exception;

class DatabaseConnectionService
{
    private array $connections = [];
    private array $supportedDrivers = [
        'postgresql' => 'pgsql',
        'mysql' => 'mysql',
        'sqlite' => 'sqlite',
        'sqlserver' => 'sqlsrv'
    ];

    public function __construct(
        private QueryCacheService $cacheService = new QueryCacheService()
    ) {}

    /**
     * Get database connection for a data source
     */
    public function getConnection(DataSource $dataSource): PDO
    {
        $connectionKey = "datasource_{$dataSource->id}";
        
        if (isset($this->connections[$connectionKey])) {
            return $this->connections[$connectionKey];
        }

        $connection = $this->createConnection($dataSource);
        $this->connections[$connectionKey] = $connection;
        
        return $connection;
    }

    /**
     * Create a new database connection
     */
    private function createConnection(DataSource $dataSource): PDO
    {
        $config = $dataSource->connection_config;
        $driver = $this->supportedDrivers[$dataSource->type] ?? null;

        if (!$driver) {
            throw new Exception("Unsupported database type: {$dataSource->type}");
        }

        try {
            switch ($dataSource->type) {
                case 'postgresql':
                    return $this->createPostgreSQLConnection($config);
                case 'mysql':
                    return $this->createMySQLConnection($config);
                case 'sqlite':
                    return $this->createSQLiteConnection($config);
                case 'sqlserver':
                    return $this->createSQLServerConnection($config);
                default:
                    throw new Exception("Unsupported database type: {$dataSource->type}");
            }
        } catch (PDOException $e) {
            Log::error("Database connection failed for data source {$dataSource->id}", [
                'error' => $e->getMessage(),
                'type' => $dataSource->type,
                'config' => array_except($config, ['password']) // Don't log passwords
            ]);
            
            throw new Exception("Failed to connect to database: " . $e->getMessage());
        }
    }

    /**
     * Create PostgreSQL connection
     */
    private function createPostgreSQLConnection(array $config): PDO
    {
        $dsn = sprintf(
            'pgsql:host=%s;port=%s;dbname=%s',
            $config['host'],
            $config['port'] ?? 5432,
            $config['database']
        );

        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_TIMEOUT => 30,
        ];

        return new PDO($dsn, $config['username'], $config['password'], $options);
    }

    /**
     * Create MySQL connection
     */
    private function createMySQLConnection(array $config): PDO
    {
        $dsn = sprintf(
            'mysql:host=%s;port=%s;dbname=%s;charset=utf8mb4',
            $config['host'],
            $config['port'] ?? 3306,
            $config['database']
        );

        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_TIMEOUT => 30,
            PDO::MYSQL_ATTR_INIT_COMMAND => "SET sql_mode='STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION'"
        ];

        return new PDO($dsn, $config['username'], $config['password'], $options);
    }

    /**
     * Create SQLite connection
     */
    private function createSQLiteConnection(array $config): PDO
    {
        $dsn = 'sqlite:' . $config['database'];

        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_TIMEOUT => 30,
        ];

        return new PDO($dsn, null, null, $options);
    }

    /**
     * Create SQL Server connection
     */
    private function createSQLServerConnection(array $config): PDO
    {
        $dsn = sprintf(
            'sqlsrv:Server=%s,%s;Database=%s',
            $config['host'],
            $config['port'] ?? 1433,
            $config['database']
        );

        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_TIMEOUT => 30,
        ];

        return new PDO($dsn, $config['username'], $config['password'], $options);
    }

    /**
     * Test database connection
     */
    public function testConnection(DataSource $dataSource): array
    {
        try {
            $connection = $this->createConnection($dataSource);
            
            // Simple test query
            $stmt = $connection->query('SELECT 1 as test');
            $result = $stmt->fetch();
            
            if ($result && $result['test'] == 1) {
                return [
                    'success' => true,
                    'message' => 'Connection successful',
                    'connected_at' => now()->toISOString()
                ];
            }
            
            return [
                'success' => false,
                'message' => 'Connection test failed'
            ];
            
        } catch (Exception $e) {
            Log::error("Connection test failed for data source {$dataSource->id}", [
                'error' => $e->getMessage()
            ]);
            
            return [
                'success' => false,
                'message' => $e->getMessage()
            ];
        }
    }

    /**
     * Execute SQL query safely with caching
     */
    public function executeQuery(DataSource $dataSource, string $sql, int $limit = 1000): array
    {
        // Security: Validate SQL is read-only
        if (!$this->isReadOnlyQuery($sql)) {
            throw new Exception('Only SELECT queries are allowed');
        }

        // Add LIMIT if not present
        if (!preg_match('/\bLIMIT\s+\d+/i', $sql)) {
            $sql = rtrim($sql, '; ') . " LIMIT {$limit}";
        }

        // Try cache first if caching is appropriate
        if ($this->cacheService->shouldCache($sql)) {
            $cached = $this->cacheService->getCachedQuery($dataSource, $sql);
            if ($cached) {
                return $cached;
            }
        }

        $connection = $this->getConnection($dataSource);
        
        try {
            $startTime = microtime(true);
            $stmt = $connection->prepare($sql);
            $stmt->execute();
            $results = $stmt->fetchAll();
            $executionTime = (microtime(true) - $startTime) * 1000;

            $response = [
                'success' => true,
                'results' => $results,
                'row_count' => count($results),
                'execution_time_ms' => round($executionTime, 2),
                'cached' => false
            ];

            // Cache the results if appropriate
            if ($this->cacheService->shouldCache($sql)) {
                $this->cacheService->cacheQuery($dataSource, $sql, $results, $executionTime);
            }

            return $response;

        } catch (PDOException $e) {
            Log::error("Query execution failed", [
                'data_source_id' => $dataSource->id,
                'sql' => $sql,
                'error' => $e->getMessage()
            ]);

            return [
                'success' => false,
                'error' => $e->getMessage(),
                'results' => [],
                'row_count' => 0,
                'execution_time_ms' => 0,
                'cached' => false
            ];
        }
    }

    /**
     * Get database schema information
     */
    public function getSchema(DataSource $dataSource): array
    {
        $connection = $this->getConnection($dataSource);
        
        try {
            switch ($dataSource->type) {
                case 'postgresql':
                    return $this->getPostgreSQLSchema($connection);
                case 'mysql':
                    return $this->getMySQLSchema($connection, $dataSource->connection_config['database']);
                case 'sqlite':
                    return $this->getSQLiteSchema($connection);
                case 'sqlserver':
                    return $this->getSQLServerSchema($connection);
                default:
                    throw new Exception("Schema retrieval not implemented for {$dataSource->type}");
            }
        } catch (Exception $e) {
            Log::error("Schema retrieval failed for data source {$dataSource->id}", [
                'error' => $e->getMessage()
            ]);
            
            return ['tables' => []];
        }
    }

    /**
     * Check if SQL query is read-only
     */
    private function isReadOnlyQuery(string $sql): bool
    {
        $sql = trim(strtoupper($sql));
        $dangerousKeywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
            'TRUNCATE', 'REPLACE', 'MERGE', 'EXEC', 'EXECUTE'
        ];

        foreach ($dangerousKeywords as $keyword) {
            if (str_starts_with($sql, $keyword)) {
                return false;
            }
        }

        return str_starts_with($sql, 'SELECT') || str_starts_with($sql, 'WITH');
    }

    /**
     * Get PostgreSQL schema
     */
    private function getPostgreSQLSchema(PDO $connection): array
    {
        $sql = "
            SELECT 
                t.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key
            FROM information_schema.tables t
            LEFT JOIN information_schema.columns c ON t.table_name = c.table_name
            LEFT JOIN information_schema.key_column_usage pk ON c.table_name = pk.table_name 
                AND c.column_name = pk.column_name
                AND pk.constraint_name LIKE '%_pkey'
            WHERE t.table_schema = 'public' 
                AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name, c.ordinal_position
        ";

        return $this->buildSchemaFromResults($connection, $sql);
    }

    /**
     * Get MySQL schema
     */
    private function getMySQLSchema(PDO $connection, string $database): array
    {
        $sql = "
            SELECT 
                t.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                CASE WHEN c.column_key = 'PRI' THEN true ELSE false END as is_primary_key
            FROM information_schema.tables t
            LEFT JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE t.table_schema = ? AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name, c.ordinal_position
        ";

        $stmt = $connection->prepare($sql);
        $stmt->execute([$database]);
        $results = $stmt->fetchAll();

        return $this->buildSchemaFromResults($connection, $sql, [$database]);
    }

    /**
     * Get SQLite schema
     */
    private function getSQLiteSchema(PDO $connection): array
    {
        $tables = [];
        
        // Get table names
        $stmt = $connection->query("SELECT name FROM sqlite_master WHERE type='table'");
        $tableNames = $stmt->fetchAll(PDO::FETCH_COLUMN);
        
        foreach ($tableNames as $tableName) {
            $stmt = $connection->prepare("PRAGMA table_info(?)");
            $stmt->execute([$tableName]);
            $columns = $stmt->fetchAll();
            
            $tableColumns = [];
            foreach ($columns as $column) {
                $tableColumns[] = [
                    'name' => $column['name'],
                    'type' => $column['type'],
                    'nullable' => !$column['notnull'],
                    'default' => $column['dflt_value'],
                    'is_primary_key' => (bool)$column['pk']
                ];
            }
            
            $tables[$tableName] = ['columns' => $tableColumns];
        }
        
        return ['tables' => $tables];
    }

    /**
     * Get SQL Server schema
     */
    private function getSQLServerSchema(PDO $connection): array
    {
        $sql = "
            SELECT 
                t.TABLE_NAME as table_name,
                c.COLUMN_NAME as column_name,
                c.DATA_TYPE as data_type,
                c.IS_NULLABLE as is_nullable,
                c.COLUMN_DEFAULT as column_default,
                CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END as is_primary_key
            FROM INFORMATION_SCHEMA.TABLES t
            LEFT JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME
            LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk ON c.TABLE_NAME = pk.TABLE_NAME 
                AND c.COLUMN_NAME = pk.COLUMN_NAME
            WHERE t.TABLE_TYPE = 'BASE TABLE'
            ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION
        ";

        return $this->buildSchemaFromResults($connection, $sql);
    }

    /**
     * Build schema array from SQL results
     */
    private function buildSchemaFromResults(PDO $connection, string $sql, array $params = []): array
    {
        $stmt = $connection->prepare($sql);
        $stmt->execute($params);
        $results = $stmt->fetchAll();

        $tables = [];
        foreach ($results as $row) {
            $tableName = $row['table_name'];
            if (!isset($tables[$tableName])) {
                $tables[$tableName] = ['columns' => []];
            }
            
            if ($row['column_name']) {
                $tables[$tableName]['columns'][] = [
                    'name' => $row['column_name'],
                    'type' => $row['data_type'],
                    'nullable' => $row['is_nullable'] === 'YES' || $row['is_nullable'] === '1',
                    'default' => $row['column_default'],
                    'is_primary_key' => (bool)$row['is_primary_key']
                ];
            }
        }

        return ['tables' => $tables];
    }

    /**
     * Close connection
     */
    public function closeConnection(DataSource $dataSource): void
    {
        $connectionKey = "datasource_{$dataSource->id}";
        unset($this->connections[$connectionKey]);
    }

    /**
     * Close all connections
     */
    public function closeAllConnections(): void
    {
        $this->connections = [];
    }
}