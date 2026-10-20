import React from 'react';
import { ErrorBoundary } from './ErrorBoundary';

interface PageLayoutProps {
  children: React.ReactNode;
  title: string;
}

export function PageLayout({ children, title }: PageLayoutProps) {
  return (
    <div className="page-shell">
      <div>
        <div className="page-heading">
          <div className="eyebrow">Farm management</div>
          <h1>{title}</h1>
        </div>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </div>
    </div>
  );
}
