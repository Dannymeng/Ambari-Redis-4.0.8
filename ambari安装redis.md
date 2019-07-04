# Ambari安装redis文档

## Redis安装情况
实际安装情况（以安装者机器虚拟机为例，三台虚拟机，计划每台结点安装3个Redis实例，共9个Redis实例，分配3个master，6个slave。其中每1个master有2个slave）

| 虚拟机      |  IP | redis实例数  |
| --------- | -------- | :-----: | 
| ambari01   | 192.168.92.161  | 3 |
|ambari02|192.168.92.162|3|   
|ambari03|192.168.92.163|3|   

Ambari Web UI 设置Redis副本数为2，即1主2从模式



## Ambari安装redis具体流程

  Ambari Web UI 前端(如下面两张图，第一张图选择redis安装结点，第二张图第二个选项选择每个结点上的redis实例)：

  - 1. redis集群的redis结点
  
  - 2. redis集群每个结点安装的redis实例：“192.168.92.141:3，192.168.92.142:3，192.168.92.143:3”，其中192.168.92.141:3表示在192.168.92.141结点上安装3个Redis实例
  

 <div align="center"> <img src="pictrue/7%E3%80%81%E5%89%8D%E7%AB%AF%E9%80%89%E6%8B%A9redis%20server.png" width="500px"> </div><br>

 <div align="center"> <img src="pictrue/6%E3%80%81%E5%89%8D%E7%AB%AF%E7%95%8C%E9%9D%A2.png" width="500px"> </div><br>

### 安装逻辑：(在server.py方法中)

- 1. install方法：
  - 1. 获取前端用户输入的redis结点的IP 、每个节点上安装的redis实例，判断是否合法，判断合法的逻辑是输入的字符串是否符合“192.168.92.141:3，192.168.92.142:3，192.168.92.143:3”这种样式;并且ip要与之前选择的redis安装结点对应。

  - 2. 在每个redis节点上安装gcc、openssl、ruby环境

  - 3. 创建redis目录，分为两个目录：
    - /opt/redis/redis/      :  redis的安装目录    $REDIS_HOME
    - /data/redis/cluster    :  redis实例的配置信息、日志信息等  $CLUSTER_HOME

  - 4. 在所有结点上创建servers.txt文件（保存所有结点的redis实例的IP+端口）

- 2. configure方法：

   - 在每个结点上的每个端口的目录下创建redis.conf文件

- 3. start方法

  - 1. 每个redis结点启动自身所有的redis实例 : `$REDIS_HOME/src/redis-server $CLUSTER_HOME/7000/redis.conf`

  - 2. 由于刚开始安装的时候需要初始化redis集群,nodes-7000.conf在未初始化时文件为两行，初始化后不止两行

- 4. stop方法
   在安装redis的时候，根据redis.conf中配置的pidfile，其中保存着每个redis实例的进程号。
   - kill \`cat $CLUSTER_HOME/port/redis.pid\`
   - rm -f $pidfile
## 检测Redis集群是否安装成功
进入redis后台命令： `./redis-cli -c -p 7000 -h 192.168.92.161`
(使用-c启动集群模式，否则后面测试会出错)


1. 进入redis安装目录：`cd /opt/redis/redis/src`
2. 查看redis集群状态：`/opt/redis/redis/redis-cluster.sh check ambari01:7000`
    发现集群中master和slave数量比即设置的1:2
 <div align="center"> <img src="pictrue/1%E3%80%81redis%E9%9B%86%E7%BE%A4%E6%A6%82%E8%A7%88.png" width="500px"> </div><br>

3. Java客户端连接Redis集群：
```java
// 连接本地的 Redis 服务 
Jedis jedis = new Jedis("192.168.92.161",7000);   
System.out.println("连接成功"); 
// 查看服务是否运行 
System.out.println("服务正在运行: " + jedis.ping());
```

结果：`ping`后显示`pong`表示连接成功
 <div align="center"> <img src="pictrue/2%E3%80%81java%E5%AE%A2%E6%88%B7%E7%AB%AF%E8%BF%9E%E6%8E%A5%E5%B0%9D%E8%AF%95.png" width="500px"> </div><br>

4. Java客户端操作Redis集群（增删数据）
```java

public static void main(String[] args){
    // 连接虚拟机的 Redis 服务 
    Set<HostAndPort> jedisClusterNodes = new HashSet<HostAndPort>();
    String host = "192.168.92.161";
    jedisClusterNodes.add(new HostAndPort(host, 7000));
    jedisClusterNodes.add(new HostAndPort(host, 7001));
    jedisClusterNodes.add(new HostAndPort(host, 7002));
    host = "192.168.92.162";
    jedisClusterNodes.add(new HostAndPort(host, 7000));
    jedisClusterNodes.add(new HostAndPort(host, 7001));
    jedisClusterNodes.add(new HostAndPort(host, 7002));
    host = "192.168.92.163";
    jedisClusterNodes.add(new HostAndPort(host, 7000));
    jedisClusterNodes.add(new HostAndPort(host, 7001));
    jedisClusterNodes.add(new HostAndPort(host, 7002));
    JedisCluster jc = new JedisCluster(jedisClusterNodes);
    jc.set("foo","bar"); //添加映射
    String s = jc.get("foo"); //获取值
    System.out.println(s);
    jc.del("foo"); //删除映射        
  }
}
```
结果：得到value并输出，并且将redis中新增的该条数据删除
 <div align="center"> <img src="pictrue/3%E3%80%81java%E5%AE%A2%E6%88%B7%E7%AB%AF%E6%93%8D%E4%BD%9Credis.png" width="500px"> </div><br>

5. 删除节点：删除master结点之后，redis集群又推选了一个新的master，并且查找被删除节点上的值依旧可以访问
 <div align="center"> <img src="pictrue/4%E3%80%81%E5%88%A0%E9%99%A4%E8%8A%82%E7%82%B9.png" width="500px"> </div><br>

6. 添加结点：`/opt/redis/redis/src/redis-server /data/redis/redis/cluster/7002/redis.conf`
 <div align="center"> <img src="pictrue/5%E3%80%81%E6%B7%BB%E5%8A%A0%E5%88%A0%E9%99%A4%E7%9A%84%E7%BB%93%E7%82%B9.png" width="500px"> </div><br>

