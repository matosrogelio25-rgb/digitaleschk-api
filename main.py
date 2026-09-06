import os
import braintree
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Conectamos con Braintree usando las llaves guardadas en Render
# (Asegúrate de cambiar a braintree.Environment.Production si usas llaves reales)
gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        environment=braintree.Environment.Sandbox,
        merchant_id=os.environ.get("BT_MERCHANT_ID"),
        public_key=os.environ.get("BT_PUBLIC_KEY"),
        private_key=os.environ.get("BT_PRIVATE_KEY")
    )
)

# Estructura flexible para recibir cualquier formato de tarjeta que envíe el bot
class CardCheckRequest(BaseModel):
    card_number: Optional[str] = None
    cc_number: Optional[str] = None
    expiration_month: Optional[str] = None
    exp_month: Optional[str] = None
    expiration_year: Optional[str] = None
    exp_year: Optional[str] = None
    cvv: Optional[str] = None

def procesar_pago(amount: str, data: CardCheckRequest):
    # Unificamos los campos automáticamente
    num = data.card_number or data.cc_number
    mes = data.expiration_month or data.exp_month
    anio = data.expiration_year or data.exp_year
    cvv_val = data.cvv

    if not all([num, mes, anio, cvv_val]):
        raise HTTPException(status_code=400, detail="Faltan datos de la tarjeta.")

    result = gateway.transaction.sale({
        "amount": amount,
        "credit_card": {
            "number": num,
            "expiration_month": mes,
            "expiration_year": anio,
            "cvv": cvv_val
        },
        "options": {
            "submit_for_settlement": True
        }
    })

    if result.is_success:
        return {
            "status": "Approved",
            "message": "¡Aprobada!",
            "transaction_id": result.transaction.id
        }
    else:
        return {
            "status": "Declined",
            "message": result.message
        }

# Cubrimos ABSOLUTAMENTE TODAS las rutas posibles para evitar el error 404
@app.post("/check-card")
@app.post("/api/v1/charge")
@app.post("/api/v1/ccn-auth")
@app.post("/charge")
@app.post("/ccn-auth")
async def check_card(data: CardCheckRequest):
    try:
        return procesar_pago("1.00", data)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

