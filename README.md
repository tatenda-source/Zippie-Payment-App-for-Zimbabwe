# Zippie Payment App for Zimbabwe

A modern payment application built with React (frontend) and Node.js/Express (backend) for the Zimbabwean market.

## Features

- 💳 Multiple payment methods (EcoCash, OneMoney, Steward Bank, CBZ ZIPIT)
- 💸 Send money to other users
- 📱 Request payments from others
- 📊 Transaction history
- 🎨 Modern, responsive UI
- 🔒 Secure API endpoints

## Project Structure

```
├── App.tsx                    # Main React component
├── components/                # React components
│   ├── HomeDashboard.tsx     # Dashboard screen
│   ├── SendMoney.tsx         # Send money screen
│   ├── RequestPayment.tsx    # Request payment screen
│   ├── TransactionHistory.tsx # Transaction history screen
│   ├── PaymentSuccess.tsx    # Success screen
│   └── ui/                   # Reusable UI components
├── backend/                  # Node.js/Express backend
│   ├── server.js            # Main server file
│   └── package.json         # Backend dependencies
├── src/                     # React source files
│   ├── index.tsx           # React entry point
│   └── index.css           # Global styles
└── public/                 # Static files
    └── index.html          # HTML template
```

## Quick Start

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn

### Frontend Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm start
   ```

3. **Open your browser:**
   Navigate to `http://localhost:3000`

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create environment file:**
   ```bash
   cp env.example .env
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

5. **API will be available at:**
   `http://localhost:5000`

## API Endpoints

### Health Check
- `GET /api/health` - Check if API is running

### User Accounts
- `GET /api/users/:userId/accounts` - Get user's payment accounts

### Transactions
- `GET /api/users/:userId/transactions` - Get user's transaction history
- `POST /api/transactions/send` - Send money to another user
- `POST /api/transactions/request` - Request payment from another user
- `GET /api/transactions/:transactionId` - Get specific transaction details

## Development

### Frontend Development

The frontend is built with:
- React 18 with TypeScript
- Tailwind CSS for styling
- shadcn/ui components
- Lucide React for icons

### Backend Development

The backend is built with:
- Node.js with Express
- CORS enabled for frontend communication
- Helmet for security headers
- Morgan for request logging

## Production Deployment

### Frontend
```bash
npm run build
```

### Backend
```bash
npm start
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For support, email support@zippie.co.zw or create an issue in this repository. 