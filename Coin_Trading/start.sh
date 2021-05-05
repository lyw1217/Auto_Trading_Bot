#!/bin/bash
command=( `ps -ef | grep upbitTrading.py | grep -v grep | awk '{print $2}'` )

echo -e "> \033[40;34;1mPROCESS KILL\033[0m"

if [ -n "$command" ]
then
	for pid in "${command[@]}"
	do
		echo -e "- Found working bot! pid : $pid"
		kill -9 $pid
		echo -e "kill -9 $pid"
	done
else
	echo -e "- There are no working bot!"
fi

sleep 1s

echo -e "> \033[40;34;1mGIT PULL\033[0m"
git pull

echo -e ""
echo -e "> \033[40;34;1mS T A R T Python Auto COIN Trading Bot in background\033[0m"
echo -e ""

NOW=$(date "+%y%d%m")

nohup python3 upbitTrading.py > coin_${NOW}.log 2>&1 &

sleep 1s

command=( `ps -ef | grep upbitTrading.py | grep -v grep | awk '{print $2}'` )

if [ -n "$command" ]
then
	for pid in "${command[@]}"
	do
		echo -e "\033[40;32;1mO\033[0m Startup \033[40;32;1mSuccessfully\033[0m!  pid : $pid\033[0m"
	done
else
	echo -e "\033[40;31;1mX\033[0m Startup \033[40;31;1mFailure\033[0m, Try Agin..\033[0m"
fi

echo -e ""
