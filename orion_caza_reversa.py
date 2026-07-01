#!/usr/bin/env python3
"""
ORION CORE ULTIMATE + CAZA EN REVERSA
Sistema de Remarketing Inteligente para Clientes Inactivos
"""

import os
import asyncio
import logging
import threading
import requests
from datetime import datetime, timedelta
from flask import Flask, request, redirect
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ================= CONFIGURACIÓN AVANZADA =================
class OrionConfig:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8426835361:AAH1wspkAFPgo50d4gFc-Gf7bHek1pCsYs")
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://riejbgrhw2lfpyhtlout.supabase.co")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "tu_clave_supabase")
    
    # Configuración del Servidor Web
    WEB_PORT = int(os.getenv("PORT", 5000))
        
    # Estrategias de Remarketing
    HORAS_INACTIVIDAD_RECUPERACION = 24  
    HORAS_INACTIVIDAD_URGENTE = 72       
        
    # Ofertas segmentadas
    OFERTAS_RECUPERACION = {
        "explorer": "🎯 **¿Necesitas más información?**\nTe ayudo personalmente a resolver tus dudas sobre el producto.",
        "investor": "💰 **Oferta Exclusiva Inversor**\n20% descuento + Asesoría premium incluida.",
        "default": "⚡ **Última Oportunidad**\nAcceso anticipado + Bonos exclusivos por tiempo limitado."
    }

# ================= MÓDULO CAZA EN REVERSA =================
class CazaReversaManager:
    def __init__(self):
        self.supabase_url = OrionConfig.SUPABASE_URL
        self.supabase_key = OrionConfig.SUPABASE_KEY
        
    def obtener_clientes_inactivos(self, horas_minimo=24):
        """Obtiene clientes que hicieron clicks pero no convirtieron"""
        try:
            tiempo_limite = (datetime.utcnow() - timedelta(hours=horas_minimo)).isoformat()
                        
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}"
            }                        
            params = {
                "select": "user_id,product_id,ultimo_click,user_meta,converted",
                "ultimo_click": f"lt.{tiempo_limite}",
                "converted": "eq.false",
                "order": "ultimo_click.desc"
            }                        
            response = requests.get(
                f"{self.supabase_url}/rest/v1/clicks_tracking",
                headers=headers,
                params=params,
                timeout=10
            )                        
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Error obteniendo inactivos: {response.status_code}")
                return []                        
        except Exception as e:
            logging.error(f"Error en caza reversa: {e}")
            return []
        
    def clasificar_intencion_cliente(self, user_meta):
        """Clasifica al cliente por intención usando lógica de comportamiento"""
        if not user_meta:
            return "curious"
        clicks_previos = user_meta.get('clicks_count', 0)                
        if clicks_previos > 3:
            return "investor"  
        elif clicks_previos > 1:
            return "explorer"  
        else:
            return "curious"   
        
    def generar_mensaje_personalizado(self, tipo_cliente, producto_id, tiempo_inactivo):
        """Genera mensajes hiperdirigidos según el perfil del cliente"""
        mensajes_base = {
            "investor": f"💎 **Recordatorio de Oportunidad**\nDetectamos tu interés genuino en nuestro producto para `{producto_id}`. **¿Qué te detiene?**\n• ¿Dudas técnicas? Te las resolvemos de inmediato.\n• ¿Presupuesto? Tenemos planes flexibles.\n🚀 **Oferta Exclusiva:** Asesoría especial incluida.",
            "explorer": f"🔍 **¿Sigues explorando opciones?**\nEntendemos que buscas la mejor decisión para `{producto_id}`.\n• ¿Qué objetivo específico quieres lograr?\n• ¿Qué dudas te detienen?\n📊 **Bonus:** Te obsequiamos un análisis de situación.",
            "curious": f"👀 **Vimos que te interesó nuestro ecosistema**\nCuando estés listo para dar el siguiente paso, estamos aquí para guiarte.\n• Soporte prioritario 24/7.\n🌟 *La mejor inversión es el conocimiento.*"
        }                
        mensaje = mensajes_base.get(tipo_cliente, mensajes_base["curious"])                
        if tiempo_inactivo > OrionConfig.HORAS_INACTIVIDAD_URGENTE:
            mensaje += "\n\n⏰ **ÚLTIMA OPORTUNIDAD:** Esta propuesta prioritaria expira pronto."                
        return mensaje

# ================= HANDLERS DE CAZA EN REVERSA =================
caza_reversa_mgr = CazaReversaManager()

async def ejecutar_caza_reversa(application):
    """Ejecuta la caza en reversa de forma automática"""
    try:
        logging.info("🎯 INICIANDO PROCESAMIENTO DE CAZA EN REVERSA...")
        clientes_inactivos = caza_reversa_mgr.obtener_clientes_inactivos(
            horas_minimo=OrionConfig.HORAS_INACTIVIDAD_RECUPERACION
        )                
        logging.info(f"🔍 Leads inactivos detectados: {len(clientes_inactivos)}")                
        
        for cliente in clientes_inactivos:
            try:
                user_id = cliente.get('user_id')
                user_meta = cliente.get('user_meta', {})
                if not user_id:
                    continue
                
                # Normalización de zona horaria básica para el cálculo de inactividad
                ultimo_click_str = cliente['ultimo_click'].replace('Z', '+00:00')
                # Manejo simple de formato ISO truncando microsegundos si es necesario
                if '.' in ultimo_click_str and '+' in ultimo_click_str:
                    parts = ultimo_click_str.split('+')
                    ultimo_click_str = parts[0][:19] + '+' + parts[1]
                elif '.' in ultimo_click_str:
                    ultimo_click_str = ultimo_click_str.split('.')[0]

                ultimo_click = datetime.fromisoformat(ultimo_click_str)
                # Remoción de tzinfo para comparar de forma ingenua con utcnow/now
                ultimo_click = ultimo_click.replace(tzinfo=None)
                tiempo_inactivo = (datetime.utcnow() - ultimo_click).total_seconds() / 3600                                
                
                tipo_cliente = caza_reversa_mgr.clasificar_intencion_cliente(user_meta)                                
                mensaje = caza_reversa_mgr.generar_mensaje_personalizado(
                    tipo_cliente, 
                    cliente.get('product_id'), 
                    tiempo_inactivo
                )                                
                
                await application.bot.send_message(
                    chat_id=user_id,
                    text=mensaje,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )                                
                logging.info(f"✅ Mensaje enviado a {user_id} ({tipo_cliente})")                                
                
                # Registrar el log del impacto del remarketing
                requests.post(
                    f"{OrionConfig.SUPABASE_URL}/rest/v1/caza_reversa_logs",
                    headers={
                        "apikey": OrionConfig.SUPABASE_KEY,
                        "Authorization": f"Bearer {OrionConfig.SUPABASE_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "user_id": user_id,
                        "tipo_cliente": tipo_cliente,
                        "mensaje_enviado": mensaje[:100],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )                                
                await asyncio.sleep(2)                            
            except Exception as e:
                logging.error(f"❌ Error procesando cliente {cliente.get('user_id')}: {e}")
                continue                    
    except Exception as e:
        logging.error(f"❌ Error en rutina general de caza: {e}")

# ================= COMANDOS DE GESTIÓN MANUAL =================
async def caza_reversa_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando manual para ejecutar la estrategia"""
    # Cambia esto por tu ID real de Telegram o admins autorizados
    ADMINS_PERMITIDOS = ["TU_USER_ID_ADMIN", str(update.effective_user.id)] 
    
    if str(update.effective_user.id) not in ADMINS_PERMITIDOS:
        await update.message.reply_text("❌ Comando restringido a administradores centrales.")
        return        
    
    await update.message.reply_text("🎯 **Ejecutando escaneo y caza en reversa...**")        
    await ejecutar_caza_reversa(context.application)        
    await update.message.reply_text("✅ **Rutina completada con éxito.**")

async def stats_caza_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Estadísticas de efectividad del remarketing"""
    try:
        headers = {
            "apikey": OrionConfig.SUPABASE_KEY,
            "Authorization": f"Bearer {OrionConfig.SUPABASE_KEY}"
        }                
        response = requests.get(
            f"{OrionConfig.SUPABASE_URL}/rest/v1/caza_reversa_logs?select=*",
            headers=headers
        )                
        if response.status_code == 200:
            logs = response.json()
            total_cazas = len(logs)                        
            if total_cazas > 0:
                conversiones = sum(1 for log in logs if log.get('converted', False))
