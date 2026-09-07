"""Flujo:
  1. Crear un caso de importación con chat
  2. Subir Factura, Packing List y Bill of Lading.
  3. Procesar documentos (extraer campos -> JSON del caso).
  4. Ver validación (DAM(verde/amarillo/rojo)) y las comparaciones cruzadas.
  5. Editar/confirmar campos manualmente.
  6. Ver el % de "Preparación DAM".
  7. Preview final y botón "GENERAR EXCEL".

Todo el estado del caso guardarlo en un archivo JSON"""
import json
import os
import shutil
import uuid #Universally Unique Identifier
from datetime import datetime

import streamlit as st

from modulos import lector, extractor, validador, generator_excel

st.set_page_config(
    page_title="DAMIX",
    page_icon="📄",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARPETA_CASOS = os.path.join(BASE_DIR, "datos", "casos")
CARPETA_DOCUMENTOS = os.path.join(BASE_DIR, "datos", "documentos")
CARPETA_OUTPUT = os.path.join(BASE_DIR, "datos", "output")
RUTA_PLANTILLA = os.path.join(BASE_DIR, "plantilla", "plantilla_DAM.xlsx")
RUTA_LOGO = os.path.join(BASE_DIR, "imagenes", "logo.png")

os.makedirs(CARPETA_CASOS, exist_ok=True)
os.makedirs(CARPETA_DOCUMENTOS, exist_ok=True)
os.makedirs(CARPETA_OUTPUT, exist_ok=True)

generator_excel.crear_plantilla_ejemplo(RUTA_PLANTILLA)


types_doc = {
    "factura": "Factura comercial",
    "packing_list": "Packing List",
    "bill_of_lading": "Bill of Lading",
    "seguro": "Certificado de Seguro",
}
Colors_DAM = {
    "verde": "🟢",
    "amarillo":"🟡",
    "rojo":"🔴",
}
#JSON
def ruta_json_caso(id_caso: str):
    return os.path.join(CARPETA_CASOS, f"{id_caso}.json") #falta crear mas para el json

def guardar_caso(datos_caso: dict) -> None:
    with open(ruta_json_caso(datos_caso["id_caso"]), "w", encoding="utf-8") as f: #explote auidaaa, ya no hago mas a mimir 
        json.dump(datos_caso, f, ensure_ascii=False, indent=2)

def cargar_caso(id_caso: str) -> dict:
    with open(ruta_json_caso(id_caso), "r", encoding="utf-8") as f:
        return json.load(f)

def listar_casos() -> list:
    if not os.path.exists(CARPETA_CASOS):
        return []
    archivos = [f for f in os.listdir(CARPETA_CASOS) if f.endswith(".json")]
    return sorted(archivos)

def crear_caso_nuevo(nombre_caso: str) -> dict:
    id_caso = f"CASO_{uuid.uuid4().hex[:8].upper()}"
    datos_caso = {
        "id_caso": id_caso,
        "nombre_caso": nombre_caso,
        "creado": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "documentos": {},          # se llena al procesar cada documento
        "campos_confirmados": [],  # claves tipo "factura.ruc" o "comparacion.Peso bruto"
    }
    guardar_caso(datos_caso)
    return datos_caso

def eliminar_caso(id_caso: str) -> None:
    ruta_json = ruta_json_caso(id_caso)
    if os.path.exists(ruta_json):
        os.remove(ruta_json)

    carpeta_docs_caso = os.path.join(CARPETA_DOCUMENTOS, id_caso)
    if os.path.exists(carpeta_docs_caso):
        shutil.rmtree(carpeta_docs_caso)


#Config de la Web?
st.image(RUTA_LOGO, width=220)

st.caption(
    "Asistente de preparación documental previa a la DAM de importación"
)

if "id_caso_actual" not in st.session_state:
    st.session_state.id_caso_actual = None

#el sidebar subir imagens/ crear caso
with st.sidebar:
    st.header("Gestion de casos")

    with st.form("crear_caso_form"):
        nombre_nuevo_caso = st.text_input("Nombre del caso: ", placeholder= "Ej: Importacion de X")
        crear = st.form_submit_button("Crear caso")
        if crear and nombre_nuevo_caso.strip():
            nuevo = crear_caso_nuevo(nombre_nuevo_caso.strip())
            st.session_state.id_caso_actual = nuevo["id_caso"]
            st.rerun()

        st.divider()
    
    st.subheader("Casos existentes")

    archivos_casos = listar_casos()
    if not archivos_casos:
        st.info("No hay casos existentes. Crea uno nuevo.")
    else:
        for archivo_caso in archivos_casos:
            id_caso_item = archivo_caso.replace(".json", "")
            caso_item = cargar_caso(id_caso_item)
            num_docs = len(caso_item.get("documentos", {}))
            etiqueta = f" {caso_item['nombre_caso']} · {num_docs} docs"
            if st.button(etiqueta, key=f"btn_{id_caso_item}", use_container_width=True):
                st.session_state.id_caso_actual = id_caso_item
                st.rerun()
            st.caption(f"Creado: {caso_item.get('creado', '—')}")

    if st.session_state.id_caso_actual:
        st.divider()
        st.subheader("Eliminar caso actual")
        caso_a_eliminar = cargar_caso(st.session_state.id_caso_actual)
        st.caption(f"Caso seleccionado: {caso_a_eliminar['nombre_caso']}")

        if "confirmar_borrado" not in st.session_state:
            st.session_state.confirmar_borrado = False

        if not st.session_state.confirmar_borrado:
            if st.button("Eliminar caso", key="btn_eliminar_caso"):
                st.session_state.confirmar_borrado = True
                st.rerun()
        else:
            st.warning(
                f"¿Seguro que quieres eliminar '{caso_a_eliminar['nombre_caso']}'? "
                "Esta acción no se puede deshacer."
            )
            col_si, col_no = st.columns(2)
            with col_si:
                if st.button("Sí, eliminar", key="btn_confirmar_eliminar"):
                    eliminar_caso(st.session_state.id_caso_actual)
                    st.session_state.id_caso_actual = None
                    st.session_state.confirmar_borrado = False
                    st.rerun()
            with col_no:
                if st.button("Cancelar", key="btn_cancelar_eliminar"):
                    st.session_state.confirmar_borrado = False
                    st.rerun()

#si no hay enviar este mensaje y stop.

if not st.session_state.id_caso_actual:
    st.info("Crea o selecciona un caso en la barra lateral para comenzar.")
    st.stop()

datos_caso = cargar_caso(st.session_state.id_caso_actual)

st.subheader(f"Caso: {datos_caso['nombre_caso']}  ·  `{datos_caso['id_caso']}`")

# Resumen del caso — todo calculado con datos que ya existen en datos_caso
_documentos_caso = datos_caso.get("documentos", {})
_campos_encontrados = sum(len(doc.get("datos", {})) for doc in _documentos_caso.values())
_campos_confirmados = len(datos_caso.get("campos_confirmados", []))
_porcentaje_resumen = validador.calcular_preparacion_dam(datos_caso)

col_r1, col_r2, col_r3, col_r4 = st.columns(4)
col_r1.metric("Documentos procesados", len(_documentos_caso))
col_r2.metric("Campos encontrados", _campos_encontrados)
col_r3.metric("Campos confirmados", _campos_confirmados)
col_r4.metric("Preparación DAM", f"{_porcentaje_resumen}%")

#Ahora viene lo chido xd | Paso 1: Subir los documentos

st.markdown("Paso 1: Subir documentos")

columnas = st.columns(4)
carpeta_docs_caso = os.path.join(CARPETA_DOCUMENTOS, datos_caso["id_caso"])

for columna, tipo_doc in zip(columnas, types_doc.keys()):
    with columna:
        st.markdown(f"**{types_doc[tipo_doc]}**")
        archivo_subido = st.file_uploader(
            f"Subir {types_doc[tipo_doc]}",
            type=["pdf"],
            key=f"upload_{tipo_doc}",
            label_visibility="collapsed",
        )

        if archivo_subido is not None:
            ruta_guardada = lector.guardar_archivo_subido(archivo_subido, carpeta_docs_caso)
            st.success(f"Guardado: {archivo_subido.name}")

            # Guardar la ruta pendiente de procesar!!
            datos_caso.setdefault("documentos_pendientes", {})[tipo_doc] = ruta_guardada
            guardar_caso(datos_caso)

        if tipo_doc in datos_caso.get("documentos", {}):
            st.caption("Procesado")
        elif tipo_doc in datos_caso.get("documentos_pendientes", {}):
            st.caption("Subido, falta procesar")
        else:
            st.caption("— Sin subir")

st.divider()

#Paso 2 - procesar docs
st.markdown("2. Procesar documentos")

st.write("DEBUG pendientes:", datos_caso.get("documentos_pendientes", {}))

if st.button("Procesar documentos subidos", type="primary"):
    pendientes = datos_caso.get("documentos_pendientes", {})
    if not pendientes:
        st.warning("No hay documentos nuevos para procesar.")
    else:
        pendientes_restantes = dict(pendientes)
        for tipo_doc, ruta_doc in pendientes.items():
            texto = lector.leer_texto_pdf(ruta_doc)
            datos_extraidos = extractor.extraer_datos(tipo_doc, texto, os.path.basename(ruta_doc))
            datos_caso.setdefault("documentos", {})[tipo_doc] = {
                "archivo": os.path.basename(ruta_doc),
                "datos": datos_extraidos,
            }
            pendientes_restantes.pop(tipo_doc, None)

        datos_caso["documentos_pendientes"] = pendientes_restantes
        guardar_caso(datos_caso)
        st.success("Documentos procesados correctamente.")
        st.rerun()


# Si todavía no hay ningún doc procesado, no seguir.
if not datos_caso.get("documentos"):
    st.info("Sube y procesa al menos un documento para continuar.")
    st.stop()

st.divider()

#VALIDACION? PASO 3
st.markdown("3. Validación de campos obligatorios")

validaciones_campos = validador.validar_campos_obligatorios(datos_caso)

for tipo_doc in datos_caso["documentos"]:
    with st.expander(f"{types_doc[tipo_doc]}", expanded=True):
        datos_doc = datos_caso["documentos"][tipo_doc]["datos"]
        for campo, valor in datos_doc.items():
            clave = f"{tipo_doc}.{campo}"
            estado = validaciones_campos.get(clave, "rojo")
            confirmado = clave in datos_caso.get("campos_confirmados", [])

            col_valor, col_estado, col_accion = st.columns([3, 1, 2])
            with col_valor:
                nuevo_valor = st.text_input(
                    campo.replace("_", " ").capitalize(),
                    value=str(valor),
                    key=f"input_{tipo_doc}_{campo}",
                )
                if str(nuevo_valor) != str(valor):
                    datos_caso["documentos"][tipo_doc]["datos"][campo] = nuevo_valor
                    guardar_caso(datos_caso)
            with col_estado:
                st.markdown(f"<br>{Colors_DAM.get(estado, '?')} {estado}", unsafe_allow_html=True)
            with col_accion:
                st.markdown("<br>", unsafe_allow_html=True)
                if not confirmado:
                    if st.button("Confirmar", key=f"confirmar_{tipo_doc}_{campo}"):
                        datos_caso.setdefault("campos_confirmados", []).append(clave)
                        guardar_caso(datos_caso)
                        st.rerun()
                else:
                    st.caption("Confirmado por el usuario")

if st.button("CONFIRMAR TODOS LOS CAMPOS", key="btn_confirmar_todos"):
    campos_confirmados = datos_caso.setdefault("campos_confirmados", [])
    for tipo_doc_c, info_doc_c in datos_caso.get("documentos", {}).items():
        for campo_c, valor_c in info_doc_c.get("datos", {}).items():
            if valor_c is None or valor_c == "":
                continue  # no confirmar campos vacíos
            clave_c = f"{tipo_doc_c}.{campo_c}"
            if clave_c not in campos_confirmados:
                campos_confirmados.append(clave_c)
    guardar_caso(datos_caso)
    st.success("Todos los campos con datos fueron confirmados.")
    st.rerun()

st.markdown("4. Comparación entre documentos")

comparaciones = validador.comparar_documentos(datos_caso)

if not comparaciones:
    st.info("Todavía no hay suficientes documentos en común para comparar campos.")
else:
    for comparacion in comparaciones:
        estado = comparacion["estado"]
        clave_comparacion = f"comparacion.{comparacion['campo']}"
        confirmado = clave_comparacion in datos_caso.get("campos_confirmados", [])

        with st.container(border=True):
            col_info, col_accion = st.columns([4, 1])
            with col_info:
                st.markdown(f"{Colors_DAM.get(estado, '?')} **{comparacion['mensaje']}**")
                for nombre_doc, valor_doc in comparacion["documentos"].items():
                    st.caption(f"- {nombre_doc}: {valor_doc}")
            with col_accion:
                if estado != "verde" and not confirmado:
                    if st.button("Confirmar", key=f"confirmar_{clave_comparacion}"):
                        datos_caso.setdefault("campos_confirmados", []).append(clave_comparacion)
                        guardar_caso(datos_caso)
                        st.rerun()
                elif confirmado:
                    st.caption("Confirmado")

st.divider()

#Prep para la DAM
porcentaje = validador.calcular_preparacion_dam(datos_caso)
st.markdown("5. Preparación DAM")
st.progress(porcentaje / 100)
st.markdown(f"Preparación DAM: **{porcentaje}%**")

if porcentaje < 100:
    st.caption("El porcentaje sube al completar campos faltantes, resolver inconsistencias o confirmarlas manualmente.")

st.divider()

#PREVIEW FINAL? Y GENERAR EXCEL




#GENERAR EL EXCEL
st.markdown("7. Generar Excel de la DAM")

if porcentaje < 100:
    st.warning("Todavía hay campos pendientes de revisión. Puedes generar el Excel de todas formas, "
               "pero se recomienda revisar los elementos en AMARILLO o ROJO primero.")

if st.button("GENERAR EXCEL", type="primary"):
    try:
        ruta_generada = generator_excel.generar_excel(datos_caso, RUTA_PLANTILLA, CARPETA_OUTPUT)
        st.success(f"Excel generado correctamente: {os.path.basename(ruta_generada)}")
        with open(ruta_generada, "rb") as f:
            st.download_button(
                "Descargar DAM_GENERADA.xlsx",
                data=f.read(),
                file_name="DAM_GENERADA.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    except Exception as error:
        st.error(f"No se pudo generar el Excel: {error}")