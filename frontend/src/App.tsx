import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import FarmsAndCrops from './pages/FarmsAndCrops';
import DiseaseScan from './pages/DiseaseScan';
import DiseaseHistory from './pages/DiseaseHistory';
import Marketplace from './pages/Marketplace';
import SoilHealth from './pages/SoilHealth';
import Irrigation from './pages/Irrigation';
import YieldPrediction from './pages/YieldPrediction';
import Finance from './pages/Finance';
import Schemes from './pages/Schemes';
import Alerts from './pages/Alerts';
import Admin from './pages/Admin';
import BuyerCart from './pages/BuyerCart';
import BuyerOrders from './pages/BuyerOrders';
import BuyerMessages from './pages/BuyerMessages';
import SavedListings from './pages/SavedListings';
import BuyerAddresses from './pages/BuyerAddresses';
import BuyerNotifications from './pages/BuyerNotifications';
import FarmerOrders from './pages/FarmerOrders';
import { ProtectedRoute } from './components/ProtectedRoute';
import { RoleRoute } from './components/RoleRoute';
import { Layout } from './components/Layout';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      {/* Authenticated routes with shared layout */}
      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        {/* Dashboard - all authenticated users */}
        <Route path="/dashboard" element={<Dashboard />} />

        {/* Farmer-only routes */}
        <Route
          path="/farms-and-crops"
          element={<RoleRoute allowedRoles={['farmer']}><FarmsAndCrops /></RoleRoute>}
        />
        <Route
          path="/disease-scan"
          element={<RoleRoute allowedRoles={['farmer']}><DiseaseScan /></RoleRoute>}
        />
        <Route
          path="/disease-history"
          element={<RoleRoute allowedRoles={['farmer']}><DiseaseHistory /></RoleRoute>}
        />
        <Route
          path="/soil-health"
          element={<RoleRoute allowedRoles={['farmer']}><SoilHealth /></RoleRoute>}
        />
        <Route
          path="/irrigation"
          element={<RoleRoute allowedRoles={['farmer']}><Irrigation /></RoleRoute>}
        />
        <Route
          path="/yield-prediction"
          element={<RoleRoute allowedRoles={['farmer']}><YieldPrediction /></RoleRoute>}
        />
        <Route
          path="/finance"
          element={<RoleRoute allowedRoles={['farmer']}><Finance /></RoleRoute>}
        />
        <Route
          path="/schemes"
          element={<RoleRoute allowedRoles={['farmer']}><Schemes /></RoleRoute>}
        />

        {/* Alerts - farmers, officers, admins */}
        <Route
          path="/alerts"
          element={<RoleRoute allowedRoles={['farmer', 'officer', 'admin']}><Alerts /></RoleRoute>}
        />

        {/* Marketplace - farmers and buyers */}
        <Route
          path="/marketplace"
          element={<RoleRoute allowedRoles={['farmer', 'buyer']}><Marketplace /></RoleRoute>}
        />
        <Route path="/cart" element={<RoleRoute allowedRoles={['buyer']}><BuyerCart /></RoleRoute>} />
        <Route path="/orders" element={<RoleRoute allowedRoles={['buyer']}><BuyerOrders /></RoleRoute>} />
        <Route path="/messages" element={<RoleRoute allowedRoles={['buyer']}><BuyerMessages /></RoleRoute>} />
        <Route path="/saved-listings" element={<RoleRoute allowedRoles={['buyer']}><SavedListings /></RoleRoute>} />
        <Route path="/addresses" element={<RoleRoute allowedRoles={['buyer']}><BuyerAddresses /></RoleRoute>} />
        <Route path="/notifications" element={<RoleRoute allowedRoles={['buyer']}><BuyerNotifications /></RoleRoute>} />
        <Route path="/farmer-orders" element={<RoleRoute allowedRoles={['farmer']}><FarmerOrders /></RoleRoute>} />

        {/* Admin-only routes */}
        <Route
          path="/admin"
          element={<RoleRoute allowedRoles={['admin']}><Admin /></RoleRoute>}
        />
      </Route>

      {/* Redirect routes */}
      <Route path="/listings/:id" element={<Navigate to="/marketplace" replace />} />
      <Route path="/listings/:id/messages" element={<Navigate to="/marketplace" replace />} />
      <Route path="/transactions" element={<Navigate to="/marketplace" replace />} />
      <Route path="/checkout" element={<Navigate to="/marketplace" replace />} />
      <Route path="/admin-config" element={<Navigate to="/admin" replace />} />
      <Route path="/admin-users" element={<Navigate to="/admin" replace />} />
      <Route path="/admin-audit-logs" element={<Navigate to="/admin" replace />} />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;
