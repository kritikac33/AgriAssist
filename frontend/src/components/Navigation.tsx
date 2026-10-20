import { useEffect, useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { buyerAPI } from '../api/buyer';
import './Navigation.css';

const navLinks = {
  farmer: [
    { path: '/dashboard', label: 'Dashboard' }, { path: '/farms-and-crops', label: 'Farms & Crops' },
    { path: '/disease-scan', label: 'Disease Scan' }, { path: '/soil-health', label: 'Soil Health' },
    { path: '/irrigation', label: 'Irrigation' }, { path: '/yield-prediction', label: 'Yield' },
    { path: '/alerts', label: 'Alerts' }, { path: '/marketplace', label: 'Marketplace' },
    { path: '/farmer-orders', label: 'Orders' }, { path: '/finance', label: 'Finance' }, { path: '/schemes', label: 'Schemes' },
  ],
  buyer: [
    { path: '/dashboard', label: 'Dashboard' }, { path: '/marketplace', label: 'Marketplace' },
    { path: '/cart', label: 'Cart' }, { path: '/orders', label: 'My Orders' },
    { path: '/messages', label: 'Messages' }, { path: '/saved-listings', label: 'Saved' },
    { path: '/addresses', label: 'Addresses' }, { path: '/notifications', label: 'Updates' },
  ],
  officer: [{ path: '/dashboard', label: 'Dashboard' }, { path: '/alerts', label: 'Alerts' }],
  admin: [{ path: '/dashboard', label: 'Dashboard' }, { path: '/admin', label: 'Admin Panel' }],
};

export function Navigation() {
  const { user, role, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [cartCount, setCartCount] = useState(0);

  useEffect(() => {
    if (role !== 'buyer') return;
    const refresh = () => buyerAPI.dashboard().then((data) => setCartCount(data.cart_item_count)).catch(() => {});
    refresh();
    window.addEventListener('buyer-cart-updated', refresh);
    return () => window.removeEventListener('buyer-cart-updated', refresh);
  }, [role]);
  if (!user) return null;
  const links = role ? navLinks[role as keyof typeof navLinks] || [] : [];

  return <header className="app-header">
    <div className="app-header-inner">
      <Link to="/dashboard" className="app-brand" aria-label="AgriAssist home">
        <span className="brand-mark" aria-hidden="true"><svg viewBox="0 0 32 32" fill="none"><path d="M25.8 6.3C15 6.3 7 10.7 7 19.2c0 3.7 2.5 6.3 6.1 6.3 8.6 0 12.7-8.1 12.7-19.2Z" fill="currentColor"/><path d="M5 27c3.7-6.7 8.4-10.4 15.6-13.4" stroke="#123d2b" strokeWidth="2" strokeLinecap="round"/></svg></span>
        <span>AgriAssist<small>Farm intelligence</small></span>
      </Link>
      <button className="mobile-nav-toggle" type="button" aria-expanded={menuOpen} aria-controls="primary-navigation" onClick={() => setMenuOpen((open) => !open)}>
        <span>{menuOpen ? 'Close' : 'Menu'}</span><span aria-hidden="true">{menuOpen ? '×' : '☰'}</span>
      </button>
      <nav id="primary-navigation" aria-label={`${role || 'Main'} navigation`} className={`app-nav ${menuOpen ? 'is-open' : ''}`}>
        {links.map((item) => <NavLink key={item.path} to={item.path} end={item.path === '/dashboard'} onClick={() => setMenuOpen(false)} className={({ isActive }) => `app-nav-link ${isActive ? 'active' : ''}`}>
          {item.label}{item.path === '/cart' && cartCount > 0 && <span className="nav-count">{cartCount}</span>}
        </NavLink>)}
        <div className="mobile-profile"><span>{user.full_name}</span><span className="role-chip">{role}</span><button type="button" onClick={logout}>Log out</button></div>
      </nav>
      <div className="header-profile"><div className="profile-avatar" aria-hidden="true">{user.full_name?.trim().charAt(0).toUpperCase() || 'A'}</div><div className="profile-text"><span>{user.full_name}</span><small>{role}</small></div><button type="button" onClick={logout} className="logout-button">Log out</button></div>
    </div>
  </header>;
}
