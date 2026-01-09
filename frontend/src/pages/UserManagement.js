import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { toast } from 'sonner';
import { Users, Lock, Eye, EyeOff, RefreshCw, Edit, Trash2, Save, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const UserManagement = () => {
  const { token } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [changingPassword, setChangingPassword] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [showPasswords, setShowPasswords] = useState({});
  const [editingUser, setEditingUser] = useState(null);
  const [editFormData, setEditFormData] = useState({});
  const [deletingUser, setDeletingUser] = useState(null);

  // Check if in development mode
  const isDev = process.env.NODE_ENV === 'development' || process.env.REACT_APP_ENVIRONMENT === 'development';

  useEffect(() => {
    if (!isDev) {
      toast.error('User management is only available in development mode');
      return;
    }
    if (token) {
      fetchUsers();
    }
  }, [isDev, token]);

  const fetchUsers = async () => {
    if (!token) {
      toast.error('Please login first to access user management');
      return;
    }
    
    try {
      setLoading(true);
      const response = await axios.get(`${API}/auth/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      console.log('Users fetched:', response.data);
      setUsers(response.data.users || []);
    } catch (error) {
      console.error('Error fetching users:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to load users';
      console.error('Full error:', error.response?.data);
      toast.error(`Failed to load users: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (email) => {
    if (!newPassword.trim() || newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    try {
      setChangingPassword(email);
      await axios.post(
        `${API}/auth/change-password`,
        {
          email: email,
          new_password: newPassword
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      toast.success(`Password changed successfully for ${email}`);
      setNewPassword('');
      setChangingPassword(null);
      await fetchUsers(); // Refresh list
    } catch (error) {
      console.error('Error changing password:', error);
      toast.error(error.response?.data?.detail || 'Failed to change password');
    } finally {
      setChangingPassword(null);
    }
  };

  const togglePasswordVisibility = (email) => {
    setShowPasswords(prev => ({
      ...prev,
      [email]: !prev[email]
    }));
  };

  const handleEditUser = (user) => {
    setEditingUser(user.email);
    setEditFormData({
      name: user.name || '',
      department: user.department || '',
      role: user.role || '',
      status: user.status || 'active'
    });
  };

  const handleSaveEdit = async (email) => {
    try {
      const response = await axios.put(
        `${API}/auth/users/${encodeURIComponent(email)}`,
        editFormData,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      toast.success(response.data.message || 'User updated successfully');
      setEditingUser(null);
      setEditFormData({});
      await fetchUsers(); // Refresh list
    } catch (error) {
      console.error('Error updating user:', error);
      toast.error(error.response?.data?.detail || 'Failed to update user');
    }
  };

  const handleCancelEdit = () => {
    setEditingUser(null);
    setEditFormData({});
  };

  const handleDeleteUser = async (email) => {
    if (!window.confirm(`Are you sure you want to delete user ${email}? This action cannot be undone.`)) {
      return;
    }

    try {
      setDeletingUser(email);
      const response = await axios.delete(
        `${API}/auth/users/${encodeURIComponent(email)}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      toast.success(response.data.message || 'User deleted successfully');
      await fetchUsers(); // Refresh list
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete user');
    } finally {
      setDeletingUser(null);
    }
  };

  if (!isDev) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-gray-600">User management is only available in development mode.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Users className="w-8 h-8 text-indigo-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
                <p className="text-sm text-gray-500">Development Mode Only</p>
              </div>
            </div>
            <Button
              onClick={fetchUsers}
              disabled={loading}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto" />
              <p className="mt-4 text-gray-600">Loading users...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Department
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Password Hash
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {user.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {editingUser === user.email ? (
                          <Input
                            type="text"
                            value={editFormData.name}
                            onChange={(e) => setEditFormData({...editFormData, name: e.target.value})}
                            className="w-32 h-8 text-xs"
                            placeholder="Name"
                          />
                        ) : (
                          user.name || 'N/A'
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {editingUser === user.email ? (
                          <select
                            value={editFormData.department}
                            onChange={(e) => setEditFormData({...editFormData, department: e.target.value})}
                            className="w-32 h-8 text-xs border border-gray-300 rounded px-2"
                          >
                            <option value="">Select Department</option>
                            <option value="sales">Sales</option>
                            <option value="operations">Operations</option>
                            <option value="finance">Finance</option>
                            <option value="hr">Human Resources</option>
                            <option value="marketing">Marketing</option>
                            <option value="technology">Technology</option>
                          </select>
                        ) : (
                          user.department || 'N/A'
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {editingUser === user.email ? (
                          <select
                            value={editFormData.role}
                            onChange={(e) => setEditFormData({...editFormData, role: e.target.value})}
                            className="w-32 h-8 text-xs border border-gray-300 rounded px-2"
                          >
                            <option value="">Select Role</option>
                            <option value="VP">VP</option>
                            <option value="Director">Director</option>
                            <option value="Manager">Manager</option>
                            <option value="Team Member">Team Member</option>
                          </select>
                        ) : (
                          user.role || 'N/A'
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {editingUser === user.email ? (
                          <select
                            value={editFormData.status}
                            onChange={(e) => setEditFormData({...editFormData, status: e.target.value})}
                            className="w-24 h-8 text-xs border border-gray-300 rounded px-2"
                          >
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                          </select>
                        ) : (
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            user.status === 'active' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {user.status}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs">
                            {showPasswords[user.email] 
                              ? user.password_hash 
                              : user.password_hash ? '••••••••••••••••' : 'N/A'}
                          </span>
                          {user.password_hash && (
                            <button
                              onClick={() => togglePasswordVisibility(user.email)}
                              className="text-gray-400 hover:text-gray-600"
                            >
                              {showPasswords[user.email] ? (
                                <EyeOff className="w-4 h-4" />
                              ) : (
                                <Eye className="w-4 h-4" />
                              )}
                            </button>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="flex items-center gap-2">
                          {editingUser === user.email ? (
                            <>
                              <Button
                                onClick={() => handleSaveEdit(user.email)}
                                size="sm"
                                className="bg-green-600 hover:bg-green-700 h-8 text-xs"
                              >
                                <Save className="w-3 h-3 mr-1" />
                                Save
                              </Button>
                              <Button
                                onClick={handleCancelEdit}
                                size="sm"
                                variant="outline"
                                className="h-8 text-xs"
                              >
                                <X className="w-3 h-3 mr-1" />
                                Cancel
                              </Button>
                            </>
                          ) : changingPassword === user.email ? (
                            <>
                              <Input
                                type="password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                placeholder="New password"
                                className="w-32 h-8 text-xs"
                                autoFocus
                              />
                              <Button
                                onClick={() => handleChangePassword(user.email)}
                                size="sm"
                                className="bg-green-600 hover:bg-green-700 h-8 text-xs"
                              >
                                Save
                              </Button>
                              <Button
                                onClick={() => {
                                  setChangingPassword(null);
                                  setNewPassword('');
                                }}
                                size="sm"
                                variant="outline"
                                className="h-8 text-xs"
                              >
                                Cancel
                              </Button>
                            </>
                          ) : (
                            <>
                              <Button
                                onClick={() => handleEditUser(user)}
                                size="sm"
                                className="bg-blue-600 hover:bg-blue-700 h-8 text-xs"
                              >
                                <Edit className="w-3 h-3 mr-1" />
                                Edit
                              </Button>
                              <Button
                                onClick={() => setChangingPassword(user.email)}
                                size="sm"
                                className="bg-indigo-600 hover:bg-indigo-700 h-8 text-xs"
                              >
                                <Lock className="w-3 h-3 mr-1" />
                                Password
                              </Button>
                              <Button
                                onClick={() => handleDeleteUser(user.email)}
                                size="sm"
                                disabled={deletingUser === user.email}
                                className="bg-red-600 hover:bg-red-700 h-8 text-xs"
                              >
                                <Trash2 className="w-3 h-3 mr-1" />
                                {deletingUser === user.email ? 'Deleting...' : 'Delete'}
                              </Button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {users.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-gray-500">No users found</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserManagement;

