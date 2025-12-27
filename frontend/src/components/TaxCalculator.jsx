import { useState, useEffect } from 'react';
import { taxAPI } from '../api';
import { Calculator, History } from 'lucide-react';

export default function TaxCalculator() {
  const [formData, setFormData] = useState({
    financial_year: '2023-2024',
    gross_income: '',
    deductions: '',
  });
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [brackets, setBrackets] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchBrackets();
    fetchHistory();
  }, []);

  const fetchBrackets = async () => {
    try {
      const response = await taxAPI.getBrackets();
      setBrackets(response.data);
    } catch (error) {
      console.error('Error fetching tax brackets:', error);
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await taxAPI.getHistory();
      setHistory(response.data);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await taxAPI.calculate({
        ...formData,
        gross_income: parseFloat(formData.gross_income),
        deductions: formData.deductions ? parseFloat(formData.deductions) : 0,
      });
      setResult(response.data);
      fetchHistory();
    } catch (err) {
      setError(err.response?.data?.detail || 'Calculation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="px-4 py-6 sm:px-0">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Australian Tax Calculator</h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Calculator Form */}
          <div className="card">
            <div className="flex items-center mb-4">
              <Calculator className="h-6 w-6 text-primary-600 mr-2" />
              <h2 className="text-xl font-semibold">Calculate Tax</h2>
            </div>

            {error && (
              <div className="bg-red-50 text-red-800 p-3 rounded-md mb-4">{error}</div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Financial Year</label>
                <select
                  className="input-field mt-1"
                  value={formData.financial_year}
                  onChange={(e) => setFormData({ ...formData, financial_year: e.target.value })}
                >
                  <option value="2023-2024">2023-2024</option>
                  <option value="2024-2025">2024-2025</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Gross Income ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  className="input-field mt-1"
                  placeholder="Enter your annual income"
                  value={formData.gross_income}
                  onChange={(e) => setFormData({ ...formData, gross_income: e.target.value })}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Deductions ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  className="input-field mt-1"
                  placeholder="Work-related expenses, etc."
                  value={formData.deductions}
                  onChange={(e) => setFormData({ ...formData, deductions: e.target.value })}
                />
              </div>

              <button type="submit" disabled={loading} className="btn-primary w-full">
                {loading ? 'Calculating...' : 'Calculate Tax'}
              </button>
            </form>

            {/* Tax Brackets Info */}
            {brackets && (
              <div className="mt-6 border-t pt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">
                  Tax Brackets ({brackets.financial_year})
                </h3>
                <div className="space-y-2">
                  {brackets.brackets.map((bracket, index) => (
                    <div key={index} className="text-xs text-gray-600 flex justify-between">
                      <span>{bracket.range}</span>
                      <span className="font-medium">{bracket.rate}</span>
                    </div>
                  ))}
                  <div className="text-xs text-gray-600 pt-2 border-t">
                    Medicare Levy: {brackets.medicare_levy}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Results */}
          <div className="space-y-6">
            {result && (
              <div className="card">
                <h2 className="text-xl font-semibold mb-4">Tax Calculation Result</h2>
                <div className="space-y-3">
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-gray-600">Gross Income</span>
                    <span className="font-semibold">${parseFloat(result.gross_income).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-gray-600">Taxable Income</span>
                    <span className="font-semibold">${parseFloat(result.taxable_income).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-gray-600">Income Tax</span>
                    <span className="font-semibold text-red-600">${parseFloat(result.tax_payable).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-gray-600">Medicare Levy</span>
                    <span className="font-semibold text-red-600">${parseFloat(result.medicare_levy).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between py-3 border-b-2 border-gray-300">
                    <span className="font-semibold text-lg">Total Tax</span>
                    <span className="font-bold text-lg text-red-600">${parseFloat(result.total_tax).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between py-3 bg-green-50 -mx-6 px-6 rounded-b-lg">
                    <span className="font-semibold text-lg">Net Income</span>
                    <span className="font-bold text-lg text-green-600">${parseFloat(result.net_income).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between py-2 text-sm">
                    <span className="text-gray-600">Effective Tax Rate</span>
                    <span className="font-semibold">{result.effective_tax_rate.toFixed(2)}%</span>
                  </div>
                </div>
              </div>
            )}

            {/* History */}
            <div className="card">
              <div className="flex items-center mb-4">
                <History className="h-6 w-6 text-primary-600 mr-2" />
                <h2 className="text-xl font-semibold">Calculation History</h2>
              </div>
              {history.length === 0 ? (
                <p className="text-gray-500 text-sm">No calculations yet</p>
              ) : (
                <div className="space-y-3">
                  {history.map((item) => (
                    <div key={item.id} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex justify-between mb-1">
                        <span className="text-sm font-medium">{item.financial_year}</span>
                        <span className="text-xs text-gray-500">
                          {new Date(item.calculated_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Income: ${parseFloat(item.gross_income).toFixed(2)}</span>
                        <span className="text-red-600">Tax: ${parseFloat(item.total_tax).toFixed(2)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
