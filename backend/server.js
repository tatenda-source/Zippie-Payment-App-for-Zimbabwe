const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

// In-memory data storage (replace with database in production)
let users = [
  {
    id: '1',
    name: 'John Doe',
    email: 'john@example.com',
    phone: '+263771234567',
    accounts: [
      { id: '1', name: 'EcoCash', type: 'mobile', balance: 250.50, currency: 'USD', color: '#f59e0b' },
      { id: '2', name: 'OneMoney', type: 'mobile', balance: 1500.00, currency: 'ZWL', color: '#ef4444' },
      { id: '3', name: 'Steward Bank', type: 'bank', balance: 850.25, currency: 'USD', color: '#3b82f6' },
      { id: '4', name: 'CBZ ZIPIT', type: 'bank', balance: 2250.00, currency: 'ZWL', color: '#10b981' }
    ]
  }
];

let transactions = [
  {
    id: '1',
    userId: '1',
    type: 'received',
    amount: 50.00,
    currency: 'USD',
    recipient: 'John Doe',
    sender: 'Tendai Mukamuri',
    description: 'Lunch money',
    status: 'completed',
    date: '2025-01-08T10:30:00Z',
    paymentMethod: 'EcoCash'
  },
  {
    id: '2',
    userId: '1',
    type: 'sent',
    amount: 25.00,
    currency: 'USD',
    recipient: 'Chipo Nhongo',
    sender: 'John Doe',
    description: 'Coffee',
    status: 'completed',
    date: '2025-01-07T14:15:00Z',
    paymentMethod: 'Steward Bank'
  }
];

// Routes

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', message: 'Zippie API is running' });
});

// Get user accounts
app.get('/api/users/:userId/accounts', (req, res) => {
  const { userId } = req.params;
  const user = users.find(u => u.id === userId);
  
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }
  
  res.json(user.accounts);
});

// Get user transactions
app.get('/api/users/:userId/transactions', (req, res) => {
  const { userId } = req.params;
  const userTransactions = transactions.filter(t => t.userId === userId);
  
  res.json(userTransactions);
});

// Send money
app.post('/api/transactions/send', (req, res) => {
  const { userId, recipientPhone, amount, currency, description, paymentMethod } = req.body;
  
  if (!userId || !recipientPhone || !amount || !currency || !paymentMethod) {
    return res.status(400).json({ error: 'Missing required fields' });
  }
  
  // Validate amount
  if (amount <= 0) {
    return res.status(400).json({ error: 'Amount must be greater than 0' });
  }
  
  // Find user and their account
  const user = users.find(u => u.id === userId);
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }
  
  const account = user.accounts.find(a => a.name === paymentMethod);
  if (!account) {
    return res.status(404).json({ error: 'Payment method not found' });
  }
  
  // Check if user has sufficient balance
  if (account.balance < amount) {
    return res.status(400).json({ error: 'Insufficient balance' });
  }
  
  // Create transaction
  const transaction = {
    id: uuidv4(),
    userId,
    type: 'sent',
    amount,
    currency,
    recipient: recipientPhone,
    sender: user.name,
    description,
    status: 'completed',
    date: new Date().toISOString(),
    paymentMethod
  };
  
  // Update account balance
  account.balance -= amount;
  
  // Add transaction to list
  transactions.push(transaction);
  
  res.status(201).json({
    message: 'Payment sent successfully',
    transaction,
    newBalance: account.balance
  });
});

// Request payment
app.post('/api/transactions/request', (req, res) => {
  const { userId, recipientPhone, amount, currency, description } = req.body;
  
  if (!userId || !recipientPhone || !amount || !currency) {
    return res.status(400).json({ error: 'Missing required fields' });
  }
  
  // Validate amount
  if (amount <= 0) {
    return res.status(400).json({ error: 'Amount must be greater than 0' });
  }
  
  const user = users.find(u => u.id === userId);
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }
  
  // Create payment request
  const transaction = {
    id: uuidv4(),
    userId,
    type: 'request',
    amount,
    currency,
    recipient: recipientPhone,
    sender: user.name,
    description,
    status: 'pending',
    date: new Date().toISOString()
  };
  
  transactions.push(transaction);
  
  res.status(201).json({
    message: 'Payment request sent successfully',
    transaction
  });
});

// Get transaction by ID
app.get('/api/transactions/:transactionId', (req, res) => {
  const { transactionId } = req.params;
  const transaction = transactions.find(t => t.id === transactionId);
  
  if (!transaction) {
    return res.status(404).json({ error: 'Transaction not found' });
  }
  
  res.json(transaction);
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

app.listen(PORT, () => {
  console.log(`🚀 Zippie API server running on port ${PORT}`);
  console.log(`📱 Health check: http://localhost:${PORT}/api/health`);
}); 