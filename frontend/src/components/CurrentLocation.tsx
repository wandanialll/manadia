import { useState, useEffect, useMemo } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import MapComponent from "./MapComponent";
import { getLocations, Location } from "../api/client";
import "./Dashboard.css";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Card, CardContent } from "./ui/card";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "./ui/select";
import { Field, FieldLabel } from "./ui/field";

export default function CurrentLocation() {
	const { username, logout } = useAuth();
	const navigate = useNavigate();
	const [searchParams, setSearchParams] = useSearchParams();

	const userParam = searchParams.get("user");

	const [locations, setLocations] = useState<Location[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	// Fetch locations on mount and poll
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
		const interval = setInterval(fetchLocations, 10000);
		return () => clearInterval(interval);
	}, []);

	const uniqueUsers = useMemo(
		() =>
			[
				...new Set(locations.map((loc) => loc.tracker_id).filter(Boolean)),
			] as string[],
		[locations],
	);

	// Auto-select first user if none selected
	useEffect(() => {
		if (!userParam && uniqueUsers.length > 0) {
			setSearchParams({ user: uniqueUsers[0] }, { replace: true });
		}
	}, [userParam, uniqueUsers, setSearchParams]);

	// Get the latest location for the selected user
	const currentLocation = useMemo(() => {
		if (!userParam) return null;
		const userLocations = locations.filter(
			(loc) => loc.tracker_id === userParam,
		);
		if (userLocations.length === 0) return null;
		return userLocations.reduce((latest, loc) =>
			new Date(loc.timestamp) > new Date(latest.timestamp) ? loc : latest,
		);
	}, [locations, userParam]);

	const displayLocations = currentLocation ? [currentLocation] : [];

	if (loading && locations.length === 0) {
		return <div className="dashboard-loading">Loading locations...</div>;
	}

	return (
		<div className="dashboard">
			<div className="dashboard-sidebar">
				<div className="flex justify-between items-center mx-3">
					<h1>Current Location</h1>
					<div className="flex items-center gap-2">
						<Button variant="outline" size="sm" onClick={() => navigate("/")}>
							Dashboard
						</Button>
						<Badge variant="outline">{username}</Badge>
						<Button variant="outline" size="sm" onClick={logout}>
							Logout
						</Button>
					</div>
				</div>

				<div className="mx-3 my-2">
					<Field>
						<FieldLabel>User</FieldLabel>
						<Select
							value={userParam || ""}
							onValueChange={(value) =>
								setSearchParams({ user: value }, { replace: true })
							}
						>
							<SelectTrigger>
								<SelectValue placeholder="Select a user" />
							</SelectTrigger>
							<SelectContent>
								{uniqueUsers.map((user) => (
									<SelectItem key={user} value={user}>
										{user}
									</SelectItem>
								))}
							</SelectContent>
						</Select>
					</Field>
				</div>

				{error && <div className="error mx-3">{error}</div>}

				<div className="flex-1 overflow-hidden px-3 pb-3">
					{currentLocation ? (
						<Card className="my-2 py-3">
							<CardContent className="flex flex-col gap-2 text-sm py-0">
								<div className="flex justify-between items-center">
									<span className="font-semibold">
										{currentLocation.tracker_id}
									</span>
									<span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
										{currentLocation.device_id || "Unknown"}
									</span>
								</div>
								<p className="font-mono text-xs text-muted-foreground">
									{currentLocation.latitude.toFixed(6)},{" "}
									{currentLocation.longitude.toFixed(6)}
								</p>
								{currentLocation.altitude != null && (
									<p className="text-xs text-muted-foreground">
										<strong>Altitude:</strong>{" "}
										{currentLocation.altitude.toFixed(1)}m
									</p>
								)}
								{currentLocation.accuracy != null && (
									<p className="text-xs text-muted-foreground">
										<strong>Accuracy:</strong>{" "}
										{currentLocation.accuracy.toFixed(1)}m
									</p>
								)}
								{currentLocation.battery != null && (
									<p className="text-xs text-muted-foreground">
										<strong>Battery:</strong> {currentLocation.battery}%
									</p>
								)}
								{currentLocation.connection && (
									<p className="text-xs text-muted-foreground">
										<strong>Connection:</strong> {currentLocation.connection}
									</p>
								)}
								<p className="text-xs text-muted-foreground">
									<strong>Last seen:</strong>{" "}
									{new Date(currentLocation.timestamp).toLocaleString()}
								</p>
							</CardContent>
						</Card>
					) : (
						<p className="text-sm text-muted-foreground mt-4">
							{userParam
								? "No location data for this user."
								: "Select a user to see their current location."}
						</p>
					)}
				</div>
			</div>
			<div className="dashboard-map">
				<MapComponent locations={displayLocations} />
			</div>
		</div>
	);
}
