# -*- coding: utf-8 -*-

import random
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class SimulationEngine:
    def __init__(self):
        self.assets = self._load_or_generate_assets()
        self.alerts = []
        self.tick = 0
        self.scenario = "normal"
        self.intensity = 3
        self.history = []
        self._load_alert_templates()

    def _load_alert_templates(self):
        self.alert_templates = {
            "ciberataque": [
                "Anomalous traffic detected on {name}",
                "Unauthorized access attempt on {name}",
                "Ransomware pattern identified on {name}",
                "Potential data leak on {name}",
                "DDoS attack targeting {name}",
                "Compromised credentials on {name}"
            ],
            "desastre_natural": [
                "Seismic alert in area of {name}",
                "Flood detected near {name}",
                "Extreme winds affecting {name}",
                "Wildfire near {name}",
                "Electrical storm over {name}",
                "Landslide in {name}"
            ],
            "normal": [
                "Abnormal latency on {name}",
                "Voltage fluctuation on {name}",
                "Critical temperature on {name}",
                "Abnormal pressure on {name}",
                "Vibration level exceeded on {name}"
            ],
            "mixto": []
        }

    def _load_or_generate_assets(self) -> List[Dict]:
        asset_file = os.path.join(os.path.dirname(__file__), "data", "assets.json")
        if os.path.exists(asset_file):
            try:
                with open(asset_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return self._generate_assets()

    def _generate_assets(self) -> List[Dict]:
        return [
            {"id": str(uuid.uuid4()), "name": "Vaca Muerta Pipeline", 
             "type": "oleoducto", "lat": -38.9, "lng": -69.1, "status": "operativo", 
             "criticality": 5, "description": "Main Neuquen basin pipeline"},
            {"id": str(uuid.uuid4()), "name": "Atucha I Power Plant", 
             "type": "electrica", "lat": -33.9, "lng": -59.2, "status": "operativo",
             "criticality": 5, "description": "Nuclear power plant"},
            {"id": str(uuid.uuid4()), "name": "CABA Fiber Optic Node", 
             "type": "comunicaciones", "lat": -34.6, "lng": -58.4, "status": "operativo",
             "criticality": 4, "description": "Main communications node"},
            {"id": str(uuid.uuid4()), "name": "Bahia Blanca Port", 
             "type": "transporte", "lat": -38.7, "lng": -62.3, "status": "operativo",
             "criticality": 4, "description": "Deep water port"},
            {"id": str(uuid.uuid4()), "name": "Yacyreta Hydroelectric", 
             "type": "electrica", "lat": -27.4, "lng": -56.3, "status": "operativo",
             "criticality": 4, "description": "Binational dam"},
            {"id": str(uuid.uuid4()), "name": "Nestor Kirchner Gas Pipeline", 
             "type": "gas", "lat": -38.0, "lng": -68.0, "status": "operativo",
             "criticality": 5, "description": "Southern trunk gas pipeline"},
            {"id": str(uuid.uuid4()), "name": "ARSAT Satellite Station", 
             "type": "comunicaciones", "lat": -34.5, "lng": -58.7, "status": "operativo",
             "criticality": 5, "description": "Satellite control center"},
            {"id": str(uuid.uuid4()), "name": "MINCyT Data Center", 
             "type": "comunicaciones", "lat": -34.6, "lng": -58.4, "status": "operativo",
             "criticality": 4, "description": "Strategic data center"},
            {"id": str(uuid.uuid4()), "name": "Colorado River Aqueduct", 
             "type": "agua", "lat": -38.2, "lng": -62.5, "status": "operativo",
             "criticality": 3, "description": "Water supply system"},
            {"id": str(uuid.uuid4()), "name": "Embalse Nuclear Plant", 
             "type": "electrica", "lat": -32.2, "lng": -64.3, "status": "operativo",
             "criticality": 4, "description": "Nuclear power plant"},
            {"id": str(uuid.uuid4()), "name": "Transandino Pipeline", 
             "type": "oleoducto", "lat": -32.9, "lng": -68.8, "status": "operativo",
             "criticality": 3, "description": "Chile connection"},
            {"id": str(uuid.uuid4()), "name": "Ezeiza Customs IT Center", 
             "type": "comunicaciones", "lat": -34.8, "lng": -58.5, "status": "operativo",
             "criticality": 3, "description": "Critical customs infrastructure"}
        ]

    def update(self, config=None) -> List[Dict]:
        self.tick += 1
        if config:
            self.scenario = config.scenario
            self.intensity = config.intensity

        new_alerts = []
        for asset in self.assets:
            risk_factor = asset.get("criticality", 3) / 5.0
            base_prob = 0.005 * risk_factor * (self.intensity / 3.0)

            if self.scenario == "ciberataque":
                if random.random() < base_prob * 4:
                    new_alerts.extend(self._generate_alert(asset, "ciberataque"))
            elif self.scenario == "desastre_natural":
                if random.random() < base_prob * 3:
                    new_alerts.extend(self._generate_alert(asset, "desastre_natural"))
            elif self.scenario == "mixto":
                for cause in ["ciberataque", "desastre_natural", "normal"]:
                    if random.random() < base_prob:
                        new_alerts.extend(self._generate_alert(asset, cause))
            else:
                if random.random() < base_prob:
                    new_alerts.extend(self._generate_alert(asset, "normal"))

        self._update_asset_status()
        self.alerts.extend(new_alerts)
        self.alerts = sorted(self.alerts, key=lambda x: x["timestamp"], reverse=True)[:200]

        self.history.append({
            "tick": self.tick,
            "timestamp": datetime.now().isoformat(),
            "scenario": self.scenario,
            "new_alerts": len(new_alerts),
            "total_alerts": len(self.alerts)
        })
        return new_alerts

    def _generate_alert(self, asset: Dict, cause: str) -> List[Dict]:
        templates = self.alert_templates.get(cause, self.alert_templates["normal"])
        if cause == "mixto":
            templates = (self.alert_templates["ciberataque"] + 
                        self.alert_templates["desastre_natural"] + 
                        self.alert_templates["normal"])

        severity = random.choices(
            ["baja", "media", "alta", "critica"],
            weights=[0.4, 0.3, 0.2, 0.1]
        )[0]

        if asset.get("criticality", 3) >= 4:
            severity = random.choices(
                ["baja", "media", "alta", "critica"],
                weights=[0.1, 0.2, 0.3, 0.4]
            )[0]

        return [{
            "id": str(uuid.uuid4()),
            "asset_id": asset["id"],
            "severity": severity,
            "message": random.choice(templates).format(name=asset["name"]),
            "timestamp": datetime.now().isoformat(),
            "resolved": False,
            "category": cause
        }]

    def _update_asset_status(self):
        for asset in self.assets:
            unresolved = [a for a in self.alerts if a["asset_id"] == asset["id"] and not a["resolved"]]
            if len(unresolved) >= 3:
                asset["status"] = "critico"
            elif len(unresolved) >= 1:
                asset["status"] = "alerta"
            else:
                asset["status"] = "operativo"
            asset["last_update"] = datetime.now().isoformat()

    def resolve_alert(self, alert_id: str) -> bool:
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["resolved"] = True
                alert["resolved_at"] = datetime.now().isoformat()
                return True
        return False

    def get_metrics(self) -> Dict:
        total = len(self.assets)
        critical = sum(1 for a in self.assets if a["status"] == "critico")
        alerts = len([a for a in self.alerts if not a["resolved"]])
        critical_alerts = len([a for a in self.alerts if not a["resolved"] and a["severity"] in ["alta", "critica"]])

        uptime = max(90, 99.99 - (alerts * 0.005))

        type_dist = {}
        for asset in self.assets:
            t = asset["type"]
            type_dist[t] = type_dist.get(t, 0) + 1

        severity_dist = {}
        for alert in self.alerts:
            if not alert["resolved"]:
                s = alert["severity"]
                severity_dist[s] = severity_dist.get(s, 0) + 1

        return {
            "total_assets": total,
            "critical_assets": critical,
            "active_alerts": alerts,
            "critical_alerts": critical_alerts,
            "uptime": round(uptime, 2),
            "last_update": datetime.now().isoformat(),
            "type_distribution": type_dist,
            "severity_distribution": severity_dist,
            "scenario": self.scenario,
            "tick": self.tick
        }

    def get_alert_history(self, limit: int = 100) -> List[Dict]:
        return self.alerts[:limit]

    def get_asset_by_id(self, asset_id: str):
        for asset in self.assets:
            if asset["id"] == asset_id:
                return asset
        return None

    def reset(self):
        self.assets = self._generate_assets()
        self.alerts = []
        self.tick = 0
        self.history = []
