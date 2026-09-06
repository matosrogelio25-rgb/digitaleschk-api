import os
import braintree
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Conectamos con Braintree usando las llaves de tu Sandbox guardadas en Render
gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        environment=braintree.Environment.Sandbox,
        merchant_id=os.environ.get("BT_MERCHANT_ID"),
        public_key=os.environ.get("BT_PUBLIC_KEY"),
        private_key=os.environ.get("BT_PRIVATE_KEY")
    )
)

# Estructura de los datos de la tarjeta que recibirá la API
class CardCheckRequest(BaseModel):
    card_number: str
    expiration_month: str
    expiration_year: str
    cvv: str

@app.post("/check-card")
async def check_card(data: CardCheckRequest):
    try:
        # Intentamos procesar la transacción de prueba en Braintree por $1.00 USD
        result = gateway.transaction.sale({
            "amount": "1.00",
            "credit_card": {
                "number": data.card_number,
                "expiration_month": data.expiration_month,
                "expiration_year": data.expiration_year,
                "cvv": data.cvv
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
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
