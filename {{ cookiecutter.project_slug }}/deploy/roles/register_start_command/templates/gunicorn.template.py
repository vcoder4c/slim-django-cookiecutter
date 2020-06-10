bind = '{{private_ip}}:{{django_port}}'
forwarded_allow_ips = "{% for host in groups['load_balancer'] %}{% if loop.index0 != 0 %},{% endif %}{{ hostvars[host]['private_ip'] }}{% endfor %}"
max_requests = {{max_requests}}
workers = {{workers}}
worker_class = '{{worker_class}}'
graceful_timeout = {{graceful_timeout}}
timeout = {{timeout}}
keepalive = {{keepalive}}
chdir = '{{chdir}}'
errorlog = '{{errorlog}}'