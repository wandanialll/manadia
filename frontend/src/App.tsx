import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Dashboard from "./components/Dashboard";
import CurrentLocation from "./components/CurrentLocation";
import Login from "./components/Login";
import "./App.css";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
	const { isAuthenticated } = useAuth();
	if (!isAuthenticated) return <Login />;
	return <>{children}</>;
}

function AppContent() {
	return (
		<Routes>
			<Route
				path="/"
				element={
					<ProtectedRoute>
						<Dashboard />
					</ProtectedRoute>
				}
			/>
			<Route
				path="/current-location"
				element={
					<ProtectedRoute>
						<CurrentLocation />
					</ProtectedRoute>
				}
			/>
			<Route path="*" element={<Navigate to="/" replace />} />
		</Routes>
	);
}

function App() {
	return (
		<BrowserRouter>
			<AuthProvider>
				<AppContent />
			</AuthProvider>
		</BrowserRouter>
	);
}

export default App;
