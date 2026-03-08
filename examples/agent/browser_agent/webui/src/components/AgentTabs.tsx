import React from 'react';
import { useStore } from '../store/useStore';
import { Layout, Globe } from 'lucide-react';

const AgentTabs: React.FC = () => {
  const { tabs, activeTab, setActiveTab } = useStore();

  return (
    <div className="flex bg-gray-100 border-b border-borderSubtle overflow-x-auto no-scrollbar">
      {tabs.map((tabId) => (
        <div
          key={tabId}
          onClick={() => setActiveTab(tabId)}
          className={`chrome-tab ${activeTab === tabId ? 'active' : ''}`}
        >
          {tabId === 'plan' ? (
            <>
              <Layout className="w-4 h-4 mr-2" />
              <span>Plan</span>
            </>
          ) : (
            <>
              <Globe className="w-4 h-4 mr-2" />
              <span>{tabId.split('_').pop() || tabId}</span>
            </>
          )}
        </div>
      ))}
    </div>
  );
};

export default AgentTabs;
