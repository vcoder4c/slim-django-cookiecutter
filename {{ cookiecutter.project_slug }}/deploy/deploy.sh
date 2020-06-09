ansible-playbook -i env/$1/hosts build.yml
ansible-playbook -i env/$1/hosts release.yml
