import json
from datetime import datetime, timedelta, timezone

events = []
start_time = datetime(2026, 7, 9, 10, 0, 0, tzinfo=timezone.utc)

for i in range(5001):
    events.append({
        "event_id": f"evt_bulk_{i+1:05}",
        "tenant_id": "tenant_alpha_01",
        "source": "web",
        "event_type": "click",
        "timestamp": (start_time + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        "payload": {
            "page": "home",
            "button": "signup",
            "sequence": i + 1
        }
    })

data = {"events": events}

with open("bulk_5001_events.json", "w") as f:
    json.dump(data, f, indent=2)

print("Generated bulk_5001_events.json with", len(events), "events")