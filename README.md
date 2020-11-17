# Slim Django Cookiecutter
Version: 1.0.0

## Features
- Quick build API service & web application with Django & Django Rest Framework
- Deploy Django Service with gUnicorn and support asynchronous with Gevent
- Deploy Nginx as Load Balancer
- Auto generate/renew SSL with Let's Encrypt
- Support scale-out django services


## How to Use
1. Create project with this cookiecutter
```
cookiecutter gh:vcoder4c/slim-django-cookiecutter
```

2. Push code to git & configure repo URL at ```deploy/env/live/group_vars/all.yml```
```
# source code
# TODO: fill the git link here in order to do deployment via Ansible
git_repo: "source git"
git_branch: master
```

3. Configure host to deploy at ```deploy/env/hosts```
```
live-1 ansible_host=[public ip] private_ip=[private ip]

[django_server_hosts]
live-1

[load_balancer]
live-1
```

4. Configure SSL or Let's Encrypt at ```deploy/release.yml```

5. Now, it's ready to deploy on Remote Host 
```
cd deploy
./deploy live
```