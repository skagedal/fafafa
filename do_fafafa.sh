#!/bin/bash

LOGFILE="/home/skagedal/fafafa/fafafa_log.txt"
FAFAFA="/home/skagedal/fafafa/fafafa.py"

# Featured Articles
echo -n "Regenerating fa.xml at " >> ${LOGFILE}
date >> ${LOGFILE}

if ${FAFAFA} --fa >> ${LOGFILE} 2>&1; then
    echo "OK" >> ${LOGFILE}
#    echo "I just generated fa.xml, it was cool!"
else
    echo "NOT OK" >> ${LOGFILE}
    echo "Something went wrong with generating fa.xml today!"
fi

# Picture of the day
echo -n "Regenerating potd.xml at " >> ${LOGFILE}
date >> ${LOGFILE}

if ${FAFAFA} --potd >> ${LOGFILE} 2>&1; then
    echo "OK" >> ${LOGFILE}
#    echo "I just generated potd.xml, it was cool!"
else
    echo "NOT OK" >> ${LOGFILE}
    echo "Something went wrong with generating potd.xml today!"
fi

# Selected anniversaries
echo -n "Regenerating sa.xml at " >> ${LOGFILE}
date >> ${LOGFILE}

if ${FAFAFA} --sa >> ${LOGFILE} 2>&1; then
    echo "OK" >> ${LOGFILE}
#    echo "I just generated sa.xml, it was cool!"
else
    echo "NOT OK" >> ${LOGFILE}
    echo "Something went wrong with generating sa.xml today!"
fi

# Quote of the day
echo -n "Regenerating qotd.xml at " >> ${LOGFILE}
date >> ${LOGFILE}

if ${FAFAFA} --qotd >> ${LOGFILE} 2>&1; then
    echo "OK" >> ${LOGFILE}
#    echo "I just generated sa.xml, it was cool!"
else
    echo "NOT OK" >> ${LOGFILE}
    echo "Something went wrong with generating qotd.xml today!"
fi

