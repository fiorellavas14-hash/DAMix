import random
import json
import requests

MODO_MOCK = False

MODELO_OLLAMA = "qwen3:4b"
OLLAMA_URL = "http://localhost:11434/api/generate"


#factura comercial

def extraer_factura(texto: str, nombre_archivo: str = "") -> dict: #extraer los campos de la factura
    
    if MODO_MOCK:
        return {
            "numero_factura": "INV-2026-00873",
            "importador": "COMERCIAL ANDINA SAC",
            "ruc": "20601234567",
            "pais_origen": "China",
            "valor_fob": 18500.00,
            "moneda": "USD",
            "incoterm": "FOB",
        }

#Conexion con la IA para extraer los campos de la factura
    return extraer_con_ia(texto, tipo_documento="factura")

#Packing list

def extraer_packing_list(texto: str, nombre_archivo: str = "") -> dict: #extraer los campos

    if MODO_MOCK:
        return {
            "numero_bultos": 120,
            "peso_neto": 5450.0,
            "peso_bruto": 5820.0,
        }

    return extraer_con_ia(texto, tipo_documento="packing_list")

#Bill of landing
def extraer_bill_of_lading(texto: str, nombre_archivo: str = "") -> dict:
    
    if MODO_MOCK:
        return {
            "puerto_origen": "Shanghai",
            "puerto_destino": "Callao",
            "peso_bruto": 5280.0,   #A propósito distinto al Packing List
            "consignatario": "COMERCIAL ANDINA SAC",
        }

    return extraer_con_ia(texto, tipo_documento="bill_of_lading")

#Certificado / Póliza de seguro de carga
def extraer_seguro(texto: str, nombre_archivo: str = "") -> dict:

    if MODO_MOCK:
        return {
            "numero_certificado": "2026-58187",
            "asegurado": "COMERCIAL ANDINA SAC",
            "suma_asegurada": 4954.84,
            "moneda": "EUR",
            "numero_factura": "116167",
            "numero_bl": "26-2155",
        }

    return extraer_con_ia(texto, tipo_documento="seguro")


#Decide que extractor usar 
EXTRACTORES = {
    "factura": extraer_factura,
    "packing_list": extraer_packing_list,
    "bill_of_lading": extraer_bill_of_lading,
    "seguro": extraer_seguro,
}

#Recibe el tipo de documento y su texto, y devuelve el dic de campos extraídos.
    
def extraer_datos(tipo_documento: str, texto: str, nombre_archivo: str = "") -> dict:
    
    funcion = EXTRACTORES.get(tipo_documento)
    if funcion is None:
        raise ValueError(f"Tipo de documento no soportado: {tipo_documento}")
    return funcion(texto, nombre_archivo)

# Conexion con la IA
def extraer_con_ia(texto: str, tipo_documento: str) -> dict:

    if tipo_documento == "factura":
        campos = """
        {
            "numero_factura": null,
            "fecha_factura": null,
            "importador": null,
            "exportador": null,
            "ruc": null,
            "pais_origen": null,
            "pais_procedencia": null,
            "incoterm": null,
            "moneda": null,
            "valor_fob": null,
            "valor_total": null,
            "flete": null,
            "seguro": null,
            "descripcion_mercancia": null,
            "numero_bultos": null,
            "peso_bruto": null,
            "peso_neto": null
        }
        """

    elif tipo_documento == "packing_list":
        campos = """
        {
            "numero_bultos": null,
            "tipo_bultos": null,
            "peso_neto": null,
            "peso_bruto": null,
            "unidad_peso": null,
            "volumen": null,
            "descripcion_mercancia": null,
            "pais_origen": null
        }
        """

    elif tipo_documento == "bill_of_lading":
        campos = """
        {
            "numero_bl": null,
            "numero_awb": null,
            "shipper": null,
            "consignatario": null,
            "notify_party": null,
            "buque": null,
            "viaje": null,
            "puerto_carga": null,
            "puerto_descarga": null,
            "lugar_recepcion": null,
            "lugar_entrega": null,
            "numero_contenedor": null,
            "numero_precinto": null,
            "peso_bruto": null,
            "volumen": null,
            "numero_bultos": null,
            "descripcion_mercancia": null
        }
        """

    elif tipo_documento == "seguro":
        campos = """
        {
            "numero_certificado": null,
            "numero_poliza": null,
            "asegurado": null,
            "beneficiario": null,
            "numero_factura": null,
            "numero_bl": null,
            "numero_awb": null,
            "suma_asegurada": null,
            "moneda": null,
            "prima_seguro": null,
            "fecha_emision": null,
            "fecha_salida": null,
            "buque": null,
            "viaje": null,
            "modo_transporte": null,
            "origen": null,
            "destino": null,
            "descripcion_mercancia": null,
            "tipo_cobertura": null,
            "compania_aseguradora": null,
            "agente_broker": null
        }
        """

    else:
        raise ValueError(f"Tipo de documento no soportado en extraer_con_ia: {tipo_documento}")

    prompt = f"""
Eres un asistente para extraer datos de documentos de importación.

Tipo de documento:
{tipo_documento}

Devuelve únicamente un JSON con esta estructura:

{campos}

Reglas:
- No inventes datos.
- Si un dato no aparece, usa null.
- Los pesos deben ser números.
- Los valores monetarios deben ser números.
- No escribas explicaciones.
- Devuelve solamente JSON válido.

Texto del documento:

{texto}
"""

    respuesta = requests.post(
        OLLAMA_URL,
        json={
            "model": MODELO_OLLAMA,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "think": False
        },
        timeout=300
    )

    respuesta.raise_for_status()

    resultado = respuesta.json()

    return json.loads(resultado["response"])