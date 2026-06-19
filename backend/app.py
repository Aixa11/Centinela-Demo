# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from datetime import datetime
import jwt
import asyncio
from typing import List
from contextlib import asynccontextmanager

from models import SimulationConfig
from simulation import SimulationEngine
from auth import create_access_token, verify_token

# ============================================
# CONFIGURACION
# ============================================
security = HTTPBearer()
sim_engine = SimulationEngine()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Error: {e}")
        return False

# ============================================
# USUARIOS CON HASHS GENERADOS
# ============================================
USERS = {
    "admin": {
        "username": "admin", 
        "password": "$2b$12$BaG8rrvKBLMGjgb9JoTvWeNs8MtImHoOSwy6uS5e.1MN5EFJdRnt2", 
        "role": "admin"
    },
    "analyst": {
        "username": "analyst", 
        "password": "$2b$12$0LvPy3Mozh6zDrUQJ.vpZOQojKi9KbdmRMJr1ASpE.qH3Wixv3Ii.", 
        "role": "analyst"
    },
    "viewer": {
        "username": "viewer", 
        "password": "$2b$12$pnjN6EvBhEFwJmhrSJ4cMue8CpTNISowBRipmRnVEBUoODQy40w9.", 
        "role": "viewer"
    }
}

# ============================================
# FASTAPI
# ============================================
app = FastAPI(title="Centinela API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# AUTH
# ============================================
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

# ============================================
# ENDPOINTS
# ============================================
@app.get("/")
def root():
    return {"service": "Centinela API", "version": "3.0", "status": "operational", "docs": "/docs"}

@app.post("/auth/login")
def login(user: dict):
    username = user.get("username")
    password = user.get("password")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    
    stored = USERS.get(username)
    if not stored:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(password, stored["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"username": username, "role": stored["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"username": username, "role": stored["role"]}
    }

# ============================================
# ENDPOINTS PUBLICOS
# ============================================
@app.get("/api/assets")
def get_assets():
    return {"assets": sim_engine.assets}

@app.get("/api/alerts")
def get_alerts(limit: int = 50, resolved: bool = False):
    alerts = sim_engine.alerts
    if not resolved:
        alerts = [a for a in alerts if not a["resolved"]]
    return {"alerts": alerts[:limit], "total": len(alerts)}

@app.get("/api/metrics")
def get_metrics():
    return sim_engine.get_metrics()

@app.post("/api/simulate")
def simulate(config: SimulationConfig):
    new_alerts = sim_engine.update(config)
    return {"status": "simulated", "new_alerts": len(new_alerts), "scenario": config.scenario}

@app.post("/api/alerts/resolve/{alert_id}")
def resolve_alert(alert_id: str):
    if sim_engine.resolve_alert(alert_id):
        return {"status": "resolved", "alert_id": alert_id}
    raise HTTPException(status_code=404, detail="Alert not found")

@app.post("/api/scenario")
def change_scenario(config: SimulationConfig):
    sim_engine.scenario = config.scenario
    sim_engine.intensity = config.intensity
    return {"status": "updated", "scenario": config.scenario, "intensity": config.intensity}

@app.get("/api/history")
def get_history(limit: int = 50):
    return {"history": sim_engine.history[-limit:]}

# ============================================
# INICIO
# ============================================
if __name__ == "__main__":
    import uvicorn
    print("🚀 Centinela API v3.0")
    print("📍 http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("")
    print("🔑 Credentials:")
    print("  admin / admin123 (admin)")
    print("  analyst / analyst123 (analyst)")
    print("  viewer / viewer123 (viewer)")
    print("")
    
    # Probar autenticacion
    test_pass = "admin123"
    if verify_password(test_pass, USERS["admin"]["password"]):
        print("  ✅ Autenticacion verificada correctamente")
    else:
        print("  ❌ Error en autenticacion")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
