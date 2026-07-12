# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# BlissOSINT VM: `vagrant up` gives you a booted, XP-themed OSINT workstation.
#
#   vagrant up          # build + provision the VM (full desktop + toolkit)
#   vagrant reload       # reboot to land on the themed desktop
#   vagrant ssh          # shell in
#   vagrant destroy      # tear it down (treat as disposable -- see docs/opsec.md)
#
# Requires Vagrant + a provider (VirtualBox or libvirt). This runs the SAME
# provision/provision.sh as an in-place install, so the VM and a manual setup
# stay in sync.

Vagrant.configure("2") do |config|
  config.vm.box = "debian/bookworm64"
  config.vm.hostname = "bliss-osint"

  # A GUI desktop needs some headroom.
  config.vm.provider "virtualbox" do |vb|
    vb.name = "BlissOSINT"
    vb.gui = true
    vb.memory = 4096
    vb.cpus = 2
    # Enable a usable display for the XFCE/XP desktop.
    vb.customize ["modifyvm", :id, "--vram", "128"]
    vb.customize ["modifyvm", :id, "--graphicscontroller", "vmsvga"]
  end

  config.vm.provider "libvirt" do |lv|
    lv.memory = 4096
    lv.cpus = 2
    lv.graphics_type = "spice"
  end

  # Full provision: desktop + XP theming + OSINT toolkit.
  # BLISS_USER tells the theming which account to skin (Vagrant's default user).
  config.vm.provision "shell", inline: <<-SHELL
    set -e
    export BLISS_USER=vagrant
    /vagrant/provision/provision.sh
    echo "BlissOSINT provisioned. Run 'vagrant reload' then log in as vagrant."
  SHELL
end
