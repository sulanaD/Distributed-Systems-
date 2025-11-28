// API Configuration
const API_URL = '/api';

// State
let token = localStorage.getItem('token');
let currentUser = null;

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});

function checkAuth() {
    if (token) {
        // Verify token is still valid
        fetchCurrentUser();
    } else {
        showAuthSection();
    }
}

// ==================== AUTH FUNCTIONS ====================

async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            token = data.access_token;
            localStorage.setItem('token', token);
            currentUser = data.user;
            showMessage('Login successful!', 'success');
            showCalculatorSection();
        } else {
            showMessage(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        showMessage('Connection error. Is the server running?', 'error');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    const firstName = document.getElementById('reg-first-name').value;
    const lastName = document.getElementById('reg-last-name').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    
    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                first_name: firstName,
                last_name: lastName,
                email,
                password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            token = data.access_token;
            localStorage.setItem('token', token);
            currentUser = data.user;
            showMessage('Account created successfully!', 'success');
            showCalculatorSection();
        } else {
            showMessage(data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        showMessage('Connection error. Is the server running?', 'error');
    }
}

async function fetchCurrentUser() {
    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            showCalculatorSection();
        } else {
            // Token invalid, logout
            logout();
        }
    } catch (error) {
        showAuthSection();
    }
}

function logout() {
    token = null;
    currentUser = null;
    localStorage.removeItem('token');
    showAuthSection();
    showMessage('Logged out successfully', 'success');
}

// ==================== TAX CALCULATION ====================

async function handleCalculate(event) {
    event.preventDefault();
    
    const grossIncome = parseFloat(document.getElementById('gross-income').value);
    const deductions = parseFloat(document.getElementById('deductions').value) || 0;
    
    try {
        const response = await fetch(`${API_URL}/tax/calculate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                gross_income: grossIncome,
                deductions: deductions
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayResults(data);
            loadHistory();
        } else {
            showMessage(data.error || 'Calculation failed', 'error');
        }
    } catch (error) {
        showMessage('Connection error. Is the server running?', 'error');
    }
}

function displayResults(data) {
    document.getElementById('results').classList.remove('hidden');
    
    document.getElementById('result-gross').textContent = formatCurrency(data.gross_income);
    document.getElementById('result-deductions').textContent = formatCurrency(data.deductions);
    document.getElementById('result-taxable').textContent = formatCurrency(data.taxable_income);
    document.getElementById('result-income-tax').textContent = formatCurrency(data.income_tax);
    document.getElementById('result-medicare').textContent = formatCurrency(data.medicare_levy);
    document.getElementById('result-total-tax').textContent = formatCurrency(data.total_tax);
    document.getElementById('result-net').textContent = formatCurrency(data.net_income);
    document.getElementById('result-rate').textContent = `${data.effective_tax_rate}%`;
}

async function loadHistory() {
    console.log('loadHistory called, token:', token ? 'exists' : 'null');
    
    if (!token) {
        console.error('No token available for history fetch');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/tax/history?limit=5`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        console.log('History response status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('History data:', data);
            displayHistory(data.calculations);
        } else {
            const errorData = await response.json();
            console.error('History fetch failed:', response.status, errorData);
        }
    } catch (error) {
        console.error('Failed to load history:', error);
        showMessage('Failed to load history', 'error');
    }
}

function displayHistory(calculations) {
    const historyList = document.getElementById('history-list');
    console.log('displayHistory called with', calculations?.length, 'items');
    
    if (!calculations || calculations.length === 0) {
        historyList.innerHTML = '<p class="empty-state">No calculations yet</p>';
        return;
    }
    
    // Show most recent 5 (API returns sorted by date DESC, so newest first)
    historyList.innerHTML = calculations.slice(0, 5).map((calc, index) => `
        <div class="history-item ${index === 0 ? 'latest' : ''}">
            <div>
                <span class="date">${formatDate(calc.calculated_at)}</span>
            </div>
            <div>
                <span class="income">Income: ${formatCurrency(calc.gross_income)}</span>
            </div>
            <div>
                <span class="tax">Tax: ${formatCurrency(calc.total_tax)}</span>
            </div>
        </div>
    `).join('');
}

// ==================== UI HELPERS ====================

function showAuthSection() {
    document.getElementById('auth-section').classList.remove('hidden');
    document.getElementById('calculator-section').classList.add('hidden');
    document.getElementById('user-info').classList.add('hidden');
}

function showCalculatorSection() {
    document.getElementById('auth-section').classList.add('hidden');
    document.getElementById('calculator-section').classList.remove('hidden');
    document.getElementById('user-info').classList.remove('hidden');
    
    if (currentUser) {
        document.getElementById('user-name').textContent = `Welcome, ${currentUser.first_name}!`;
    }
    
    loadHistory();
}

function showLogin() {
    document.getElementById('login-form').classList.remove('hidden');
    document.getElementById('register-form').classList.add('hidden');
}

function showRegister() {
    document.getElementById('login-form').classList.add('hidden');
    document.getElementById('register-form').classList.remove('hidden');
}

function showMessage(text, type) {
    const messageEl = document.getElementById('message');
    messageEl.textContent = text;
    messageEl.className = `message ${type}`;
    messageEl.classList.remove('hidden');
    
    setTimeout(() => {
        messageEl.classList.add('hidden');
    }, 3000);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-AU', {
        style: 'currency',
        currency: 'AUD'
    }).format(amount);
}

function formatDate(dateString) {
    // Handle ISO format from backend (UTC) - append Z if not present
    const isoString = dateString.endsWith('Z') ? dateString : dateString + 'Z';
    const date = new Date(isoString);
    return date.toLocaleDateString('en-AU', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}
