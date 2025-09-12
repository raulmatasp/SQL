<?php

namespace App\Http\Controllers;

use App\Models\DataSource;
use App\Models\Project;
use App\Models\Query;
use App\Services\AIService;
use App\Services\DatabaseConnectionService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ChartController extends Controller
{
    public function __construct(
        private AIService $aiService,
        private DatabaseConnectionService $dbService
    ) {}

    public function suggestCharts(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'query_id' => 'required|uuid|exists:queries,id',
            'data_source_id' => 'required|uuid|exists:data_sources,id'
        ]);

        try {
            $query = Query::findOrFail($validated['query_id']);
            $dataSource = DataSource::findOrFail($validated['data_source_id']);

            $this->authorize('view', $query);
            $this->authorize('view', $dataSource);

            $chartSuggestions = $this->generateChartSuggestions(
                $query->results ?? [],
                $query->generated_sql,
                $query->natural_language
            );

            return response()->json([
                'suggestions' => $chartSuggestions,
                'query_id' => $query->id
            ]);

        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Failed to generate chart suggestions',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    public function generateChart(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'query_id' => 'required|uuid|exists:queries,id',
            'chart_type' => 'required|in:bar,line,pie,scatter,area,histogram,heatmap',
            'x_axis' => 'required|string',
            'y_axis' => 'sometimes|string',
            'title' => 'nullable|string',
            'options' => 'nullable|array'
        ]);

        try {
            $query = Query::findOrFail($validated['query_id']);
            $this->authorize('view', $query);

            if (!$query->results || empty($query->results)) {
                return response()->json([
                    'error' => 'No data available for chart generation'
                ], 400);
            }

            $chartConfig = $this->buildChartConfig(
                $validated['chart_type'],
                $query->results,
                $validated['x_axis'],
                $validated['y_axis'] ?? null,
                $validated['title'] ?? null,
                $validated['options'] ?? []
            );

            return response()->json([
                'chart_config' => $chartConfig,
                'data_summary' => [
                    'total_rows' => count($query->results),
                    'columns' => array_keys($query->results[0] ?? [])
                ]
            ]);

        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Failed to generate chart',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    public function analyzeTrends(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'data_source_id' => 'required|uuid|exists:data_sources,id',
            'table' => 'required|string',
            'date_column' => 'required|string',
            'metric_column' => 'required|string',
            'time_period' => 'sometimes|in:day,week,month,quarter,year',
            'limit' => 'sometimes|integer|min:1|max:1000'
        ]);

        try {
            $dataSource = DataSource::findOrFail($validated['data_source_id']);
            $this->authorize('view', $dataSource);

            $timePeriod = $validated['time_period'] ?? 'day';
            $limit = $validated['limit'] ?? 100;

            $trendQuery = $this->buildTrendQuery(
                $validated['table'],
                $validated['date_column'],
                $validated['metric_column'],
                $timePeriod,
                $limit,
                $dataSource->type
            );

            $result = $this->dbService->executeQuery($dataSource, $trendQuery);

            if (!$result['success']) {
                return response()->json([
                    'error' => 'Failed to analyze trends',
                    'message' => $result['error'] ?? 'Unknown error'
                ], 400);
            }

            $trendAnalysis = $this->analyzeTrendData($result['results']);

            return response()->json([
                'trend_data' => $result['results'],
                'analysis' => $trendAnalysis,
                'suggested_charts' => $this->suggestTrendCharts($result['results'])
            ]);

        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Failed to analyze trends',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    private function generateChartSuggestions(array $data, string $sql, string $naturalLanguage): array
    {
        if (empty($data)) {
            return [];
        }

        $columns = array_keys($data[0]);
        $numericColumns = [];
        $textColumns = [];
        $dateColumns = [];

        foreach ($columns as $column) {
            $sampleValue = $data[0][$column] ?? null;
            
            if (is_numeric($sampleValue)) {
                $numericColumns[] = $column;
            } elseif ($this->isDateColumn($column, $sampleValue)) {
                $dateColumns[] = $column;
            } else {
                $textColumns[] = $column;
            }
        }

        $suggestions = [];

        if (!empty($numericColumns) && !empty($textColumns)) {
            $suggestions[] = [
                'type' => 'bar',
                'title' => 'Bar Chart',
                'description' => 'Compare values across categories',
                'x_axis' => $textColumns[0],
                'y_axis' => $numericColumns[0],
                'confidence' => 0.8
            ];
        }

        if (count($numericColumns) >= 2) {
            $suggestions[] = [
                'type' => 'scatter',
                'title' => 'Scatter Plot',
                'description' => 'Show relationship between two metrics',
                'x_axis' => $numericColumns[0],
                'y_axis' => $numericColumns[1],
                'confidence' => 0.7
            ];
        }

        if (!empty($dateColumns) && !empty($numericColumns)) {
            $suggestions[] = [
                'type' => 'line',
                'title' => 'Time Series',
                'description' => 'Show trends over time',
                'x_axis' => $dateColumns[0],
                'y_axis' => $numericColumns[0],
                'confidence' => 0.9
            ];
        }

        if (!empty($textColumns) && count($data) <= 20) {
            $suggestions[] = [
                'type' => 'pie',
                'title' => 'Pie Chart',
                'description' => 'Show distribution of categories',
                'x_axis' => $textColumns[0],
                'y_axis' => $numericColumns[0] ?? null,
                'confidence' => 0.6
            ];
        }

        return array_slice($suggestions, 0, 5);
    }

    private function buildChartConfig(string $type, array $data, string $xAxis, ?string $yAxis, ?string $title, array $options): array
    {
        $config = [
            'type' => $type,
            'data' => [
                'labels' => array_column($data, $xAxis),
                'datasets' => []
            ],
            'options' => [
                'responsive' => true,
                'maintainAspectRatio' => false,
                'plugins' => [
                    'title' => [
                        'display' => !empty($title),
                        'text' => $title ?? "Chart for {$xAxis}"
                    ]
                ]
            ]
        ];

        if ($yAxis) {
            $config['data']['datasets'][] = [
                'label' => $yAxis,
                'data' => array_column($data, $yAxis),
                'backgroundColor' => $this->generateColors(count($data)),
                'borderColor' => $this->generateBorderColors(count($data)),
                'borderWidth' => 1
            ];
        }

        return array_merge_recursive($config, $options);
    }

    private function buildTrendQuery(string $table, string $dateColumn, string $metricColumn, string $timePeriod, int $limit, string $dbType): string
    {
        $dateFormat = match($dbType) {
            'postgresql' => match($timePeriod) {
                'day' => "DATE({$dateColumn})",
                'week' => "DATE_TRUNC('week', {$dateColumn})",
                'month' => "DATE_TRUNC('month', {$dateColumn})",
                'quarter' => "DATE_TRUNC('quarter', {$dateColumn})",
                'year' => "DATE_TRUNC('year', {$dateColumn})",
                default => "DATE({$dateColumn})"
            },
            'mysql' => match($timePeriod) {
                'day' => "DATE({$dateColumn})",
                'week' => "YEARWEEK({$dateColumn})",
                'month' => "DATE_FORMAT({$dateColumn}, '%Y-%m')",
                'quarter' => "CONCAT(YEAR({$dateColumn}), '-Q', QUARTER({$dateColumn}))",
                'year' => "YEAR({$dateColumn})",
                default => "DATE({$dateColumn})"
            },
            default => "DATE({$dateColumn})"
        };

        return "
            SELECT 
                {$dateFormat} as period,
                COUNT(*) as record_count,
                SUM({$metricColumn}) as total_{$metricColumn},
                AVG({$metricColumn}) as avg_{$metricColumn},
                MIN({$metricColumn}) as min_{$metricColumn},
                MAX({$metricColumn}) as max_{$metricColumn}
            FROM {$table}
            WHERE {$dateColumn} IS NOT NULL 
              AND {$metricColumn} IS NOT NULL
            GROUP BY {$dateFormat}
            ORDER BY period DESC
            LIMIT {$limit}
        ";
    }

    private function analyzeTrendData(array $data): array
    {
        if (count($data) < 2) {
            return ['trend' => 'insufficient_data'];
        }

        $values = array_column($data, 'total_' . array_keys($data[0])[2]);
        $trend = $this->calculateTrend($values);
        
        return [
            'trend' => $trend,
            'total_periods' => count($data),
            'growth_rate' => $this->calculateGrowthRate($values),
            'volatility' => $this->calculateVolatility($values)
        ];
    }

    private function suggestTrendCharts(array $data): array
    {
        return [
            [
                'type' => 'line',
                'title' => 'Trend Over Time',
                'x_axis' => 'period',
                'y_axis' => array_keys($data[0])[2] ?? 'value'
            ],
            [
                'type' => 'area',
                'title' => 'Area Chart',
                'x_axis' => 'period',
                'y_axis' => array_keys($data[0])[2] ?? 'value'
            ]
        ];
    }

    private function isDateColumn(string $columnName, $sampleValue): bool
    {
        $dateIndicators = ['date', 'time', 'created', 'updated', 'timestamp'];
        
        foreach ($dateIndicators as $indicator) {
            if (str_contains(strtolower($columnName), $indicator)) {
                return true;
            }
        }

        return false;
    }

    private function generateColors(int $count): array
    {
        $colors = [
            'rgba(54, 162, 235, 0.6)',
            'rgba(255, 99, 132, 0.6)', 
            'rgba(255, 206, 86, 0.6)',
            'rgba(75, 192, 192, 0.6)',
            'rgba(153, 102, 255, 0.6)',
            'rgba(255, 159, 64, 0.6)'
        ];

        return array_slice(array_merge(...array_fill(0, ceil($count / count($colors)), $colors)), 0, $count);
    }

    private function generateBorderColors(int $count): array
    {
        $colors = [
            'rgba(54, 162, 235, 1)',
            'rgba(255, 99, 132, 1)',
            'rgba(255, 206, 86, 1)', 
            'rgba(75, 192, 192, 1)',
            'rgba(153, 102, 255, 1)',
            'rgba(255, 159, 64, 1)'
        ];

        return array_slice(array_merge(...array_fill(0, ceil($count / count($colors)), $colors)), 0, $count);
    }

    private function calculateTrend(array $values): string
    {
        if (count($values) < 2) return 'stable';

        $first = array_slice($values, 0, count($values) / 2);
        $second = array_slice($values, count($values) / 2);

        $firstAvg = array_sum($first) / count($first);
        $secondAvg = array_sum($second) / count($second);

        $change = ($secondAvg - $firstAvg) / $firstAvg * 100;

        if ($change > 5) return 'increasing';
        if ($change < -5) return 'decreasing';
        return 'stable';
    }

    private function calculateGrowthRate(array $values): float
    {
        if (count($values) < 2) return 0;

        $first = reset($values);
        $last = end($values);

        if ($first == 0) return 0;

        return round(($last - $first) / $first * 100, 2);
    }

    private function calculateVolatility(array $values): float
    {
        if (count($values) < 2) return 0;

        $mean = array_sum($values) / count($values);
        $variance = array_sum(array_map(fn($x) => pow($x - $mean, 2), $values)) / count($values);
        
        return round(sqrt($variance), 2);
    }
}