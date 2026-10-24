# DAMix 📄🔍

Prototipo de una plataforma de preauditoría documental para comercio exterior, desarrollado como propuesta para Disrupton 2026.

## El problema

Antes de preparar una Declaración Aduanera de Mercancías (DAM), es necesario revisar información distribuida en distintos documentos.

Cuando esta revisión se realiza manualmente, identificar diferencias, datos faltantes o inconsistencias puede consumir tiempo y generar errores.

## La propuesta

DAMix busca reunir esa revisión en un solo flujo:

1. Cargar los documentos de una operación.
2. Extraer y organizar sus datos.
3. Comparar la información entre documentos.
4. Señalar posibles inconsistencias.
5. Presentar los resultados para que un especialista los revise.

El objetivo es apoyar el trabajo del especialista y facilitar la preparación de información antes de continuar con el despacho.

## Alcance

DAMix está planteado como una herramienta complementaria a los sistemas de gestión de comercio exterior.

No realiza declaraciones ante SUNAT ni reemplaza el criterio profesional del especialista.

## Tecnologías

- **Python:** desarrollo y procesamiento de información.
- **Ollama:** exploración de modelos de lenguaje ejecutados localmente.

## Estructura del proyecto

- `modulos/`: componentes de la aplicación.
- `plantilla/`: plantillas utilizadas por el prototipo.
- `imagenes/`: recursos visuales.
- `main.py`: punto de entrada de la aplicación.

## Estado actual

🚧 **Prototipo / MVP en desarrollo.**

Este repositorio documenta la implementación inicial. El flujo descrito representa el alcance propuesto; las funciones requieren pruebas y validación antes de utilizarse en operaciones reales.

## Aprendizajes y retos

- Procesar documentos con formatos diferentes.
- Estructurar información para comparar datos.
- Explorar el uso de IA local en la revisión documental.
- Comunicar hallazgos de manera clara y verificable.


Proyecto independiente presentado como propuesta para Disrupton 2026. No es una herramienta oficial de SUNAT.
Prototype / MVP
