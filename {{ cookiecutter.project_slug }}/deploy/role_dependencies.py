import graphviz as gv
from glob import glob
import yaml

g = gv.Digraph('roles')

role_nodes = {}


def add_role(role):
    if role not in role_nodes:
        role_nodes[role] = g.node(role)


def link_roles(dependent_role, depended_role):
    g.edge(
        dependent_role,
        depended_role
    )


for path in glob('roles/*/meta/main.yml'):
    dependent_role = path.split('/')[1]

    add_role(dependent_role)

    with open(path, 'r') as f:
        config = yaml.load(f.read())
        if config:
            for dependency in config.get('dependencies', []):
                depended_role = dependency['role']

                add_role(depended_role)
                link_roles(dependent_role, depended_role)

g.render('ansible-roles', view=True)
