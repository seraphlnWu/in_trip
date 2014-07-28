#!/usr/bin/env bash
MONGO_SERVER=192.168.1.117
DB_NAME=buzz_master
TARGET_DIR=/data/mongo_backup
FILE_NAME=$DB_NAME-`date +%Y-%m-%d`.tar.gz

if [ -d $TARGET_DIR/$DB_NAME ];then
    mv $TARGET_DIR/$DB_NAME $TARGET_DIR/$DB_NAME.backup
fi
mongodump -h $MONGO_SERVER -d $DB_NAME -o $TARGET_DIR 

cd $TARGET_DIR
tar zcvf $FILE_NAME $DB_NAME --remove-files
cd -
