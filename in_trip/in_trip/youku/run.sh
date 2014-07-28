#!/bin/sh
PYTHONPATH='~/BuzzMaster' python service.py &
PYTHONPATH='~/BuzzMaster' rqworker -v update  >> "./log/update.log" 2>&1 &
PYTHONPATH='~/BuzzMaster' rqworker -v new >> "./log/new.log" 2>&1 &
PYTHONPATH='~/BuzzMaster' rqworker -v retry >>"./log/retry.log" 2>&1 &
PYTHONPATH='~/BuzzMaster' rqworker -v get >>"./log/get.log" 2>&1 &
rq-dashboard >> "./log/monitor.log" 2>&1 &
