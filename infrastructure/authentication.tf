resource "digitalocean_ssh_key" "default" {
  name       = "droplet-access-key"
  public_key = file(var.ssh_pub_key_path)
}

