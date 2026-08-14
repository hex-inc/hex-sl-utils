#!/bin/bash
# Based on https://github.com/usil/mssql-docker-enhanced/blob/main/db_init.sh
export DB_INIT_FOLDER="/docker-entrypoint-initdb.d"
export DB_INIT_LOG_FILE="/var/log/docker/sqlserver_db_init.log"

function echo_log {
  DATE='date +%Y/%m/%d:%H:%M:%S'
  echo `$DATE`" $1"
  echo `$DATE`" $1" >> "$DB_INIT_LOG_FILE"
}

function fail_init {
  echo_log "[db_init_failed] $1"
  exit 1
}

echo_log "DB initilization start"

MAX_RETRIES=30
RETRY_INTERVAL=2
CHECK_STRING="SQL_SERVER_STARTED_123"

for i in $(seq 1 $MAX_RETRIES); do
    echo_log "Attempt $i of $MAX_RETRIES to connect to SQL Server"
    OUTPUT=$(/opt/mssql-tools/bin/sqlcmd -S localhost -U "${MSSQL_USER}" -P "${MSSQL_SA_PASSWORD}" -Q "SELECT '${CHECK_STRING}' AS ready_check" -h -1 2>&1)
    if [[ $OUTPUT == *"$CHECK_STRING"* ]]; then
        echo_log "Successfully connected to SQL Server"
        break
    fi
    if [ $i -eq $MAX_RETRIES ]; then
        echo_log "Error: MSSQL SERVER took more than $((MAX_RETRIES * RETRY_INTERVAL)) seconds to start up."
        echo_log "Last output: $OUTPUT"
        fail_init "MSSQL SERVER did not become ready"
    fi
    echo_log "Connection attempt failed. Retrying in $RETRY_INTERVAL seconds..."
    sleep $RETRY_INTERVAL
done

echo_log "MSSQL SERVER started"

if [ -z "$(find "$DB_INIT_FOLDER" -maxdepth 1 -name '*.sql' -print -quit)" ]; then
   echo_log "there are not any *.sql script in $DB_INIT_FOLDER"
else

    for script_absolute_location in "$DB_INIT_FOLDER"/*.sql; do
        echo_log "Executing $script_absolute_location"
        /opt/mssql-tools/bin/sqlcmd -U "${MSSQL_USER}" -P "${MSSQL_SA_PASSWORD}" -d master -i "$script_absolute_location"
        if [ $? -eq 0 ]
        then
            echo_log "script $script_absolute_location was executed successfully"
        else
            echo_log "sql execution returned an error"
            fail_init "script $script_absolute_location failed"
        fi
    done
fi

echo_log "[db_init_completed]"
