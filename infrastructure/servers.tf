resource "digitalocean_droplet" "web" {
  image  = "ubuntu-18-04-x64"
  name   = "twitch-chat-service"
  region = "lon1"
  size   = "s-1vcpu-1gb"
  ssh_keys = [digitalocean_ssh_key.default.fingerprint]
}