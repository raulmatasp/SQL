import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dataSourceService, projectService, type DataSource, type Project } from '../services/api';
import { useParams } from 'react-router-dom';

const DataSources: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);

  // Fetch project and data sources
  const { data: project, isLoading: projectLoading } = useQuery<Project>({
    queryKey: ['project', projectId],
    queryFn: () => projectService.getById(projectId!),
    enabled: !!projectId,
  });

  const { data: dataSources, isLoading: sourcesLoading } = useQuery<DataSource[]>({
    queryKey: ['dataSources', projectId],
    queryFn: () => dataSourceService.getAll(projectId!),
    enabled: !!projectId,
  });

  // Mutations
  const testConnectionMutation = useMutation({
    mutationFn: dataSourceService.testConnection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataSources', projectId] });
    },
  });

  const deleteDataSourceMutation = useMutation({
    mutationFn: dataSourceService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataSources', projectId] });
    },
  });

  if (projectLoading || sourcesLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{project?.name}</h1>
          <p className="text-gray-600">Manage data sources for this project</p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Add Data Source
        </button>
      </div>

      {/* Data Sources List */}
      <div className="grid gap-4">
        {dataSources?.map((dataSource) => (
          <DataSourceCard
            key={dataSource.id}
            dataSource={dataSource}
            onTestConnection={(id) => testConnectionMutation.mutate(id)}
            onDelete={(id) => deleteDataSourceMutation.mutate(id)}
            isTestingConnection={testConnectionMutation.isPending}
          />
        ))}

        {(!dataSources || dataSources.length === 0) && (
          <div className="text-center py-12">
            <div className="text-gray-500 text-lg">No data sources configured</div>
            <p className="text-gray-400">Add your first data source to get started</p>
          </div>
        )}
      </div>

      {/* Add Data Source Form */}
      {showAddForm && (
        <AddDataSourceForm
          projectId={projectId!}
          onClose={() => setShowAddForm(false)}
          onSuccess={() => {
            setShowAddForm(false);
            queryClient.invalidateQueries({ queryKey: ['dataSources', projectId] });
          }}
        />
      )}
    </div>
  );
};

// Data Source Card Component
interface DataSourceCardProps {
  dataSource: DataSource;
  onTestConnection: (id: string) => void;
  onDelete: (id: string) => void;
  isTestingConnection: boolean;
}

const DataSourceCard: React.FC<DataSourceCardProps> = ({
  dataSource,
  onTestConnection,
  onDelete,
  isTestingConnection
}) => {
  const statusColor = dataSource.status === 'active' 
    ? 'text-green-600 bg-green-100' 
    : 'text-red-600 bg-red-100';

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-medium text-gray-900">{dataSource.name}</h3>
            <span className={`px-2 py-1 text-xs rounded-full ${statusColor}`}>
              {dataSource.status}
            </span>
            <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
              {dataSource.type.toUpperCase()}
            </span>
          </div>
          
          <div className="text-sm text-gray-600 space-y-1">
            <div>Host: {dataSource.connection_config.host || 'N/A'}</div>
            <div>Database: {dataSource.connection_config.database}</div>
            {dataSource.last_connected_at && (
              <div>Last connected: {new Date(dataSource.last_connected_at).toLocaleString()}</div>
            )}
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => onTestConnection(dataSource.id)}
            disabled={isTestingConnection}
            className="bg-blue-50 text-blue-600 px-3 py-1 rounded text-sm hover:bg-blue-100 disabled:opacity-50"
          >
            {isTestingConnection ? 'Testing...' : 'Test Connection'}
          </button>
          <button
            onClick={() => onDelete(dataSource.id)}
            className="bg-red-50 text-red-600 px-3 py-1 rounded text-sm hover:bg-red-100"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
};

// Add Data Source Form Component
interface AddDataSourceFormProps {
  projectId: string;
  onClose: () => void;
  onSuccess: () => void;
}

const AddDataSourceForm: React.FC<AddDataSourceFormProps> = ({
  projectId,
  onClose,
  onSuccess
}) => {
  const [formData, setFormData] = useState({
    name: '',
    type: 'postgresql' as DataSource['type'],
    connection_config: {
      host: '',
      port: '',
      database: '',
      username: '',
      password: '',
    },
  });

  const addDataSourceMutation = useMutation({
    mutationFn: (data: typeof formData) => dataSourceService.create(projectId, data),
    onSuccess,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    addDataSourceMutation.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">Add Data Source</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Database Type</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value as DataSource['type'] })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="postgresql">PostgreSQL</option>
              <option value="mysql">MySQL</option>
              <option value="sqlite">SQLite</option>
              <option value="bigquery">BigQuery</option>
              <option value="snowflake">Snowflake</option>
            </select>
          </div>

          {formData.type !== 'sqlite' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Host</label>
                <input
                  type="text"
                  value={formData.connection_config.host}
                  onChange={(e) => setFormData({
                    ...formData,
                    connection_config: { ...formData.connection_config, host: e.target.value }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
                <input
                  type="number"
                  value={formData.connection_config.port}
                  onChange={(e) => setFormData({
                    ...formData,
                    connection_config: { ...formData.connection_config, port: e.target.value }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {formData.type === 'sqlite' ? 'Database File Path' : 'Database Name'}
            </label>
            <input
              type="text"
              value={formData.connection_config.database}
              onChange={(e) => setFormData({
                ...formData,
                connection_config: { ...formData.connection_config, database: e.target.value }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {formData.type !== 'sqlite' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                <input
                  type="text"
                  value={formData.connection_config.username}
                  onChange={(e) => setFormData({
                    ...formData,
                    connection_config: { ...formData.connection_config, username: e.target.value }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  type="password"
                  value={formData.connection_config.password}
                  onChange={(e) => setFormData({
                    ...formData,
                    connection_config: { ...formData.connection_config, password: e.target.value }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </>
          )}

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={addDataSourceMutation.isPending}
              className="flex-1 bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {addDataSourceMutation.isPending ? 'Adding...' : 'Add Data Source'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-md hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DataSources;