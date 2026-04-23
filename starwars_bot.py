import requests
import schedule
import time
from datetime import datetime
import xml.etree.ElementTree as ET
import re
import json
import os

# ============================================================
# CONFIGURACIÓN
# ============================================================
TELEGRAM_TOKEN = "8386451412:AAEmY3mpZwFguFN_wqwiFKYL9_qWCW0U48s"
CANALES = [
    "-1003953625410",
    "-1003595840163",
]
HORA_MANANA = "09:00"
HORA_TARDE = "18:00"
AVISO_MAUL_LUNES = True  # Cambia a False cuando acabe la serie el 4 de mayo
HISTORIAL_FILE = "noticias_enviadas.json"

# ============================================================
# FUENTES RSS
# ============================================================
FUENTES_NOTICIAS = [
    {"nombre": "Star Wars News Net", "url": "https://www.starwarsnewsnet.com/feed"},
    {"nombre": "Jedi News", "url": "https://www.jedinews.com/feed/"},
    {"nombre": "The Direct", "url": "https://thedirect.com/rss/star-wars"},
]

FUENTES_LORE = [
    {"nombre": "Youtini", "url": "https://youtini.com/articles.rss"},
    {"nombre": "Jedi News Literatura", "url": "https://www.jedinews.com/category/literature/feed/"},
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ============================================================
# HISTORIAL — para no repetir noticias
# ============================================================
def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, "r") as f:
            return json.load(f)
    return []

def guardar_historial(historial):
    with open(HISTORIAL_FILE, "w") as f:
        json.dump(historial[-200:], f)  # Guarda solo las últimas 200

def ya_enviada(link, historial):
    return link in historial

# ============================================================
# TRADUCCIÓN
# ============================================================
def traducir(texto):
    """Traduce texto al castellano usando MyMemory API (gratis)"""
    if not texto:
        return texto
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": texto[:500], "langpair": "en|es"}
        response = requests.get(url, params=params, timeout=8)
        data = response.json()
        traducido = data["responseData"]["translatedText"]
        if traducido and len(traducido) > 3:
            return traducido
    except:
        pass
    return texto  # Si falla devuelve el original

# ============================================================
# RSS
# ============================================================
def obtener_noticias_rss(fuentes, historial):
    noticias = []
    for fuente in fuentes:
        try:
            response = requests.get(fuente["url"], headers=HEADERS, timeout=10)
            root = ET.fromstring(response.content)
            items = root.findall(".//item")[:8]
            for item in items:
                titulo = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                descripcion = re.sub(r'<[^>]+>', '', item.findtext("description", "").strip())[:300]
                if titulo and link and not ya_enviada(link, historial):
                    noticias.append({
                        "titulo": titulo,
                        "link": link,
                        "descripcion": descripcion,
                        "fuente": fuente["nombre"]
                    })
            print(f"   → {fuente['nombre']}: {len(items)} encontradas")
        except Exception as e:
            print(f"   ❌ Error en {fuente['nombre']}: {e}")
    return noticias

def seleccionar_mejores(todas, cantidad=2):
    seleccionadas = []
    fuentes_usadas = set()
    for noticia in todas:
        if len(seleccionadas) >= cantidad:
            break
        if noticia["fuente"] not in fuentes_usadas:
            seleccionadas.append(noticia)
            fuentes_usadas.add(noticia["fuente"])
    for noticia in todas:
        if len(seleccionadas) >= cantidad:
            break
        if noticia not in seleccionadas:
            seleccionadas.append(noticia)
    return seleccionadas[:cantidad]

# ============================================================
# MENSAJES
# ============================================================
def formatear_noticias(noticias):
    fecha = datetime.now().strftime("%d/%m/%Y")
    mensaje = f"🌌 *NOTICIAS STAR WARS* — {fecha}\n\n"
    emojis = ["⚡", "🔦"]
    for i, n in enumerate(noticias):
        emoji = emojis[i] if i < len(emojis) else "🔸"
        titulo_es = traducir(n["titulo"])
        desc_es = traducir(n["descripcion"][:200]) if n["descripcion"] else ""
        mensaje += f"{emoji} *{titulo_es}*\n"
        if desc_es:
            mensaje += f"_{desc_es[:180]}..._\n"
        mensaje += f"🔗 [Leer más]({n['link']})\n"
        mensaje += f"📡 _Fuente: {n['fuente']}_\n\n"
    mensaje += "——————————————\n"
    mensaje += "🤖 _La Fuerza Informa — R3-PORT_"
    return mensaje

def formatear_lore(noticias):
    fecha = datetime.now().strftime("%d/%m/%Y")
    mensaje = f"📖 *LORE & CURIOSIDADES STAR WARS* — {fecha}\n\n"
    emojis = ["🌑", "✨"]
    for i, n in enumerate(noticias):
        emoji = emojis[i] if i < len(emojis) else "🔸"
        titulo_es = traducir(n["titulo"])
        desc_es = traducir(n["descripcion"][:200]) if n["descripcion"] else ""
        mensaje += f"{emoji} *{titulo_es}*\n"
        if desc_es:
            mensaje += f"_{desc_es[:180]}..._\n"
        mensaje += f"🔗 [Leer más]({n['link']})\n"
        mensaje += f"📡 _Fuente: {n['fuente']}_\n\n"
    mensaje += "——————————————\n"
    mensaje += "🤖 _La Fuerza Informa — R3-PORT_"
    return mensaje

def mensaje_maul_lunes():
    return (
        "🔴 *¡NUEVOS EPISODIOS DE MAUL: SHADOW LORD!* 🔴\n\n"
        "Esta semana han salido dos capítulos nuevos en Disney+.\n"
        "¿Ya los has visto? Cuéntanos qué te han parecido 👇\n\n"
        "——————————————\n"
        "🤖 _La Fuerza Informa — R3-PORT_"
    )

# ============================================================
# ENVÍO
# ============================================================
def enviar_telegram(mensaje):
    for canal in CANALES:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": canal, "text": mensaje, "parse_mode": "Markdown", "disable_web_page_preview": False}
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print(f"✅ Enviado a {canal} a las {datetime.now().strftime('%H:%M:%S')}")
            else:
                print(f"❌ Error en {canal}: {response.text}")
        except Exception as e:
            print(f"❌ Error conexión {canal}: {e}")

# ============================================================
# TAREAS
# ============================================================
def tarea_manana():
    print(f"\n🌅 TAREA MAÑANA — {datetime.now().strftime('%H:%M:%S')}")
    historial = cargar_historial()

    # Aviso Maul los lunes
    if AVISO_MAUL_LUNES and datetime.now().weekday() == 0:
        print("   → Lunes: enviando aviso Maul Shadow Lord")
        enviar_telegram(mensaje_maul_lunes())
        time.sleep(3)

    todas = obtener_noticias_rss(FUENTES_NOTICIAS, historial)
    if not todas:
        print("⚠️ Sin noticias nuevas")
        return

    mejores = seleccionar_mejores(todas, 2)
    mensaje = formatear_noticias(mejores)
    enviar_telegram(mensaje)

    for n in mejores:
        historial.append(n["link"])
    guardar_historial(historial)

def tarea_tarde():
    print(f"\n🌆 TAREA TARDE — {datetime.now().strftime('%H:%M:%S')}")
    historial = cargar_historial()
    todas = obtener_noticias_rss(FUENTES_LORE, historial)

    if not todas:
        # Si no hay lore nuevo, usa fuentes de noticias
        todas = obtener_noticias_rss(FUENTES_NOTICIAS, historial)

    if not todas:
        print("⚠️ Sin contenido nuevo")
        return

    mejores = seleccionar_mejores(todas, 2)
    mensaje = formatear_lore(mejores)
    enviar_telegram(mensaje)

    for n in mejores:
        historial.append(n["link"])
    guardar_historial(historial)

# ============================================================
# ARRANCAR
# ============================================================
if __name__ == "__main__":
    print(f"🤖 Bot La Fuerza Informa v2 arrancado")
    print(f"📅 Mañana: {HORA_MANANA} | Tarde: {HORA_TARDE}")
    print(f"💬 Canal ID: {CHAT_ID}")
    print("—" * 40)

    print("🚀 Ejecutando prueba inicial...")
    tarea_manana()

    schedule.every().day.at(HORA_MANANA).do(tarea_manana)
    schedule.every().day.at(HORA_TARDE).do(tarea_tarde)

    while True:
        schedule.run_pending()
        time.sleep(60)


