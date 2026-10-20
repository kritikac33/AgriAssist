import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { buyerAPI, type BuyerDashboardData } from '../api/buyer';
import { marketplaceAPI, type Listing } from '../api/marketplace';
import farmAPI from '../api/farm';
import cropAPI from '../api/crop';
import diseaseAPI from '../api/disease';
import soilAPI from '../api/soil';
import irrigationAPI from '../api/irrigation';
import yieldAPI from '../api/yield';
import { alertsAPI } from '../api/alerts';
import type { CropResponse, FarmResponse } from '../types';
import { formatError } from '../utils/errorFormatter';
import './Dashboard.css';

type Activity = { title: string; detail: string; date: string; path: string; type: string };
const modules = [
  { title: 'Farms & Crops', description: 'Manage fields, plantings and farm details.', path: '/farms-and-crops', icon: '01' },
  { title: 'Disease Scan', description: 'Upload a crop image for diagnosis.', path: '/disease-scan', icon: '02' },
  { title: 'Soil Health', description: 'Review soil records and nutrient guidance.', path: '/soil-health', icon: '03' },
  { title: 'Irrigation', description: 'Plan water needs with field conditions.', path: '/irrigation', icon: '04' },
  { title: 'Yield Prediction', description: 'Estimate harvest from recorded inputs.', path: '/yield-prediction', icon: '05' },
  { title: 'Alerts', description: 'Review active regional advisories.', path: '/alerts', icon: '06' },
  { title: 'Marketplace', description: 'List produce or browse available crops.', path: '/marketplace', icon: '07' },
  { title: 'Finance Tracker', description: 'Track recorded farm income and expenses.', path: '/finance', icon: '08' },
  { title: 'Government Schemes', description: 'Explore scheme information and eligibility.', path: '/schemes', icon: '09' },
];

function daysUntil(dateText: string, now: Date) {
  const target = new Date(dateText);
  return Math.ceil((new Date(target.getFullYear(), target.getMonth(), target.getDate()).getTime() - new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()) / 86400000);
}
function fmtDate(date?: string | null) { return date ? new Date(date).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) : 'Date unavailable'; }

export default function Dashboard() {
  const { role, user } = useAuth(); const navigate = useNavigate();
  const [today] = useState(() => new Date());
  const [buyerData, setBuyerData] = useState<BuyerDashboardData | null>(null);
  const [recentListings, setRecentListings] = useState<Listing[]>([]);
  const [recentOrders, setRecentOrders] = useState<any[]>([]); const [recentConversations, setRecentConversations] = useState<any[]>([]); const [recentNotifications, setRecentNotifications] = useState<any[]>([]);
  const [farms, setFarms] = useState<FarmResponse[]>([]); const [crops, setCrops] = useState<CropResponse[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]); const [alertCount, setAlertCount] = useState<number | null>(null);
  const [buyerError, setBuyerError] = useState(''); const [farmerError, setFarmerError] = useState(''); const [search, setSearch] = useState('');

  useEffect(() => {
    if (role === 'buyer') Promise.all([buyerAPI.dashboard(), marketplaceAPI.getListings({ sort_by: 'newest', limit: 6 }), buyerAPI.orders().catch(() => []), buyerAPI.conversations().catch(() => []), buyerAPI.notifications().catch(() => [])])
      .then(([summary, listings, orders, conversations, notifications]) => { setBuyerData(summary); setRecentListings(listings); setRecentOrders(orders.slice(0, 4)); setRecentConversations(conversations.slice(0, 4)); setRecentNotifications(notifications.filter((n) => !n.is_read).slice(0, 3)); })
      .catch((error) => setBuyerError(formatError(error) || 'Could not load buyer dashboard data'));
    if (role === 'farmer') {
      let mounted = true;
      const load = async () => {
        try {
          const farmResponse = await farmAPI.getFarms(); const farmRows = farmResponse.data;
          const cropResponse = await cropAPI.getCrops(); const cropRows = cropResponse.data;
          if (!mounted) return; setFarms(farmRows); setCrops(cropRows);
          const requests = await Promise.allSettled([
            diseaseAPI.getDiagnoses(), soilAPI.getSoilRecords(), irrigationAPI.getSchedules(),
            yieldAPI.getPredictions(), alertsAPI.getAlerts(),
          ]);
          if (!mounted) return;
          const [diagnoses, soil, schedules, predictions, alerts] = requests.map((result) => result.status === 'fulfilled' ? ('data' in result.value ? result.value.data : result.value) : []);
          const events: Activity[] = [
            ...farmRows.map((row) => ({ title: 'Farm added', detail: row.name, date: row.created_at, path: '/farms-and-crops', type: 'farm' })),
            ...cropRows.map((row) => ({ title: 'Crop recorded', detail: `${row.name}${row.variety ? ` · ${row.variety}` : ''}`, date: row.created_at, path: '/farms-and-crops', type: 'crop' })),
            ...diagnoses.map((row: any) => ({ title: 'Disease scan recorded', detail: row.disease_name || 'Diagnosis result available', date: row.diagnosed_at || row.created_at, path: '/disease-history', type: 'diagnosis' })),
            ...soil.map((row: any) => ({ title: 'Soil test recorded', detail: `Farm #${row.farm_id}`, date: row.test_date || row.created_at, path: '/soil-health', type: 'soil' })),
            ...schedules.map((row: any) => ({ title: 'Irrigation schedule created', detail: row.notes || row.status, date: row.created_at, path: '/irrigation', type: 'water' })),
            ...predictions.map((row: any) => ({ title: 'Yield estimate generated', detail: `Prediction v${row.version}`, date: row.created_at, path: '/yield-prediction', type: 'yield' })),
            ...alerts.filter((row: any) => row.is_active).map((row: any) => ({ title: 'Active regional alert', detail: `${row.disease_name} · ${row.region_description}`, date: row.created_at, path: '/alerts', type: 'alert' })),
          ].filter((event) => event.date && !Number.isNaN(new Date(event.date).getTime())).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).slice(0, 7);
          setActivities(events); setAlertCount(alerts.filter((row: any) => row.is_active).length);
        } catch (error) { if (mounted) setFarmerError(formatError(error) || 'Could not load farm records'); }
      };
      void load(); return () => { mounted = false; };
    }
  }, [role]);

  const harvests = useMemo(() => crops.filter((crop) => crop.expected_harvest_date && crop.status?.toLowerCase() !== 'harvested')
    .map((crop) => {
      const farm = farms.find((row) => row.id === crop.farm_id); const days = daysUntil(crop.expected_harvest_date!, today);
      const start = crop.planting_date ? new Date(crop.planting_date).getTime() : 0;
      const end = new Date(crop.expected_harvest_date!).getTime(); const duration = start > 0 ? Math.max(1, end - start) : 0;
      const elapsed = start > 0 ? today.getTime() - start : 0; const progress = duration ? Math.max(0, Math.min(100, Math.round(elapsed / duration * 100))) : null;
      return { ...crop, farmName: farm?.name || `Farm #${crop.farm_id}`, days, progress };
    }).filter((crop) => crop.days >= -30).sort((a, b) => a.days - b.days).slice(0, 4), [crops, farms, today]);

  if (role === 'buyer') {
    const stats = [
      ['Active orders', buyerData?.active_orders ?? '—'], ['Awaiting payment', buyerData?.awaiting_payment ?? '—'],
      ['In fulfilment', buyerData?.in_fulfillment ?? '—'], ['Delivered', buyerData?.delivered_orders ?? '—'],
      ['Paid purchases', `₹${Number(buyerData?.paid_purchase_value || 0).toLocaleString('en-IN')}`], ['Unread messages', buyerData?.unread_message_count ?? '—'],
    ];
    return <div className="buyer-dashboard space-y-7">
      <section className="dashboard-hero"><div className="hero-copy"><div className="eyebrow">Your marketplace</div><h1>Welcome, {user?.full_name || 'Buyer'}</h1><p>Source fresh produce directly from farmers and keep your orders, conversations and saved crops together.</p><form className="hero-search" onSubmit={(e) => { e.preventDefault(); navigate(`/marketplace?crop=${encodeURIComponent(search.trim())}`); }}><label htmlFor="buyer-search" className="sr-only">Search crops or locations</label><input id="buyer-search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search crops or locations"/><button>Search produce</button></form></div><div className="hero-note"><span className="note-leaf" aria-hidden="true">✳</span><span><b>Closer to the source</b><small>Browse current farmer listings</small></span></div></section>
      {buyerError && <p role="alert" className="notice-error">{buyerError}</p>}
      <section><div className="section-title"><div><div className="eyebrow">Account overview</div><h2>Your buying activity</h2></div></div><div className="stat-grid buyer-stat-grid">{stats.map(([label, value]) => <article className="stat-tile" key={label}><span>{label}</span><strong>{value}</strong></article>)}</div></section>
      <section><div className="section-title"><div><div className="eyebrow">Shortcuts</div><h2>Quick access</h2></div></div><div className="quick-links">{[['Cart','/cart'],['My Orders','/orders'],['Messages','/messages'],['Saved Listings','/saved-listings'],['Addresses','/addresses'],['Notifications','/notifications']].map(([label,path])=><Link key={path} to={path}>{label}<span aria-hidden="true">↗</span></Link>)}</div></section>
      <section><div className="section-title"><div><div className="eyebrow">From the marketplace</div><h2>Recently added produce</h2></div><Link to="/marketplace" className="text-link">Browse all listings</Link></div>{recentListings.length ? <div className="listing-grid">{recentListings.map((listing) => <article key={listing.id} className="listing-tile"><div className="listing-kicker">Available produce</div><h3>{listing.crop_name}</h3><p>{listing.seller_name || 'Farmer'} · {listing.location || 'Location not provided'}</p><div className="listing-price">₹{Number(listing.price_per_quintal).toLocaleString('en-IN')} <small>/ quintal</small></div><div className="listing-footer"><span>{listing.quantity_quintals} quintals available</span><Link to="/marketplace">View listing</Link></div></article>)}</div> : <div className="empty-panel">No available listings yet.</div>}</section>
      <div className="dashboard-columns"><section className="dashboard-panel"><div className="section-title"><div><div className="eyebrow">Purchases</div><h2>Recent orders</h2></div><Link to="/orders" className="text-link">View all</Link></div>{recentOrders.length ? <div className="buyer-recent-list">{recentOrders.map((order)=><Link key={order.id} to="/orders" className="buyer-recent-row"><span><b>{order.crop_name}</b><small>{order.order_number} · {new Date(order.created_at).toLocaleDateString()}</small></span><span className="buyer-row-meta">₹{Number(order.total_amount).toLocaleString('en-IN')}<small>{order.status.replaceAll('_',' ')}</small></span></Link>)}</div> : <div className="empty-panel">Your orders will appear here after checkout.</div>}</section><section className="dashboard-panel"><div className="section-title"><div><div className="eyebrow">Messages</div><h2>Farmer conversations</h2></div><Link to="/messages" className="text-link">Open messages</Link></div>{recentConversations.length ? <div className="buyer-recent-list">{recentConversations.map((thread)=><Link key={thread.listing_id} to="/messages" className="buyer-recent-row"><span><b>{thread.seller_name} · {thread.crop_name}</b><small>{thread.last_message}</small></span><span className="buyer-row-meta">{thread.unread_count > 0 ? `${thread.unread_count} new` : 'Open'}<small>{new Date(thread.last_message_at).toLocaleDateString()}</small></span></Link>)}</div> : <div className="empty-panel">No farmer conversations yet.</div>}</section></div>
      <section className="dashboard-panel"><div className="section-title"><div><div className="eyebrow">Account updates</div><h2>Unread notifications</h2></div><Link to="/notifications" className="text-link">View all</Link></div>{recentNotifications.length ? <div className="buyer-notice-list">{recentNotifications.map((notification)=><article key={notification.id}><b>{notification.subject}</b><p>{notification.content}</p></article>)}</div> : <p className="subtle-note">You’re all caught up. New order and marketplace updates will show here.</p>}</section>
    </div>;
  }

  if (role === 'farmer') {
    const activeCrops = crops.filter((crop) => crop.status?.toLowerCase() === 'active').length;
    const stats = [['Farms', farms.length, '/farms-and-crops'], ['Active crops', activeCrops, '/farms-and-crops'], ['Upcoming harvests', harvests.length, '/farms-and-crops'], ['Active alerts', alertCount ?? '—', '/alerts']];
    return <div className="farmer-dashboard space-y-7">
      <section className="dashboard-hero"><div className="hero-copy"><div className="eyebrow">Farm management workspace</div><h1>Good to see you, {user?.full_name?.split(' ')[0] || 'Farmer'}</h1><p>Keep your farm records, crop plans and field decisions in one clear view.</p><div className="hero-actions"><Link to="/farms-and-crops" className="hero-primary">View my farms</Link><Link to="/disease-scan" className="hero-secondary">Start a disease scan</Link></div></div><div className="hero-note"><span className="note-leaf" aria-hidden="true">✳</span><span><b>Plan from your records</b><small>Advisories reflect submitted field inputs</small></span></div></section>
      {farmerError && <p role="alert" className="notice-error">{farmerError}</p>}
      <section className="stat-grid">{stats.map(([label,value,path])=><Link className="stat-tile" to={String(path)} key={String(label)}><span>{label}</span><strong>{value}</strong><small>Open details <span aria-hidden="true">↗</span></small></Link>)}</section>
      <section><div className="section-title"><div><div className="eyebrow">Your workspace</div><h2>Farm tools</h2></div></div><div className="module-grid">{modules.map((module)=><Link key={module.path} to={module.path} className="module-tile"><span className="module-index">{module.icon}</span><span className="module-copy"><b>{module.title}</b><small>{module.description}</small></span><span className="module-arrow" aria-hidden="true">↗</span></Link>)}</div></section>
      <div className="dashboard-columns">
        <section className="dashboard-panel"><div className="section-title"><div><div className="eyebrow">Field log</div><h2>Recent activity</h2></div><Link to="/farms-and-crops" className="text-link">Open farm records</Link></div>{activities.length ? <ol className="activity-list">{activities.map((event,index)=><li key={`${event.type}-${event.date}-${index}`}><span className="activity-mark" aria-hidden="true">{event.type === 'alert' ? '!' : '•'}</span><span className="activity-copy"><Link to={event.path}>{event.title}</Link><small>{event.detail}</small><time dateTime={event.date}>{fmtDate(event.date)}</time></span></li>)}</ol> : <div className="empty-panel">No farm activity has been recorded yet. Your farm events will appear here as you use AgriAssist.</div>}</section>
        <section className="dashboard-panel"><div className="section-title"><div><div className="eyebrow">Crop calendar</div><h2>Harvest planner</h2></div><Link to="/farms-and-crops" className="text-link">Manage crops</Link></div>{harvests.length ? <div className="harvest-list">{harvests.map((crop)=><article className="harvest-item" key={crop.id}><div className="harvest-top"><span><b>{crop.name}{crop.variety ? ` · ${crop.variety}` : ''}</b><small>{crop.farmName}</small></span><span className={`harvest-days ${crop.days < 0 ? 'past' : ''}`}>{crop.days < 0 ? `${Math.abs(crop.days)}d past` : crop.days === 0 ? 'Today' : `${crop.days}d left`}</span></div><div className="harvest-track"><span style={{ width: `${crop.progress ?? 0}%` }}/></div><div className="harvest-dates"><span>Planted {fmtDate(crop.planting_date)}</span><span>Expected {fmtDate(crop.expected_harvest_date)}</span></div>{crop.progress === null && <small className="subtle-note">Planting date not recorded; progress is unavailable.</small>}</article>)}</div> : <div className="empty-panel">No upcoming harvest dates are recorded. Add planting and expected harvest dates to your crops to use this planner.</div>}</section>
      </div>
    </div>;
  }

  const roleTitle = role === 'officer' ? 'Extension workspace' : role === 'admin' ? 'Administration workspace' : 'AgriAssist';
  const quickLinks = role === 'officer' ? [{ title: 'Alerts', description: 'Review and manage regional advisories.', path: '/alerts' }] : role === 'admin' ? [{ title: 'Admin Panel', description: 'Manage system users and configuration.', path: '/admin' }] : [];
  return <div className="farmer-dashboard space-y-7"><section className="dashboard-hero"><div className="hero-copy"><div className="eyebrow">AgriAssist</div><h1>{roleTitle}</h1><p>Welcome, {user?.full_name}. Continue to your available tools.</p></div></section><div className="module-grid">{quickLinks.map((item)=><Link key={item.path} to={item.path} className="module-tile"><span className="module-copy"><b>{item.title}</b><small>{item.description}</small></span><span className="module-arrow">↗</span></Link>)}</div></div>;
}
