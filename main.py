from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import database as db
import os
import socket

app = FastAPI(title="Personal Finance Engine API")

# Ensure static folder exists
os.makedirs("static", exist_ok=True)

# Initialize DB
db.init_db()

# Models
class Transaccion(BaseModel):
    fecha: str
    tipo: str
    categoria: str
    monto: float
    descripcion: str
    meta_id: Optional[int] = None

class MetaReq(BaseModel):
    nombre_meta: str
    monto_objetivo: float
    fecha_limite: str
    icono: str

class Inyeccion(BaseModel):
    monto: float

class GastoFijoReq(BaseModel):
    nombre: str
    monto: float

@app.get("/api/balance")
def get_balance():
    ingresos, gastos, balance = db.get_balance_global()
    return {"ingresos": ingresos, "gastos": gastos, "balance": balance}

@app.get("/api/metas")
def get_metas():
    return db.get_metas()

@app.post("/api/metas")
def create_meta(meta: MetaReq):
    db.add_meta(meta.nombre_meta, meta.monto_objetivo, meta.fecha_limite, meta.icono)
    return {"status": "success"}

@app.post("/api/metas/{meta_id}/inyeccion")
def inyectar_meta(meta_id: int, iny: Inyeccion):
    db.update_meta_funds(meta_id, iny.monto)
    return {"status": "success"}

@app.get("/api/categorias")
def get_categorias(tipo: Optional[str] = None):
    return db.get_categorias(tipo)

@app.get("/api/transacciones")
def get_transacciones():
    return db.get_transacciones()

@app.delete("/api/transacciones/{t_id}")
def delete_transaccion_api(t_id: int):
    db.delete_transaccion(t_id)
    return {"status": "success"}

@app.post("/api/transacciones")
def create_transaccion(txn: Transaccion):
    txn_id = db.add_transaccion(txn.fecha, txn.tipo, txn.categoria, txn.monto, txn.descripcion, txn.meta_id)
    
    # Auto-descuento de gastos fijos
    if txn.tipo == "Ingreso" and txn.categoria == "Nómina":
        gastos_fijos = db.get_gastos_fijos()
        for gf in gastos_fijos:
            db.add_transaccion(
                fecha=txn.fecha,
                tipo="Gasto",
                categoria="Descuento Fijo",
                monto=gf['monto'],
                descripcion=f"Auto-pago: {gf['nombre']} (Nómina)"
            )

    if txn.meta_id and txn.tipo == "Gasto":
        db.update_meta_funds(txn.meta_id, txn.monto)
    return {"status": "success", "id": txn_id}

# Gastos Fijos API
@app.get("/api/gastos_fijos")
def api_get_gastos_fijos():
    return db.get_gastos_fijos()

@app.post("/api/gastos_fijos")
def api_add_gasto_fijo(gf: GastoFijoReq):
    db.add_gasto_fijo(gf.nombre, gf.monto)
    return {"status": "success"}

@app.delete("/api/gastos_fijos/{g_id}")
def api_delete_gasto_fijo(g_id: int):
    db.delete_gasto_fijo(g_id)
    return {"status": "success"}

@app.get("/")
def serve_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

app.mount("/", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    # Get local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"
        
    print("="*60)
    print("[INFO] DANIEL ACOSTA EDITION: MOTOR DE FINANZAS INICIALIZADO")
    print(f"[INFO] Accede desde tu PC o celular abriendo: http://{local_ip}:8000")
    print("="*60)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
