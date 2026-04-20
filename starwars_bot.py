import requests
import schedule
import time
from datetime import datetime
import xml.etree.ElementTree as ET
import re

# ============================================================
# CONFIGURACIÓN
# ============================================================
TELEGRAM_TOKEN = "8386451412:AAEmY3mpZwFguFN_wqwiFKYL9_qWCW0U48s"
CHAT_ID = "-1003953625410"
HORA_ENVIO = "09:00"

# ============================================================
# FUENTES RSS
# ============================================================
FUENTES_RSS = [
    {"nombre": "Star Wars News Net", "url": "https://www.starwarsnewsnet.com/feed"},
    {"nombre": "Jedi News", "url": "https://www.jedinews.com/feed/"},
    {"nombre": "The Direct", "url": "https://thedirect.com/rss/star-wars"},
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def obtener_noticias_rss(fuente):
    noticias = []
    try:
        response = requests.get(fuente["url"], headers=HEADERS, timeout=10)
        root = ET.fromstring(response.content)
        items = root.findall(".//item")[:5]
        for item in items:
            titulo = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            descripcion = re.sub(r'<[^>]+>', '', item.findtext("description", "").strip())[:200]
            if titulo and link:
                noticias.append({"titulo": titulo, "link": link, "descripcion": descripcion, "fuente": fuente["nombre"]})
    except Exception as e:
        print(f"Error en {fuente['nombre']}: {e}")
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

def formatear_mensaje(noticias):
    fecha = datetime.now().strftime("%d/%m/%Y")
    mensaje = f"🌌 *NOTICIAS STAR WARS* — {fecha}\n\n"
    emojis = ["⚡", "🔦"]
    for i, noticia in enumerate(noticias):
        emoji = emojis[i] if i < len(emojis) else "🔸"
        mensaje += f"{emoji} *{noticia['titulo']}*\n"
        if noticia["descripcion"]:
            mensaje += f"_{noticia['descripcion'][:150]}..._\n"
        mensaje += f"🔗 [Leer más]({noticia['link']})\n"
        mensaje += f"📡 _Fuente: {noticia['fuente']}_\n\n"
    mensaje += "——————————————\n"
    mensaje += "🤖 _La Fuerza Informa — Bot automático_"
    return mensaje

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown", "disable_web_page_preview": False}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"✅ Mensaje enviado a las {datetime.now().strftime('%H:%M:%S')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

def ejecutar_bot():
    print(f"🔍 Buscando noticias... {datetime.now().strftime('%H:%M:%S')}")
    todas = []
    for fuente in FUENTES_RSS:
        noticias = obtener_noticias_rss(fuente)
        todas.extend(noticias)
        print(f"   → {fuente['nombre']}: {len(noticias)} noticias encontradas")
    if not todas:
        print("⚠️ No se encontraron noticias hoy")
        return
    mejores = seleccionar_mejores(todas, cantidad=2)
    mensaje = formatear_mensaje(mejores)
    enviar_telegram(mensaje)

if __name__ == "__main__":
    print(f"🤖 Bot La Fuerza Informa arrancado")
    print(f"📅 Publicará cada día a las {HORA_ENVIO}")
    print(f"💬 Canal ID: {CHAT_ID}")
    print("—" * 40)
    print("🚀 Ejecutando prueba inicial...")
    ejecutar_bot()
    schedule.every().day.at(HORA_ENVIO).do(ejecutar_bot)
    while True:
        schedule.run_pending()
        time.sleep(60)
