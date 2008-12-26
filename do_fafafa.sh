#!/bin/bash

# This wrapper should soon go, with fafafa doing logging through the Python logging API

LOGFILE="/home/skagedal/fafafa/fafafa_log.txt"
FAFAFA="/home/skagedal/fafafa/fafafa.py"

echo -n "Regenerating feeds at " >> ${LOGFILE}
date >> ${LOGFILE}
if ${FAFAFA} fa potd sa qotd >> ${LOGFILE} 2>&1; then
    echo "OK" >> ${LOGFILE}
else
    echo "NOT OK" >> ${LOGFILE}
    echo "Something went wrong with generating feeds today!"
fi

