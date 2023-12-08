#!/bin/bash
TYPE=n1-standard-1
NAME=slothbot
NEW_UUID=$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c 4 ; echo)

ZONE=us-west1-a
OPTION=$1
PREEMPTIBLE="--preemptible"
UBUNTU_VERSION="ubuntu-2204-jammy-v20231201"
IP=""

echo "This instance is preemtible, unless it's started with --prod";
case $OPTION in
    -p|--prod|--production)
       unset PREEMPTIBLE
       echo "Production mode enabled..."
       IP="104.199.116.124"
       echo;
esac

if [ -f secrets.sh ]; then
   source secrets.sh # truly, a travesty, sets TOKEN=token-[passphrase]
   echo "Here's where I say, hold on a second while we fire things up."
   gcloud compute project-info add-metadata --metadata token=$TOKEN
   echo;
else
   echo "Create 'secrets.sh', put a TOKEN=f00bar statement in it and then rerun this script."
   echo;
   exit;
fi

SLOTH_VERSION=0.1.0
SCRIPT=$(cat <<EOF
#!/bin/bash
if [ -d "/opt/slothbot/" ]; then
  echo "starting slothbot"
  sleep 10
  cd /opt/slothbot/
  /opt/start-slothbot.sh
else
  sudo su -
  date >> /opt/start.time
  apt-get update -y

  apt-get install unzip -y
  apt-get install python3-pip -y

  # conda
  mkdir -p ~/miniconda3
  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
  bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
  rm -rf ~/miniconda3/miniconda.sh

  # entropy
  apt-get -y install rng-tools
  cat "RNGDEVICE=/dev/urandom" >> /etc/default/rng-tools
  /etc/init.d/rng-tools restart

  cd /opt/
  git clone https://github.com/MittaAI/mitta-community.git
  mv mitta-community/cookbooks/piratebot ./mittabot
  
  cd /opt/mittabot
  pip3 install -r requirements.txt

  date >> /opt/done.time
fi
EOF
)

gcloud compute instances create $NAME-$NEW_UUID \
--machine-type $TYPE \
--image "$UBUNTU_VERSION" \
--image-project "ubuntu-os-cloud" \
--boot-disk-size "100GB" \
--boot-disk-type "pd-ssd" \
--boot-disk-device-name "$NEW_UUID" \
--service-account sloth-759@sloth-ai.iam.gserviceaccount.com \
--zone $ZONE \
--labels type=slothbot \
--tags slothbot,token-$TOKEN \
$PREEMPTIBLE \
--network-interface=address=$IP,network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
--metadata startup-script="$SCRIPT"
sleep 15

# add data
gcloud compute instances add-metadata $NAME-$NEW_UUID --zone $ZONE --metadata-from-file=shutdown-script=stop-mittabot-gc.sh

IP=$(gcloud compute instances describe $NAME-$NEW_UUID --zone $ZONE  | grep natIP | cut -d: -f2 | sed 's/^[ \t]*//;s/[ \t]*$//')

# gcloud compute firewall-rules create sloth-proxy --target-tags sloth --allow tcp:8389
echo "Password token is: $TOKEN"
echo "IP is: $IP"