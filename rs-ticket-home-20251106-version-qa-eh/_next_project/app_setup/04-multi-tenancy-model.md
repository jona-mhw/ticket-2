# 4. Modelo de Datos Multi-tenant

La arquitectura multi-tenant permite que una sola instancia de la aplicación y una sola base de datos sirvan a múltiples "inquilinos" (en el caso de Ticket Home, las clínicas) de forma aislada. La clave es segregar los datos a nivel de aplicación.

## El Principio: `tenant_id` en Cada Tabla

La forma más sencilla de implementar multi-tenancy es añadir una columna `tenant_id` (o `clinic_id` en nuestro caso) a cada tabla que contenga datos específicos de un inquilino.

### `models.py` - Implementación con SQLAlchemy

Se puede crear una clase base que incluya esta columna y otros campos comunes.

```python
# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Modelo para los inquilinos
class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    # ... otros campos del inquilino

# Clase base para modelos multi-tenant
class TenantScopedModel(db.Model):
    __abstract__ = True  # No crea una tabla para este modelo

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Clave foránea que apunta al inquilino
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    tenant = db.relationship('Tenant')

# Ejemplo de un modelo de datos que hereda la segregación
class Product(TenantScopedModel):
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Product {self.name}>'

# El modelo de Usuario también debe estar segregado
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    # ... otros campos

    # El usuario pertenece a un inquilino
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True) # Nullable para superusuarios
    tenant = db.relationship('Tenant')
```

## Filtrado Automático de Queries

El siguiente paso es asegurarse de que **todas las consultas a la base de datos estén filtradas por el `tenant_id` del usuario actual**.

Esto se puede lograr de varias maneras:

1.  **Manualmente en cada query**:
    ```python
    from flask_login import current_user

    products = Product.query.filter_by(tenant_id=current_user.tenant_id).all()
    ```
    Esto es propenso a errores, ya que es fácil olvidar el filtro.

2.  **Con un Query Base Personalizado (Recomendado)**:
    Puedes crear una clase de consulta personalizada que aplique el filtro automáticamente.

    ```python
    # models.py
    from sqlalchemy.orm import Query
    from flask_login import current_user

    class TenantScopedQuery(Query):
        def get(self, ident):
            # Sobrescribir `get` para que también filtre por tenant
            obj = super().get(ident)
            if obj is not None and hasattr(obj, 'tenant_id') and obj.tenant_id != current_user.tenant_id:
                 # Aquí podrías lanzar un 404 o retornar None
                 return None
            return obj

        def all(self):
            # Sobrescribir `all` para añadir el filtro
            if current_user.is_authenticated and hasattr(current_user, 'tenant_id') and current_user.tenant_id is not None:
                return super().filter_by(tenant_id=current_user.tenant_id).all()
            return super().all() # O lanzar un error si no hay inquilino

    # En tus modelos, especifica que usen esta query
    class Product(TenantScopedModel):
        query_class = TenantScopedQuery
        # ...
    ```
    Esta es una técnica más avanzada pero mucho más segura.

## Superusuarios

Los superusuarios son una excepción a la regla. No pertenecen a un solo inquilino (`tenant_id` es `NULL`) y pueden ver los datos de todos los inquilinos. La lógica de la aplicación debe tener en cuenta este caso especial al realizar consultas.

```python
# Ejemplo de una ruta que maneja superusuarios
@app.route('/products')
@login_required
def list_products():
    if current_user.is_superuser:
        # El superusuario ve todo
        products = Product.query.all()
    else:
        # El usuario normal solo ve lo suyo
        products = Product.query.filter_by(tenant_id=current_user.tenant_id).all()
    return render_template('products.html', products=products)
```

---

**Próximo paso:** [5. Integración con IAP](./05-iap-integration.md)
