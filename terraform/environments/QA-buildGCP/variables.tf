variable "project_id" {
  description = "The ID of the project in which to provision resources."
  type        = string
}

variable "region" {
  description = "The region for the resources."
  type        = string
  default     = "us-central1"
}

variable "image_url" {
  description = "The URL of the image to build and push."
  type        = string
}

variable "source_dir" {
  description = "The local directory containing the source code."
  type        = string
  default     = "../../.."
}
