# ============================================
# OUTPUTS
# ============================================
# Define qué información mostrar después de aplicar

output "secret_id" {
  description = "ID completo del secret creado"
  value       = google_secret_manager_secret.example.id
}

output "secret_name" {
  description = "Nombre corto del secret"
  value       = google_secret_manager_secret.example.secret_id
}

output "next_steps" {
  description = "Qué hacer después"
  value       = <<-EOT
    ✅ Secret creado exitosamente!

    Para agregar un valor al secret:

    echo "mi-valor-secreto" | \
      gcloud secrets versions add ${google_secret_manager_secret.example.secret_id} --data-file=-

    Para ver el secret en GCP Console:
    https://console.cloud.google.com/security/secret-manager/secret/${google_secret_manager_secret.example.secret_id}

    Para listar versiones:
    gcloud secrets versions list ${google_secret_manager_secret.example.secret_id}

    Para acceder al valor (requiere permisos):
    gcloud secrets versions access latest --secret=${google_secret_manager_secret.example.secret_id}
  EOT
}

# ============================================
# EXPLICACIÓN
# ============================================
#
# 1. OUTPUT BLOCK:
#    - Muestra información después de terraform apply
#    - Accesible con: terraform output
#    - Útil para:
#      - IPs, URLs, nombres de recursos
#      - Instrucciones para el usuario
#      - Inputs para otros módulos
#
# 2. VALUE:
#    - Puede referenciar atributos de recursos
#    - Formato: resource_type.resource_name.attribute
#
# 3. EOT (End Of Text):
#    - Heredoc para strings multi-línea
#    - Útil para instrucciones largas
#
# 4. VER OUTPUTS:
#    terraform output                 # Ver todos
#    terraform output secret_id       # Ver uno específico
#    terraform output -json            # Formato JSON
