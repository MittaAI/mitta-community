#!/bin/bash
CONFIG_FILE="deploy_config.sh"

# Function to prompt user for missing variables
prompt_missing_variables() {
    echo "Please provide the following information:"
    read -p "Enter TOKEN: " TOKEN
    read -p "Enter SERVICE_ACCOUNT: " SERVICE_ACCOUNT
    read -p "Enter GC_PROJECT: " GC_PROJECT
}

# Function to update or create the config file
update_config_file() {
    echo "TOKEN=\"$TOKEN\"" > $CONFIG_FILE
    echo "SERVICE_ACCOUNT=\"$SERVICE_ACCOUNT\"" >> $CONFIG_FILE
    echo "GC_PROJECT=\"$GC_PROJECT\"" >> $CONFIG_FILE
}

# Load configuration if exists
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# Check if variables are defined, if not prompt the user
if [ -z "$TOKEN" ] || [ -z "$SERVICE_ACCOUNT" ] || [ -z "$GC_PROJECT" ]; then
    prompt_missing_variables
    update_config_file
fi

# Setup boxes
TYPE=g2-standard-8
NAME=instructor
NEW_UUID=$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c 4 ; echo)

PREEMPTIBLE=" \
--maintenance-policy=TERMINATE \
--provisioning-model=SPOT \
--instance-termination-action=STOP \
"

# load arguments
for arg in "$@"; do
	case $arg in
		-z=*|--zone=*)
			ZONE="${arg#*=}"
			;;
		-p|--prod|--production)
			PROD_MODE="true"
			;;
	esac
done

if [ "$PROD_MODE" == "true" ]; then
	unset PREEMPTIBLE
	echo "Production mode enabled..."
	IP=""
	echo
else
	echo "This instance is preemtible, unless it's started with --prod"
fi

# Check if there are any uncommitted changes in the Git repository
if [[ $(git status --porcelain) ]]; then
  echo "Failing to deploy as local directory is not committed to Github."
  exit 1
else
  echo "Git repository is up to date."
  # Add your deployment script commands here
fi

if [ -z "$ZONE" ]; then
	echo "Need a valid zone to start [us-central1-a|us-east1-b]: --zone=us-central1-a"
	exit 1
fi

SCRIPT=$(cat <<EOF
#!/bin/bash
if [ -d "/opt/mitta-community/" ]; then
  echo "Starting Instructor services..."
  /opt/deeplearning/install-driver.sh
  cd /opt/mitta-community/services/gpu/instructor/
  bash start-instructor.sh

else
  sudo su -
  date >> /opt/start.time

  apt-get update -y

  apt-get install apache2-utils -y
  apt-get install nginx -y
  apt-get install build-essential -y
  apt-get install unzip -y
  apt-get install python3-pip -y
  apt-get install git -y
  apt-get install gcc -y
  
  # install cuda drivers, every time
  /opt/deeplearning/install-driver.sh
  
  # download code
  cd /opt/
  git clone https://github.com/MittaAI/mitta-community.git
  cd /opt/mitta-community/services/gpu/instructor/

  # copy files
  cp bid_token.py /root/
  cp nginx.conf.instructor /etc/nginx/nginx.conf

  # grab the tokens and write to nginx htpasswrd and env
  cd /root
  python3 bid_token.py instructor

  # fschat

  # huggingface
  pip install --upgrade huggingface_hub

  # requirements
  cd /opt/mitta-community/services/gpu/instructor/
  pip install -r requirements.txt

  # restart ngninx
  systemctl restart nginx.service

  # start instructor service
  bash start-instructor.sh

  date >> /opt/done.time

fi
EOF
)

gcloud compute instances create $NAME-$NEW_UUID \
--project=$GC_PROJECT \
--zone=$ZONE \
--machine-type=$TYPE \
--network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
--no-restart-on-failure \
$PREEMPTIBLE \
--service-account=$SERVICE_ACCOUNT \
--scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
--accelerator=count=1,type=nvidia-l4 \
--create-disk=auto-delete=yes,boot=yes,device-name=instance-1,image=projects/ml-images/global/images/c0-deeplearning-common-gpu-v20230925-debian-11-py310,mode=rw,size=200,type=projects/$GC_PROJECT/zones/$ZONE/diskTypes/pd-ssd \
--no-shielded-secure-boot \
--shielded-vtpm \
--shielded-integrity-monitoring \
--labels=type=beast \
--tags beast,token-$TOKEN \
--reservation-affinity=any \
--metadata startup-script="$SCRIPT"
sleep 15

# add data
gcloud compute instances add-metadata $NAME-$NEW_UUID --zone $ZONE --metadata-from-file=shutdown-script=stop-sloth.sh

IP=$(gcloud compute instances describe $NAME-$NEW_UUID --zone $ZONE  | grep natIP | cut -d: -f2 | sed 's/^[ \t]*//;s/[ \t]*$//')

# gcloud compute firewall-rules create beast --target-tags beast --allow tcp:8888
echo "Password token is: $TOKEN"
echo "IP is: $IP"
