<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('queries', function (Blueprint $table) {
            $table->id();
            $table->string('query_id')->unique(); // WrenAI query ID
            $table->text('question'); // Natural language question
            $table->longText('sql')->nullable(); // Generated SQL
            $table->text('sql_generation_reasoning')->nullable();
            $table->json('chart_schema')->nullable(); // Vega-Lite schema
            $table->string('chart_type')->nullable();
            $table->json('suggested_tables')->nullable();
            $table->enum('status', ['pending', 'completed', 'failed', 'stopped'])->default('pending');
            $table->text('error_message')->nullable();
            $table->string('trace_id')->nullable();
            $table->integer('execution_time_ms')->nullable();
            $table->foreignId('thread_id')->constrained()->onDelete('cascade');
            $table->foreignId('project_id')->constrained()->onDelete('cascade');
            $table->timestamps();

            $table->index(['thread_id', 'status']);
            $table->index(['project_id', 'status']);
            $table->index('query_id');
            $table->index('trace_id');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('queries');
    }
};
