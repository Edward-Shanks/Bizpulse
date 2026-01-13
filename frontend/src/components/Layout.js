import React from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/App';
import { useTheme } from '@/contexts/ThemeContext';
import { 
  LayoutDashboard, 
  Users, 
  Tag, 
  Layers, 
  FileText, 
  Target, 
  FolderKanban,
  Lightbulb,
  Bell,
  Settings,
  User,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  AlertCircle,
  Trello,
  BarChart3,
  Moon,
  Sun,
  LogOut
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import AIAssistant from '@/components/AIAssistant';

const Layout = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);
  const [businessCompassOpen, setBusinessCompassOpen] = React.useState(true); // Always open by default

  // Check if any Business Compass sub-item is active
  const businessCompassPaths = ['/compass', '/brands', '/customers', '/categories', '/sales-analysis'];
  const isBusinessCompassActive = businessCompassPaths.includes(location.pathname);

  // Keep Business Compass dropdown always open
  React.useEffect(() => {
    setBusinessCompassOpen(true);
  }, [location.pathname]);

  const menuItems = [
    { path: '/', icon: Target, label: 'Cockpit', color: '#f59e0b' },
    { path: '/strategic-deployment', icon: FolderKanban, label: 'Strategy Deployment' },
    { path: '/kanban', icon: Trello, label: 'Revenue Sentinel' },
    {
      path: '/compass',
      icon: LayoutDashboard,
      label: 'Business Compass',
      hasSubmenu: true,
      submenu: [
        { path: '/brands', icon: Tag, label: 'Brands' },
        { path: '/customers', icon: Users, label: 'Customers' },
        { path: '/categories', icon: Layers, label: 'Categories' },
        { path: '/sales-analysis', icon: TrendingUp, label: 'Sales Analysis' },
      ]
    },
    { path: '/customer-insights', icon: BarChart3, label: 'Customer Deep Intelligence' },
    { path: '/root-cause-analysis', icon: AlertCircle, label: 'Root Cause Analysis' },
    { path: '/projects', icon: FolderKanban, label: 'Projects' },
    { path: '/reports', icon: FileText, label: 'Reports' },
  ];

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'dark bg-gray-900' : 'bg-gray-50'}`}>
      {/* Top Header */}
      <header className={`h-16 fixed top-0 left-0 right-0 z-50 ${theme === 'dark' ? 'bg-gray-950 border-b border-gray-800' : ''}`} style={theme === 'dark' ? { background: '#030712' } : { background: '#184464' }}>
        <div className="h-full px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img 
              src="/vector_logo_white.svg" 
              alt="Vector AI Studio Logo" 
              className="h-14 w-auto"
            />
            <div>
              <h1 className="text-lg font-bold text-white" style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}>
                BeaconIQ
              </h1>
              <p className="text-xs text-gray-300">by Vector AI Studio</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <button className={`relative p-2 rounded-lg transition ${theme === 'dark' ? 'hover:bg-gray-800' : 'hover:bg-blue-700'}`}>
              <Bell className="w-5 h-5 text-white" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>
            
            {/* Settings Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className={`p-2 rounded-lg transition ${theme === 'dark' ? 'hover:bg-gray-800' : 'hover:bg-blue-700'}`}>
                  <Settings className="w-5 h-5 text-white" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>Settings</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={toggleTheme} className="cursor-pointer">
                  {theme === 'light' ? (
                    <>
                      <Moon className="mr-2 h-4 w-4" />
                      <span>Dark Theme</span>
                    </>
                  ) : (
                    <>
                      <Sun className="mr-2 h-4 w-4" />
                      <span>Light Theme</span>
                    </>
                  )}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="cursor-pointer text-red-600 focus:text-red-600">
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Logout</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            
            <button 
              className={`p-2 rounded-lg transition ${theme === 'dark' ? 'hover:bg-gray-800' : 'hover:bg-blue-700'}`}
              title="User Profile"
            >
              <User className="w-5 h-5 text-white" />
            </button>
          </div>
        </div>
      </header>

      <div className="flex pt-16">
        {/* Sidebar */}
        <aside 
          className={`fixed left-0 top-16 bottom-0 border-r transition-all duration-300 ${
            theme === 'dark' 
              ? 'bg-gray-800 border-gray-700' 
              : 'bg-white border-gray-200'
          } ${
            sidebarCollapsed ? 'w-20' : 'w-64'
          }`}
        >
          <div className="h-full flex flex-col">
            {/* Collapse Button */}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="absolute -right-3 top-6 w-6 h-6 bg-white border border-gray-200 rounded-full flex items-center justify-center hover:bg-gray-50 transition"
            >
              {sidebarCollapsed ? (
                <ChevronRight className="w-4 h-4 text-gray-600" />
              ) : (
                <ChevronLeft className="w-4 h-4 text-gray-600" />
              )}
            </button>

            {/* Navigation Title */}
            {!sidebarCollapsed && (
              <div className="px-4 py-4">
                <h3 className={`text-xs font-semibold uppercase tracking-wider ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  Navigation
                </h3>
              </div>
            )}

            {/* Menu Items */}
            <nav className="flex-1 px-3 py-2 overflow-y-auto">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                const hasSubmenu = item.hasSubmenu && item.submenu;
                const isParentActive = hasSubmenu && item.submenu.some(sub => sub.path === location.pathname);
                
                // For Business Compass, check if it or any sub-item is active
                const isItemActive = isActive || (item.path === '/compass' && isBusinessCompassActive);
                
                return (
                  <div key={item.path}>
                    <div
                      className={`w-full flex items-center gap-3 px-3 py-2.5 mb-1 rounded-lg transition-all ${
                        isItemActive || isParentActive
                          ? theme === 'dark'
                            ? 'bg-amber-900/30 text-amber-300 font-medium'
                            : 'bg-amber-50 text-amber-900 font-medium'
                          : theme === 'dark'
                            ? 'text-gray-300 hover:bg-gray-700'
                            : 'text-gray-700 hover:bg-gray-50'
                      }`}
                      style={(isItemActive || isParentActive) ? { borderLeft: '3px solid #f59e0b' } : {}}
                    >
                      <button
                        onClick={() => {
                          if (hasSubmenu) {
                            // If not on Business Compass page, navigate to it and expand submenu
                            if (location.pathname !== item.path) {
                              navigate(item.path);
                              setBusinessCompassOpen(true);
                            }
                            // If already on page, clicking main button doesn't toggle - only chevron does
                          } else {
                            navigate(item.path);
                          }
                        }}
                        className="flex items-center gap-3 flex-1 text-left"
                      >
                        <Icon 
                          className={`w-5 h-5 flex-shrink-0 ${
                            isItemActive || isParentActive 
                              ? 'text-amber-600' 
                              : theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                          }`} 
                        />
                        {!sidebarCollapsed && (
                          <span className="text-sm">{item.label}</span>
                        )}
                      </button>
                      {!sidebarCollapsed && hasSubmenu && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            // Keep Business Compass always open - prevent toggle
                            if (item.label === 'Business Compass') {
                              return;
                            }
                            setBusinessCompassOpen(!businessCompassOpen);
                          }}
                          className="p-1 hover:bg-gray-200 rounded transition flex-shrink-0"
                          aria-label={businessCompassOpen ? 'Collapse menu' : 'Expand menu'}
                        >
                          {businessCompassOpen ? (
                            <ChevronUp className="w-4 h-4 text-gray-500" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-gray-500" />
                          )}
                        </button>
                      )}
                    </div>
                    
                    {/* Submenu Items */}
                    {hasSubmenu && !sidebarCollapsed && businessCompassOpen && (
                      <div className="ml-4 mb-1 space-y-1">
                        {item.submenu.map((subItem) => {
                          const SubIcon = subItem.icon;
                          const isSubActive = location.pathname === subItem.path;
                          
                          return (
                            <button
                              key={subItem.path}
                              onClick={() => navigate(subItem.path)}
                              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all ${
                                isSubActive
                                  ? theme === 'dark'
                                    ? 'bg-amber-900/30 text-amber-300 font-medium'
                                    : 'bg-amber-50 text-amber-900 font-medium'
                                  : theme === 'dark'
                                    ? 'text-gray-400 hover:bg-gray-700'
                                    : 'text-gray-600 hover:bg-gray-50'
                              }`}
                              style={isSubActive ? { borderLeft: '3px solid #f59e0b' } : {}}
                            >
                              <SubIcon 
                                className={`w-4 h-4 flex-shrink-0 ${
                                  isSubActive 
                                    ? 'text-amber-600' 
                                    : theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
                                }`} 
                              />
                              <span className="text-sm">{subItem.label}</span>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </nav>

            {/* Footer */}
            {!sidebarCollapsed && (
              <div className={`p-4 border-t ${
                theme === 'dark' ? 'border-gray-700' : 'border-gray-200'
              }`}>
                <p className={`text-xs text-center ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  BeaconIQ by Vector AI Studio
                </p>
              </div>
            )}
          </div>
        </aside>

        {/* Main Content */}
        <main 
          className={`flex-1 transition-all duration-300 ${
            sidebarCollapsed ? 'ml-20' : 'ml-64'
          } ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}
        >
          <div className={`p-8 ${theme === 'dark' ? 'bg-gray-900 text-gray-100' : ''}`}>
            {children || <Outlet />}
          </div>
        </main>
      </div>

      {/* AI Assistant Floating Button - Available on all pages */}
      <AIAssistant />
    </div>
  );
};

export default Layout;