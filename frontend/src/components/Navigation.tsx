import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export function Navigation() {
  const { user, role, logout } = useAuth();
  const location = useLocation();

  if (!user) {
    return null;
  }

  const navLinks = {
    farmer: [
      { path: '/dashboard', label: 'Dashboard', icon: '🏠' },
      { path: '/farms-and-crops', label: 'Farms & Crops', icon: '🌾' },
      { path: '/disease-scan', label: 'Disease', icon: '🔬' },
      { path: '/soil-health', label: 'Soil', icon: '🌱' },
      { path: '/irrigation', label: 'Irrigation', icon: '💧' },
      { path: '/yield-prediction', label: 'Yield', icon: '📊' },
      { path: '/alerts', label: 'Alerts', icon: '🚨' },
      { path: '/marketplace', label: 'Market', icon: '🛒' },
      { path: '/finance', label: 'Finance', icon: '💰' },
      { path: '/schemes', label: 'Schemes', icon: '🏛️' },
    ],
    buyer: [
      { path: '/dashboard', label: 'Dashboard', icon: '🏠' },
      { path: '/marketplace', label: 'Marketplace', icon: '🛒' },
    ],
    officer: [
      { path: '/dashboard', label: 'Dashboard', icon: '🏠' },
      { path: '/alerts', label: 'Alerts', icon: '🚨' },
    ],
    admin: [
      { path: '/dashboard', label: 'Dashboard', icon: '🏠' },
      { path: '/admin', label: 'Admin Panel', icon: '⚙️' },
    ],
  };

  const currentLinks = role ? navLinks[role] || [] : [];

  return (
    <nav className="bg-[#166534] text-white shadow-lg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          <div className="flex items-center flex-1">
            <Link to="/dashboard" className="flex-shrink-0 mr-6">
              <h1 className="text-lg font-bold text-white">AgriAssist</h1>
            </Link>
            <div className="hidden md:flex items-center flex-1 overflow-x-auto no-scrollbar">
              <div className="flex items-center gap-1 whitespace-nowrap">
                {currentLinks.map((link: { path: string; label: string; icon: string }) => (
                  <Link
                    key={link.path}
                    to={link.path}
                    className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      location.pathname === link.path
                        ? 'bg-[#22a55a] text-white'
                        : 'text-green-100 hover:bg-[#22a55a]'
                    }`}
                  >
                    <span className="mr-1">{link.icon}</span>
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-3 flex-shrink-0">
            <span className="text-xs text-green-100 truncate max-w-[120px]">
              {user.full_name}
            </span>
            <span className="text-xs bg-[#22a55a] px-2 py-0.5 rounded-full font-medium">
              {role}
            </span>
            <button
              onClick={logout}
              className="bg-[#22a55a] hover:bg-[#1a8a4a] text-white px-3 py-1.5 rounded-md text-xs font-medium transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <div className="md:hidden border-t border-[#22a55a]">
        <div className="px-2 pt-2 pb-3 space-y-1">
          {currentLinks.map((link: { path: string; label: string; icon: string }) => (
            <Link
              key={link.path}
              to={link.path}
              className={`block px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                location.pathname === link.path
                  ? 'bg-[#22a55a] text-white'
                  : 'text-green-100 hover:bg-[#22a55a]'
              }`}
            >
              <span className="mr-1">{link.icon}</span>
              {link.label}
            </Link>
          ))}
          <div className="border-t border-[#22a55a] pt-4 mt-4">
            <div className="px-3 py-2 text-sm text-green-100">
              {user.full_name}
            </div>
            <div className="px-3 py-2">
              <span className="text-xs bg-[#22a55a] px-2 py-1 rounded-full">
                {role}
              </span>
            </div>
            <button
              onClick={logout}
              className="w-full text-left px-3 py-2 text-sm font-medium text-green-100 hover:bg-[#22a55a] rounded-md transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
