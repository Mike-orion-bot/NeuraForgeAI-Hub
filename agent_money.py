"""
Agente de Monetización v1.0
===========================

Un agente especializado para gestionar, analizar y optimizar estrategias de monetización.
Soporta múltiples proveedores de pago (Stripe, PayPal, MercadoPago), modelos de monetización
(suscripciones, pagos únicos, donaciones) y generación de reportes financieros.

Características:
- Detección automática de plataformas y modelos de monetización
- Integración con múltiples APIs de pago
- Análisis de métricas financieras (ingresos, conversiones, churn rate)
- Validación de configuraciones de proveedores
- Generación de reportes detallados
- Modo vigilancia continua
- Backup automático de configuraciones
- Configuración personalizable

Uso:
    python monetization_agent.py [OPCIONES]

Opciones:
    --config, -c      Archivo de configuración (default: config.json)
    --providers, -p   Proveedores a analizar (stripe,paypal,mercadopago)
    --check, -k       Solo verificar configuraciones
    --analyze, -a     Analizar métricas financieras
    --watch, -w       Modo vigilancia continua
    --interval, -i    Intervalo de vigilancia en segundos (default: 300)
    --report, -r      Generar reporte detallado
    --backup, -b      Crear backup antes de cambios
    --install         Instalar como script ejecutable
"""

import os
import sys
import json
import shutil
import argparse
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import requests
import pandas as pd
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


# =============================================================================
# CONFIGURACIÓN POR DEFECTO
# =============================================================================

DEFAULT_CONFIG = {
    "providers": {
        "stripe": {
            "enabled": True,
            "api_key_env": "STRIPE_SECRET_KEY",
            "webhook_secret_env": "STRIPE_WEBHOOK_SECRET",
            "models": ["subscriptions", "one_time_payments"]
        },
        "paypal": {
            "enabled": True,
            "client_id_env": "PAYPAL_CLIENT_ID",
            "client_secret_env": "PAYPAL_CLIENT_SECRET",
            "models": ["subscriptions", "one_time_payments", "donations"]
        },
        "mercadopago": {
            "enabled": True,
            "access_token_env": "MP_ACCESS_TOKEN",
            "models": ["subscriptions", "one_time_payments"]
        }
    },
    "monetization_models": {
        "subscriptions": {
            "enabled": True,
            "metrics": ["mrr", "arr", "churn_rate", "ltv", "active_subscribers"]
        },
        "one_time_payments": {
            "enabled": True,
            "metrics": ["total_revenue", "conversion_rate", "average_order_value"]
        },
        "donations": {
            "enabled": True,
            "metrics": ["total_donations", "average_donation", "donor_count"]
        }
    },
    "analysis_period": "30d",  # Período de análisis por defecto
    "currency": "USD",
    "watch_interval": 300,  # 5 minutos
    "log_file": "monetization_agent.log",
    "report_file": "monetization_report.json",
    "backup_dir": "backups",
    "report_dir": "reports",
    "ignore_errors": False
}


# =============================================================================
# MODELOS DE DATOS
# =============================================================================

@dataclass
class MonetizationCheck:
    """Resultado de una verificación individual de monetización."""
    name: str
    passed: bool
    message: str = ""
    details: Optional[Dict[str, Any]] = None
    provider: str = ""
    model: str = ""


@dataclass
class FinancialMetrics:
    """Métricas financieras para un proveedor."""
    total_revenue: float = 0.0
    mrr: float = 0.0  # Monthly Recurring Revenue
    arr: float = 0.0  # Annual Recurring Revenue
    churn_rate: float = 0.0
    ltv: float = 0.0  # Lifetime Value
    arpu: float = 0.0  # Average Revenue Per User
    conversion_rate: float = 0.0
    active_subscribers: int = 0
    total_transactions: int = 0
    failed_transactions: int = 0
    average_order_value: float = 0.0
    total_donations: float = 0.0
    average_donation: float = 0.0
    donor_count: int = 0


@dataclass
class ProviderReport:
    """Reporte para un proveedor de pago."""
    provider: str
    is_configured: bool = False
    is_connected: bool = False
    configuration_checks: Dict[str, MonetizationCheck] = field(default_factory=dict)
    financial_metrics: FinancialMetrics = field(default_factory=FinancialMetrics)
    supported_models: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class MonetizationReport:
    """Reporte completo de monetización."""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    providers: Dict[str, ProviderReport] = field(default_factory=dict)
    overall_metrics: FinancialMetrics = field(default_factory=FinancialMetrics)
    total_revenue: float = 0.0
    issues_found: int = 0
    issues_fixed: int = 0
    configuration_score: float = 0.0
    health_score: float = 0.0


# =============================================================================
# INTERFAZ PARA PROVEEDORES DE PAGO
# =============================================================================

class PaymentProvider(ABC):
    """Interfaz base para proveedores de pago."""
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Verifica si el proveedor está configurado."""
        pass
    
    @abstractmethod
    def test_connection(self) -> MonetizationCheck:
        """Prueba la conexión con el API del proveedor."""
        pass
    
    @abstractmethod
    def get_financial_metrics(self, period: str = "30d") -> FinancialMetrics:
        """Obtiene métricas financieras del proveedor."""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Obtiene los modelos de monetización soportados."""
        pass
    
    def validate_configuration(self) -> Dict[str, MonetizationCheck]:
        """Valida la configuración del proveedor."""
        results = {}
        
        # Verificar si está configurado
        results["configuration"] = MonetizationCheck(
            name="Configuration Check",
            passed=self.is_configured(),
            message="✅ Configured" if self.is_configured() else "❌ Not configured",
            provider=self.name
        )
        
        # Verificar conexión
        conn_check = self.test_connection()
        results["connection"] = conn_check
        
        return results


# =============================================================================
# IMPLEMENTACIONES DE PROVEEDORES
# =============================================================================

class StripeProvider(PaymentProvider):
    """Proveedor Stripe."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("stripe", config)
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    def is_configured(self) -> bool:
        return bool(self.api_key and self.webhook_secret)
    
    def test_connection(self) -> MonetizationCheck:
        if not self.is_configured():
            return MonetizationCheck(
                name="Connection Test",
                passed=False,
                message="❌ Stripe not configured",
                provider="stripe"
            )
        
        try:
            # Probar conexión con la API de Stripe
            import stripe
            stripe.api_key = self.api_key
            
            # Hacer una llamada simple para verificar
            stripe.Account.retrieve()
            
            return MonetizationCheck(
                name="Connection Test",
                passed=True,
                message="✅ Stripe connection successful",
                provider="stripe"
            )
        except Exception as e:
            return MonetizationCheck(
                name="Connection Test",
                passed=False,
                message=f"❌ Stripe connection failed: {str(e)}",
                details={"error": str(e)},
                provider="stripe"
            )
    
    def get_financial_metrics(self, period: str = "30d") -> FinancialMetrics:
        metrics = FinancialMetrics()
        
        if not self.is_configured():
            return metrics
        
        try:
            import stripe
            stripe.api_key = self.api_key
            
            now = int(time.time())
            
            # Calcular fecha de inicio según el período
            if period.endswith("d"):
                days = int(period[:-1])
                start = now - (days * 24 * 60 * 60)
            elif period.endswith("m"):
                months = int(period[:-1])
                start = now - (months * 30 * 24 * 60 * 60)  # Aproximación
            else:
                start = now - (30 * 24 * 60 * 60)  # Default 30 días
            
            # Obtener balance (simplificado - en producción usar Balance Transactions)
            balance = stripe.Balance.retrieve()
            
            # Obtener suscripciones activas
            subscriptions = stripe.Subscription.list(
                status="active",
                limit=100
            )
            
            # Obtener pagos recientes
            charges = stripe.Charge.list(
                created={"gte": start},
                limit=100
            )
            
            # Calcular métricas
            total_revenue = sum(
                charge.amount / 100 for charge in charges.data 
                if charge.paid and charge.amount > 0
            )
            
            active_subscribers = len(subscriptions.data)
            total_transactions = len(charges.data)
            failed_transactions = sum(
                1 for charge in charges.data if not charge.paid
            )
            
            # MRR (Monthly Recurring Revenue) - aproximación
            mrr = sum(
                sub.plan.amount / 100 for sub in subscriptions.data 
                if sub.status == "active"
            )
            
            metrics.total_revenue = total_revenue
            metrics.mrr = mrr
            metrics.arr = mrr * 12
            metrics.active_subscribers = active_subscribers
            metrics.total_transactions = total_transactions
            metrics.failed_transactions = failed_transactions
            metrics.conversion_rate = 1.0 - (failed_transactions / total_transactions) if total_transactions > 0 else 0.0
            metrics.average_order_value = total_revenue / total_transactions if total_transactions > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"Error getting Stripe metrics: {e}")
        
        return metrics
    
    def get_supported_models(self) -> List[str]:
        return ["subscriptions", "one_time_payments"]


class PayPalProvider(PaymentProvider):
    """Proveedor PayPal."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("paypal", config)
        self.client_id = os.getenv("PAYPAL_CLIENT_ID")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
        self.access_token = None
    
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)
    
    def _get_access_token(self) -> Optional[str]:
        """Obtiene el access token de PayPal."""
        if not self.is_configured():
            return None
        
        try:
            auth = (self.client_id, self.client_secret)
            response = requests.post(
                "https://api.sandbox.paypal.com/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=auth
            )
            if response.status_code == 200:
                self.access_token = response.json().get("access_token")
                return self.access_token
        except Exception as e:
            self.logger.error(f"Error getting PayPal token: {e}")
        return None
    
    def test_connection(self) -> MonetizationCheck:
        if not self.is_configured():
            return MonetizationCheck(
                name="Connection Test",
                passed=False,
                message="❌ PayPal not configured",
                provider="paypal"
            )
        
        token = self._get_access_token()
        if token:
            return MonetizationCheck(
                name="Connection Test",
                passed=True,
                message="✅ PayPal connection successful",
                provider="paypal"
            )
        else:
            return MonetizationCheck(
                name="Connection Test",
                passed=False,
                message="❌ PayPal connection failed",
                provider="paypal"
            )
    
    def get_financial_metrics(self, period: str = "30d") -> FinancialMetrics:
        metrics = FinancialMetrics()
        
        if not self.is_configured():
            return metrics
        
        try:
            token = self._get_access_token()
            if not token:
                return metrics
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Obtener transacciones (simplificado)
            now = datetime.now()
            if period.endswith("d"):
                days = int(period[:-1])
                start_date = (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                start_date = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # PayPal API para transacciones
            response = requests.get(
                f"https://api.sandbox.paypal.com/v2/payments/payouts?start_date={start_date}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                # Procesar datos (simplificado)
                total_amount = sum(
                    float(item.get("amount", {}).get("value", 0)) 
                    for item in data.get("items", [])
                )
                metrics.total_revenue = total_amount
                metrics.total_transactions = len(data.get("items", []))
            
        except Exception as e:
            self.logger.error(f"Error getting PayPal metrics: {e}")
        
        return metrics
    
    def get_supported_models(self) -> List[str]:
        return ["subscriptions", "one_time_payments", "donations"]


class MercadoPagoProvider(PaymentProvider):
    """Proveedor MercadoPago."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("mercadopago", config)
        self.access_token = os.getenv("MP_ACCESS_TOKEN")
    
    def is_configured(self) -> bool:
        return bool(self.access_token)
    
    def test_connection(self) -> MonetizationCheck:
        if not self.is_configured():
            return MonetizationCheck(
                name="Connection Test",
                passed=False,
                message="❌ MercadoPago not configured",
                provider="mercadopago"
            )
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            response = requests.get(
                "https://api.mercadopago.com/v1/me",
                headers=headers
            )
            
            if response.status_code == 200:
                return MonetizationCheck(
                    name="Connection Test",
                    passed=True,
                    message="✅ MercadoPago connection successful",
                    provider="mercadopago"
                )
            else:
                return MonetizationCheck(
                    name="Connection Test",
                    passed=False,
                    message=f"❌ MercadoPago connection failed: {response.status_code}",
                    provider="mercadopago"
                )
        except Exception as e:
            return MonetizationCheck(
                name="Connection Test",
                passed=False,
                message=f"❌ MercadoPago connection failed: {str(e)}",
                provider="mercadopago"
            )
    
    def get_financial_metrics(self, period: str = "30d") -> FinancialMetrics:
        metrics = FinancialMetrics()
        
        if not self.is_configured():
            return metrics
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            # Obtener pagos recientes
            now = datetime.now()
            if period.endswith("d"):
                days = int(period[:-1])
                start_date = (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")
            else:
                start_date = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")
            
            # API de MercadoPago para búsqueda de pagos
            params = {
                "q": f"date_created:[{start_date} TO NOW]",
                "limit": 100
            }
            
            response = requests.get(
                "https://api.mercadopago.com/v1/payments/search",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                total_amount = sum(
                    float(payment.get("transaction_amount", 0)) 
                    for payment in results 
                    if payment.get("status") == "approved"
                )
                total_transactions = len(results)
                failed_transactions = sum(
                    1 for payment in results 
                    if payment.get("status") != "approved"
                )
                
                metrics.total_revenue = total_amount
                metrics.total_transactions = total_transactions
                metrics.failed_transactions = failed_transactions
                metrics.conversion_rate = 1.0 - (failed_transactions / total_transactions) if total_transactions > 0 else 0.0
                
        except Exception as e:
            self.logger.error(f"Error getting MercadoPago metrics: {e}")
        
        return metrics
    
    def get_supported_models(self) -> List[str]:
        return ["subscriptions", "one_time_payments"]


# =============================================================================
# FÁBRICA DE PROVEEDORES
# =============================================================================

def get_provider(provider_name: str, config: Optional[Dict] = None) -> Optional[PaymentProvider]:
    """Obtiene una instancia del proveedor solicitado."""
    providers = {
        "stripe": StripeProvider,
        "paypal": PayPalProvider,
        "mercadopago": MercadoPagoProvider
    }
    
    provider_class = providers.get(provider_name.lower())
    if provider_class:
        return provider_class(config)
    return None


# =============================================================================
# GESTOR DE CONFIGURACIÓN
# =============================================================================

class ConfigManager:
    """Gestiona la configuración del agente de mone
