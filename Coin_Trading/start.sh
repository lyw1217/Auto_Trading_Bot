#!/bin/bash
pid=$(ps -ef | grep upbitTrading.py | grep -v grep | awk '{print $2}')

if [ -n "$pid" ]
then
	echo "Found working bot! pid : $pid"
	kill -9 $pid
	echo "kill -9 $pid"
else
	echo "There are no working bot!"
fi

sleep 1s

echo ""
echo "S T A R T Python Auto COIN Trading Bot in background"
echo ""

NOW=$(date "+%y%d%m")

nohup python3 upbitTrading.py > coin_${NOW}.log 2>&1 &

sleep 1s

pid=$(ps -ef | grep upbitTrading.py | grep -v grep | awk '{print $2}')

if [ -n "$pid" ]
then
	echo "Startup Successfully!  pid : $pid"
else
	echo "Startup Failure, Try Agin.."
fi

echo ""
