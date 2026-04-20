import requests
from bs4 import BeautifulSoup
import schedule
import time
from datetime import datetime

# ============================================================
# CONFIGURACIÓN
# ============================================================
TELEGRAM_TOKEN = "8386451412:AAEmY3mpZwFguFN_wqwiFKYL9_qWCW0U48s"
CHAT_ID = "-1003953625410"
HORA_ENVIO = "09:00"  # Hora a la que se publica cada día (formato 24h)

# ============================================================
# FUENTES
# ============================================================
FUENTES = [
    {
        "nombre": "Star Wars News Net",
        "url": "https://www.starwarsnewsnet.com/",
        "selector_articulos": "article",
        "selector_titulo": "h2",
        "selector_link": "h2 a",
        "selector_descripcion": "p",
    },
    {
        "nombre": "Youtini",
        "url": "https://youtini.com/articles",
        "selector_articulos": "article",
        "selector_titulo": "h2, h3",
        "selector_link": "a",
        "selector_descripcion": "p",
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ============================================================
# FUNCIONES
# ============================================================

def obtener_noticias(fuente):
    """Raspa las noticias de una fuente"""
    noticias = []
    try:
        response = requests.get(fuente["url"], headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        articulos = soup.find_all(fuente["selector_articulos"])[:5]

        for art in articulos:
            titulo_tag = art.find(fuente["selector_titulo"].split(",")[0].strip())
            link_tag = art.find("a", href=True)
            desc_tag = art.find("p")

            if titulo_tag and link_tag:
                titulo = titulo_tag.get_text(strip=True)
                link = link_tag["href"]
                if not link.startswith("http"):
                    base = fuente["url"].rstrip("/")
                    link = base + link
                descripcion = desc_tag.get_text(strip=True)[:200] if desc_tag else ""

                if titulo and len(titulo) > 10:
                    noticias.append({
                        "titulo": titulo,
                        "link": link,
                        "descripcion": descripcion,
                        "fuente": fuente["nombre"]
                    })
    except Exception as e:
        print(f"Error raspando {fuente['nombre']}: {e}")

    return noticias


def seleccionar_mejores(todas_las_noticias, cantidad=2):
    """Selecciona las 2 noticias más relevantes priorizando variedad de fuentes"""
    if len(todas_las_noticias) <= cantidad:
        return todas_las_noticias

    seleccionadas = []
    fuentes_usadas = set()

    # Primero una de cada fuente
    for noticia in todas_las_noticias:
        if noticia["fuente"] not in fuentes_usadas and len(seleccionadas) < cantidad:
            seleccionadas.append(noticia)
            fuentes_usadas.add(noticia["fuente"])

    # Si no hay suficientes, rellena con lo que queda
    for noticia in todas_las_noticias:
        if len(seleccionadas) >= cantidad:
            break
        if noticia not in seleccionadas:
            seleccionadas.append(noticia)

    return seleccionadas[:cantidad]


def formatear_mensaje(noticias):
    """Formatea las noticias en un mensaje de Telegram"""
    fecha = datetime.now().strftime("%d/%m/%Y")
    mensaje = f"🌌 *NOTICIAS STAR WARS* — {fecha}\n\n"

    for i, noticia in enumerate(noticias, 1):
        emoji = "⚡" if i == 1 else "🔦"
        mensaje += f"{emoji} *{noticia['titulo']}*\n"
        if noticia["descripcion"]:
            mensaje += f"_{noticia['descripcion'][:150]}..._\n"
        mensaje += f"🔗 [Leer más]({noticia['link']})\n"
        mensaje += f"📡 _Fuente: {noticia['fuente']}_\n\n"

    mensaje += "——————————————\n"
    mensaje += "🤖 _La Fuerza Informa — Bot automático_"

    return mensaje


def enviar_telegram(mensaje):
    """Envía el mensaje al canal de Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"✅ Mensaje enviado correctamente a las {datetime.now().strftime('%H:%M:%S')}")
        else:
            print(f"❌ Error al enviar: {response.text}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")


def ejecutar_bot():
    """Función principal que junta todo"""
    print(f"🔍 Buscando noticias... {datetime.now().strftime('%H:%M:%S')}")

    todas = []
    for fuente in FUENTES:
        noticias = obtener_noticias(fuente)
        todas.extend(noticias)
        print(f"   → {fuente['nombre']}: {len(noticias)} noticias encontradas")

    if not todas:
        print("⚠️ No se encontraron noticias hoy")
        return

    mejores = seleccionar_mejores(todas, cantidad=2)
    mensaje = formatear_mensaje(mejores)
    enviar_telegram(mensaje)


# ============================================================
# PROGRAMAR Y ARRANCAR
# ============================================================
if __name__ == "__main__":
    print(f"🤖 Bot La Fuerza Informa arrancado")
    print(f"📅 Publicará cada día a las {HORA_ENVIO}")
    print(f"💬 Canal ID: {CHAT_ID}")
    print("—" * 40)

    # Prueba inmediata al arrancar
    print("🚀 Ejecutando prueba inicial...")
    ejecutar_bot()

    # Programar ejecución diaria
    schedule.every().day.at(HORA_ENVIO).do(ejecutar_bot)

    # Bucle infinito
    while True:
        schedule.run_pending()
        time.sleep(60)
