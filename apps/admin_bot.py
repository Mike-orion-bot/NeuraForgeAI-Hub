import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Variables de Entorno (Se configuran en Render)
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Tu ID de Telegram (para que nadie más pueda usar el bot)
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

async def check_admin(update: Update) -> bool:
    """Verifica si el usuario es el administrador maestro."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Acceso denegado. Este nodo es de uso exclusivo administrativo.")
        return False
    return True

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando de inicio y menú principal."""
    if not await check_admin(update): return
    
    mensaje = (
        "🔱 **NeuraforgeAI - Panel de Control Maestro** 🔱\n\n"
        "Sistemas en línea y sincronizados. ¿Qué deseas hacer, Jefe?\n\n"
        "📊 /stats - Ver rendimiento de la red\n"
        "💻 /nodos - Estado del hardware reciclado\n"
        "💰 /forgecoins - Resumen financiero y liquidez\n"
        "📢 /broadcast [mensaje] - Enviar alerta a todos los sub-afiliados"
    )
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra las métricas globales del ecosistema."""
    if not await check_admin(update): return
    
    # Aquí conectarías con tu base de datos (Ej. Supabase o PostgreSQL)
    # Por ahora simulamos los datos de tu dashboard HTML
    mensaje = (
        "📊 **MÉTRICAS DEL ECOSISTEMA**\n\n"
        "👥 **Sub-Afiliados Activos:** 12 Bots\n"
        "⚡ **Salud de la Red:** Óptima (84% aportación)\n"
        "📈 **Proyectos de Inversión:** 3 Activos\n"
        "👦 **Modo Junior:** 14 Perfiles nuevos hoy"
    )
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def forgecoins_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el estado financiero."""
    if not await check_admin(update): return
    
    mensaje = (
        "💰 **RESERVA DE FORGECOINS (FGC)**\n\n"
        "🪙 **Generados (24h):** 145.50 FGC\n"
        "🔄 **Comisiones de red:** +3.5 FGC\n"
        "₿ **Equivalencia BTC:** ≈ 0.0012 BTC\n\n"
        "🟢 _Retiros automáticos activados._"
    )
    await update.message.reply_text(mensaje, parse_mode='Markdown')

def main():
    """Inicialización del bot."""
    if not BOT_TOKEN or not ADMIN_ID:
        logging.error("Faltan variables de entorno BOT_TOKEN o ADMIN_ID.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Registro de comandos
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("stats", stats_handler))
    application.add_handler(CommandHandler("forgecoins", forgecoins_handler))

    logging.info("🚀 Bot Administrativo de NeuraforgeAI Iniciado...")
    application.run_polling()

if __name__ == "__main__":
    main()
