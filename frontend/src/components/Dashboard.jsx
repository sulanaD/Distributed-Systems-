import { useState, useEffect } from 'react';
import { accountsAPI, transfersAPI } from '../api';
import { CreditCard, TrendingUp, TrendingDown, DollarSign } from 'lucide-react';

export default function Dashboard({ user }) {
  const [accounts, setAccounts] = useState([]);
  const [recentTransfers, setRecentTransfers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalBalance, setTotalBalance] = useState(0);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [accountsRes, transfersRes] = await Promise.all([
        accountsAPI.getAccounts(),
        transfersAPI.getHistory(10),
      ]);
      
      setAccounts(accountsRes.data);
      setRecentTransfers(transfersRes.data);
      
      const total = accountsRes.data.reduce((sum, acc) => sum + parseFloat(acc.balance), 0);
      setTotalBalance(total);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="px-4 py-6 sm:px-0">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Welcome back, {user?.first_name}!
        </h1>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 mb-8">
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <DollarSign className="h-8 w-8 text-primary-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Balance</dt>
                  <dd className="text-2xl font-semibold text-gray-900">
                    ${totalBalance.toFixed(2)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CreditCard className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Active Accounts</dt>
                  <dd className="text-2xl font-semibold text-gray-900">{accounts.length}</dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Transactions</dt>
                  <dd className="text-2xl font-semibold text-gray-900">
                    {recentTransfers.length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Accounts List */}
        <div className="card mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Accounts</h2>
          {accounts.length === 0 ? (
            <p className="text-gray-500">No accounts found. Create one to get started!</p>
          ) : (
            <div className="space-y-4">
              {accounts.map((account) => (
                <div
                  key={account.id}
                  className="flex justify-between items-center p-4 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">{account.account_number}</p>
                    <p className="text-sm text-gray-500 capitalize">{account.account_type}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold text-gray-900">
                      ${parseFloat(account.balance).toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-500">{account.currency}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Transactions */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Transactions</h2>
          {recentTransfers.length === 0 ? (
            <p className="text-gray-500">No transactions yet</p>
          ) : (
            <div className="space-y-3">
              {recentTransfers.slice(0, 5).map((transfer) => (
                <div
                  key={transfer.id || transfer.transaction_id}
                  className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center">
                    <TrendingDown className="h-5 w-5 text-red-500 mr-3" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        To {transfer.to_account_number}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(transfer.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-900">
                      -${parseFloat(transfer.total_amount || transfer.amount).toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">Fee: ${parseFloat(transfer.fee || 0).toFixed(2)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
