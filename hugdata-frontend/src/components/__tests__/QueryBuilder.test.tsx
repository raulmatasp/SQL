import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import QueryBuilder from '../QueryBuilder';

describe('QueryBuilder Component', () => {
  const mockOnQuerySubmit = jest.fn();
  const mockTableSchema = {
    tables: [
      {
        name: 'users',
        columns: [
          { name: 'id', type: 'integer' },
          { name: 'name', type: 'varchar' },
          { name: 'email', type: 'varchar' },
          { name: 'created_at', type: 'timestamp' }
        ]
      },
      {
        name: 'orders',
        columns: [
          { name: 'id', type: 'integer' },
          { name: 'user_id', type: 'integer' },
          { name: 'amount', type: 'decimal' },
          { name: 'status', type: 'varchar' }
        ]
      }
    ]
  };

  beforeEach(() => {
    mockOnQuerySubmit.mockClear();
  });

  test('renders query builder interface', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} schema={mockTableSchema} />);
    
    expect(screen.getByText(/query builder/i)).toBeInTheDocument();
    expect(screen.getByText(/natural language query/i)).toBeInTheDocument();
    expect(screen.getByText(/visual query builder/i)).toBeInTheDocument();
  });

  test('renders natural language query input', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} schema={mockTableSchema} />);
    
    expect(screen.getByPlaceholderText(/describe what you want to find/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /generate query/i })).toBeInTheDocument();
  });

  test('renders table selector', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} schema={mockTableSchema} />);
    
    expect(screen.getByText('users')).toBeInTheDocument();
    expect(screen.getByText('orders')).toBeInTheDocument();
  });

  test('shows column selector when table is selected', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} schema={mockTableSchema} />);
    
    fireEvent.click(screen.getByText('users'));
    
    expect(screen.getByText('id')).toBeInTheDocument();
    expect(screen.getByText('name')).toBeInTheDocument();
    expect(screen.getByText('email')).toBeInTheDocument();
    expect(screen.getByText('created_at')).toBeInTheDocument();
  });

  test('handles natural language query submission', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} schema={mockTableSchema} />);
    
    const input = screen.getByPlaceholderText(/describe what you want to find/i);
    const button = screen.getByRole('button', { name: /generate query/i });
    
    fireEvent.change(input, { target: { value: 'Find all active users' } });
    fireEvent.click(button);
    
    expect(mockOnQuerySubmit).toHaveBeenCalledWith({
      type: 'natural_language',
      query: 'Find all active users',
      schema: mockTableSchema
    });
  });

  test('handles visual query builder submission', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} schema={mockTableSchema} />);
    
    // Select table
    fireEvent.click(screen.getByText('users'));
    
    // Select columns
    fireEvent.click(screen.getByText('name'));
    fireEvent.click(screen.getByText('email'));
    
    // Add condition
    const addConditionButton = screen.getByRole('button', { name: /add condition/i });
    fireEvent.click(addConditionButton);
    
    // Generate query
    const generateButton = screen.getByRole('button', { name: /generate sql/i });
    fireEvent.click(generateButton);
    
    expect(mockOnQuerySubmit).toHaveBeenCalledWith({
      type: 'visual',
      table: 'users',
      columns: ['name', 'email'],
      conditions: expect.any(Array),
      schema: mockTableSchema
    });
  });

  test('validates required fields', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} schema={mockTableSchema} />);
    
    const generateButton = screen.getByRole('button', { name: /generate sql/i });
    fireEvent.click(generateButton);
    
    expect(screen.getByText(/please select a table/i)).toBeInTheDocument();
    expect(mockOnQuerySubmit).not.toHaveBeenCalled();
  });

  test('shows preview of generated SQL', async () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} schema={mockTableSchema} />);
    
    // Build a simple query
    fireEvent.click(screen.getByText('users'));
    fireEvent.click(screen.getByText('name'));
    fireEvent.click(screen.getByText('email'));
    
    const generateButton = screen.getByRole('button', { name: /generate sql/i });
    fireEvent.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText(/sql preview/i)).toBeInTheDocument();
      expect(screen.getByText(/SELECT name, email FROM users/i)).toBeInTheDocument();
    });
  });

  test('handles condition operators', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} schema={mockTableSchema} />);
    
    // Select table and column
    fireEvent.click(screen.getByText('users'));
    fireEvent.click(screen.getByText('name'));
    
    // Add condition
    fireEvent.click(screen.getByRole('button', { name: /add condition/i }));
    
    // Check operator options
    const operatorSelect = screen.getByDisplayValue('equals');
    fireEvent.click(operatorSelect);
    
    expect(screen.getByText('contains')).toBeInTheDocument();
    expect(screen.getByText('starts with')).toBeInTheDocument();
    expect(screen.getByText('greater than')).toBeInTheDocument();
    expect(screen.getByText('less than')).toBeInTheDocument();
  });

  test('allows removing conditions', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} schema={mockTableSchema} />);
    
    // Select table
    fireEvent.click(screen.getByText('users'));
    
    // Add condition
    fireEvent.click(screen.getByRole('button', { name: /add condition/i }));
    
    // Verify condition exists
    expect(screen.getByRole('button', { name: /remove condition/i })).toBeInTheDocument();
    
    // Remove condition
    fireEvent.click(screen.getByRole('button', { name: /remove condition/i }));
    
    // Verify condition is removed
    expect(screen.queryByRole('button', { name: /remove condition/i })).not.toBeInTheDocument();
  });

  test('handles empty schema gracefully', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} schema={{ tables: [] }} />);
    
    expect(screen.getByText(/no tables available/i)).toBeInTheDocument();
  });

  test('shows column types in selector', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} schema={mockTableSchema} />);
    
    fireEvent.click(screen.getByText('users'));
    
    expect(screen.getByText(/id.*integer/)).toBeInTheDocument();
    expect(screen.getByText(/name.*varchar/)).toBeInTheDocument();
    expect(screen.getByText(/email.*varchar/)).toBeInTheDocument();
  });
});