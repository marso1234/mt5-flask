#!/bin/bash

# Exit on any error
set -e

echo "Updating package list..."
sudo apt update

echo "Installing Xfce desktop environment..."
sudo apt install -y xfce4 xfce4-goodies

echo "Installing xRDP..."
sudo apt install -y xrdp

echo "Configuring xRDP to use Xfce..."
echo "startxfce4" > ~/.xsession
sudo cp ~/.xsession /etc/skel/.xsession

echo "Updating startwm.sh to launch Xfce..."
sudo sed -i '/^test -x .*startwm.sh/,$d' /etc/xrdp/startwm.sh
echo "startxfce4" | sudo tee -a /etc/xrdp/startwm.sh

echo "Configuring xrdp.ini for session policy..."
sudo sed -i '/\\[Xorg\\]/,/^\\[/ s/^session_policy=.*/session_policy=allow/' /etc/xrdp/xrdp.ini

echo "Configuring sesman.ini to prevent session termination..."
sudo sed -i 's/^KillDisconnected=.*/KillDisconnected=false/' /etc/xrdp/sesman.ini
sudo sed -i 's/^IdleTimeLimit=.*/IdleTimeLimit=0/' /etc/xrdp/sesman.ini
sudo sed -i 's/^DisconnectedTimeLimit=.*/DisconnectedTimeLimit=0/' /etc/xrdp/sesman.ini

echo "Restarting xRDP services..."
sudo systemctl restart xrdp
sudo systemctl restart xrdp-sesman

echo "✅ xRDP with persistent Xfce session is configured successfully."
