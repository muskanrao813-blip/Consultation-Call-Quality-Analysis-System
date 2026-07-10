import React from 'react';
import { Search, Bell, HelpCircle } from 'lucide-react';
import { SystemSettings } from '../types';

interface HeaderProps {
  currentView: string;
  settings: SystemSettings;
  searchQuery: string;
  onSearchQueryChange: (query: string) => void;
}

export default function Header({
  currentView,
  settings,
  searchQuery,
  onSearchQueryChange
}: HeaderProps) {
  // Get contextual header title or search placeholder
  const getSearchPlaceholder = () => {
    switch (currentView) {
      case 'dashboard':
        return 'Search analytics, dieticians, or QA tags...';
      case 'upload':
        return 'Search files, active uploads, or transcripts...';
      case 'transcriptions':
        return 'Search patient transcripts or recording IDs...';
      case 'insights':
        return 'Search call performance analyses...';
      case 'reports':
        return 'Search dieticians, active staff, or training reports...';
      case 'alerts':
        return 'Search compliance alerts, severity, or SOP rules...';
      case 'settings':
        return 'Search settings and preferences...';
      default:
        return 'Search analytics portal...';
    }
  };

  const getBreadcrumb = () => {
    switch (currentView) {
      case 'dashboard':
        return 'Executive Performance Overview';
      case 'upload':
        return 'Call Upload & Ingestion';
      case 'transcriptions':
        return 'Clinical Transcriptions';
      case 'insights':
        return 'Call Performance Analysis';
      case 'reports':
        return 'Performance & Training Report';
      case 'alerts':
        return 'QA Compliance Alerts';
      case 'settings':
        return 'System Settings';
      default:
        return 'Clinical Intelligence';
    }
  };

  return (
    <header className="h-16 border-b border-[#1A1A1A]/10 bg-white flex items-center justify-between px-8 sticky top-0 z-40 select-none">
      {/* Left side: Contextual search input */}
      <div className="flex items-center gap-6 flex-1 max-w-xl">
        <div className="relative w-full max-w-sm">
          <Search className="w-3.5 h-3.5 absolute left-1 top-1/2 -translate-y-1/2 text-[#1A1A1A]/50" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
            placeholder={getSearchPlaceholder()}
            className="w-full bg-transparent border-b border-[#1A1A1A]/10 pl-7 pr-2 py-1 text-xs text-[#1A1A1A] placeholder:text-[#1A1A1A]/40 focus:outline-none focus:border-[#8B7E66] transition-all"
          />
        </div>
        <div className="h-6 w-[1px] bg-[#1A1A1A]/10 hidden sm:block"></div>
        <div className="hidden sm:flex items-center gap-2">
          <span className="text-sm font-serif italic text-[#1A1A1A]">{getBreadcrumb()}</span>
          <span className="bg-[#8B7E66] text-white text-[9px] font-sans font-bold px-1.5 py-0.5 tracking-widest uppercase">
            Internal
          </span>
        </div>
      </div>

      {/* Right side: Actions & User Info */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <button className="text-[#1A1A1A]/60 hover:text-[#1A1A1A] p-2 rounded-none transition-all relative">
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-[#A34E36]"></span>
          </button>
          <button className="text-[#1A1A1A]/60 hover:text-[#1A1A1A] p-2 rounded-none transition-all">
            <HelpCircle className="w-4 h-4" />
          </button>
        </div>

        <div className="h-8 w-[1px] bg-[#1A1A1A]/10"></div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden md:block">
            <p className="text-xs font-serif font-semibold text-[#1A1A1A] leading-tight">
              {settings.accountProfile.name}
            </p>
            <p className="text-[8px] font-sans font-bold text-[#8B7E66] uppercase tracking-widest">
              {settings.accountProfile.role}
            </p>
          </div>
          <div className="relative">
            <img
              src={settings.accountProfile.avatar}
              alt="User Portrait"
              className="w-9 h-9 rounded-none border border-[#1A1A1A]/20 p-[2px] bg-white object-cover shadow-none select-none"
              referrerPolicy="no-referrer"
            />
          </div>
        </div>
      </div>
    </header>
  );
}
