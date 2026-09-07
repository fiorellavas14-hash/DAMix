import re

# Campos obligatorios por tipo de documento.

CAMPOS_OBLIGATORIOS = {
    "factura": [
        "numero_factura",
        "importador",
        "ruc",
        "pais_origen",
        "valor_fob",
        "moneda",
        "incoterm",
    ],
    "packing_list": [
        "numero_bultos",
        "peso_neto",
        "peso_bruto",
    ],
    "bill_of_lading": [
        "numero_bl",
        "puerto_carga",
        "puerto_descarga",
        "peso_bruto",
        "consignatario",
    ],
    "seguro": [
        "numero_certificado",
        "asegurado",
        "suma_asegurada",
        "moneda",
    ],
}

TOLERANCIA_AMARILLO_KG = 5
TOLERANCIA_ROJO_KG = 5  # por encima de esto, es rojo


def _campo_presente(datos_documento: dict, campo: str) -> bool:
    valor = datos_documento.get(campo) if datos_documento else None
    return valor is not None and valor != ""


def normalizar_texto(valor) -> str:
    """Deja el texto en mayúsculas, sin puntos/comas y sin espacios duplicados,
    para poder comparar 'Camioncito Azul SAC' con 'CAMIONCITO AZUL S.A.C.'"""
    if valor is None:
        return ""
    texto = str(valor).upper()
    texto = texto.replace(".", "").replace(",", "")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def validar_campos_obligatorios(datos_caso: dict) -> dict:
    resultados = {}
    documentos = datos_caso.get("documentos", {})

    for tipo_doc, campos in CAMPOS_OBLIGATORIOS.items():
        if tipo_doc not in documentos:
            continue  # el documento aún no fue subido o procesado
        datos_doc = documentos[tipo_doc].get("datos", {})
        for campo in campos:
            clave = f"{tipo_doc}.{campo}"
            resultados[clave] = "verde" if _campo_presente(datos_doc, campo) else "rojo"

    return resultados

# Reglas de comparación cruzada

REGLAS_COMPARACION = [
    {
        "etiqueta": "Peso bruto",
        "doc_a": "packing_list", "campo_a": "peso_bruto",
        "doc_b": "bill_of_lading", "campo_b": "peso_bruto",
        "tipo": "numero",
    },
    {
        "etiqueta": "Consignatario / Importador",
        "doc_a": "bill_of_lading", "campo_a": "consignatario",
        "doc_b": "factura", "campo_b": "importador",
        "tipo": "texto",
    },
    {
        "etiqueta": "Número de factura",
        "doc_a": "factura", "campo_a": "numero_factura",
        "doc_b": "seguro", "campo_b": "numero_factura",
        "tipo": "texto",
    },
    {
        "etiqueta": "Número de Bill of Lading",
        "doc_a": "bill_of_lading", "campo_a": "bl/number",
        "doc_b": "seguro", "campo_b": "bl/number",
        "tipo": "texto",
    },
    {
        "etiqueta": "Asegurado / Importador",
        "doc_a": "seguro", "campo_a": "asegurado",
        "doc_b": "factura", "campo_b": "importador",
        "tipo": "texto",
    },
    # NO se agrega aquí "suma_asegurada" vs "valor_total": son conceptos
    # distintos y no deben tratarse como el mismo dato.
]


def _comparar_texto(valor_a, valor_b) -> str:
    return "verde" if normalizar_texto(valor_a) == normalizar_texto(valor_b) else "rojo"


def _comparar_numero(valor_a, valor_b) -> str:
    try:
        diferencia = abs(float(valor_a) - float(valor_b))
    except (TypeError, ValueError):
        return "rojo"
    if diferencia == 0:
        return "verde"
    elif diferencia <= TOLERANCIA_AMARILLO_KG:
        return "amarillo"
    return "rojo"


def comparar_documentos(datos_caso: dict) -> list:
    documentos = datos_caso.get("documentos", {})
    comparaciones = []

    def obtener(tipo_doc, campo):
        return documentos.get(tipo_doc, {}).get("datos", {}).get(campo)

    for regla in REGLAS_COMPARACION:
        # Si falta alguno de los dos documentos en el caso, no comparamos.
        if regla["doc_a"] not in documentos or regla["doc_b"] not in documentos:
            continue

        valor_a = obtener(regla["doc_a"], regla["campo_a"])
        valor_b = obtener(regla["doc_b"], regla["campo_b"])

        # Si el campo puntual no fue extraído en alguno de los dos, tampoco.
        if valor_a is None or valor_b is None:
            continue

        if regla["tipo"] == "numero":
            estado = _comparar_numero(valor_a, valor_b)
            texto_a, texto_b = f"{valor_a} kg", f"{valor_b} kg"
        else:
            estado = _comparar_texto(valor_a, valor_b)
            texto_a, texto_b = str(valor_a), str(valor_b)

        comparaciones.append({
            "campo": regla["etiqueta"],
            "documentos": {
                f"{regla['doc_a']} ({regla['campo_a']})": texto_a,
                f"{regla['doc_b']} ({regla['campo_b']})": texto_b,
            },
            "estado": estado,
            "mensaje": f"{regla['etiqueta']} consistente" if estado == "verde"
                       else f"{regla['etiqueta']} inconsistente",
        })

    return comparaciones



def calcular_preparacion_dam(datos_caso: dict) -> int:
    documentos = datos_caso.get("documentos", {})
    campos_confirmados = datos_caso.get("campos_confirmados", [])

    validaciones_campos = validar_campos_obligatorios(datos_caso)
    comparaciones = comparar_documentos(datos_caso)

    total_elementos = 0
    puntos = 0.0

    # Puntaje por campos obligatorios
    for clave, estado in validaciones_campos.items():
        total_elementos += 1
        if clave in campos_confirmados:
            puntos += 1
        elif estado == "verde":
            puntos += 1
        elif estado == "amarillo":
            puntos += 0.5
        # rojo = 0 puntos

    #Puntaje por comparaciones cruzadas
    for comparacion in comparaciones:
        total_elementos += 1
        clave_comparacion = f"comparacion.{comparacion['campo']}"
        if clave_comparacion in campos_confirmados:
            puntos += 1
        elif comparacion["estado"] == "verde":
            puntos += 1
        elif comparacion["estado"] == "amarillo":
            puntos += 0.5

    # Si todavía no hay ningún documento subido, el % es 0
    if not documentos or total_elementos == 0:
        return 0

    porcentaje = round((puntos / total_elementos) * 100)
    return porcentaje


def resumen_estado_general(datos_caso: dict) -> str:
    validaciones_campos = validar_campos_obligatorios(datos_caso)
    comparaciones = comparar_documentos(datos_caso)

    estados = list(validaciones_campos.values()) + [c["estado"] for c in comparaciones]

    if not estados:
        return "rojo"
    if "rojo" in estados:
        return "rojo"
    if "amarillo" in estados:
        return "amarillo"
    return "verde"
