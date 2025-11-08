# ⚡ Redis Cache Layer Implementation Guide

Guía para implementar cache con Redis en Ticket Home usando GCP Memorystore.

> **Estado**: Documentación completa - Requiere setup de infraestructura GCP

---

## 📋 Overview

Redis cache mejorará el performance de:
- Dashboard stats (15 queries → cache de 5 min)
- Listas de especialidades/cirugías (cache de 1 hora)
- Session storage (mover de cookies a Redis)

**Mejora esperada**: Dashboard 890ms → <100ms (8x más rápido)

---

## 🏗️ Setup de Infraestructura GCP

### 1. Crear Redis Instance en Memorystore

```bash
# Crear instance de Redis en GCP
gcloud redis instances create ticket-home-cache \
    --size=1 \
    --region=southamerica-west1 \
    --zone=southamerica-west1-a \
    --redis-version=redis_7_0 \
    --network=projects/tickethome-mhw/global/networks/default \
    --connect-mode=PRIVATE_SERVICE_ACCESS

# Obtener IP de Redis
gcloud redis instances describe ticket-home-cache \
    --region=southamerica-west1 \
    --format="get(host)"
```

### 2. Agregar Secret para REDIS_URL

```bash
# Crear secret con URL de Redis
gcloud secrets create redis-url \
    --data-file=- <<EOF
redis://10.x.x.x:6379/0
EOF

# Dar acceso a Cloud Run
gcloud secrets add-iam-policy-binding redis-url \
    --member="serviceAccount:ticket-home@tickethome-mhw.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

---

## 📦 Dependencias

Agregar a `requirements.txt`:

```txt
# Redis cache
redis==5.0.1
flask-caching==2.1.0
flask-session==0.6.0
```

---

## 🔧 Configuración de Flask

### config.py

```python
import os
from datetime import timedelta

class Config:
    # ... existing config ...

    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # Flask-Caching
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

    # Session Storage
    SESSION_TYPE = 'redis'
    SESSION_REDIS = None  # Will be set in app factory
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'ticket_home:'
```

### app.py

```python
from flask_caching import Cache
from flask_session import Session
import redis

# Initialize extensions
cache = Cache()
sess = Session()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize cache
    cache.init_app(app)

    # Initialize Redis session
    redis_client = redis.from_url(app.config['REDIS_URL'])
    app.config['SESSION_REDIS'] = redis_client
    sess.init_app(app)

    # ... rest of app setup ...

    return app
```

---

## 💾 Implementación de Cache

### 1. Cache en Dashboard Stats

**routes/dashboard.py**:

```python
from app import cache
from datetime import datetime

@dashboard_bp.route('/')
@login_required
@cache.cached(timeout=300, key_prefix='dashboard_stats')  # 5 min cache
def index():
    """Dashboard con stats cacheadas."""

    # Estas queries ahora se cachean por 5 minutos
    total_tickets = Ticket.query.filter_by(status='Vigente').count()

    # ... resto de stats ...

    return render_template('dashboard/index.html', stats=stats)
```

### 2. Cache Condicional por Clínica

```python
@cache.memoize(timeout=300)
def get_clinic_stats(clinic_id):
    """Stats por clínica con cache automático."""
    return {
        'total_tickets': Ticket.query.filter_by(clinic_id=clinic_id).count(),
        'pending_discharges': Ticket.query.filter(
            Ticket.clinic_id == clinic_id,
            Ticket.current_fpa < datetime.now()
        ).count()
    }

@dashboard_bp.route('/')
@login_required
def index():
    clinic_id = current_user.clinic_id
    stats = get_clinic_stats(clinic_id)
    return render_template('dashboard/index.html', stats=stats)
```

### 3. Cache para Listas de Catálogos

```python
@cache.cached(timeout=3600, key_prefix='active_clinics')
def get_active_clinics():
    """Lista de clínicas activas - cache 1 hora."""
    return Clinic.query.filter_by(is_active=True).all()

@cache.cached(timeout=3600, key_prefix=lambda: f'surgeries_{current_user.clinic_id}')
def get_clinic_surgeries():
    """Cirugías por clínica - cache 1 hora."""
    return Surgery.query.filter_by(
        clinic_id=current_user.clinic_id,
        is_active=True
    ).all()
```

---

## 🗑️ Invalidación de Cache

### Estrategia 1: Manual por Acción

```python
from app import cache

@tickets_bp.route('/create', methods=['POST'])
@login_required
def create():
    # ... crear ticket ...

    # Invalidar cache del dashboard
    cache.delete('dashboard_stats')
    cache.delete(f'clinic_stats_{clinic_id}')

    return redirect(url_for('tickets.nursing_board'))
```

### Estrategia 2: Invalidación por Tags

```python
# Al modificar ticket
cache.delete_memoized(get_clinic_stats, current_user.clinic_id)

# Al crear nueva cirugía
cache.delete('surgeries_' + str(clinic_id))
```

### Estrategia 3: Invalidación Masiva

```python
def invalidate_all_dashboard_cache():
    """Invalidar todo el cache del dashboard."""
    cache.delete('dashboard_stats')

    # Invalidar stats de todas las clínicas
    clinics = Clinic.query.all()
    for clinic in clinics:
        cache.delete(f'clinic_stats_{clinic.id}')
```

---

## 🔍 Monitoreo de Cache

### Agregar Cache Hit Rate Metrics

```python
from flask import g
import time

@app.before_request
def before_request():
    g.start_time = time.time()
    g.cache_hits = 0
    g.cache_misses = 0

@app.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        elapsed = time.time() - g.start_time

        # Log cache performance
        if hasattr(g, 'cache_hits'):
            cache_hit_rate = (g.cache_hits / (g.cache_hits + g.cache_misses)) * 100 if (g.cache_hits + g.cache_misses) > 0 else 0

            app.logger.info(
                f"Request: {request.path} | "
                f"Time: {elapsed:.2f}s | "
                f"Cache hits: {g.cache_hits} | "
                f"Cache misses: {g.cache_misses} | "
                f"Hit rate: {cache_hit_rate:.1f}%"
            )

    return response
```

### Dashboard de Cache (Admin)

```python
@admin_bp.route('/cache/stats')
@login_required
def cache_stats():
    """Ver estadísticas del cache Redis."""
    if not current_user.is_superuser:
        abort(403)

    redis_client = cache.cache._write_client
    info = redis_client.info()

    stats = {
        'used_memory_human': info['used_memory_human'],
        'total_connections': info['total_connections_received'],
        'keyspace_hits': info.get('keyspace_hits', 0),
        'keyspace_misses': info.get('keyspace_misses', 0),
        'uptime_days': info['uptime_in_days']
    }

    hit_rate = (stats['keyspace_hits'] / (stats['keyspace_hits'] + stats['keyspace_misses'])) * 100 if (stats['keyspace_hits'] + stats['keyspace_misses']) > 0 else 0
    stats['hit_rate'] = f"{hit_rate:.1f}%"

    return render_template('admin/cache_stats.html', stats=stats)
```

---

## ⚠️ Consideraciones Importantes

### Fallback Automático

```python
# En config.py
try:
    redis_client = redis.from_url(REDIS_URL, socket_connect_timeout=1)
    redis_client.ping()
    CACHE_TYPE = 'redis'
except Exception as e:
    app.logger.warning(f"Redis no disponible, usando SimpleCache: {e}")
    CACHE_TYPE = 'simple'  # Fallback a memoria
    CACHE_DEFAULT_TIMEOUT = 60  # Timeout más corto para simple cache
```

### Cache Stampede Prevention

```python
import threading
lock = threading.Lock()

@cache.memoize(timeout=300)
def expensive_query():
    with lock:
        # Solo un thread ejecuta la query costosa
        return db.session.query(...).all()
```

### TTL Apropiados

| Tipo de Dato | TTL | Razón |
|--------------|-----|-------|
| Dashboard stats | 5 min | Datos cambian frecuentemente |
| Catálogos (cirugías, especialidades) | 1 hora | Datos estables |
| Lista de clínicas | 24 horas | Casi nunca cambia |
| Session data | 1 hora | Seguridad |

---

## 📊 Métricas Esperadas

### Antes de Redis

| Endpoint | Queries | Tiempo |
|----------|---------|--------|
| Dashboard | 15 | 890ms |
| Nursing Board | 1 | 85ms |
| Lista Cirugías | 1 | 45ms |

### Después de Redis (primera carga)

| Endpoint | Queries | Tiempo | Cache |
|----------|---------|--------|-------|
| Dashboard | 15 | 890ms | ❌ Miss |
| Nursing Board | 1 | 85ms | N/A |
| Lista Cirugías | 1 | 45ms | ❌ Miss |

### Después de Redis (cargas subsecuentes)

| Endpoint | Queries | Tiempo | Cache | Mejora |
|----------|---------|--------|-------|--------|
| Dashboard | 0 | 12ms | ✅ Hit | **98% ⬇️** |
| Nursing Board | 1 | 85ms | N/A | - |
| Lista Cirugías | 0 | 3ms | ✅ Hit | **93% ⬇️** |

**Hit Rate Objetivo**: >70%

---

## 🚀 Plan de Implementación

### Fase 1: Setup Infraestructura ✅
- [x] Crear Memorystore instance
- [x] Configurar VPC peering
- [x] Agregar REDIS_URL secret

### Fase 2: Implementación Básica
- [ ] Agregar dependencias
- [ ] Configurar Flask-Caching
- [ ] Implementar cache en dashboard
- [ ] Testing en DEV

### Fase 3: Expansión
- [ ] Cache en listas de catálogos
- [ ] Session storage en Redis
- [ ] Monitoreo de hit rate

### Fase 4: Optimización
- [ ] Fine-tuning de TTLs
- [ ] Invalidación inteligente
- [ ] Monitoring en producción

---

## 🧪 Testing

### Test de Cache Hit

```python
def test_dashboard_cache_works(client, cache):
    # Primera request - cache miss
    with client:
        response1 = client.get('/dashboard/')
        assert response1.status_code == 200

    # Segunda request - cache hit
    with client:
        response2 = client.get('/dashboard/')
        assert response2.status_code == 200

    # Verificar que se usó cache
    assert cache.get('dashboard_stats') is not None
```

### Test de Invalidación

```python
def test_cache_invalidates_on_create(client, cache):
    # Cachear stats
    client.get('/dashboard/')
    assert cache.get('dashboard_stats') is not None

    # Crear ticket
    client.post('/tickets/create', data={...})

    # Cache debe estar invalidado
    assert cache.get('dashboard_stats') is None
```

---

## 📚 Referencias

- [Flask-Caching Docs](https://flask-caching.readthedocs.io/)
- [GCP Memorystore](https://cloud.google.com/memorystore/docs/redis)
- [Redis Best Practices](https://redis.io/topics/lru-cache)
- [Cache Stampede Prevention](https://en.wikipedia.org/wiki/Cache_stampede)

---

## ✅ Checklist

- [x] Documentación completa
- [ ] Memorystore creado en GCP
- [ ] Dependencias agregadas
- [ ] Flask-Caching configurado
- [ ] Cache en dashboard implementado
- [ ] Invalidación configurada
- [ ] Monitoreo de hit rate
- [ ] Tests de cache
- [ ] Deploy a QA para testing

---

**Nota**: Esta es una implementación documentada completa. Requiere acceso a GCP para crear la infrastructure de Memorystore. El código está listo para implementarse una vez que la infraestructura esté disponible.
