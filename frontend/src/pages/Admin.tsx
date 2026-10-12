import { useState, useEffect } from 'react';
import { adminAPI, type DashboardStats, type SystemConfig, type AuditLog } from '../api/admin';
import { formatError } from '../utils/errorFormatter';

export default function Admin() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'config' | 'users' | 'audit'>('dashboard');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [configs, setConfigs] = useState<SystemConfig[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [error, setError] = useState('');

  const [searchQuery, setSearchQuery] = useState('');
  const [editingConfig, setEditingConfig] = useState<{ config_key: string; config_value: string } | null>(null);

  useEffect(() => {
    if (activeTab === 'dashboard') fetchDashboard();
    if (activeTab === 'config') fetchConfig();
    if (activeTab === 'users') fetchUsers();
    if (activeTab === 'audit') fetchAuditLogs();
  }, [activeTab]);

  const fetchDashboard = async () => {
    try {
      const data = await adminAPI.getDashboard();
      setStats(data);
    } catch (err: any) {
      setError(formatError(err) || 'Failed to fetch dashboard');
    }
  };

  const fetchConfig = async () => {
    try {
      const data = await adminAPI.getConfig();
      setConfigs(data);
    } catch (err: any) {
      setError(formatError(err) || 'Failed to fetch config');
    }
  };

  const fetchUsers = async () => {
    try {
      const data = await adminAPI.getUsers(searchQuery ? { search: searchQuery } : {});
      setUsers(data);
    } catch (err: any) {
      setError(formatError(err) || 'Failed to fetch users');
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const data = await adminAPI.getAuditLogs(50);
      setAuditLogs(data);
    } catch (err: any) {
      setError(formatError(err) || 'Failed to fetch audit logs');
    }
  };

  const handleUpdateConfig = async (configKey: string, configValue: string) => {
    try {
      await adminAPI.updateConfig(configKey, configValue);
      setEditingConfig(null);
      await fetchConfig();
    } catch (err: any) {
      setError(formatError(err) || 'Failed to update config');
    }
  };

  const getRoleColor = (role: string) => {
    if (role === 'admin') return 'bg-green-100 text-green-800';
    if (role === 'officer') return 'bg-amber-100 text-amber-800';
    if (role === 'farmer') return 'bg-blue-100 text-blue-800';
    if (role === 'buyer') return 'bg-purple-100 text-purple-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <span className="text-4xl">⚙️</span>
          Admin Panel
        </h1>
        <p className="text-gray-600 mt-1">Manage system configuration, users, and view audit logs</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="flex border-b border-gray-200">
          {[
            { id: 'dashboard', label: 'Dashboard' },
            { id: 'config', label: 'Config' },
            { id: 'users', label: 'Users' },
            { id: 'audit', label: 'Audit Logs' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-primary-600 border-b-2 border-primary-600 bg-primary-50'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        {activeTab === 'dashboard' && stats && (
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Dashboard Statistics</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-primary-50 rounded-lg p-5 border border-primary-200">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Total Users</h3>
                <p className="text-2xl font-bold text-gray-900">{stats.total_users}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-5 border border-green-200">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Farmers</h3>
                <p className="text-2xl font-bold text-gray-900">{(stats.users_by_role as any)?.farmer || 0}</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-5 border border-blue-200">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Buyers</h3>
                <p className="text-2xl font-bold text-gray-900">{(stats.users_by_role as any)?.buyer || 0}</p>
              </div>
              <div className="bg-amber-50 rounded-lg p-5 border border-amber-200">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Officers</h3>
                <p className="text-2xl font-bold text-gray-900">{(stats.users_by_role as any)?.officer || 0}</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-5 border border-purple-200">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Diagnoses</h3>
                <p className="text-2xl font-bold text-gray-900">{stats.total_diagnoses}</p>
              </div>
              <div className="bg-pink-50 rounded-lg p-5 border border-pink-200">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Listings</h3>
                <p className="text-2xl font-bold text-gray-900">{stats.total_listings}</p>
              </div>
              <div className="bg-cyan-50 rounded-lg p-5 border border-cyan-200">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Open Listings</h3>
                <p className="text-2xl font-bold text-gray-900">{stats.open_listings}</p>
              </div>
              <div className="bg-indigo-50 rounded-lg p-5 border border-indigo-200">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Transaction Volume</h3>
                <p className="text-2xl font-bold text-gray-900">₹{Number(stats.total_transaction_volume).toFixed(2)}</p>
              </div>
              <div className="bg-red-50 rounded-lg p-5 border border-red-200">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Active Alerts</h3>
                <p className="text-2xl font-bold text-gray-900">{stats.active_alerts}</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'config' && (
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">System Configuration</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-primary-50 border-b border-primary-200">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Key</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Value</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Description</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Last Updated</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {configs.map((config, index) => (
                    <tr key={config.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-4 py-3 text-sm font-medium">{config.config_key}</td>
                      <td className="px-4 py-3 text-sm">
                        {editingConfig?.config_key === config.config_key ? (
                          <input
                            type="text"
                            value={editingConfig.config_value}
                            onChange={(e) => setEditingConfig({ ...editingConfig, config_value: e.target.value })}
                            className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                          />
                        ) : (
                          <span className="font-mono text-gray-700">{config.config_value}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">{config.description}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">{config.updated_at}</td>
                      <td className="px-4 py-3 text-sm">
                        {editingConfig?.config_key === config.config_key ? (
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleUpdateConfig(config.config_key, editingConfig.config_value)}
                              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs font-medium transition-colors"
                            >
                              Save
                            </button>
                            <button
                              onClick={() => setEditingConfig(null)}
                              className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded text-xs font-medium transition-colors"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setEditingConfig({ config_key: config.config_key, config_value: config.config_value || '' })}
                            className="bg-primary-600 hover:bg-primary-700 text-white px-3 py-1 rounded text-xs font-medium transition-colors"
                          >
                            Edit
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">User Management</h2>
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                placeholder="Search users..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <button
                onClick={fetchUsers}
                className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Search
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-primary-50 border-b border-primary-200">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">ID</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Name</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Email</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Role</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Active</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user, index) => (
                    <tr key={user.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-4 py-3 text-sm">{user.id}</td>
                      <td className="px-4 py-3 text-sm font-medium">{user.full_name}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{user.email}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRoleColor(user.role)}`}>
                          {user.role}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {user.is_active ? 'Yes' : 'No'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Audit Logs</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-primary-50 border-b border-primary-200">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Timestamp</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">User ID</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Action</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Resource</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Details</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">IP Address</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((log, index) => (
                    <tr key={log.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-4 py-3 text-sm text-gray-500">{log.created_at}</td>
                      <td className="px-4 py-3 text-sm">{log.user_id}</td>
                      <td className="px-4 py-3 text-sm font-medium">{log.action}</td>
                      <td className="px-4 py-3 text-sm">{log.entity_type}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{log.details}</td>
                      <td className="px-4 py-3 text-sm text-gray-500">{log.ip_address}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
