#!/bin/bash
REDIS_HOME=/opt/redis/redis-4.0.8
CLUSTER_HOME=/data/redis
HOST_PORT=(`cat ${REDIS_HOME}/servers.txt`)
BLOCK=" "

if [ "$1" == "create" ]
 then
 CLUSTER_NODES="" 
	for((i=0;i<${#HOST_PORT[@]};i++)){
		CLUSTER_NODES=${CLUSTER_NODES}${BLOCK}${HOST_PORT[i]}

		

	}
	${REDIS_HOME}/src/redis-trib.rb  create --replicas 1 ${CLUSTER_NODES}
	echo "Create RedisCluster ${CLUSTER_NODES}"
        exit 0
fi

if [ "$1" == "start-node" ]
then
        if [ $# == 2  ]
        then
                HOST_PORT_ARRAY=(`echo "$2" | xargs -d : -n 1`)
                ssh ${HOST_PORT_ARRAY[0]} " ${REDIS_HOME}/src/redis-server   ${CLUSTER_HOME}/cluster/${HOST_PORT_ARRAY[1]}/redis.conf"
		echo "Start node $2"
        else
                echo "缺少参数hostport"
        fi
        exit 0

fi

if [ "$1" == "start-single-node" ]
then
        if [ $# == 2  ]
        then
                HOST_PORT_ARRAY_TARGET=(`echo "$2" | xargs -d : -n 1`)
                for((i=0;i<${#HOST_PORT[@]};i++)){
                HOST_PORT_ARRAY=(`echo ${HOST_PORT[i]} | xargs -d : -n 1`)
                if [ ${HOST_PORT_ARRAY_TARGET[0]} = ${HOST_PORT_ARRAY[0]}  ]
                then
                         ssh  ${HOST_PORT_ARRAY[0]} " ${REDIS_HOME}/src/redis-server   ${CLUSTER_HOME}/cluster/${HOST_PORT_ARRAY[1]}/redis.conf"
                         echo "Start ${HOST_PORT[i]}  path:${CLUSTER_HOME}/cluster/${HOST_PORT_ARRAY[1]}"
                fi
        }
                ssh ${HOST_PORT_ARRAY[0]} " ${REDIS_HOME}/src/redis-server   ${CLUSTER_HOME}/cluster/${HOST_PORT_ARRAY[1]}/redis.conf"
                echo "Start node $2"
        else
                echo "缺少参数hostport"
        fi
        exit 0

fi


if [ "$1" == "start" ]
then
	for((i=0;i<${#HOST_PORT[@]};i++)){
         	HOST_PORT_ARRAY=(`echo ${HOST_PORT[i]} | xargs -d : -n 1`)
		ssh  ${HOST_PORT_ARRAY[0]} " ${REDIS_HOME}/src/redis-server   ${CLUSTER_HOME}/cluster/${HOST_PORT_ARRAY[1]}/redis.conf"
		echo "Start ${HOST_PORT[i]}  path:${CLUSTER_HOME}/cluster/${HOST_PORT_ARRAY[1]}"
	}
	exit 0
fi 

if [ "$1" == "stop-node" ]
then
	if [ $# == 2  ]
        then
        	HOST_PORT_ARRAY=(`echo "$2" | xargs -d : -n 1`)
                ${REDIS_HOME}/src/redis-cli  -h ${HOST_PORT_ARRAY[0]}  -p ${HOST_PORT_ARRAY[1]} shutdown nosave
		echo "Stop node $2"
	else
                echo "缺少参数hostport"
        fi
    	exit 0

fi

#停止单个节点上的所有redis实例
if [ "$1" == "stop-single-node" ]
then
        if [ $# == 2  ]
        then
                HOST_PORT_ARRAY_TARGET=(`echo "$2" | xargs -d : -n 1`)
                for((i=0;i<${#HOST_PORT[@]};i++)){
                HOST_PORT_ARRAY=(`echo ${HOST_PORT[i]} | xargs -d : -n 1`)
                if [ ${HOST_PORT_ARRAY_TARGET[0]} = ${HOST_PORT_ARRAY[0]}  ]
                then
                         ${REDIS_HOME}/src/redis-cli  -h ${HOST_PORT_ARRAY[0]}  -p ${HOST_PORT_ARRAY[1]} shutdown nosave
                         echo "Stop ${HOST_PORT[i]}  path:${CLUSTER_HOME}/cluster/${HOST_PORT_ARRAY[1]}"
                fi
        }
                echo "Stop node $2"
        else
                echo "缺少参数hostport"
        fi
        exit 0

fi


if [ "$1" == "stop" ]
then
	 for((i=0;i<${#HOST_PORT[@]};i++)){
        	echo "Stopping ${HOST_PORT[i]}"
         	HOST_PORT_ARRAY=(`echo ${HOST_PORT[i]} | xargs -d : -n 1`)
        	${REDIS_HOME}/src/redis-cli  -h ${HOST_PORT_ARRAY[0]}  -p ${HOST_PORT_ARRAY[1]} shutdown nosave

	}
    	exit 0
fi

if [ "$1" == "add-node" ]
then
        if [ $# == 2  ]
        then
                ${REDIS_HOME}/src/redis-trib.rb  add-node --slave  "$2" ${HOST_PORT[0]}
                FLAGE=true
		NEW_HOST_PORT="$2"
                for((i=0;i<${#HOST_PORT[@]};i++)){
                	 if [ ${HOST_PORT[i]} == "$2" ]
                        then
                                FLAGE=false
                        fi 
		}
		 if [ ${FLAGE} == "true"  ]
                        then
                                echo "$2" >> ${REDIS_HOME}/servers.txt
                                echo "Add node $2"
                        fi
        elif [ $# == 3  ]
        then
               	${REDIS_HOME}/src/redis-trib.rb  add-node --slave --master-id "$3"  "$2" ${HOST_PORT[0]}
		FLAGE=true
                for((i=0;i<${#HOST_PORT[@]};i++)){
			echo "${HOST_PORT[i]}"
        		if [ ${HOST_PORT[i]} == "$2" ]
        		then
				FLAGE=false
        		fi                
	
                }
		 if [ ${FLAGE} == "true"  ]
                        then
				echo "$2" >> ${REDIS_HOME}/servers.txt
                       		echo "Add node $2"	
                        fi 
	else
		echo "缺少参数"
	exit 0
        fi

fi


if [ "$1" == "delete-node" ]
then
        if [ $# == 2  ]
        then
                for((i=0;i<${#HOST_PORT[@]};i++)){
			if [ ${HOST_PORT[i]} == $2 ]
        		then
			host_port=`echo "${HOST_PORT[i]}"`
       			HOST_PORT_ARRAY=(`echo ${HOST_PORT[i]} | xargs -d : -n 1`)
			echo $2 > localFile
                        ssh "${HOST_PORT_ARRAY[0]}" " cat ${CLUSTER_HOME}/cluster/${HOST_PORT_ARRAY[1]}/data/nodes-${HOST_PORT_ARRAY[1]}.conf " >> localFile;
			NODE_DATA=(`cat localFile | awk 'BEGIN{getline;host_port=$1}{if( $2 == host_port  ) print $1 }'`)
			${REDIS_HOME}/src/redis-trib.rb del-node "${HOST_PORT[i]}"  ${NODE_DATA[0]}
			`rm -rf localFile`
			echo "Delete Node $2"
			else
			echo "${HOST_PORT[i]}" >> hostport_new 
			fi	
		}
		`rm -rf servers.txt`
		`mv hostport_new servers.txt`
        else
                echo "缺少参数hostport"
        fi
        exit 0

fi


if [ "$1" == "reshard" ]
then
        if [ $# == 2 ]
        then
                ${REDIS_HOME}/src/redis-trib.rb reshard $2
		echo "Reshard  master-node  $2"
        else
                echo "缺少参数hostport"
        fi
    exit 0
fi

if [ "$1" == "clean-node" ]
then
        if [ $# == 2 ]
        then
		HOST_PORT_ARRAY=(`echo "$2" | xargs -d : -n 1`)
        	ssh ${HOST_PORT_ARRAY[0]} " rm -rf ${CLUSTER_HOME}/cluster/${HOST_PORT_ARRAY[1]}/data/* "
		echo "Clean node  $2"        
        else
        	echo "缺少参数hostport"
        fi
    exit 0
fi

if [ "$1" == "clear" ]
then
        for((i=0;i<${#HOST_PORT[@]};i++)){
                HOST_PORT_ARRAY=(`echo ${HOST_PORT[i]} | xargs -d : -n 1`)
                ssh ${HOST_PORT_ARRAY[0]} " rm -rf ${CLUSTER_HOME}/cluster/${HOST_PORT_ARRAY[1]}/data/* "
		echo "Clean ${HOST_PORT[i]} data"
        }
        exit 0
fi

if [ "$1" == "check" ]
then
	 if [ $# == 2  ]
        then
                HOST_PORT_ARRAY=(`echo "$2" | xargs -d : -n 1`)
		echo "Checking redis cluster  status ...."
        	${REDIS_HOME}/src/redis-trib.rb check $2
        else
                echo "缺少参数hostport"
        fi
        exit 0
fi

echo "Usage: $0 [start|start-node|start-single-node|create|stop|stop-node|stop-single-node|add-node|clean-node|clear|delete-node|reshard|check]"
