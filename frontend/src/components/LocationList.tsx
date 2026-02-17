import { Location } from "../api/client";
import { Card, CardContent } from "./ui/card";

interface LocationListProps {
	locations: Location[];
	onClose?: () => void;
}

export default function LocationList({
	locations,
	onClose,
}: LocationListProps) {
	return (
		<div className="location-list">
			<div className="flex justify-between items-center px-1 py-2">
				<h3 className="text-sm font-semibold m-0 p-0">
					Recent Locations ({locations.length})
				</h3>
				{onClose && (
					<button
						onClick={onClose}
						className="text-muted-foreground hover:text-foreground text-lg leading-none cursor-pointer md:hidden"
					>
						&times;
					</button>
				)}
			</div>
			<div className="list-items">
				{locations.length === 0 ? (
					<p className="empty">No locations match your filters</p>
				) : (
					locations.slice(0, 20).map((loc, idx) => (
						<Card key={idx} className="mx-1 my-2 py-3">
							<CardContent className="flex flex-col gap-1 text-sm py-0">
								<div className="flex justify-between items-center">
									<span className="font-semibold">{loc.tracker_id}</span>
									<span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
										{loc.device_id || "Unknown"}
									</span>
								</div>
								<p className="font-mono text-xs text-muted-foreground">
									{loc.latitude.toFixed(4)}, {loc.longitude.toFixed(4)}
								</p>
								<p className="text-xs text-muted-foreground">
									{new Date(loc.timestamp).toLocaleString()}
								</p>
							</CardContent>
						</Card>
					))
				)}
			</div>
		</div>
	);
}
