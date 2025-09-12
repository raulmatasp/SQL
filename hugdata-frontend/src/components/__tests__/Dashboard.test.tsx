import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from '../Dashboard';

// Mock the API service
jest.mock('../../services/api', () => ({
  getQueries: jest.fn(),
  createQuery: jest.fn(),
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const renderWithProviders = (component: React.ReactElement) => {
  const testQueryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={testQueryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders dashboard title', () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
  });

  test('renders query input form', () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByPlaceholderText(/enter your query/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
  });

  test('handles query submission', async () => {
    const mockCreateQuery = require('../../services/api').createQuery;
    mockCreateQuery.mockResolvedValue({
      data: { sql: 'SELECT * FROM users', result: [] }
    });

    renderWithProviders(<Dashboard />);
    
    const input = screen.getByPlaceholderText(/enter your query/i);
    const submitButton = screen.getByRole('button', { name: /submit/i });

    fireEvent.change(input, { target: { value: 'Show me all users' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockCreateQuery).toHaveBeenCalledWith('Show me all users');
    });
  });

  test('displays loading state during query', async () => {
    const mockCreateQuery = require('../../services/api').createQuery;
    mockCreateQuery.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

    renderWithProviders(<Dashboard />);
    
    const input = screen.getByPlaceholderText(/enter your query/i);
    const submitButton = screen.getByRole('button', { name: /submit/i });

    fireEvent.change(input, { target: { value: 'Show me all users' } });
    fireEvent.click(submitButton);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  test('displays error message on query failure', async () => {
    const mockCreateQuery = require('../../services/api').createQuery;
    mockCreateQuery.mockRejectedValue(new Error('Query failed'));

    renderWithProviders(<Dashboard />);
    
    const input = screen.getByPlaceholderText(/enter your query/i);
    const submitButton = screen.getByRole('button', { name: /submit/i });

    fireEvent.change(input, { target: { value: 'Invalid query' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  test('renders query results', async () => {
    const mockCreateQuery = require('../../services/api').createQuery;
    const mockResult = {
      data: {
        sql: 'SELECT * FROM users',
        result: [
          { id: 1, name: 'John Doe', email: 'john@example.com' },
          { id: 2, name: 'Jane Smith', email: 'jane@example.com' }
        ]
      }
    };
    mockCreateQuery.mockResolvedValue(mockResult);

    renderWithProviders(<Dashboard />);
    
    const input = screen.getByPlaceholderText(/enter your query/i);
    const submitButton = screen.getByRole('button', { name: /submit/i });

    fireEvent.change(input, { target: { value: 'Show me all users' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });
  });

  test('clears results when new query is submitted', async () => {
    const mockCreateQuery = require('../../services/api').createQuery;
    mockCreateQuery.mockResolvedValueOnce({
      data: { sql: 'SELECT * FROM users', result: [{ id: 1, name: 'John' }] }
    });
    mockCreateQuery.mockResolvedValueOnce({
      data: { sql: 'SELECT * FROM products', result: [{ id: 1, name: 'Product A' }] }
    });

    renderWithProviders(<Dashboard />);
    
    const input = screen.getByPlaceholderText(/enter your query/i);
    const submitButton = screen.getByRole('button', { name: /submit/i });

    // First query
    fireEvent.change(input, { target: { value: 'Show users' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('John')).toBeInTheDocument();
    });

    // Second query
    fireEvent.change(input, { target: { value: 'Show products' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Product A')).toBeInTheDocument();
      expect(screen.queryByText('John')).not.toBeInTheDocument();
    });
  });
});