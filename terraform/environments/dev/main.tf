# Este archivo es el punto de entrada para el ambiente de DEV.
# Llama al módulo principal de la aplicación y le pasa las variables
# definidas en el archivo terraform.tfvars.

module "app" {
  source = "../../modules/app"

  # Las variables se cargan automáticamente desde terraform.tfvars
  # por lo que no es necesario repetirlas aquí.
}
