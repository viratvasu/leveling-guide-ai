import { useState } from 'react';
import { Outlet, useNavigate, useLocation, NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './DashboardLayout.css';

export default function DashboardLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const { user, company, navigation, logoutUser } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = () => {
        logoutUser();
        navigate('/login');
    };

    const toggleSidebar = () => {
        setSidebarOpen(!sidebarOpen);
    };

    return (
        <div className="dashboard-container">
            {/* Sidebar */}
            <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
                <div className="sidebar-header">
                    <h2 className="sidebar-logo">LG AI</h2>
                    <button className="sidebar-toggle" onClick={toggleSidebar}>
                        {sidebarOpen ? '←' : '→'}
                    </button>
                </div>

                <nav className="sidebar-nav">
                    {navigation && navigation.length > 0 ? (
                        <ul className="nav-list">
                            {navigation.map((item) => (
                                <li key={item.key}>
                                    <NavLink
                                        to={item.path}
                                        className={({ isActive }) =>
                                            `nav-item ${isActive ? 'active' : ''}`
                                        }
                                        onClick={() => {
                                            // Close sidebar on mobile after clicking
                                            if (window.innerWidth <= 768) {
                                                setSidebarOpen(false);
                                            }
                                        }}
                                    >
                                        <span className="nav-icon">{item.icon}</span>
                                        {sidebarOpen && <span className="nav-label">{item.label}</span>}
                                    </NavLink>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="sidebar-empty">No menu items available</p>
                    )}
                </nav>

                <div className="sidebar-footer">
                    <div className="user-info">
                        <div className="user-avatar">
                            {user?.username?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        {sidebarOpen && (
                            <div className="user-details">
                                <span className="user-name">{user?.username || 'User'}</span>
                                <span className="user-role">
                                    {user?.current_role || company?.name || user?.email || ''}
                                </span>
                            </div>
                        )}
                    </div>
                    <button className="logout-button" onClick={handleLogout}>
                        {sidebarOpen ? 'Logout' : '↪'}
                    </button>
                </div>
            </aside>

            {/* Mobile sidebar overlay */}
            {sidebarOpen && (
                <div className="sidebar-overlay" onClick={toggleSidebar}></div>
            )}

            {/* Main content area */}
            <main className={`main-content ${sidebarOpen ? '' : 'sidebar-closed'}`}>
                <header className="main-header">
                    <button className="mobile-menu-toggle" onClick={toggleSidebar}>
                        ☰
                    </button>
                    <h1>Dashboard</h1>
                    {company && (
                        <span className="company-badge">{company.name}</span>
                    )}
                </header>

                <div className="content-area">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
