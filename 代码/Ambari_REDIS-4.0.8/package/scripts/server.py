# -*- coding: utf-8 -*-
import socket
import re
import os, base64, socket, sys, glob, pwd, grp, signal, time
from time import sleep
from resource_management import *
import subprocess
import pexpect
from resource_management.core.exceptions import ComponentIsNotRunning
from resource_management.core.logger import Logger
from resource_management.core import shell

## redis集群版安装脚本

reload(sys)
sys.setdefaultencoding('utf8')


class Master(Script):

    # 安装Redis服务
    def install(self , env):

        import params;
        env.set_params(params)
        config = Script.get_config()

        #获取redis安装结点的IP
        redis_master_host = config['clusterHostInfo']['redis_server_hosts']
        # 获取每个结点安装redis实例 redis_node_detail
        redis_node_detail = params.redis_node_detail

        #IP的个数
        ip_len = len(redis_node_detail.split(','))

        #获取ip和redis数量
        ips_and_redisnum = redis_node_detail.split(',')

        # 判断redis.node.detail中IP是否合法  （192.168.92.1:1,192.168.93.2:2,192.168.92.3:3）
        for i in range(ip_len):
            if re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,2}$", ips_and_redisnum[i]):
                print("合法")
            else:
                raise Exception('---> ip和redis数量书写不合法！！ <---')

        # 判断两个输入的IP个数是否正确
        if(len(redis_master_host) != ip_len):
            raise Exception('---> 请确认输入的结点IP是否正确 <---')

        # 判断输入的redis个数是否合法
        #redis实例的数量
        redis_num = 0
        for i in range(ip_len):
             redis_num += int(ips_and_redisnum[i].split(':')[1])
        # print('master及其副本数之和：'+str(int(params.redis_replication_num)+ip_len))
        # print('实例总数为：'+str(redis_num))
        if(redis_num%(int(params.redis_replication_num)+1)!=0):
            raise Exception('---> 请确认输入的redis实例总数是master及其副本数的倍数 <---')


        # 判断输入的redis_server_host和redis_node_detail的ip是否匹配上
        for i in range(len(config['clusterHostInfo']['redis_server_hosts'])):
            redis_server_host = config['clusterHostInfo']['redis_server_hosts'][i]
            server_ip = socket.gethostbyname(str(redis_server_host))
            flag = 0
            for j in range(len(config['clusterHostInfo']['redis_server_hosts'])):
                if(server_ip == ips_and_redisnum[j].split(':')[0]):
                    flag = 1
            if(flag == 1):
                print('IP格式正确')
            else:
                raise Exception('---> 请确认输入的两个IP是否正确 <---')

        # # 安裝gcc等环境
        cmd = format("yum -y install gcc")
        Execute(cmd, user=params.redis_user)

        # 判断安装的目录是否为空
        if os.path.exists('/opt/redis') and os.listdir('/opt/redis'):
            raise Exception('redis安装目录不为空，请先清空该文件夹，然后再次尝试')
        if(os.path.exists('/data/redis/cluster')):
            raise Exception('---> 保存每个结点上每个redis实例的配置信息和log信息的目录非空，请清空再安装 <---')

        ## 创建保存每个端口的配置信息和log信息的目录和文件 /data/redis/redis/cluster
        if(os.path.exists('/data/redis/cluster')==False):
            cmd = format("mkdir -p /data/redis/redis/cluster")
            Execute(cmd, user=params.redis_user)
        # 获取本地ip
        localIP = socket.gethostbyname(socket.gethostname())
        # 创建必要的文件夹
        for i in range(len(redis_node_detail.split(','))):
            if(redis_node_detail.split(',')[i].split(':')[0] == localIP):
                 print('ip为：' + redis_node_detail.split(',')[i].split(':')[0])
                 port_num = int(redis_node_detail.split(',')[i].split(':')[1])
                 print('端口数量'+ str(port_num))
                 for j in range(port_num):
                     port = 7000 + j
                     cmd = format("cd /data/redis/redis ; mkdir -p cluster/" + str(port) +"/data")
                     Execute(cmd, user=params.redis_user)

        # 下载redis
        cmd = format("cd /opt ;wget {redis_download_url}/pci-redis-4.0.8.tar.gz -O redis.tar.gz")
        Execute(cmd, user=params.redis_user)

        # 解压redis安装包
        cmd = format("cd /opt; tar -zxvf redis.tar.gz ;cd  /opt/redis/install/rpm; rpm -ivh tcl-8.5.7-6.el6.x86_64.rpm;rpm -ivh expect-5.44.1.15-4.el6.x86_64.rpm;cd /opt/redis/redis;make")
        Execute(cmd, user=params.redis_user)

        # 删除redis安装包
        cmd = format("rm -rf /opt/redis.tar.gz")
        Execute(cmd, user=params.redis_user)

        # 创建servers.txt文件
        if(os.path.exists('/opt/redis/redis/servers.txt')==True):
            raise Exception('---> servers.txt文件已经存在,请删除后再安装 <---')
        for i in range(len(config['clusterHostInfo']['redis_server_hosts'])):
            server_ip = redis_node_detail.split(',')[i].split(':')[0]
            port_num = int(redis_node_detail.split(',')[i].split(':')[1])
            for j in range(port_num):
                cmd = format("cd /opt/redis/redis; echo " + server_ip + ":"+str(7000+j)+" >> servers.txt")
                Execute(cmd, user=params.redis_user)

        # 创建必要的文件和修改权限
        if(os.path.exists('/etc/redis')==False):
            cmd = format("mkdir /etc/redis")
            Execute(cmd, user=params.redis_user)
        cmd = format("mkdir -p  /opt/redis/redis/data")
        Execute(cmd, user=params.redis_user)
        cmd = format("cp /opt/redis/redis/src/redis-server  /usr/local/bin/; cp /opt/redis/redis/src/redis-cli  /usr/local/bin")
        Execute(cmd, user=params.redis_user)
        cmd = format("chmod 755 /usr/local/bin/redis-server;chmod 755 /usr/local/bin/redis-cli")
        Execute(cmd, user=params.redis_user)


        ## 在每台机器上安装ruby(需要安装zlib和openssl)
        #安装zlib 和 openssl
        cmd = format("yum -y install zlib zlib-devel ; yum -y install openssl-devel ;rm -rf /usr/bin/pod2man")
        Execute(cmd, user=params.redis_user)
        if(os.path.exists('/opt/openssl')==False):
            cmd = format("mkdir /opt/openssl")
            Execute(cmd, user=params.redis_user)
        # 下载openssl
        cmd = format("cd /opt/openssl ; wget {redis_download_url}/openssl-1.0.1e.tar.gz")
        Execute(cmd, user=params.redis_user)
        cmd = format("cd /opt/openssl ; tar -zvxf openssl-1.0.1e.tar.gz ; cd /opt/openssl/openssl-1.0.1e; ./config -fPIC --prefix=/usr/local/openssl enable-shared ; ./config -t ; make ; make install")
        Execute(cmd, user=params.redis_user)

        # 安装ruby
        if(os.path.exists('/opt/ruby')==False):
             cmd = format("mkdir /opt/ruby")
             Execute(cmd, user=params.redis_user)
        cmd = format("cd /opt/ruby ; wget {redis_download_url}/ruby-2.5.0.tar.gz")
        Execute(cmd, user=params.redis_user)
        cmd = format("cd /opt/ruby ; tar -zvxf ruby-2.5.0.tar.gz ; cd /opt/ruby/ruby-2.5.0 ; ./configure ; make ; make install ; cd /opt/ruby/ruby-2.5.0/ext/zlib/ ; ruby extconf.rb ; sed -i '3i\\top_srcdir = ../..' Makefile ; make & make install")
        Execute(cmd, user=params.redis_user)
        cmd = format("cd /opt/ruby/ruby-2.5.0/ext/openssl ; ruby extconf.rb  --with-openssl-include=/usr/local/openssl/include/ --with-openssl-lib=/usr/local/openssl/lib ; sed -i '3i\\top_srcdir = ../..' Makefile ; make ; make install")
        Execute(cmd, user=params.redis_user)

        # 安装redis.gem
        cmd = format("cd /opt/redis ; wget {redis_download_url}/redis-4.0.1.gem ; gem install redis-4.0.1.gem")
        Execute(cmd, user=params.redis_user)

        #卸载openssl、ruby、redis-4.0.1.gem安装包
        cmd = format("rm -rf /opt/openssl-1.0.1e.tar.gz ; rm -rf ruby-2.5.0.tar.gz ; rm -rf redis-4.0.1.gem")
        Execute(cmd, user=params.redis_user)


        # 生成redis-cluster.sh文件
        File(format("/opt/redis/redis/redis-cluster.sh"),
             content=Template("redis-cluster.sh.template", configurations=params.redis_env),
             owner=params.redis_user,
             group=params.redis_group
             )
        # 给redis-cluster.sh添加执行权限
        cmd = ("chmod +x /opt/redis/redis/redis-cluster.sh")
        Execute(cmd, user=params.redis_user)




        ## 下面是需要删除的










        # # 生成redis.conf文件
        # localIP = socket.gethostbyname(socket.gethostname())
        # for i in range(len(redis_node_detail.split(','))):
        #     if(redis_node_detail.split(',')[i].split(':')[0] == localIP):
        #         port_num = int(redis_node_detail.split(',')[i].split(':')[1])
        #         for j in range(port_num):
        #             port = 7000 + j
        #             File(format("/data/redis/redis/cluster/"+str(port)+"/redis.conf"),
        #                  content=Template("redis.conf.template", configurations=params.redis_env),
        #                  owner=params.redis_user,
        #                  group=params.redis_group
        #                  )
        #
        # localIP = socket.gethostbyname(socket.gethostname())
        # # 针对每个ip 修改redis.conf
        # for i in range(len(redis_node_detail.split(','))):
        #     if (redis_node_detail.split(',')[i].split(':')[0] == localIP):
        #         print('ip为：' + redis_node_detail.split(',')[i].split(':')[0])
        #         port_num = int(redis_node_detail.split(',')[i].split(':')[1])
        #         print('端口数量' + str(port_num))
        #         for j in range(port_num):
        #             # sed -i '69d' redis.conf : 删除redis.conf的第69行内容
        #             # sed -i '69i\\bind 127.0.0.1' redis.conf : 将redis.conf的第69行添加内容：bind 127.0.0.1
        #             cmd = format("cd /data/redis/redis/cluster/"+str(7000 + j)+"; sed -i '69d' redis.conf ; sed -i '69i\\bind " + localIP +"' redis.conf")
        #             Execute(cmd, user=params.redis_user)
        #             cmd = format("cd /data/redis/redis/cluster/"+str(7000 + j)+"; sed -i '158d' redis.conf ; sed -i '158i\\pidfile /data/redis/redis/cluster/"+ str(j + 7000) +"/redis.pid' redis.conf")
        #             Execute(cmd, user=params.redis_user)
        #             cmd = format("cd /data/redis/redis/cluster/"+str(7000 + j)+"; sed -i '92d' redis.conf ; sed -i '92i\\port "+ str(j + 7000) + "' redis.conf")
        #             Execute(cmd, user=params.redis_user)
        #             cmd = format("cd /data/redis/redis/cluster/"+str(7000 + j)+"; sed -i '171d' redis.conf ; sed -i '171i\\logfile /data/redis/redis/cluster/"+ str(j + 7000) +"/log.log' redis.conf")
        #             Execute(cmd, user=params.redis_user)
        #             cmd = format("cd /data/redis/redis/cluster/"+str(7000 + j)+"; sed -i '261d' redis.conf ; sed -i '261i\\dir /data/redis/redis/cluster/"+ str(j + 7000) +"/data' redis.conf")
        #             Execute(cmd, user=params.redis_user)
        #             cmd = format("cd /data/redis/redis/cluster/"+str(7000 + j)+"; sed -i '821d' redis.conf ; sed -i '821i\\cluster-config-file nodes-"+ str(j + 7000) +".conf' redis.conf")
        #             Execute(cmd, user=params.redis_user)


    def configure(self, env):
        import params, sys
        reload(sys)
        sys.setdefaultencoding('utf-8')
        env.set_params(params)
        config = Script.get_config()

        #获取redis安装结点的IP
        redis_master_host = config['clusterHostInfo']['redis_server_hosts']

        # 获取每个结点安装redis实例 redis_node_detail
        redis_node_detail = params.redis_node_detail

        # 生成redis.conf文件
        localIP = socket.gethostbyname(socket.gethostname())

        for i in range(len(redis_node_detail.split(','))):
            if(redis_node_detail.split(',')[i].split(':')[0] == localIP):
                port_num = int(redis_node_detail.split(',')[i].split(':')[1])
                for j in range(port_num):
                    port = 7000 + j

                    file_handle=open('/root/1.txt',mode='a')
                    file_handle.write('\n' +'本地ip为 ：' + str(port))
                    file_handle.close()

                    File(format("/data/redis/redis/cluster/"+str(port)+"/redis.conf"),
                         content=Template("redis.conf.template", configurations=params.redis_config),
                         owner=params.redis_user,
                         group=params.redis_group
                         )

        localIP = socket.gethostbyname(socket.gethostname())
        # 针对每个ip 修改redis.conf
        for i in range(len(redis_node_detail.split(','))):
            if (redis_node_detail.split(',')[i].split(':')[0] == localIP):
                print('ip为：' + redis_node_detail.split(',')[i].split(':')[0])
                port_num = int(redis_node_detail.split(',')[i].split(':')[1])
                print('端口数量' + str(port_num))
                for j in range(port_num):
                    # sed -i '69d' redis.conf : 删除redis.conf的第69行内容
                    # sed -i '69i\\bind 127.0.0.1' redis.conf : 将redis.conf的第69行添加内容：bind 127.0.0.1
                    cmd = format("cd /data/redis/redis/cluster/"+str(7000 + j)+"; sed -i '69d' redis.conf ; sed -i '69i\\bind " + localIP +"' redis.conf")
                    Execute(cmd, user=params.redis_user)
                    cmd = format("cd /data/redis/redis/cluster/"+str(7000 + j)+"; sed -i '158d' redis.conf ; sed -i '158i\\pidfile /data/redis/redis/cluster/"+ str(j + 7000) +"/redis.pid' redis.conf")
                    Execute(cmd, user=params.redis_user)
                    cmd = format("cd /data/redis/redis/cluster/"+str(7000 + j)+"; sed -i '92d' redis.conf ; sed -i '92i\\port "+ str(j + 7000) + "' redis.conf")
                    Execute(cmd, user=params.redis_user)
                    cmd = format("cd /data/redis/redis/cluster/"+str(7000 + j)+"; sed -i '171d' redis.conf ; sed -i '171i\\logfile /data/redis/redis/cluster/"+ str(j + 7000) +"/log.log' redis.conf")
                    Execute(cmd, user=params.redis_user)
                    cmd = format("cd /data/redis/redis/cluster/"+str(7000 + j)+"; sed -i '261d' redis.conf ; sed -i '261i\\dir /data/redis/redis/cluster/"+ str(j + 7000) +"/data' redis.conf")
                    Execute(cmd, user=params.redis_user)
                    cmd = format("cd /data/redis/redis/cluster/"+str(7000 + j)+"; sed -i '821d' redis.conf ; sed -i '821i\\cluster-config-file nodes-"+ str(j + 7000) +".conf' redis.conf")
                    Execute(cmd, user=params.redis_user)

    def start(self, env):
        print('start')
        import params
        env.set_params(params)
        self.configure(env)

        redis_node_detail = params.redis_node_detail
        CLUSTER_HOME = '/data/redis/redis'
        REDIS_HOME = '/opt/redis/redis-4.0.8'
        # 获取本地ip
        localIP = socket.gethostbyname(socket.gethostname())
        # 启动本地的redis实例
        for i in range(len(redis_node_detail.split(','))):
            if (redis_node_detail.split(',')[i].split(':')[0] == localIP):
                port_num = int(redis_node_detail.split(',')[i].split(':')[1])
                for j in range(port_num):
                    port = 7000 + j
                    cmd = format("cd /opt/redis/redis;nohup " + REDIS_HOME + "/src/redis-server " + CLUSTER_HOME + "/cluster/"+str(port)+"/redis.conf > /dev/null 2>&1" )
                    Execute(cmd, user=params.redis_user)


        # 判断每个redis实例是否启动成功，启动失败抛异常

        # 目的：判断是否需要  './redis-cluster.sh create'
        #从reid集群列表的第一个结点开始判断redis是否运行正常（通过判断pid判断）
        # 若运行正常，则使用该结点判断的/data/redis/redis/cluster/7000/data/nodes-7000.conf文件
        # nodes-7000.conf文件中初始为两行，添加结点后该文件行数增加（即判断行数是否超过2行）


        # nodes-7000.conf初始内容：
            # 6127a7abc0cdf199ffbd7b970d578fb7916d1838 :0@0 myself,master - 0 0 0 connected
            # vars currentEpoch 0 lastVoteEpoch 0
        #获取nodes-7000.conf文件的行数
        count = len(open('/data/redis/redis/cluster/7000/data/nodes-7000.conf', 'r').readlines())
        # 如果nodes-7000.conf文件中初始为两行，则表明redis集群还没有初始化
        if(count==2):
                if (redis_node_detail.split(',')[0].split(':')[0] == localIP):
                    time.sleep(5)
                    #获取reids7000进程的pid
                    pid = subprocess.check_output("cat /data/redis/redis/cluster/7000/redis.pid", shell=True)
                    pid = pid.replace("\n","") # pid的最后一位是\n, 需要清除
                    #获取pid的控制台输出
                    res = subprocess.check_output("ps auxwww | grep redis | grep " + pid +"| awk -F' ' '{print $2}'", shell=True)
                    print(res)

                    if((pid) in res):
                        # cmd = format('/opt/redis/redis/redis-cluster.sh create')
                        # Execute(cmd, user=params.redis_user)
                        print('端口号进程存在 输出正确')

                        child = pexpect.spawn('/opt/redis/redis/redis-cluster.sh create')
                        #将pexpect的输入和输出信息写到/root/mylog.txt中
                        fout = file('/root/mylog.txt','w')
                        child.logfile = fout
                        # expect方法用来判断子程序产生的输出，判断是否匹配相应字符串
                        child.expect(".*accept.*")
                        child.sendline('yes')
                        #child.interact()
                        try:
                            child.expect('#')
                        except:
                            print("")
                        # child.expect(pexpect.EOF)
                    else:
                        print('端口号进程存在 初始化失败')



    def stop(self, env):
        print('stop')
        import params
        env.set_params(params)

        redis_node_detail = params.redis_node_detail
        # CLUSTER_HOME = '/data/redis/redis'
        # REDIS_HOME = '/opt/redis/redis-4.0.8'
        # 获取本地ip
        localIP = socket.gethostbyname(socket.gethostname())
        for i in range(len(redis_node_detail.split(','))):
            if (redis_node_detail.split(',')[i].split(':')[0] == localIP):
                # print('ip为：' + redis_node_detail.split(',')[i].split(':')[0])
                port_num = int(redis_node_detail.split(',')[i].split(':')[1])
                # print('端口数量' + str(port_num))
                for j in range(port_num):
                    port = 7000 + j
                    if(os.path.exists("/data/redis/redis/cluster/"+ str(port) +"/redis.pid")==True):
                        cmd = format("kill `cat /data/redis/redis/cluster/" + str(port)+"/redis.pid` >/dev/null 2>&1")
                        Execute(cmd, user=params.redis_user)
                        cmd = format("rm -f /data/redis/redis/cluster/"+ str(port) +"/redis.pid")
                        Execute(cmd, user=params.redis_user)
        print("stop 成功")


    def status(self, env):
        print('status')
        from resource_management.core import sudo
        import params
        env.set_params(params)
        # file_handle=open('/root/1.txt',mode='a')
        # file_handle.write('\n' + "check_pricess_status : " + str(check_process_status(status_params.pid_file)))
        # file_handle.close()
        # # Use built-in method to check status using pidfile
        # check_process_status(status_params.pid_file)
        if(os.path.exists('/data/redis/redis/cluster')==False):
            raise Exception('---> /data/redis/redis/cluster目录不存在！！！ <---')

        ## 判断每个redis实例的pid文件是否存在，不存在则抛异常
        redis_node_detail = params.redis_node_detail
        CLUSTER_HOME = '/data/redis/redis'
        REDIS_HOME = '/opt/redis/redis-4.0.8'
        localIP = socket.gethostbyname(socket.gethostname())
        for i in range(len(redis_node_detail.split(','))):
            if (redis_node_detail.split(',')[i].split(':')[0] == localIP):
                port_num = int(redis_node_detail.split(',')[i].split(':')[1])
                for j in range(port_num):
                    port = 7000 + j
                    if(os.path.exists("/data/redis/redis/cluster/"+ str(port) +"/redis.pid")==False):
                        raise ComponentIsNotRunning()

                    pid = int(sudo.read_file("/data/redis/redis/cluster/"+ str(port) +"/redis.pid"))
                    try:
                        sudo.kill(pid,0)
                    except:
                        raise ComponentIsNotRunning()



if __name__ == "__main__":
    Master().execute()