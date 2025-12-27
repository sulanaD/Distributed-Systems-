import { useState, useEffect } from 'react';
import { accountsAPI, transfersAPI } from '../api';
import { Send, AlertCircle, CheckCircle } from 'lucide-react';

export default function Transfer() {
  const [accounts, setAccounts] = useState([]);
  const [formData, setFormData] = useState({
    from_account_number: '',
    to_account_number: '',
    amount: '',
    description: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [fee, setFee] = useState(0);
  const [transferFullAmount, setTransferFullAmount] = useState(false);

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      const response = await accountsAPI.getAccounts();
      setAccounts(response.data);
    } catch (error) {
      console.error('Error fetching accounts:', error);
    }
  };

  const calculateFee = (amount) => {
    const amt = parseFloat(amount);
    if (isNaN(amt) || amt <= 0) return 0;

    if (amt <= 2000) return 0;
    if (amt <= 10000) return Math.min(amt * 0.0025, 20);
    if (amt <= 20000) return Math.min(amt * 0.002, 25);
    if (amt <= 50000) return Math.min(amt * 0.00125, 40);
    if (amt <= 100000) return Math.min(amt * 0.0008, 50);
    return Math.min(amt * 0.0005, 100);
  };

  useEffect(() => {
    if (transferFullAmount && formData.from_account_number) {
      const fromAccount = accounts.find(acc => acc.account_number === formData.from_account_number);
      if (fromAccount) {
        const balance = parseFloat(fromAccount.balance);
        // Calculate max amount after fee (iterative approximation)
        let maxAmount = balance;
        for (let i = 0; i < 5; i++) {
          const testFee = calculateFee(maxAmount);
          maxAmount = balance - testFee;
          if (maxAmount <= 0) {
            maxAmount = 0;
            break;
          }
        }
        setFormData({ ...formData, amount: maxAmount.toFixed(2) });
      }
    }
  }, [transferFullAmount, formData.from_account_number, accounts]);

  useEffect(() => {
    if (formData.amount) {
      setFee(calculateFee(formData.amount));
    }
  }, [formData.amount]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    if (formData.from_account_number === formData.to_account_number) {
      setError('Cannot transfer to the same account');
      setLoading(false);
      return;
    }

    try {
      const response = await transfersAPI.createTransfer({
        ...formData,
        amount: parseFloat(formData.amount),
      });
      setSuccess(`Transfer successful! Transaction ID: ${response.data.transaction_id}`);
      setFormData({
        from_account_number: '',
        to_account_number: '',
        amount: '',
        description: '',
      });
      fetchAccounts(); // Refresh balances
    } catch (err) {
      setError(err.response?.data?.detail || 'Transfer failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="px-4 py-6 sm:px-0">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Transfer Funds</h1>

        <div className="card">
          {error && (
            <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <p className="ml-3 text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}

          {success && (
            <div className="bg-green-50 border-l-4 border-green-400 p-4 mb-4">
              <div className="flex">
                <CheckCircle className="h-5 w-5 text-green-400" />
                <p className="ml-3 text-sm text-green-700">{success}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">From Account</label>
              <select
                className="input-field mt-1"
                value={formData.from_account_number}
                onChange={(e) =>
                  setFormData({ ...formData, from_account_number: e.target.value })
                }
                required
              >
                <option value="">Select account</option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.account_number}>
                    {account.account_number} - ${parseFloat(account.balance).toFixed(2)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">To Account Number</label>
              <input
                type="text"
                className="input-field mt-1"
                placeholder="Enter account number"
                value={formData.to_account_number}
                onChange={(e) => setFormData({ ...formData, to_account_number: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Amount ($)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                max="1000000"
                className="input-field mt-1"
                placeholder="0.00"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                disabled={transferFullAmount}
                required
              />
              <div className="mt-2 flex items-center">
                <input
                  type="checkbox"
                  id="fullAmount"
                  checked={transferFullAmount}
                  onChange={(e) => setTransferFullAmount(e.target.checked)}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="fullAmount" className="ml-2 block text-sm text-gray-700">
                  Transfer full available balance
                </label>
              </div>
              {fee > 0 && (
                <p className="mt-2 text-sm text-gray-500">
                  Transfer fee: ${fee.toFixed(2)} • Total: ${(parseFloat(formData.amount || 0) + fee).toFixed(2)}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Description (Optional)</label>
              <textarea
                className="input-field mt-1"
                rows="3"
                placeholder="What's this transfer for?"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
              <p className="text-sm text-blue-700">
                <strong>Fee Structure:</strong> $0-$2K (0%), $2K-$10K (0.25%, max $20), 
                $10K-$20K (0.20%, max $25), $20K-$50K (0.125%, max $40), 
                $50K-$100K (0.08%, max $50), $100K+ (0.05%, max $100)
              </p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center disabled:opacity-50"
            >
              <Send className="w-5 h-5 mr-2" />
              {loading ? 'Processing...' : 'Transfer Funds'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
