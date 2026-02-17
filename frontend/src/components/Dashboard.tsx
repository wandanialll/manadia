import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import MapComponent from "./MapComponent";
import LocationList from "./LocationList";
import Controls from "./Controls";
import { getLocations, Location } from "../api/client";
import "./Dashboard.css";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Card } from "./ui/card";

export default function Dashboard() {
	const { username, logout } = useAuth();
	const navigate = useNavigate();
	const [locations, setLocations] = useState<Location[]>([]);
	const [filteredLocations, setFilteredLocations] = useState<Location[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [selectedUser, setSelectedUser] = useState<string | null>(null);
	const [selectedDevice, setSelectedDevice] = useState<string | null>(null);
	const [showMobileList, setShowMobileList] = useState(false);
	const [showFilters, setShowFilters] = useState(false);

	// Fetch locations on mount and set up polling
	useEffect(() => {
		const fetchLocations = async () => {
			try {
				setLoading(true);
				const response = await getLocations();
				setLocations(response.data.data || []);
				setError(null);
			} catch (err) {
				setError(
					err instanceof Error ? err.message : "Failed to fetch locations",
				);
			} finally {
				setLoading(false);
			}
		};

		fetchLocations();
		const interval = setInterval(fetchLocations, 10000); // Poll every 10 seconds
		return () => clearInterval(interval);
	}, []);

	// Apply filters
	useEffect(() => {
		let filtered = locations;
		if (selectedUser) {
			filtered = filtered.filter((loc) => loc.tracker_id === selectedUser);
		}
		if (selectedDevice) {
			filtered = filtered.filter((loc) => loc.device_id === selectedDevice);
		}
		setFilteredLocations(filtered);
	}, [locations, selectedUser, selectedDevice]);

	const uniqueUsers = [
		...new Set(locations.map((loc) => loc.tracker_id).filter(Boolean)),
	] as string[];
	const uniqueDevices = [
		...new Set(
			locations.flatMap((loc) => (loc.device_id ? [loc.device_id] : [])),
		),
	];

	if (loading && locations.length === 0) {
		return <div className="dashboard-loading">Loading locations...</div>;
	}

	return (
		<div className="dashboard">
			<div className="dashboard-sidebar">
				<div className="flex justify-between items-center mx-3">
					<h1>Manadia Dashboard</h1>
					<div className="flex items-center gap-2">
						<Button
							variant="outline"
							size="sm"
							onClick={() =>
								navigate(
									selectedUser
										? `/current-location?user=${encodeURIComponent(selectedUser)}`
										: "/current-location",
								)
							}
						>
							Current Location
						</Button>
						<Button
							variant="outline"
							size="sm"
							onClick={() => setShowFilters(!showFilters)}
						>
							{showFilters ? "Hide Filters" : "Filters"}
							{(selectedUser || selectedDevice) && " •"}
						</Button>
						<Badge variant="outline">{username}</Badge>
						<Button variant="outline" size="sm" onClick={logout}>
							Logout
						</Button>
					</div>
				</div>
				{showFilters && (
					<Controls
						users={uniqueUsers}
						devices={uniqueDevices}
						selectedUser={selectedUser}
						selectedDevice={selectedDevice}
						onUserChange={setSelectedUser}
						onDeviceChange={setSelectedDevice}
						onRefresh={() => location.reload()}
					/>
				)}
				{error && <div className="error">{error}</div>}
				<div className="hidden md:flex flex-1 overflow-hidden">
					<LocationList locations={filteredLocations} />
				</div>
			</div>
			<div className="dashboard-map">
				<MapComponent locations={filteredLocations} />

				{/* Mobile floating list toggle */}
				{!showMobileList && (
					<Button
						className="mobile-list-toggle md:hidden absolute bottom-4 left-4 z-[1000] shadow-lg"
						onClick={() => setShowMobileList(true)}
					>
						Locations ({filteredLocations.length})
					</Button>
				)}

				{/* Mobile floating location list */}
				{showMobileList && (
					<Card className="md:hidden absolute bottom-0 left-0 right-0 z-[1000] max-h-[60vh] overflow-y-auto rounded-b-none shadow-lg">
						<LocationList
							locations={filteredLocations}
							onClose={() => setShowMobileList(false)}
						/>
					</Card>
				)}
			</div>
		</div>
	);
}
