import { useState, useEffect } from 'react';
import { accountsAPI } from '../api';
import { Plus, CreditCard, Trash2 } from 'lucide-react';

export default function Accounts() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    account_type: 'savings',
    initial_balance: 0,
  });
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      const response = await accountsAPI.getAccounts();
      setAccounts(response.data);
    } catch (error) {
      console.error('Error fetching accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');

    try {
      await accountsAPI.createAccount(formData);
      setShowCreateForm(false);
      setFormData({ account_type: 'savings', initial_balance: 0 });
      fetchAccounts();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create account');
    }
  };

  const handleDelete = async (accountNumber, balance) => {
    if (balance > 0) {
      setError('Cannot delete account with positive balance. Please transfer funds first.');
      return;
    }

    if (!confirm(`Are you sure you want to delete account ${accountNumber}? This action cannot be undone.`)) {
      return;
    }

    try {
      await accountsAPI.deleteAccount(accountNumber);
      fetchAccounts();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete account');
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="px-4 py-6 sm:px-0">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Your Accounts</h1>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="btn-primary flex items-center"
          >
            <Plus className="w-5 h-5 mr-2" />
            New Account
          </button>
        </div>

        {error && !showCreateForm && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {showCreateForm && (
          <div className="card mb-8">
            <h2 className="text-xl font-semibold mb-4">Create New Account</h2>
            {error && (
              <div className="bg-red-50 text-red-800 p-3 rounded-md mb-4">{error}</div>
            )}
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Account Type</label>
                <select
                  className="input-field mt-1"
                  value={formData.account_type}
                  onChange={(e) => setFormData({ ...formData, account_type: e.target.value })}
                >
                  <option value="savings">Savings</option>
                  <option value="checking">Checking</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Initial Balance ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  className="input-field mt-1"
                  value={formData.initial_balance}
                  onChange={(e) =>
                    setFormData({ ...formData, initial_balance: parseFloat(e.target.value) })
                  }
                />
              </div>
              <div className="flex gap-3">
                <button type="submit" className="btn-primary">
                  Create Account
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {accounts.map((account) => (
            <div key={account.id} className="card hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <CreditCard className="h-8 w-8 text-primary-600" />
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  account.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {account.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="space-y-2">
                <p className="text-sm text-gray-500">Account Number</p>
                <p className="text-lg font-mono font-semibold">{account.account_number}</p>
                <p className="text-sm text-gray-500 capitalize mt-4">{account.account_type} Account</p>
                <p className="text-3xl font-bold text-gray-900">
                  ${parseFloat(account.balance).toFixed(2)}
                </p>
                <p className="text-sm text-gray-500">{account.currency}</p>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-200">
                <button
                  onClick={() => handleDelete(account.account_number, parseFloat(account.balance))}
                  className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-md transition-colors"
                  disabled={!account.is_active}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete Account
                </button>
              </div>
            </div>
          ))}
        </div>

        {accounts.length === 0 && (
          <div className="text-center py-12">
            <CreditCard className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No accounts</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating a new account.</p>
          </div>
        )}
      </div>
    </div>
  );
}
