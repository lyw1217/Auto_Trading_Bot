#!/bin/bash
command=( `ps -ef | grep upbitTrading | grep -v grep | awk '{print $2}'` )

echo ""
echo -e "> \033[40;34;1mPROCESS KILL\033[0m"

if [ -n "$command" ]
then
	for pid in "${command[@]}"
	do
		echo -e "- Found working bot! pid : $pid"
		kill -9 $pid
		echo -e "kill -9 $pid"
	done
	
	sleep 1s
	command2=( `ps -ef | grep upbitTrading | grep -v grep | awk '{print $2}'` )
	if [ -n "$command2" ]
	then
		for pid in "${command2[@]}"
		do
			echo -e "- process stil alive! pid : $pid"
		done

		echo -e "- kill process \033[40;31;1mfail\033[0m"
		echo "- Try Again"
		exit 1
		
	else
		echo -e "- kill process \033[40;32;1mcomplete\033[0m"
	fi
else
	echo -e "- There are no working bot!"
fi

sleep 1s

echo ""
echo -e "> \033[40;34;1mGIT PULL\033[0m"
git pull

echo -e ""
echo -e "> \033[40;34;1mS T A R T Python Auto COIN Trading Bot in background\033[0m"
echo -e ""

NOW=$(date "+%y%m%d")

nohup python3 upbitTrading_all.py > coin_${NOW}.log 2>&1 &

sleep 1s

command=( `ps -ef | grep upbitTrading | grep -v grep | awk '{print $2}'` )

if [ -n "$command" ]
then
	for pid in "${command[@]}"
	do
		echo -e "\033[40;32;1mO\033[0m Startup \033[40;32;1mSuccessfully\033[0m !  pid : $pid\033[0m"
	done
else
	echo -e "\033[40;31;1mX\033[0m Startup \033[40;31;1mFailure\033[0m, Try Agin..\033[0m"
fi

echo -e ""
