import { Outlet } from 'react-router-dom';
import { Navigation } from './Navigation';

export function Layout() {
  return (
    <div className="min-h-screen">
      <Navigation />
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
