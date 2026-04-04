import { useMemo } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AppProvider, useApp } from './contexts/AppContext';

// Components
import { HomeDashboard } from './components/HomeDashboard';
import { SendMoney } from './components/SendMoney';
import { RequestPayment } from './components/RequestPayment';
import { TransactionHistory } from './components/TransactionHistory';
import { PaymentSuccess } from './components/PaymentSuccess';

// Re-export types for backward compatibility
export type { Screen } from './types/navigation';
export type { Account } from './types/account';
export type { Transaction } from './types/transaction';

function AppContent() {
  const {
    accounts,
    transactions,
    currentScreen,
    screenData,
    navigate,
    goBack,
    handlePaymentSuccess,
  } = useApp();

  // Memoized screen renderer
  const renderScreen = useMemo(() => {
    switch (currentScreen) {
      case 'home':
        return (
          <HomeDashboard accounts={accounts} transactions={transactions} onNavigate={navigate} />
        );
      case 'send':
        return <SendMoney accounts={accounts} onBack={goBack} onSuccess={handlePaymentSuccess} />;
      case 'request':
        return <RequestPayment onBack={goBack} onSuccess={handlePaymentSuccess} />;
      case 'history':
        return <TransactionHistory transactions={transactions} onBack={goBack} />;
      case 'payment-success':
        return <PaymentSuccess data={screenData.paymentData || {}} onBack={goBack} />;
      default:
        return (
          <HomeDashboard accounts={accounts} transactions={transactions} onNavigate={navigate} />
        );
    }
  }, [currentScreen, screenData, accounts, transactions, navigate, goBack, handlePaymentSuccess]);

  return (
    <div className='min-h-screen bg-background max-w-md mx-auto'>
      <div key={currentScreen} className='animate-slide-in'>
        {renderScreen}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppProvider>
        <AppContent />
      </AppProvider>
    </ErrorBoundary>
  );
}
