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
        Schema::create('data_sources', function (Blueprint $table) {
            $table->id();
            $table->string('name');
            $table->string('type'); // postgres, mysql, bigquery, etc.
            $table->json('connection_params');
            $table->text('description')->nullable();
            $table->enum('status', ['active', 'inactive', 'testing'])->default('active');
            $table->timestamp('last_connected_at')->nullable();
            $table->foreignId('project_id')->constrained()->onDelete('cascade');
            $table->timestamps();

            $table->index(['project_id', 'status']);
            $table->index(['type', 'status']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('data_sources');
    }
};
