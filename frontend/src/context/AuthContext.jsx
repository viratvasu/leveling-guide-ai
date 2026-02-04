import { createContext, useContext, useState, useEffect } from 'react';
import { getAuthToken, setAuthToken, removeAuthToken } from '../api/auth';

const AuthContext = createContext(null);

// Store full user data in localStorage
const USER_DATA_KEY = 'user_data';

function getUserData() {
    try {
        const data = localStorage.getItem(USER_DATA_KEY);
        return data ? JSON.parse(data) : null;
    } catch {
        return null;
    }
}

function setUserData(data) {
    localStorage.setItem(USER_DATA_KEY, JSON.stringify(data));
}

function removeUserData() {
    localStorage.removeItem(USER_DATA_KEY);
}

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [company, setCompany] = useState(null);
    const [permissions, setPermissions] = useState({});
    const [navigation, setNavigation] = useState([]);
    const [currentRole, setCurrentRole] = useState(null); // Added currentRole state
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check if user is already logged in
        const token = getAuthToken();
        const userData = getUserData();

        if (token && userData) {
            setUser(userData.user);
            setCompany(userData.company);
            setPermissions(userData.permissions || {});
            setNavigation(userData.navigation || []);
            setCurrentRole(userData.current_role || null); // Initialize currentRole
        }
        setLoading(false);
    }, []);

    const loginUser = (token, data) => {
        setAuthToken(token);
        setUserData(data);
        setUser(data.user);
        setCompany(data.company);
        setPermissions(data.permissions || {});
        setNavigation(data.navigation || []);
        setCurrentRole(data.current_role || null); // Set currentRole on login
    };

    const logoutUser = () => {
        removeAuthToken();
        removeUserData();
        setUser(null);
        setCompany(null);
        setPermissions({});
        setNavigation([]);
        setCurrentRole(null); // Clear currentRole on logout
    };

    // Check if user has a specific permission
    const hasPermission = (feature, action) => {
        if (!permissions || !permissions[feature]) return false;
        return permissions[feature][action] === true;
    };

    // Check if user can access a route based on navigation
    const canAccessRoute = (path) => {
        // Always allow dashboard home
        if (path === '/dashboard' || path === '/dashboard/') return true;

        // Check if path is in navigation
        return navigation.some(item => path.startsWith(item.path));
    };

    // Check if user can configure (admin) vs just view
    const canConfigure = (feature) => {
        return hasPermission(feature, 'configure');
    };

    return (
        <AuthContext.Provider value={{
            user,
            company,
            permissions,
            navigation,
            currentRole,
            loading,
            loginUser,
            logoutUser,
            hasPermission,
            canAccessRoute,
            canConfigure,
            isAuthenticated: !!user,
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
