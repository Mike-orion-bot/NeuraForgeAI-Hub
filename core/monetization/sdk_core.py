"""
Módulo de Licenciamiento y Control de Marca de Agua (SDK)
"""
import time
import logging

class NeuraforgeCoreSDK:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.is_premium = self._validate_license()
        self._boot_sequence()

    def _validate_license(self) -> bool:
        """
        Valida si el usuario pagó por la licencia comercial/marca blanca.
        En producción real, esto haría un POST a tu base de datos de Supabase.
        """
        valid_premium_keys = ["NFG-PRO-MASTER", "NFG-ENTERPRISE-2026"]
        return self.api_key in valid_premium_keys

    def _boot_sequence(self):
        """Secuencia de arranque obligatoria."""
        if self.is_premium:
            logging.info("🔑 Licencia Neuraforge PRO verificada. Marca de agua desactivada.")
        else:
            # Marca de agua obligatoria en terminal para la versión gratuita
            print("\n" + "="*55)
            print(" 🔱 NEURAFORGEAI® SDK - Community Edition 🔱")
            print(" Licencia gratuita. El código incluye firmas de red.")
            print(" Apoya el proyecto adquiriendo una API Key PRO.")
            print("="*55 + "\n")
            
            # Pequeño retraso publicitario (2 segundos) para incentivar la compra
            time.sleep(2) 
