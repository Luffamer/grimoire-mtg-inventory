# 📖 Grimoire MTG - Inventario de Cartas

Una aplicación de escritorio desarrollada en **Python** para gestionar colecciones masivas de cartas de *Magic: The Gathering*.

## ✨ Características Principales
* **Búsqueda en Tiempo Real:** Autocompletado integrado conectándose a la base de datos local al instante.
* **Conexión con Scryfall API:** Descarga de datos, colores, ediciones y carátulas de las cartas en tiempo real al añadir nuevas entradas.
* **Sistema anti-baneo:** Implementación de hilos (threading) y temporizadores (debounce) para consumir la API de forma segura y fluida.
* **Gestión de Cajas:** Organización física del inventario mediante cajas desplegables.
* **Mantenimiento:** Herramientas para rastrear IDs, mover copias entre cajas o purgar registros.

## 🛠️ Tecnologías Utilizadas
* **Lenguaje:** Python 3
* **Interfaz Gráfica:** CustomTkinter (CTk)
* **Base de Datos:** SQLite
* **Peticiones HTTP:** Requests (Scryfall API)
* **Procesamiento de Imágenes:** Pillow (PIL)

## 🚀 Cómo ejecutarlo
Si quieres ejecutar el código fuente directamente:
1. Clona este repositorio.
2. Instala las dependencias necesarias: `pip install customtkinter requests pillow`
3. Asegúrate de tener los archivos `logo_grimoire.png` y `coleccion_mtg.db` en la misma carpeta.
4. Ejecuta el archivo principal: `python interfaz.py`

*(También puedes compilar tu propio .exe usando PyInstaller).*
