#!/bin/bash

me=`basename $0`
shell="bash"
cpu="12"
cpulimit="24"
cores="0"

case "$me" in
	grabnode) cpu="12";;
	grabhalfnode) cpu="6";;
	grabquarternode) cpu="3";;
	grabcpu|grabR) cpu="1";;
esac

find_grabbed_node()
{
	gn=""
	until [ -z "$1" ]
	do
		if [ $3 == "R" ]; then
			cores=$((cores+$6))
			echo "$1 $2 $3 $4 $5 $6"
			if [ $6 -eq "12" ]; then
				gn=$5
			fi
		fi

		shift 6
	done
}

username=`id -nu`
format="\"%.7i %.8j %.2t %.10M %R %C\""
sq="squeue -o $format -u $username -p pubint|grep grab"
grabbed=`eval $sq`
if [ -n "$grabbed" ] 
then
	echo "Nodes already grabbed:"
	find_grabbed_node $grabbed
	if [ -n "$gn" ]; then
		read -p "ssh to your previously grabbed node ($gn) (y/n)? " input
		shopt -s nocasematch
		case "$input" in
			y|Y|Yes) ssh $gn; exit
		esac
		shopt -u nocasematch
	fi

	total=$(($cores + $cpu))
	if [ $total -gt $cpulimit ]; then
		echo "This allocation would exceed your limit of $cpulimit cores"
		echo "You already have $corecmd cores allocated."
		exit
	fi
fi

if [ "$me" == "grabnode" ]; then
  echo -e "\nYou have now exclusive access to this node/server with"
  echo -e "                         $cpu CPUs and 48GB memory until you type exit."            
else
  echo -e "\nYou have requested $cpu CPUs on this node/server until you type exit."
  echo -e "You have decided to share this node/server with other users, THANKS !!!\n"
  echo -e "Please DO NOT RUN more than $cpu jobs at the same time on this node/server"
  echo -e "Running more jobs than CPUs allocated interferes with other users!"
fi
echo -e "\nWarning: If you exit this shell before your jobs are finished, your jobs"
echo -e "on this node/server will be terminated. As long as you leave this shell open"
echo -e "until you are done, you can ssh to this node/server as many times as you like.\n"

if [ -d /shared/silo_researcher ]; then
  echo -e "Please find your FRED shared data files in /shared."
  echo -e "Please find your SILO large data files in /shared/silo_researcher."
  echo -e "Please find your Researcher share (R drive) at /shared/cs_researcher."
fi

echo -e "\nX applications such as Emacs will not currently run via this connection."
echo -e "To use them, create a new separate ssh connection to this node"
echo -e "(prompt has name) from either Lynx, Rhino or your Linux desktop.\n"

case "$me" in
	grabnode)
		srun -J $me -N1 -n$cpu --exclusive -p pubint --pty $shell ;;
	grabhalfnode|grabquarternode|grabcpu)
		srun -J $me -N1 -n$cpu -p pubint --pty $shell ;;	
	grabR)
		srun -J $me -p pubint --pty /usr/local/bin/R ;;	
esac
