# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Dict, List

class RulesEngine:
    def __init__(self):
        self.rules = [
            {"id": "RULE-001", "name": "Critical Cyber Attack", 
             "condition": self._cyber_critical, "action": "ESCALATE_TO_RESPONSE_TEAM", "priority": 1},
            {"id": "RULE-002", "name": "Natural Disaster Alert",
             "condition": self._natural_disaster, "action": "NOTIFY_CIVIL_DEFENSE", "priority": 1},
            {"id": "RULE-003", "name": "Multiple Alerts Same Asset",
             "condition": self._multiple_alerts, "action": "GROUP_ALERTS", "priority": 2},
            {"id": "RULE-004", "name": "Critical Asset Compromised",
             "condition": self._critical_asset, "action": "IMMEDIATE_ALERT", "priority": 1}
        ]
        self.execution_log = []

    def _cyber_critical(self, alert: Dict, context: Dict) -> bool:
        keywords = ["unauthorized", "ransomware", "data leak", "DDoS", "compromised"]
        return (alert.get("severity") in ["alta", "critica"] and
                alert.get("category") == "ciberataque" and
                any(kw in alert.get("message", "").lower() for kw in keywords))

    def _natural_disaster(self, alert: Dict, context: Dict) -> bool:
        keywords = ["seismic", "flood", "extreme winds", "wildfire", "storm"]
        return (alert.get("severity") in ["alta", "critica"] and
                alert.get("category") == "desastre_natural" and
                any(kw in alert.get("message", "").lower() for kw in keywords))

    def _multiple_alerts(self, alert: Dict, context: Dict) -> bool:
        alerts = context.get("alerts_history", [])
        count = sum(1 for a in alerts if a["asset_id"] == alert["asset_id"] and not a["resolved"])
        return count >= 3

    def _critical_asset(self, alert: Dict, context: Dict) -> bool:
        asset = context.get("assets", {}).get(alert["asset_id"])
        if asset and asset.get("criticality", 0) >= 4:
            return alert.get("severity") in ["alta", "critica"]
        return False

    def evaluate(self, alert: Dict, context: Dict) -> Dict:
        matched = []
        for rule in self.rules:
            try:
                if rule["condition"](alert, context):
                    matched.append({"rule_id": rule["id"], "rule_name": rule["name"], 
                                    "action": rule["action"], "priority": rule["priority"]})
            except:
                pass
        matched.sort(key=lambda x: x["priority"])
        self.execution_log.append({"timestamp": datetime.now().isoformat(), 
                                   "alert_id": alert["id"], "matched_rules": matched})
        return {
            "matched_rules": matched,
            "recommended_action": matched[0]["action"] if matched else "REGISTER_ALERT",
            "all_actions": [r["action"] for r in matched] if matched else ["REGISTER_ALERT"]
        }
