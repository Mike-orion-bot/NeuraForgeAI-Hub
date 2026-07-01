import os
import logging
from github import Github
from github.GithubException import GithubException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GitHubAgent:
    """Agente de IA encargado de gestionar repositorios y despliegues."""
    
    def __init__(self):
        # El agente lee tu Token de Acceso Personal desde las variables de entorno
        self.token = os.getenv("GITHUB_PAT")
        if not self.token:
            raise ValueError("🚨 El agente necesita la variable de entorno GITHUB_PAT")
        
        self.g = Github(self.token)
        self.user = self.g.get_user()
        logging.info(f"✅ Agente autenticado en GitHub como: {self.user.login}")

    def crear_o_actualizar_repositorio(self, nombre_repo: str, descripcion: str, es_privado: bool = False):
        """Crea el repositorio si no existe, o lo obtiene si ya existe."""
        try:
            repo = self.user.get_repo(nombre_repo)
            logging.info(f"El repositorio {nombre_repo} ya existe. Sincronizando...")
            return repo
        except GithubException as e:
            if e.status == 404:
                logging.info(f"Creando nuevo repositorio: {nombre_repo}...")
                return self.user.create_repo(
                    name=nombre_repo,
                    description=descripcion,
                    private=es_privado,
                    auto_init=True
                )
            else:
                raise e

    def subir_archivo(self, repo, ruta_local: str, ruta_github: str, mensaje_commit: str):
        """El agente lee un archivo local y lo empuja al repositorio."""
        try:
            with open(ruta_local, 'rb') as file:
                contenido = file.read()

            try:
                # Intenta actualizar si el archivo ya existe
                contents = repo.get_contents(ruta_github)
                repo.update_file(
                    contents.path, 
                    mensaje_commit, 
                    contenido, 
                    contents.sha
                )
                logging.info(f"🔄 Archivo actualizado: {ruta_github}")
            except GithubException:
                # Si no existe, lo crea
                repo.create_file(
                    ruta_github, 
                    mensaje_commit, 
                    contenido
                )
                logging.info(f"📄 Archivo creado: {ruta_github}")
                
        except FileNotFoundError:
            logging.error(f"❌ El agente no encontró el archivo local: {ruta_local}")
        except Exception as e:
            logging.error(f"❌ Error al subir {ruta_github}: {e}")

# ==========================================
# EJECUCIÓN DEL AGENTE
# ==========================================
if __name__ == "__main__":
    agente = GitHubAgent()
    
    # 1. El agente prepara el repositorio
    repo_neuraforge = agente.crear_o_actualizar_repositorio(
        nombre_repo="NeuraforgeAI-Hub",
        descripcion="Ecosistema de monetización, MiniApp y Motor Antifraude de NeuraforgeAI",
        es_privado=False # Cambia a True si aún no quieres que sea público
    )
    
    # 2. Rutas de los archivos que el agente va a subir (Ajusta las rutas locales según tu entorno)
    archivos_a_subir = [
        {"local": "./core/antifraud/engine.py", "github": "core/antifraud/engine.py"},
        {"local": "./core/payment/orion_cash.py", "github": "core/payment/orion_cash.py"},
        {"local": "./apps/miniapp_telegram/lucy_telegram_v2.py", "github": "apps/miniapp_telegram/lucy_telegram_v2.py"}
    ]
    
    # 3. El agente procesa la carga
    for archivo in archivos_a_subir:
        agente.subir_archivo(
            repo=repo_neuraforge,
            ruta_local=archivo["local"],
            ruta_github=archivo["github"],
            mensaje_commit=f"🤖 Agente IA: Despliegue automatizado de {archivo['github']}"
        )
    
    logging.info(f"🚀 Tarea finalizada. Repositorio listo en: https://github.com/{agente.user.login}/NeuraforgeAI-Hub")
