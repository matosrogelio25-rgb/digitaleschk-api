import os
import braintree
from fastapi import FastAPI, HTTPException, Request

app = FastAPI()

# Conectamos con Braintree usando las llaves de entorno configuradas en Render
gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        environment=braintree.Environment.Sandbox,
        merchant_id=os.environ.get("BT_MERCHANT_ID"),
        public_key=os.environ.get("BT_PUBLIC_KEY"),
        private_key=os.environ.get("BT_PRIVATE_KEY")
    )
)

async def manejar_peticion_tarjeta(request: Request):
    try:
        body = await request.json()
        print("DATOS RECIBIDOS DEL BOT:", body) # Esto aparecerá en los logs de Render
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo JSON: {str(e)}")

    # Extraemos los campos buscando múltiples variantes posibles enviadas por el bot
    num = body.get("card_number") or body.get("cc_number") or body.get("number")
    mes = body.get("expiration_month") or body.get("exp_month") or body.get("mes")
    anio = body.get("expiration_year") or body.get("exp_year") or body.get("anio") or body.get("year")
    cvv_val = body.get("cvv") or body.get("cvc")

    if not all([num, mes, anio, cvv_val]):
        print(f"FALTAN DATOS. Cuerpo recibido: {body}")
        raise HTTPException(status_code=400, detail=f"Faltan datos de la tarjeta. Recibido: {body}")

    try:
        result = gateway.transaction.sale({
            "amount": "1.00",
            "credit_card": {
                "number": str(num).strip(),
                "expiration_month": str(mes).strip(),
                "expiration_year": str(anio).strip(),
                "cvv": str(cvv_val).strip()
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
    except Exception as err:
        print(f"Error procesando en Braintree: {str(err)}")
        raise HTTPException(status_code=500, detail=str(err))

@app.post("/check-card")
@app.post("/api/v1/charge")
@app.post("/api/v1/ccn-auth")
@app.post("/charge")
@app.post("/ccn-auth")
async def check_card_alias(request: Request):
    return await manejar_peticion_tarjeta(request)
