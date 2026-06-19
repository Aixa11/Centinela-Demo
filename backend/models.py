# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class AssetStatus(str, Enum):
    OPERATIVO = "operativo"
    ALERTA = "alerta"
    CRITICO = "critico"

class AssetType(str, Enum):
    OLEODUCTO = "oleoducto"
    ELECTRICA = "electrica"
    COMUNICACIONES = "comunicaciones"
    TRANSPORTE = "transporte"
    AGUA = "agua"
    GAS = "gas"

class Asset(BaseModel):
    id: str
    name: str
    type: AssetType
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    status: AssetStatus = AssetStatus.OPERATIVO
    last_update: datetime = Field(default_factory=datetime.now)
    description: Optional[str] = None
    criticality: int = Field(ge=1, le=5, default=3)

class AlertSeverity(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

class Alert(BaseModel):
    id: str
    asset_id: str
    severity: AlertSeverity
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    category: str = "general"

class SimulationConfig(BaseModel):
    scenario: str = "normal"
    speed: int = 1
    intensity: int = Field(ge=1, le=5, default=3)

class User(BaseModel):
    username: str
    password: str
    role: str = "viewer"
