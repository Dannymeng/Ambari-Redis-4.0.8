# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
Redis Params configurations
"""

from resource_management import *
from resource_management.libraries.script.script import Script
import sys, os, glob,socket
from resource_management.libraries.functions.default import default

#配置参数
config = Script.get_config()
redis_env = config['configurations']['redis-env']
redis_config = config['configurations']['redis-config']

redis_user                                    = redis_env['redis_user']
redis_group                                   = redis_env['redis_group']
redis_download_url                            = redis_env['redis_download_url']
redis_node_detail                             = redis_env['redis_node_detail']
redis_replication_num                         = redis_env['redis_replication_num']



protected_mode                                = redis_config['protected-mode']
tcp_backlog                                   = redis_config['tcp-backlog']
timeout                                       = redis_config['timeout']
tcp_keepalive                                 = redis_config['tcp-keepalive']
daemonize                                     = redis_config['daemonize']
supervised                                    = redis_config['supervised']
loglevel                                      = redis_config['loglevel']
databases                                     = redis_config['databases']
always_show_logo                              = redis_config['always-show-logo']
stop_writes_on_bgsave_error                   = redis_config['stop-writes-on-bgsave-error']
rdbcompression                                = redis_config['rdbcompression']
rdbchecksum                                   = redis_config['rdbchecksum']
dbfilename                                    = redis_config['dbfilename']
slave_serve_stale_data                        = redis_config['slave-serve-stale-data']
slave_read_only                               = redis_config['slave-read-only']
repl_diskless_sync                            = redis_config['repl-diskless-sync']
repl_diskless_sync_delay                      = redis_config['repl-diskless-sync-delay']
appendonly                                    = redis_config['appendonly']
appendfsync                                   = redis_config['appendfsync']
hash_max_ziplist_entries                      = redis_config['hash-max-ziplist-entries']
activerehashing                               = redis_config['activerehashing']








