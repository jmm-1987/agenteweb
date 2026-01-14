# Guía de Despliegue en Render

## Pasos para Desplegar

### 1. Preparar el Repositorio

1. Asegúrate de que todos los archivos estén commitados:
```bash
git add .
git commit -m "Sistema de gestión de tareas web"
git push origin main
```

### 2. Crear Servicio en Render

1. Ve a [Render Dashboard](https://dashboard.render.com/)
2. Click en "New +" → "Web Service"
3. Conecta tu repositorio Git
4. Render detectará automáticamente el archivo `render.yaml`

### 3. Configurar Variables de Entorno

En la sección "Environment" del servicio, añade:

**Requeridas:**
- `ADMIN_PASSWORD`: Tu contraseña para el panel de administración
- `SECRET_KEY`: Genera una clave aleatoria (Render puede generarla automáticamente)

**Opcionales (ya configuradas en render.yaml):**
- `WHISPER_MODEL`: `base` (recomendado)
- `WHISPER_DEVICE`: `cpu`
- `WHISPER_COMPUTE_TYPE`: `int8`
- `DATA_DIR`: `/opt/render/project/src/data`
- `SQLITE_PATH`: `/opt/render/project/src/data/app.db`

### 4. Configurar Persistent Disk (CRÍTICO)

**⚠️ IMPORTANTE**: Sin esto, los datos se perderán en cada reinicio.

1. En la configuración del servicio, ve a "Disks"
2. Click en "Add Disk"
3. Configura:
   - **Name**: `data-disk`
   - **Mount Path**: `/opt/render/project/src/data`
   - **Size**: 1GB (mínimo)

### 5. Configurar Build y Start

Render detectará automáticamente desde `render.yaml`:

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

**Nota importante:** 
- Render usará Python 3.11.0 automáticamente
- El build es simple y directo
- Si hay problemas con la compilación de `av`, puede que necesites configurar las dependencias del sistema manualmente en Render

### 6. Desplegar

1. Click en "Create Web Service"
2. Render comenzará el build automáticamente
3. El primer build puede tardar 5-10 minutos (descarga del modelo Whisper)
4. Una vez completado, tu app estará disponible en `https://tu-app.onrender.com`

## Verificación Post-Despliegue

### 1. Verificar que la App Funciona

- Visita la URL de tu app
- Deberías ver la interfaz de gestión de tareas

### 2. Verificar Persistent Disk

1. Crea una tarea de prueba
2. Reinicia el servicio manualmente
3. Verifica que la tarea sigue existiendo

### 3. Verificar Procesamiento de Audio

1. Haz clic en "Grabar"
2. Di algo como: "Crear tarea llamar al cliente Test mañana"
3. Verifica que se transcribe y crea la tarea correctamente

## Optimizaciones para Free Tier

### Límites del Free Tier

- **Memoria**: 512MB RAM
- **CPU**: Compartido
- **Sleep**: Se duerme después de 15 minutos de inactividad
- **Disco**: Requiere Persistent Disk (gratis hasta 1GB)

### Configuraciones Recomendadas

**Para evitar "Out of Memory":**
- `WHISPER_MODEL=base` (no usar `small` o superior)
- `WHISPER_COMPUTE_TYPE=int8` (no `float16`)
- `--workers 2` (no más de 2 workers)

**Para mejor rendimiento:**
- Pre-carga del modelo durante build (ya configurado)
- Timeout de 300 segundos para procesamiento de audio
- Threads: 4 por worker

## Troubleshooting

### Error: "Out of Memory"

**Síntomas:**
- El servicio se reinicia constantemente
- Logs muestran "Ran out of memory"

**Solución:**
1. Verificar que `WHISPER_MODEL=base`
2. Verificar que `WHISPER_COMPUTE_TYPE=int8`
3. Reducir workers a 1 si persiste
4. Considerar upgrade a plan de pago

### Error: "Base de datos no persiste"

**Síntomas:**
- Las tareas desaparecen tras reinicio
- Base de datos se resetea

**Solución:**
1. Verificar que Persistent Disk esté configurado
2. Verificar que `DATA_DIR` y `SQLITE_PATH` apunten al disco
3. Verificar logs para errores de permisos

### Error: "Build falla"

**Síntomas:**
- Build no completa
- Error en preload_whisper_model.py

**Solución:**
1. El script de pre-carga no debería fallar el build
2. Si falla, verificar logs del build
3. El modelo se cargará en el primer uso si falla el pre-carga

### Error: "No se puede acceder al micrófono"

**Síntomas:**
- En el navegador aparece error de permisos
- MediaRecorder no funciona

**Solución:**
1. Verificar que la app esté en HTTPS (requerido para MediaRecorder)
2. Render proporciona HTTPS automáticamente
3. Verificar permisos del navegador

## Monitoreo

### Logs Importantes

**Build:**
```
[INFO] Pre-cargando modelo Whisper...
[INFO] Modelo: base
[INFO] ✅ Modelo pre-cargado correctamente
```

**Runtime:**
```
[INFO] Base de datos inicializada en /opt/render/project/src/data/app.db
[INFO] Procesando audio: recording.ogg
[INFO] Transcripción completada: X caracteres
```

### Métricas a Monitorear

1. **Uso de memoria**: Debe estar bajo 512MB
2. **Tiempo de respuesta**: < 5 segundos para transcripción
3. **Tasa de éxito**: % de transcripciones exitosas
4. **Errores**: Revisar logs periódicamente

## Actualizaciones

Para actualizar la aplicación:

1. Hacer cambios en tu repositorio local
2. Commit y push:
```bash
git add .
git commit -m "Descripción de cambios"
git push origin main
```
3. Render detectará automáticamente y hará nuevo deploy

## Backup

### Backup Manual de Base de Datos

1. Conectarse al servicio via SSH (si está disponible)
2. Copiar archivo de base de datos:
```bash
cp /opt/render/project/src/data/app.db backup.db
```

### Backup Automático

Considera usar un servicio de backup externo o scripts programados si los datos son críticos.

## Soporte

Si encuentras problemas:

1. Revisar logs en Render Dashboard
2. Verificar configuración de variables de entorno
3. Verificar que Persistent Disk esté montado correctamente
4. Consultar documentación de Render: https://render.com/docs

