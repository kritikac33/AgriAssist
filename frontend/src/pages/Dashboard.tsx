import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../components/Card';

export default function Dashboard() {
  const { role } = useAuth();
  const navigate = useNavigate();

  const farmerCards = [
    { title: 'My Farms & Crops', icon: '🌾', path: '/farms-and-crops', description: 'Manage your farms and crop information' },
    { title: 'Disease Scan', icon: '🔬', path: '/disease-scan', description: 'AI-powered disease detection for your crops' },
    { title: 'Soil Health', icon: '🌱', path: '/soil-health', description: 'Analyze soil quality and nutrient levels' },
    { title: 'Irrigation', icon: '💧', path: '/irrigation', description: 'Smart irrigation scheduling based on weather' },
    { title: 'Yield Prediction', icon: '📊', path: '/yield-prediction', description: 'Predict crop yields using ML models' },
    { title: 'Alerts', icon: '🚨', path: '/alerts', description: 'Pest outbreak alerts and warnings' },
    { title: 'Marketplace', icon: '🛒', path: '/marketplace', description: 'Buy and sell crops in the marketplace' },
    { title: 'Finance Tracker', icon: '💰', path: '/finance', description: 'Track income and expenses' },
    { title: 'Government Schemes', icon: '🏛️', path: '/schemes', description: 'Discover eligible government schemes' },
  ];

  const buyerCards = [
    { title: 'Marketplace', icon: '🛒', path: '/marketplace', description: 'Browse and buy crops from farmers' },
  ];

  const officerCards = [
    { title: 'Alerts', icon: '🚨', path: '/alerts', description: 'Manage pest outbreak alerts' },
  ];

  const adminCards = [
    { title: 'Admin Panel', icon: '⚙️', path: '/admin', description: 'Manage system configuration, users, and audit logs' },
  ];

  const getCards = () => {
    switch (role) {
      case 'farmer':
        return farmerCards;
      case 'buyer':
        return buyerCards;
      case 'officer':
        return officerCards;
      case 'admin':
        return adminCards;
      default:
        return [];
    }
  };

  const cards = getCards();

  return (
    <>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          {role === 'farmer' && 'Manage your farms, crops, and access agricultural advisory services'}
          {role === 'buyer' && 'Browse marketplace and manage your purchases'}
          {role === 'officer' && 'Manage alerts and provide advisory services'}
          {role === 'admin' && 'Manage system configuration and users'}
        </p>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards.map((card) => (
          <Card
            key={card.path}
            onClick={() => navigate(card.path)}
            className="p-6 hover:scale-105 transition-transform duration-200 cursor-pointer"
          >
            <div className="flex items-start space-x-4">
              <div className="text-4xl">{card.icon}</div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{card.title}</h3>
                <p className="text-gray-600 text-sm">{card.description}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </>
  );
}
