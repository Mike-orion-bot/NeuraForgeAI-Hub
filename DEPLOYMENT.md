# 🚀 Guía de Despliegue en Render.com

## Requisitos previos

1. Cuenta en [Render.com](https://render.com)
2. Repositorio GitHub público o privado
3. Variables de entorno configuradas

## Paso 1: Crear una Base de Datos PostgreSQL en Render

1. Ir a **Dashboard** → **New +** → **PostgreSQL**
2. Configurar:
   - **Name**: `neuraforge-db` (o tu nombre)
   - **Database**: `neuraforge_prod`
   - **User**: `neuraforge_user`
   - **Region**: Ohio (u otra de tu preferencia)
   - **Plan**: Starter ($7/mes)
3. Copiar la **Internal Database URL** (no External)

## Paso 2: Conectar el Repositorio GitHub

1. Ir a **Dashboard** → **New +** → **Web Service**
2. Seleccionar el repositorio `NeuraForgeAI-Hub`
3. Configurar:
   - **Name**: `neuraforge-api`
   - **Environment**: Docker
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Region**: Ohio
   - **Plan**: Starter ($7/mes)

## Paso 3: Configurar Variables de Entorno

En el dashboard de Render, agregar:

```
PORT=10000
DATABASE_URL=postgresql://user:password@host:port/neuraforge_prod
SECRET_KEY=[Render lo genera automáticamente]
ACCESS_TOKEN_EXPIRE_MINUTES=1440
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
MP_ACCESS_TOKEN=...
ALLOWED_ORIGINS=https://tudominio.com,https://www.tudominio.com
```

## Paso 4: Desplegar

1. Hacer push a GitHub:
   ```bash
   git add .
   git commit -m "🚀 Listo para producción"
   git push origin main
   ```

2. Render deployará automáticamente desde el webhook de GitHub

3. Verificar en **Logs** que todo está funcionando

## Paso 5: Verificar el Deployment

```bash
# Reemplazar con tu dominio Render
curl https://neuraforge-api.onrender.com/health

# Respuesta esperada:
# {"status":"healthy","timestamp":"2024-01-15T10:30:45.123456","version":"1.0.0"}
```

## Troubleshooting

### ❌ Error: "SECRET_KEY not configured"
- Agregar `SECRET_KEY` en Environment Variables de Render
- Render puede generar uno automáticamente marcando "generateValue"

### ❌ Error: "database connection failed"
- Verificar que `DATABASE_URL` sea la URL **Internal** de PostgreSQL
- Que está en el mismo plan/región

### ❌ Error: "Health check failed"
- Esperar 60 segundos después del despliegue
- Verificar logs: `tail -f logs`

## Monitoreo en Producción

1. **Logs**: Dashboard → Logs
2. **Métricas**: Dashboard → Metrics (CPU, Memoria, Solicitudes)
3. **Health**: `https://neuraforge-api.onrender.com/health`

## Próximos pasos

- [ ] Agregar dominio personalizado
- [ ] Configurar SSL/TLS (automático en Render)
- [ ] Agregar estudiantes para auditoría
- [ ] Configurar backups automáticos de DB
- [ ] Implementar monitoreo con Sentry o similar

---

**¿Necesitas ayuda?** Contacta a soporte: support@render.com
