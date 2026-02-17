import { useState } from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import { Location } from "../api/client";
import { CircleMarker } from "react-leaflet";
import L from "leaflet";
import { Card, CardContent } from "./ui/card";

// Fix Leaflet marker images
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
	iconRetinaUrl:
		"https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
	iconUrl:
		"https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
	shadowUrl:
		"https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

interface MapComponentProps {
	locations: Location[];
}

export default function MapComponent({ locations }: MapComponentProps) {
	const [selected, setSelected] = useState<Location | null>(null);

	if (locations.length === 0) {
		return <div className="map-empty">No locations to display</div>;
	}

	const center =
		locations.length > 0
			? ([
					locations[locations.length - 1].latitude,
					locations[locations.length - 1].longitude,
				] as [number, number])
			: ([0, 0] as [number, number]);

	return (
		<div className="relative w-full h-full">
			<MapContainer center={center} zoom={13} className="w-full h-full">
				<TileLayer
					attribution="&copy; OpenStreetMap contributors &copy; CARTO"
					url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
				/>
				{locations.map((location, idx) => (
					<CircleMarker
						key={idx}
						center={[location.latitude, location.longitude]}
						eventHandlers={{
							click: () => setSelected(location),
						}}
					/>
				))}
			</MapContainer>

			{selected && (
				<Card className="absolute bottom-4 left-4 right-4 z-[1000] shadow-lg">
					<CardContent className="flex flex-col gap-1 text-sm py-0">
						<div className="flex justify-between items-center">
							<span className="font-semibold">Location Details</span>
							<button
								onClick={() => setSelected(null)}
								className="text-muted-foreground hover:text-foreground text-lg leading-none cursor-pointer"
							>
								&times;
							</button>
						</div>
						<p>
							<strong>User:</strong> {selected.tracker_id}
						</p>
						<p>
							<strong>Device:</strong> {selected.device_id || "Unknown"}
						</p>
						<p>
							<strong>Time:</strong>{" "}
							{new Date(selected.timestamp).toLocaleString()}
						</p>
						<p>
							<strong>Accuracy:</strong>{" "}
							{selected.accuracy ? selected.accuracy.toFixed(1) + "m" : "N/A"}
						</p>
					</CardContent>
				</Card>
			)}
		</div>
	);
}
