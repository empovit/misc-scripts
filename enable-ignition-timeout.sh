#!/bin/bash

#############################################################################################
# Usage:
#   CLUSTER=<uuid> [BEARER=<token>] [BASE_URL=<url>] ./enable-ignition-timeout.sh
#
# How to get a bearer token https://github.com/openshift/assisted-service/blob/master/docs/cloud.md
#
# If downloading ingition times out (see 'httpTotal', in seconds),
# press 'Enter' when prompted to drop into shell.
#
# Diagnostics info:
# - less /run/initramfs/rdsosreport.txt
# - journalctl -a
# - dmesg
# - less /run/initramfs/init.log
# - ip address
#############################################################################################

BASE_URL=${BASE_URL:-"https://api.openshift.com/"}

if [[ -z ${CLUSTER} ]]; then
    echo "ERROR: Cluster UUID must be specified in CLUSTER environment variable" >&2
    exit 1
fi

if [[ -z ${BEARER} ]]; then
    echo "WARNING: Authentication is empty. If required, pass token (without the word 'Bearer') in BEARER environment variable" >&2
fi

CLUSTER_URL=$BASE_URL/api/assisted-install/v1/clusters/$CLUSTER

echo "Getting hosts from $CLUSTER_URL"
HOSTS=`curl -sSf -X GET -H "Content-Type: application/json" -H "authorization: ${BEARER}" "${CLUSTER_URL}" | jq "." | grep '"id"' | awk -F'"' '{print $4}'`

if [[ -z ${HOSTS} ]]; then
    echo "ERROR: No hosts could be read" >&2
    exit 1
fi

echo "Updating the hosts"
for h in ${HOSTS}
do
    if [ "$h" != "$CLUSTER" ]; then

        echo
        echo "Host: $h"
        curl -X PATCH \
            -H "Content-Type: application/json" \
            --data-binary '{"config": "{\"ignition\":{\"timeouts\":{\"httpTotal\":300},\"version\":\"3.1.0\"}}"}' \
            -H "authorization: Bearer ${BEARER}" \
            "$BASE_URL/api/assisted-install/v1/clusters/$CLUSTER/hosts/$h/ignition"

        echo
        curl -X PATCH \
            -H "Content-Type: application/json" \
            --data-binary '{"args": ["--delete-karg", "console=ttyS0,115200n8", "--append-karg", "rd.shell", "--append-karg", "rd.debug", "--append-karg", "rd.net.timeout.carrier=30"]}' \
            -H "authorization: Bearer ${BEARER}" \
            "$BASE_URL/api/assisted-install/v1/clusters/$CLUSTER/hosts/$h/installer-args"
    fi
done