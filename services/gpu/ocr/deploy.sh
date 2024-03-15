#!/bin/bash
CONFIG_FILE="config.sh"

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
NAME=ocr
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

# Get the current remote URL for 'origin'
remote_url=$(git remote get-url origin)

# Check if the URL is an SSH URL and convert it to HTTPS
if [[ "$remote_url" =~ ^git@github.com:(.+)/(.+).git$ ]]; then
    user="${BASH_REMATCH[1]}"
    repo="${BASH_REMATCH[2]}"
    REPO_URL="https://github.com/${user}/${repo}.git"
# Else, assume it's already an HTTPS URL, just remove the authentication part if present
else
    REPO_URL=$(echo $remote_url | sed -E 's/https:\/\/[^@]+@/https:\/\//')
    echo $https_url
fi

# Check if REPO_URL is not empty
if [ -z "$REPO_URL" ]; then
    echo "Failed to retrieve GitHub repository URL. Please make sure you're in a Git repository."
    exit 1
fi

# Extract the repository name from the URL
REPO_NAME=$(basename -s .git $REPO_URL)

if [ -z "$ZONE" ]; then
	echo "Need a valid zone to start [us-central1-a|us-east1-b]: --zone=us-central1-a"
	exit 1
fi

case $ZONE in
    us-central1-a)
        echo "Using $ZONE to start $NAME-$NEW_UUID..."
        ;;
    us-east1-b)
        echo "Using $ZONE to start $NAME-$NEW_UUID..."
        ;;
    *)
        echo "Invalid zone specified: $ZONE"
        exit 1
        ;;
esac

SCRIPT=$(cat <<EOF
#!/bin/bash
if [ -d "/opt/$REPO_NAME/" ]; then
  echo "Starting OCR services..."
  /opt/deeplearning/install-driver.sh
  cd /opt/mitta-community/services/gpu/ocr/
  bash start-ocr.sh

else
  sudo su -
  date >> /opt/start.time

  # apt-get
  apt-get update -y
  apt-get install python3-pip -y
  apt-get install git -y
 
  # cuda drivers
  /opt/deeplearning/install-driver.sh
  
  # download code
  cd /opt/
  git clone $REPO_URL
  cd /opt/$REPO_NAME/services/gpu/ocr/

  # copy files
  cp bid_token.py /root/
  cp nginx.conf.ocr /etc/nginx/nginx.conf

  # requirements
  pip install -r requirements.txt

  # prime the pump
  python model.py

  # grab the tokens and write to nginx htpasswrd and env
  cd /root
  python3 bid_token.py ocr

  # restart ngninx
  systemctl restart nginx.service

  # start instructor service
  cd /opt/$REPO_NAME/services/gpu/ocr/
  bash start-ocr.sh &

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
--create-disk=auto-delete=yes,boot=yes,device-name=instance-1,image=projects/ml-images/global/images/c0-deeplearning-common-gpu-v20231209-debian-11-py310,mode=rw,size=200,type=projects/$GC_PROJECT/zones/$ZONE/diskTypes/pd-ssd \
--no-shielded-secure-boot \
--shielded-vtpm \
--shielded-integrity-monitoring \
--labels=type=ocr \
--tags ocr,token-$TOKEN \
--reservation-affinity=any \
--metadata startup-script="$SCRIPT"
sleep 15

# add data
gcloud compute instances add-metadata $NAME-$NEW_UUID --zone $ZONE --metadata-from-file=shutdown-script=stop-ocr.sh

IP=$(gcloud compute instances describe $NAME-$NEW_UUID --zone $ZONE  | grep natIP | cut -d: -f2 | sed 's/^[ \t]*//;s/[ \t]*$//')

gcloud compute firewall-rules create ocr --target-tags ocr --allow tcp:9898
echo "Password token is: $TOKEN"
echo "IP is: $IP"
