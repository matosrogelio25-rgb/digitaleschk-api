import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import stripe

app = FastAPI()

stripe.api_key = os.getenv("STRIPE_API_KEY")


class CardRequest(BaseModel):
  card: str
  gate: str


class MassCardRequest(BaseModel):
  cards: list[str]
  gate: str


# --- GATE 1: CC CHARGED (/chk - $1.00 USD) ---
@app.post("/api/v1/charge")
def procesar_chk(data: CardRequest):
  try:
    partes = data.card.split("|")
    if len(partes) != 4:
      raise HTTPException(status_code=400, detail="Formato inválido")
    numero, mes, anio, cvv = partes

    # Crear el PaymentMethod primero para evitar el bloqueo de Stripe
    pm = stripe.PaymentMethod.create(
        type="card",
        card={
            "number": numero,
            "exp_month": int(mes),
            "exp_year": int(anio),
            "cvc": cvv,
        },
    )

    # Crear el PaymentIntent usando el método de pago creado
    intent = stripe.PaymentIntent.create(
        amount=100,
        currency="usd",
        payment_method=pm.id,
        confirm=True,
        off_session=True,
    )

    if intent.status == "succeeded":
      return {
          "status": "success",
          "message": "success",
          "response": "Approved ✅ [Charged $1.00 USD]",
      }
    else:
      return {
          "status": "declined",
          "message": "declined",
          "response": f"Declined ❌ [Estado: {intent.status}]",
      }
  except stripe.error.CardError as e:
    err = e.error
    return {
        "status": "declined",
        "message": "declined",
        "response": f"Declined ❌ [{err.decline_code or err.code}: {err.message}]",
    }
  except Exception as e:
    return {
        "status": "error",
        "message": "declined",
        "response": f"Error ❌ [{str(e)}]",
    }


# --- GATE 2: CCN AUTH (/ccn - $0 USD) ---
@app.post("/api/v1/ccn-auth")
def procesar_ccn(data: CardRequest):
  try:
    partes = data.card.split("|")
    if len(partes) != 4:
      raise HTTPException(status_code=400, detail="Formato inválido")
    numero, mes, anio, cvv = partes

    stripe.PaymentMethod.create(
        type="card",
        card={
            "number": numero,
            "exp_month": int(mes),
            "exp_year": int(anio),
            "cvc": cvv,
        },
    )
    return {
        "status": "success",
        "message": "success",
        "response": "Approved ✅ [Auth $0 - Verificada]",
    }
  except stripe.error.CardError as e:
    err = e.error
    return {
        "status": "declined",
        "message": "declined",
        "response": f"Declined ❌ [{err.decline_code or err.code}: {err.message}]",
    }
  except Exception as e:
    return {
        "status": "error",
        "message": "declined",
        "response": f"Error ❌ [{str(e)}]",
    }


# --- GATE 3: PAYPAL CHARGED (/pp - $5.00 USD) ---
@app.post("/api/v1/paypal-charge")
def procesar_pp(data: CardRequest):
  try:
    partes = data.card.split("|")
    if len(partes) != 4:
      raise HTTPException(status_code=400, detail="Formato inválido")
    numero, mes, anio, cvv = partes

    pm = stripe.PaymentMethod.create(
        type="card",
        card={
            "number": numero,
            "exp_month": int(mes),
            "exp_year": int(anio),
            "cvc": cvv,
        },
    )

    intent = stripe.PaymentIntent.create(
        amount=500,
        currency="usd",
        payment_method=pm.id,
        confirm=True,
        off_session=True,
    )

    if intent.status == "succeeded":
      return {
          "status": "success",
          "message": "success",
          "response": "Approved ✅ [PayPal Charged $5.00 USD]",
      }
    else:
      return {
          "status": "declined",
          "message": "declined",
          "response": f"Declined ❌ [Estado: {intent.status}]",
      }
  except stripe.error.CardError as e:
    err = e.error
    return {
        "status": "declined",
        "message": "declined",
        "response": f"Declined ❌ [{err.decline_code or err.code}: {err.message}]",
    }
  except Exception as e:
    return {
        "status": "error",
        "message": "declined",
        "response": f"Error ❌ [{str(e)}]",
    }


# --- GATE 4: MASIVOS (/mdgt, /mdccn, /mdpp) ---
@app.post("/api/v1/mass-process")
def procesar_masivo(data: MassCardRequest):
  resultados = []
  for card in data.cards:
    try:
      partes = card.split("|")
      if len(partes) != 4:
        resultados.append(
            {"card": card, "status": "declined", "response": "Format Error"}
        )
        continue
      numero, mes, anio, cvv = partes
      monto = 500 if "pp" in data.gate else (100 if "gt" in data.gate else 0)

      if monto > 0:
        pm = stripe.PaymentMethod.create(
            type="card",
            card={
                "number": numero,
                "exp_month": int(mes),
                "exp_year": int(anio),
                "cvc": cvv,
            },
        )
        intent = stripe.PaymentIntent.create(
            amount=monto,
            currency="usd",
            payment_method=pm.id,
            confirm=True,
            off_session=True,
        )
        if intent.status == "succeeded":
          resultados.append(
              {
                  "card": card,
                  "status": "success",
                  "message": "success",
                  "response": "Approved ✅",
              }
          )
        else:
          resultados.append(
              {
                  "card": card,
                  "status": "declined",
                  "message": "declined",
                  "response": f"Declined ❌ [Estado: {intent.status}]",
              }
          )
      else:
        stripe.PaymentMethod.create(
            type="card",
            card={
                "number": numero,
                "exp_month": int(mes),
                "exp_year": int(anio),
                "cvc": cvv,
            },
        )
        resultados.append(
            {
                "card": card,
                "status": "success",
                "message": "success",
                "response": "Approved ✅",
            }
        )

    except stripe.error.CardError as e:
      err = e.error
      resultados.append(
          {
              "card": card,
              "status": "declined",
              "message": "declined",
              "response": (
                  f"Declined ❌ [{err.decline_code or err.code}:"
                  f" {err.message}]"
              ),
          }
      )
    except Exception as e:
      resultados.append(
          {
              "card": card,
              "status": "error",
              "message": "declined",
              "response": f"Error ❌ [{str(e)}]",
          }
      )
  return {"results": resultados}
