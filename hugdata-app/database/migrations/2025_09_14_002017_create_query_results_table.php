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
        Schema::create('query_results', function (Blueprint $table) {
            $table->id();
            $table->json('data'); // Query result data
            $table->json('columns'); // Column metadata
            $table->integer('row_count')->default(0);
            $table->integer('execution_time_ms')->nullable();
            $table->bigInteger('data_size_bytes')->nullable();
            $table->enum('status', ['success', 'error', 'timeout'])->default('success');
            $table->text('error_details')->nullable();
            $table->foreignId('query_id')->constrained('queries')->onDelete('cascade');
            $table->timestamps();

            $table->index(['query_id', 'status']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('query_results');
    }
};
