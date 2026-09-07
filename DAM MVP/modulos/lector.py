import os
import pdfplumber


def leer_texto_pdf(ruta_archivo: str) -> str:
    
    if not os.path.exists(ruta_archivo):
        return ""

    texto_completo = []
    try:
        with pdfplumber.open(ruta_archivo) as pdf:
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_completo.append(texto_pagina)
    except Exception as error:
        # Si hacemos nueva versión, aquí se podría salir error!!
        print(f"[lector.py] No se pudo leer el PDF '{ruta_archivo}': {error}")
        return ""

    return "\n".join(texto_completo)


def guardar_archivo_subido(archivo_subido, carpeta_destino: str) -> str:
    
    os.makedirs(carpeta_destino, exist_ok=True)
    ruta_destino = os.path.join(carpeta_destino, archivo_subido.name)

    with open(ruta_destino, "wb") as f:
        f.write(archivo_subido.getbuffer())

    return ruta_destino