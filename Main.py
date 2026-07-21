import customtkinter as ctk
import sqlite3
import requests
import unicodedata
import threading
import os
import sys
import ctypes
from PIL import Image
from io import BytesIO

# --- CONFIGURACIÓN VISUAL Y COLORES DE FANTASÍA ---
ctk.set_appearance_mode("dark")  

C_FONDO_APP = "#1a211b"       
C_FONDO_PESTANAS = "#222c23"  
C_BOTON_VERDE = "#375932"     
C_BOTON_VERDE_HOVER = "#4d7c46" 
C_BOTON_MADERA = "#4a3927"    
C_BOTON_MADERA_HOVER = "#634c34"

# --- NUEVOS COLORES ---
C_MARRON_OSCURO = "#24160e"        # Marrón muy oscuro para las barras de texto y pestañas
C_MARRON_OSCURO_HOVER = "#382317"  # Para cuando pasas el ratón por la pestaña
C_GLOW_AZUL = "#3ca1e6"            # Azul mágico brillante para el aura

C_TEXTO_DORADO = "#d4b872"    
C_FONDO_CARTAS = "#2a362b"    

FUENTE_TITULO = ("Georgia", 48, "bold")
FUENTE_PESTANA = ("Georgia", 18, "bold")
FUENTE_BOTON = ("Georgia", 18, "bold")
FUENTE_TEXTO_GRANDE = ("Georgia", 18)
FUENTE_TEXTO_MEDIO = ("Georgia", 16)

class CajaDesplegable(ctk.CTkFrame):
    def __init__(self, master, nombre_caja, cartas):
        super().__init__(master, fg_color="transparent")
        self.desplegado = False
        
        self.btn_toggle = ctk.CTkButton(self, text=f"▶  📦 {nombre_caja.upper()}", anchor="w", 
                                        fg_color=C_BOTON_MADERA, hover_color=C_BOTON_MADERA_HOVER, 
                                        font=FUENTE_BOTON, height=50, command=self.toggle)
        self.btn_toggle.pack(fill="x", pady=(10, 0))
        
        self.frame_cartas = ctk.CTkFrame(self, fg_color=C_FONDO_CARTAS)
        for carta in cartas:
            ctk.CTkLabel(self.frame_cartas, text=carta, font=FUENTE_TEXTO_GRANDE, anchor="w", text_color="#e0e0e0").pack(fill="x", padx=20, pady=6)

    def toggle(self):
        if self.desplegado:
            self.frame_cartas.pack_forget()
            self.btn_toggle.configure(text=self.btn_toggle.cget("text").replace("▼", "▶"))
            self.desplegado = False
        else:
            self.frame_cartas.pack(fill="x", pady=(0, 5))
            self.btn_toggle.configure(text=self.btn_toggle.cget("text").replace("▶", "▼"))
            self.desplegado = True


class InventarioMagic(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Grimoire")
        self.geometry("1000x800")
        self.minsize(900, 700)
        self.configure(fg_color=C_FONDO_APP)

        # --- TRUCO MAESTRO PARA RUTAS (VS CODE Y .EXE) ---
        if getattr(sys, 'frozen', False):
            # Si el programa es un .exe compilado, busca en su misma carpeta real
            ruta_base = os.path.dirname(sys.executable)
        else:
            # Si lo estás ejecutando desde VS Code, busca en la carpeta del script
            ruta_base = os.path.dirname(os.path.abspath(__file__))
        # -------------------------------------------------

        # --- ELIMINAR EL CUADRADO AZUL (ICONO) ---
        try:
            ruta_icono = os.path.join(ruta_base, "icono.ico") # Usamos ruta_base
            self.iconbitmap(ruta_icono)
        except Exception as e:
            pass 
        # ----------------------------------------

        # --- TRUCO PARA CAMUFLAR LA BARRA DE WINDOWS 11 ---
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            color_fondo = C_FONDO_APP.lstrip('#') 
            r, g, b = tuple(int(color_fondo[i:i+2], 16) for i in (0, 2, 4))
            color_bgr = r | (g << 8) | (b << 16) 
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(ctypes.c_int(color_bgr)), 4)
        except:
            pass 
        # --------------------------------------------------

        # --- TÍTULO ÉPICO CON TU DIBUJO ---
        self.frame_titulo = ctk.CTkFrame(self, fg_color="transparent", height=120)
        self.frame_titulo.pack(pady=15, fill="x")
        
        try:
            ruta_imagen = os.path.join(ruta_base, "logo_grimoire.png") # Usamos ruta_base
            img_logo = Image.open(ruta_imagen)
            logo_ctk = ctk.CTkImage(light_image=img_logo, dark_image=img_logo, size=(450, 110))
            self.lbl_titulo = ctk.CTkLabel(self.frame_titulo, image=logo_ctk, text="")
        except Exception as e:
            self.lbl_titulo = ctk.CTkLabel(self.frame_titulo, text="G R I M O I R E", font=FUENTE_TITULO, text_color=C_TEXTO_DORADO)

        self.lbl_titulo.place(relx=0.5, rely=0.5, anchor="center")
        # ------------------------------------

        # Pestañas
        self.pestanas = ctk.CTkTabview(self, width=900, height=650, 
                                       fg_color=C_FONDO_PESTANAS, 
                                       segmented_button_fg_color=C_FONDO_APP,
                                       segmented_button_selected_color=C_BOTON_VERDE,
                                       segmented_button_selected_hover_color=C_BOTON_VERDE_HOVER,
                                       segmented_button_unselected_color=C_MARRON_OSCURO, # Pestañas sin seleccionar
                                       segmented_button_unselected_hover_color=C_MARRON_OSCURO_HOVER,
                                       text_color=C_TEXTO_DORADO)
        self.pestanas.pack(pady=10, padx=20, fill="both", expand=True)

        self.pestanas._segmented_button.configure(font=FUENTE_PESTANA, height=50)

        self.pestanas.add("Buscar")
        self.pestanas.add("Añadir Carta")
        self.pestanas.add("Mis Cajas")
        self.pestanas.add("Mantenimiento")

        self.imagenes_cache_busqueda = []
        self.imagen_cache_registro = None
        self.timer_busqueda = None
        self.timer_scryfall = None

        self.configurar_pestana_buscar()
        self.configurar_pestana_anadir()
        self.configurar_pestana_cajas()
        self.configurar_pestana_mantenimiento()

    # ----------------------------------------------------
    # PESTAÑA 1: BUSCADOR
    # ----------------------------------------------------
    def configurar_pestana_buscar(self):
        self.frame_busqueda = ctk.CTkFrame(self.pestanas.tab("Buscar"), fg_color="transparent")
        self.frame_busqueda.pack(pady=15, padx=20, fill="x")

        self.contenedor_busq = ctk.CTkFrame(self.frame_busqueda, fg_color="transparent")
        self.contenedor_busq.pack(side="left", padx=10, expand=True, fill="x")

        # Entrada con fondo marrón oscuro
        self.entrada_busqueda = ctk.CTkEntry(self.contenedor_busq, placeholder_text="Nombre de la carta...", font=FUENTE_TEXTO_GRANDE, 
                                             width=400, height=50, fg_color=C_MARRON_OSCURO, border_color="#3e2617")
        self.entrada_busqueda.pack(fill="x")
        self.entrada_busqueda.bind("<KeyRelease>", self.tecla_pulsada_buscar)

        self.sugerencias_busqueda = ctk.CTkFrame(self.contenedor_busq, fg_color=C_FONDO_CARTAS, corner_radius=4)

        self.btn_buscar = ctk.CTkButton(self.frame_busqueda, text="Buscar en Grimorio", font=FUENTE_BOTON, height=50, width=220,
                                        fg_color=C_BOTON_VERDE, hover_color=C_BOTON_VERDE_HOVER, command=self.ejecutar_busqueda)
        self.btn_buscar.pack(side="right", padx=10)

        self.panel_resultados = ctk.CTkScrollableFrame(self.pestanas.tab("Buscar"), fg_color="transparent")
        self.panel_resultados.pack(pady=15, padx=20, fill="both", expand=True)

    def tecla_pulsada_buscar(self, event):
        if event.keysym in ["Up", "Down", "Return", "Escape", "Tab"]: return
        if self.timer_busqueda: self.after_cancel(self.timer_busqueda)
        self.timer_busqueda = self.after(300, self.mostrar_sugerencias_locales)

    def mostrar_sugerencias_locales(self):
        termino = self.entrada_busqueda.get()
        for w in self.sugerencias_busqueda.winfo_children(): w.destroy()

        if len(termino) < 2:
            self.sugerencias_busqueda.pack_forget()
            return

        def limpiar_texto(texto):
            if not texto: return ""
            return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode("utf-8").lower()

        termino_limpio = f"%{limpiar_texto(termino)}%"
        conexion = sqlite3.connect("coleccion_mtg.db")
        conexion.create_function("LIMPIAR", 1, limpiar_texto) 
        cursor = conexion.cursor()
        cursor.execute('''SELECT DISTINCT nombre_espanol, nombre_ingles FROM inventario 
                          WHERE LIMPIAR(nombre_espanol) LIKE ? OR LIMPIAR(nombre_ingles) LIKE ? LIMIT 5''', (termino_limpio, termino_limpio))
        resultados = cursor.fetchall()
        conexion.close()

        if resultados:
            self.sugerencias_busqueda.pack(fill="x", pady=(2, 0))
            for fila in resultados:
                nom = fila[0] if fila[0] else fila[1]
                btn = ctk.CTkButton(self.sugerencias_busqueda, text=nom, fg_color="transparent", anchor="w", 
                                    font=FUENTE_TEXTO_MEDIO, hover_color=C_BOTON_VERDE_HOVER, command=lambda n=nom: self.seleccionar_sug_busqueda(n))
                btn.pack(fill="x", padx=2, pady=2)
        else:
            self.sugerencias_busqueda.pack_forget()

    def seleccionar_sug_busqueda(self, texto):
        self.entrada_busqueda.delete(0, "end")
        self.entrada_busqueda.insert(0, texto)
        self.sugerencias_busqueda.pack_forget()
        self.ejecutar_busqueda()

    def ejecutar_busqueda(self):
        self.sugerencias_busqueda.pack_forget() 
        for widget in self.panel_resultados.winfo_children(): widget.destroy()
        self.imagenes_cache_busqueda.clear()

        termino = self.entrada_busqueda.get()
        if not termino: return

        def limpiar_texto(texto):
            if not texto: return ""
            return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode("utf-8").lower()

        busqueda_sql = f"%{limpiar_texto(termino)}%"
        conexion = sqlite3.connect("coleccion_mtg.db")
        conexion.create_function("LIMPIAR", 1, limpiar_texto) 
        cursor = conexion.cursor()
        
        cursor.execute('''SELECT nombre_espanol, nombre_ingles, edicion, caja, cantidad, colores, url_imagen 
            FROM inventario WHERE LIMPIAR(nombre_espanol) LIKE ? OR LIMPIAR(nombre_ingles) LIKE ?''', (busqueda_sql, busqueda_sql))
        resultados = cursor.fetchall()
        conexion.close()

        if resultados:
            for fila in resultados:
                marco_carta = ctk.CTkFrame(self.panel_resultados, fg_color=C_FONDO_CARTAS, corner_radius=8)
                marco_carta.pack(pady=8, padx=10, fill="x")

                if fila[6]:
                    try:
                        cabeceras = {"User-Agent": "InventarioLuffamer/1.0"}
                        resp = requests.get(fila[6], headers=cabeceras, timeout=5)
                        img = Image.open(BytesIO(resp.content))
                        img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(90, 125))
                        self.imagenes_cache_busqueda.append(img_ctk)
                        ctk.CTkLabel(marco_carta, image=img_ctk, text="").pack(side="left", padx=15, pady=15)
                    except:
                        pass 

                texto = f"✦ {fila[0]} ({fila[1]})\nColor: {fila[5]}  |  Edición: {fila[2]}\nUbicación: {fila[3]}  |  Cantidad: {fila[4]}"
                ctk.CTkLabel(marco_carta, text=texto, justify="left", anchor="w", font=FUENTE_TEXTO_GRANDE).pack(side="left", padx=15, pady=15)
        else:
            ctk.CTkLabel(self.panel_resultados, text="❌ No se encontró ninguna magia con ese nombre.", font=FUENTE_TEXTO_GRANDE, text_color="#ff4d4d").pack(pady=20)

    # ----------------------------------------------------
    # PESTAÑA 2: AÑADIR CARTAS 
    # ----------------------------------------------------
    def configurar_pestana_anadir(self):
        # Entrada con fondo marrón oscuro
        self.entrada_caja = ctk.CTkEntry(self.pestanas.tab("Añadir Carta"), placeholder_text="Caja de destino (Ej: Baúl Principal)...", font=FUENTE_TEXTO_GRANDE, 
                                         width=400, height=50, fg_color=C_MARRON_OSCURO, border_color="#3e2617")
        self.entrada_caja.pack(pady=15)

        self.contenedor_anadir = ctk.CTkFrame(self.pestanas.tab("Añadir Carta"), fg_color="transparent")
        self.contenedor_anadir.pack(pady=(0, 10))

        # Entrada con fondo marrón oscuro
        self.entrada_nueva_carta = ctk.CTkEntry(self.contenedor_anadir, placeholder_text="Inscribir nueva carta...", font=FUENTE_TEXTO_GRANDE, 
                                                width=400, height=50, fg_color=C_MARRON_OSCURO, border_color="#3e2617")
        self.entrada_nueva_carta.pack(fill="x")
        self.entrada_nueva_carta.bind("<KeyRelease>", self.tecla_pulsada_anadir)

        self.sugerencias_anadir = ctk.CTkFrame(self.contenedor_anadir, fg_color=C_FONDO_CARTAS, corner_radius=4)

        self.btn_anadir = ctk.CTkButton(self.pestanas.tab("Añadir Carta"), text="Invocar y Guardar", font=FUENTE_BOTON, height=55, width=250,
                                        fg_color=C_BOTON_VERDE, hover_color=C_BOTON_VERDE_HOVER, command=self.ejecutar_registro)
        self.btn_anadir.pack(pady=15)

        self.lbl_mensaje_registro = ctk.CTkLabel(self.pestanas.tab("Añadir Carta"), text="", font=FUENTE_TEXTO_GRANDE)
        self.lbl_mensaje_registro.pack(pady=5)

        self.lbl_imagen_anadida = ctk.CTkLabel(self.pestanas.tab("Añadir Carta"), text="")
        self.lbl_imagen_anadida.pack(pady=10)

    def tecla_pulsada_anadir(self, event):
        if event.keysym in ["Up", "Down", "Return", "Escape", "Tab"]: return
        if self.timer_scryfall: self.after_cancel(self.timer_scryfall)
        self.timer_scryfall = self.after(500, self.iniciar_hilo_scryfall)

    def iniciar_hilo_scryfall(self):
        termino = self.entrada_nueva_carta.get()
        if len(termino) < 3:
            self.sugerencias_anadir.pack_forget()
            return
            
        def hilo_peticion():
            url = "https://api.scryfall.com/cards/search"
            parametros = {"q": f'{termino} lang:es', "include_multilingual": True}
            cabeceras = {"User-Agent": "InventarioLuffamer/1.0"}
            try:
                resp = requests.get(url, params=parametros, headers=cabeceras, timeout=3)
                if resp.status_code == 200:
                    data = resp.json().get("data", [])[:5] 
                    self.after(0, self.dibujar_sugerencias_anadir, data)
                else:
                    self.after(0, self.sugerencias_anadir.pack_forget)
            except:
                self.after(0, self.sugerencias_anadir.pack_forget)
                
        threading.Thread(target=hilo_peticion, daemon=True).start()

    def dibujar_sugerencias_anadir(self, data):
        for w in self.sugerencias_anadir.winfo_children(): w.destroy()
        nombres_vistos = set()
        resultados_unicos = []
        for c in data:
            nom = c.get("printed_name", c.get("name"))
            if nom not in nombres_vistos:
                nombres_vistos.add(nom)
                resultados_unicos.append(nom)
                
        if resultados_unicos:
            self.sugerencias_anadir.pack(fill="x", pady=(2, 0))
            for nom in resultados_unicos:
                btn = ctk.CTkButton(self.sugerencias_anadir, text=nom, fg_color="transparent", anchor="w", 
                            font=FUENTE_TEXTO_MEDIO, hover_color=C_BOTON_VERDE_HOVER, command=lambda n=nom: self.seleccionar_sug_anadir(n))
                btn.pack(fill="x", padx=2, pady=2)
        else:
            self.sugerencias_anadir.pack_forget()

    def seleccionar_sug_anadir(self, texto):
        self.entrada_nueva_carta.delete(0, "end")
        self.entrada_nueva_carta.insert(0, texto)
        self.sugerencias_anadir.pack_forget()

    def ejecutar_registro(self):
        self.sugerencias_anadir.pack_forget() 
        nombre = self.entrada_nueva_carta.get()
        caja = self.entrada_caja.get()

        if not nombre or not caja:
            self.lbl_mensaje_registro.configure(text="⚠️ Faltan encantamientos por rellenar.", text_color=C_TEXTO_DORADO)
            return

        self.lbl_mensaje_registro.configure(text=f"Buscando '{nombre}' en los archivos...", text_color="white")
        self.update() 

        url = "https://api.scryfall.com/cards/search"
        parametros = {"q": f'{nombre} lang:es', "include_multilingual": True}
        cabeceras = {"User-Agent": "InventarioLuffamer/1.0", "Accept": "*/*"}
        
        try:
            respuesta = requests.get(url, params=parametros, headers=cabeceras)
            if respuesta.status_code == 200:
                cartas_encontradas = respuesta.json()["data"]
                carta = cartas_encontradas[0] 

                nombre_buscado_limpio = unicodedata.normalize('NFD', nombre).encode('ascii', 'ignore').decode("utf-8").lower()
                for c in cartas_encontradas:
                    nom_ing = c.get("name", "")
                    nom_esp = c.get("printed_name", nom_ing)
                    nom_ing_limpio = unicodedata.normalize('NFD', nom_ing).encode('ascii', 'ignore').decode("utf-8").lower()
                    nom_esp_limpio = unicodedata.normalize('NFD', nom_esp).encode('ascii', 'ignore').decode("utf-8").lower()
                    
                    if nombre_buscado_limpio == nom_ing_limpio or nombre_buscado_limpio == nom_esp_limpio:
                        carta = c 
                        break

                identidad_color = carta.get("color_identity", [])
                colores = "".join(identidad_color) if identidad_color else "Incoloro"
                nombre_ingles = carta.get("name", "Desconocido")
                nombre_espanol = carta.get("printed_name", nombre_ingles)
                edicion = carta.get("set_name", "Desconocido")

                url_img = ""
                if "image_uris" in carta: url_img = carta["image_uris"].get("normal", "")
                elif "card_faces" in carta and "image_uris" in carta["card_faces"][0]: url_img = carta["card_faces"][0]["image_uris"].get("normal", "")

                conexion = sqlite3.connect("coleccion_mtg.db")
                cursor = conexion.cursor()
                cursor.execute('''SELECT id, cantidad FROM inventario WHERE nombre_ingles = ? AND caja = ? AND es_foil = 0''', (nombre_ingles, caja))
                resultado = cursor.fetchone()
                
                if resultado:
                    nueva_cantidad = resultado[1] + 1
                    cursor.execute('''UPDATE inventario SET cantidad = ? WHERE id = ?''', (nueva_cantidad, resultado[0]))
                    self.lbl_mensaje_registro.configure(text=f"🔄 Ya tenías esta carta. Nueva cantidad: {nueva_cantidad}", text_color="#4db8ff")
                else:
                    cursor.execute('''INSERT INTO inventario (nombre_ingles, nombre_espanol, edicion, colores, caja, cantidad, es_foil, url_imagen)
                                      VALUES (?, ?, ?, ?, ?, 1, 0, ?)''', (nombre_ingles, nombre_espanol, edicion, colores, caja, url_img))
                    self.lbl_mensaje_registro.configure(text=f"✅ Inscrito: {nombre_espanol} en '{caja}'", text_color="#00e676")
                
                conexion.commit()
                conexion.close()
                self.entrada_nueva_carta.delete(0, 'end')

                if url_img:
                    try:
                        resp_img = requests.get(url_img, headers=cabeceras, timeout=5)
                        img_data = Image.open(BytesIO(resp_img.content))
                        img_ctk = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(244, 340))
                        self.imagen_cache_registro = img_ctk
                        self.lbl_imagen_anadida.configure(image=img_ctk, text="")
                    except:
                        self.lbl_imagen_anadida.configure(text="⚠️ Carta guardada, pero la magia de visión falló.", image="", text_color=C_TEXTO_DORADO)

            else:
                self.lbl_mensaje_registro.configure(text="❌ Carta no encontrada en los textos antiguos.", text_color="#ff4d4d")
        except Exception as e:
            self.lbl_mensaje_registro.configure(text="❌ Error crítico de conexión.", text_color="#ff4d4d")

    # ----------------------------------------------------
    # PESTAÑA 3: MIS CAJAS 
    # ----------------------------------------------------
    def configurar_pestana_cajas(self):
        self.btn_actualizar_cajas = ctk.CTkButton(self.pestanas.tab("Mis Cajas"), text="🔄 Refrescar Archivos", font=FUENTE_BOTON, height=50, width=250,
                                                  fg_color=C_BOTON_VERDE, hover_color=C_BOTON_VERDE_HOVER, command=self.actualizar_vista_cajas)
        self.btn_actualizar_cajas.pack(pady=15)
        self.panel_cajas = ctk.CTkScrollableFrame(self.pestanas.tab("Mis Cajas"), fg_color="transparent")
        self.panel_cajas.pack(pady=10, padx=20, fill="both", expand=True)

    def actualizar_vista_cajas(self):
        for widget in self.panel_cajas.winfo_children(): widget.destroy()

        conexion = sqlite3.connect("coleccion_mtg.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT caja, nombre_espanol, cantidad, colores, edicion FROM inventario ORDER BY caja, colores, nombre_espanol")
        resultados = cursor.fetchall()
        conexion.close()

        if not resultados:
            ctk.CTkLabel(self.panel_cajas, text="Tu grimorio está vacío.", font=FUENTE_TEXTO_GRANDE).pack(pady=20)
            return

        diccionario_cajas = {}
        for fila in resultados:
            caja, nombre, cant, color, edicion = fila
            if caja not in diccionario_cajas: diccionario_cajas[caja] = []
            diccionario_cajas[caja].append(f"   ✦ {cant}x  {nombre}  |  Color: {color}  |  Edición: {edicion}")

        for nombre_caja, lista_cartas in diccionario_cajas.items():
            desplegable = CajaDesplegable(self.panel_cajas, nombre_caja, lista_cartas)
            desplegable.pack(fill="x", pady=5)

    # ----------------------------------------------------
    # PESTAÑA 4: MANTENIMIENTO 
    # ----------------------------------------------------
    def configurar_pestana_mantenimiento(self):
        frame_busq_mant = ctk.CTkFrame(self.pestanas.tab("Mantenimiento"), fg_color="transparent")
        frame_busq_mant.pack(pady=10, padx=20, fill="x")

        # Entrada con fondo marrón oscuro
        self.entrada_mant_busqueda = ctk.CTkEntry(frame_busq_mant, placeholder_text="Busca la carta para ver su ID...", font=FUENTE_TEXTO_GRANDE, 
                                                  height=50, width=400, fg_color=C_MARRON_OSCURO, border_color="#3e2617")
        self.entrada_mant_busqueda.pack(side="left", padx=10, expand=True, fill="x")

        self.btn_mant_buscar = ctk.CTkButton(frame_busq_mant, text="Rastrear ID", font=FUENTE_BOTON, height=50, width=180,
                                             fg_color=C_BOTON_VERDE, hover_color=C_BOTON_VERDE_HOVER, command=self.buscar_para_mantenimiento)
        self.btn_mant_buscar.pack(side="right", padx=10)

        # Caja de texto grande con fondo marrón oscuro
        self.caja_resultados_mant = ctk.CTkTextbox(self.pestanas.tab("Mantenimiento"), height=150, font=FUENTE_TEXTO_GRANDE, 
                                                   fg_color=C_MARRON_OSCURO, border_width=2, border_color="#3e2617")
        self.caja_resultados_mant.pack(pady=15, padx=20, fill="x")
        self.caja_resultados_mant.insert("0.0", "Rastrea una carta arriba para ver sus IDs...\n")
        self.caja_resultados_mant.configure(state="disabled")

        frame_acciones = ctk.CTkFrame(self.pestanas.tab("Mantenimiento"), fg_color="transparent")
        frame_acciones.pack(pady=10, padx=20, fill="both", expand=True)

        self.entrada_mant_id = ctk.CTkEntry(frame_acciones, placeholder_text="ID", font=FUENTE_TEXTO_GRANDE, height=50, width=100, 
                                            fg_color=C_MARRON_OSCURO, border_color="#3e2617")
        self.entrada_mant_id.grid(row=0, column=0, padx=10, pady=20)

        self.entrada_mant_cant = ctk.CTkEntry(frame_acciones, placeholder_text="Cant.", font=FUENTE_TEXTO_GRANDE, height=50, width=100, 
                                              fg_color=C_MARRON_OSCURO, border_color="#3e2617")
        self.entrada_mant_cant.grid(row=0, column=1, padx=10, pady=20)

        self.opcion_mant_accion = ctk.CTkOptionMenu(frame_acciones, values=["Mover", "Borrar"], font=FUENTE_TEXTO_GRANDE, height=50, 
                                                    fg_color=C_MARRON_OSCURO, button_color=C_MARRON_OSCURO_HOVER, dropdown_fg_color=C_MARRON_OSCURO)
        self.opcion_mant_accion.grid(row=0, column=2, padx=10, pady=20)

        self.entrada_mant_caja = ctk.CTkEntry(frame_acciones, placeholder_text="Nueva Caja (Solo Mover)", font=FUENTE_TEXTO_GRANDE, height=50, width=250, 
                                              fg_color=C_MARRON_OSCURO, border_color="#3e2617")
        self.entrada_mant_caja.grid(row=0, column=3, padx=10, pady=20)

        self.btn_ejecutar_mant = ctk.CTkButton(frame_acciones, text="Ejecutar Ritual", font=FUENTE_BOTON, height=55, width=220, 
                                               fg_color="#7a2a2a", hover_color="#9c3636", command=self.ejecutar_mantenimiento)
        self.btn_ejecutar_mant.grid(row=1, column=0, columnspan=4, pady=20)

        self.lbl_mensaje_mant = ctk.CTkLabel(frame_acciones, text="", font=FUENTE_TEXTO_GRANDE)
        self.lbl_mensaje_mant.grid(row=2, column=0, columnspan=4, pady=10)

    def buscar_para_mantenimiento(self):
        termino = self.entrada_mant_busqueda.get()
        if not termino: return
        
        def limpiar_texto(texto):
            if not texto: return ""
            return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode("utf-8").lower()
            
        busqueda_sql = f"%{limpiar_texto(termino)}%"
        conexion = sqlite3.connect("coleccion_mtg.db")
        conexion.create_function("LIMPIAR", 1, limpiar_texto) 
        cursor = conexion.cursor()
        
        cursor.execute('''SELECT id, nombre_espanol, caja, cantidad FROM inventario 
                          WHERE LIMPIAR(nombre_espanol) LIKE ? OR LIMPIAR(nombre_ingles) LIKE ?''', (busqueda_sql, busqueda_sql))
        resultados = cursor.fetchall()
        conexion.close()
        
        self.caja_resultados_mant.configure(state="normal")
        self.caja_resultados_mant.delete("0.0", "end")
        
        if resultados:
            for fila in resultados:
                self.caja_resultados_mant.insert("end", f"ID [{fila[0]}] -> {fila[1]} | Caja: {fila[2]} | Total: {fila[3]}\n")
        else:
            self.caja_resultados_mant.insert("end", "❌ No se encontraron coincidencias.\n")
            
        self.caja_resultados_mant.configure(state="disabled")

    def ejecutar_mantenimiento(self):
        id_elegido = self.entrada_mant_id.get()
        cant_str = self.entrada_mant_cant.get()
        accion = self.opcion_mant_accion.get()
        nueva_caja = self.entrada_mant_caja.get()

        if not id_elegido.isdigit() or not cant_str.isdigit():
            self.lbl_mensaje_mant.configure(text="⚠️ ID y Cantidad deben ser números enteros.", text_color=C_TEXTO_DORADO)
            return

        id_elegido, cant_operar = int(id_elegido), int(cant_str)

        conexion = sqlite3.connect("coleccion_mtg.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre_espanol, caja, cantidad, nombre_ingles, edicion, colores, es_foil, url_imagen FROM inventario WHERE id = ?", (id_elegido,))
        carta = cursor.fetchone()

        if not carta:
            self.lbl_mensaje_mant.configure(text="❌ El ID no existe en el grimorio.", text_color="#ff4d4d")
            conexion.close()
            return

        nombre_esp, caja_origen, cant_origen, nombre_ing, edicion, colores, es_foil, url_imagen = carta

        if cant_operar <= 0 or cant_operar > cant_origen:
            self.lbl_mensaje_mant.configure(text=f"⚠️ Cantidad inválida. Posees {cant_origen} copias.", text_color=C_TEXTO_DORADO)
            conexion.close()
            return

        if accion == "Borrar":
            if cant_operar == cant_origen:
                cursor.execute("DELETE FROM inventario WHERE id = ?", (id_elegido,))
            else:
                cursor.execute("UPDATE inventario SET cantidad = cantidad - ? WHERE id = ?", (cant_operar, id_elegido))
            self.lbl_mensaje_mant.configure(text=f"🗑️ Se purgaron {cant_operar} copias.", text_color="#00e676")

        elif accion == "Mover":
            if not nueva_caja:
                self.lbl_mensaje_mant.configure(text="⚠️ Escribe el nombre del nuevo contenedor.", text_color=C_TEXTO_DORADO)
                conexion.close()
                return
            
            if cant_operar == cant_origen: cursor.execute("DELETE FROM inventario WHERE id = ?", (id_elegido,))
            else: cursor.execute("UPDATE inventario SET cantidad = cantidad - ? WHERE id = ?", (cant_operar, id_elegido))
            
            cursor.execute("SELECT id FROM inventario WHERE nombre_ingles = ? AND caja = ? AND es_foil = ?", (nombre_ing, nueva_caja, es_foil))
            destino = cursor.fetchone()
            
            if destino: cursor.execute("UPDATE inventario SET cantidad = cantidad + ? WHERE id = ?", (cant_operar, destino[0]))
            else: cursor.execute('''INSERT INTO inventario (nombre_ingles, nombre_espanol, edicion, colores, caja, cantidad, es_foil, url_imagen)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (nombre_ing, nombre_esp, edicion, colores, nueva_caja, cant_operar, es_foil, url_imagen))
            self.lbl_mensaje_mant.configure(text=f"📦 Movidas {cant_operar} copias a '{nueva_caja}'.", text_color="#00e676")

        conexion.commit()
        conexion.close()
        self.buscar_para_mantenimiento()

if __name__ == "__main__":
    app = InventarioMagic()
    app.mainloop()