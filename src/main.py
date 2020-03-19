from enoslib.api import play_on, discover_networks
from enoslib.api import __python3__, __default_python3__, __docker__
from enoslib.infra.enos_g5k.provider import G5k
from enoslib.infra.enos_g5k.configuration import (Configuration,
                                                  NetworkConfiguration)
from utils import _get_address

from box import Box

from pathlib import Path
import yaml

import logging
logging.basicConfig(level=logging.DEBUG)



CLUSTER = "econome"
SITE = "nantes"

conf = Configuration.from_settings(job_type='allow_classic_ssh',
                                   job_name='working-boxes',
                                   walltime='02:00:00')
network = NetworkConfiguration(id='n1',
                               type='prod',
                               roles=['my_network'],
                               site=SITE)
conf.add_network_conf(network)\
    .add_machine(roles=['collector'],
                 cluster=CLUSTER,
                 nodes=1,
                 primary_network=network)\
    .add_machine(roles=['front', 'sensored', 'working', 'A', 'B', 'C', 'D'],
                 cluster=CLUSTER,
                 nodes=1,
                 primary_network=network)\
    .finalize()
                 


boxes = {
    'A': Box('1000'), # 1 second 
    'B': Box('1000,100'), # 1 + 0.1*x seconds
    'C': Box('1000,0,10'), # 1 + 0.01*x seconds
    'D': Box('5000') # 5 seconds
}

boxes['A'].add([(boxes['B'], 50), (boxes['C'], 50)])
boxes['B'].add([(boxes['D'], 90)])



provider = G5k(conf)
roles, networks = provider.init()

roles = discover_networks(roles, networks)

priors = [__python3__, __default_python3__, __docker__]
with play_on(pattern_hosts='all', roles=roles, priors=priors) as p:
    p.pip(display_name='Installing python-docker…', name='docker')

## #A deploy jaeger, for now, we set up with all in one
with play_on(pattern_hosts='collector', roles=roles) as p:
    p.docker_container(
        display_name=f'Installing jaeger…',
        name='jaeger',
        image='jaegertracing/all-in-one:1.17',
        detach=True, network_mode='host', state='started',
        recreate=True,
        published_ports=['5775:5775/udp',
                         '6831:6831/udp', '6832:6832/udp',
                         '5778:5778',
                         '16686:16686',
                         '14268:14268',
                         '14250:14250',
                         '9411:9411'],
        env={
            'COLLECTOR_ZIPKIN_HTTP_PORT': '9441'
        }
    )

## #B deploy envoy proxy, just here to create the appropriate id
front_address = roles['front'][0].extra['my_network_ip']
jaeger_address = roles['collector'][0].extra['my_network_ip']

envoy_path = '../emissary/front_envoy.yaml'
with Path(envoy_path).open('r') as f:
    document = yaml.load(f, Loader=yaml.FullLoader)

document['static_resources']['clusters'][0]\
    ['hosts']['socket_address']['address'] = front_address
document['static_resources']['clusters'][1]\
    ['hosts']['socket_address']['address'] = jaeger_address

with Path(envoy_path).open('w') as f:
    yaml.dump(document, f)

with play_on(pattern_hosts='front', roles=roles) as p:
    p.copy(
        display_name= 'Copying files to build envoy…',
        src='../emissary',
        dest='/tmp/',
    )
    p.docker_image(
        display_name='Building front envoy image…',
        path= '/tmp/emissary/',
        name='front-envoy',
        nocache=True,
    )
    
    p.docker_container(
        display_name='Installing front envoy…',
        name='envoy',
        image='front-envoy:latest',
        detach=True, network_mode='host', state='started',
        recreate=True,
        published_ports=['80:80'],
    )

## #C deploy working boxes
with play_on(pattern_hosts='working', roles=roles) as p:
    p.docker_image(
        display_name='Load box image…',
        name='working-box',
        tag='latest',
        load_path='/home/brnedelec/working-box_latest.tar'
    )

for box_name, box in boxes.items():
    with play_on(pattern_hosts=box_name, roles=roles) as p:
        p.docker_container(
            display_name=f'Installing box {box_name} service…',
            name=f'{box.name}', ## be careful with uniqu names
            image='working-box:latest',
            detach=True, network_mode='host', state='started',
            recreate=True,
            published_ports=[f'{box.port}:{box.port}'],
            env={
                'JAEGER_ENDPOINT': f'http://{jaeger_address}/api/traces', ## (TODO)
                'SPRING_APPLICATION_NAME': f'{box.name}',
                'SERVER_PORT': f'{box.port}',
                'BOX_POLYNOME_COEFFICIENTS': f'{box.polynome}',
                'BOX_REMOTE_CALLS': f'{box.remotes}', ## (TODO)
            },
        )

        
