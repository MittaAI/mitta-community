#!/bin/bash
CONFIG_FILE="config.sh"

# Function to prompt user for missing variables
prompt_missing_variables() {
    echo "Please provide the following information:"
    read -p "Enter TOKEN: " TOKEN
    read -p "Enter SERVICE_ACCOUNT: " SERVICE_ACCOUNT
    read -p "Enter GC_PROJECT: " GC_PROJECT
    read -p "Enter CONTROLLER_IP: " CONTROLLER_IP
}

# Function to update or create the config file
update_config_file() {
    echo "TOKEN=\"$TOKEN\"" > $CONFIG_FILE
    echo "SERVICE_ACCOUNT=\"$SERVICE_ACCOUNT\"" >> $CONFIG_FILE
    echo "GC_PROJECT=\"$GC_PROJECT\"" >> $CONFIG_FILE
    echo "CONTROLLER_IP=\"$CONTROLLER_IP\"" >> $CONFIG_FILE
}

# Load configuration if exists
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# Check if variables are defined, if not prompt the user
if [ -z "$TOKEN" ] || [ -z "$SERVICE_ACCOUNT" ] || [ -z "$GC_PROJECT" ] || [ -z "$CONTROLLER_IP" ]; then
    prompt_missing_variables
    update_config_file
fi

TYPE=e2-standard-2
NAME=controller
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
    IP=$CONTROLLER_IP
    echo
else
    IP=""
    echo "This instance is preemtible, unless it's started with --prod"
fi

# Check if there are any uncommitted changes in the Git repository
if [[ $(git status --porcelain) ]]; then
  echo "Error: There are uncommitted changes in the Git repository."
  echo "Please commit or stash your changes before deploying."
  exit 1
else
  echo "Git repository is up to date. Continuing with deployment..."
  # Add your deployment script commands here
fi

# Get the GitHub repository URL
REPO_URL=$(git config --get remote.origin.url)

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
  echo "starting controller"
  bash start-controller.sh
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

  pip install google-cloud
  pip install google-api-python-client
  pip install google-auth-httplib2
  pip install gunicorn
  pip install flask

  # download code
  cd /opt/
  git clone $REPO_URL
  cd /opt/$REPO_NAME/services/gpu/controller/

  # copy files
  cp bid_token.py /root/
  cp nginx.conf.controller /etc/nginx/nginx.conf

  # grab the tokens and write to nginx htpasswrd and env
  cd /root
  python3 bid_token.py controller

  # restart ngninx
  systemctl restart nginx.service

  cd /opt/$REPO_NAME/services/gpu/controller/
  ./start-controller.sh &

  date >> /opt/done.time

fi
EOF
)

gcloud compute instances create $NAME-$NEW_UUID \
--project=$GC_PROJECT \
--zone=$ZONE \
--machine-type=$TYPE \
--network-interface=address=$IP,network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
--no-restart-on-failure \
$PREEMPTIBLE \
--service-account=$SERVICE_ACCOUNT \
--scopes=https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/compute,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
--create-disk=auto-delete=yes,boot=yes,device-name=instance-1,image=projects/debian-cloud/global/images/debian-11-bullseye-v20231004,mode=rw,size=100,type=projects/$GC_PROJECT/zones/$ZONE/diskTypes/pd-ssd \
--no-shielded-secure-boot \
--shielded-vtpm \
--shielded-integrity-monitoring \
--labels=type=beast \
--tags controller,token-$TOKEN \
--reservation-affinity=any \
--metadata startup-script="$SCRIPT"
sleep 15

# add data
gcloud compute instances add-metadata $NAME-$NEW_UUID --zone $ZONE --metadata-from-file=shutdown-script=stop-controller.sh

IP=$(gcloud compute instances describe $NAME-$NEW_UUID --zone $ZONE  | grep natIP | cut -d: -f2 | sed 's/^[ \t]*//;s/[ \t]*$//')

# gcloud compute firewall-rules create beast --target-tags beast --allow tcp:8389
echo "Password token is: $TOKEN"
echo "IP is: $IP"
