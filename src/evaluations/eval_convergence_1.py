from enoslib.api import play_on, discover_networks
from enoslib.api import __python3__, __default_python3__, __docker__
from enoslib.infra.enos_g5k.provider import G5k
from enoslib.infra.enos_g5k.configuration import (Configuration,
                                                  NetworkConfiguration)
import sys 
sys.path.append('..') ## because in subdirectory
import logging
logging.basicConfig(level=logging.DEBUG)
import yaml
import pycurl
import json
from random import seed
from random import randint
from io import BytesIO
from pathlib import Path

from utils import _get_address
from box import Box
from energyservice.energy import Energy



SEED = 2
NB_QUERY = 400
EXPORT_TRACES_FILE = Path('../../results/result_convergence_1_s{}.json'.format(SEED))



CLUSTER = "econome"
SITE = "nantes"

conf = Configuration.from_settings(job_type='allow_classic_ssh',
                                   job_name='working-boxes convergence_1',
                                   walltime='02:00:00')
network = NetworkConfiguration(id='n1',
                               type='prod',
                               roles=['my_network'],
                               site=SITE)
conf.add_network_conf(network)\
    .add_machine(roles=['collector', 'front', 'working', 'A'],
                 cluster=CLUSTER,
                 nodes=1,
                 primary_network=network)\
    .finalize()
                 


provider = G5k(conf)
roles, networks = provider.init()
roles = discover_networks(roles, networks)



priors = [__python3__, __default_python3__, __docker__]
with play_on(pattern_hosts='all', roles=roles, priors=priors) as p:
    p.pip(display_name='Installing python-docker…', name='docker')

## #A deploy jaeger, for now, we set up with all-in-one
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

envoy_path = '../envoy/front_envoy.yaml'
with Path(envoy_path).open('r') as f:
    document = yaml.load(f, Loader=yaml.FullLoader)

document['static_resources']['clusters'][0]\
    ['hosts']['socket_address']['address'] = front_address
document['static_resources']['clusters'][1]\
    ['hosts']['socket_address']['address'] = jaeger_address ## (TODO) fix, does not seem to work

with Path(envoy_path).open('w') as f:
    yaml.dump(document, f)

with play_on(pattern_hosts='front', roles=roles) as p:
    p.copy(
        display_name= 'Copying files to build envoy…',
        src='../envoy',
        dest='/tmp/',
    )
    p.docker_image(
        display_name='Building front envoy image…',
        path= '/tmp/envoy/',
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
        force=True,
        load_path='/home/brnedelec/working-box_latest.tar'
    )


with play_on(pattern_hosts='A', roles=roles) as p:
    p.docker_container(
        display_name='Installing box-8080 service…',
        name='box-8080',
        image='working-box:latest',
        detach=True, network_mode='host', state='started',
        recreate=True,
        published_ports=['8080:8080'],
        env={
            'JAEGER_ENDPOINT': f'http://{jaeger_address}:14268/api/traces',
            'SPRING_APPLICATION_NAME': 'box-8080',
            'SERVER_PORT': '8080',
            'BOX_POLYNOMES_COEFFICIENTS': '1000,10@0',
            'BOX_REMOTE_CALLS': '',
            'BOX_ENERGY_THRESHOLD_BEFORE_SELF_TUNING_ARGS': '4',
	    'BOX_ENERGY_MAX_LOCAL_DATA': '10',
	    'BOX_ENERGY_FACTOR_LOCALDATAKEPT_DIFFERENTDATAMONITORED': '10',
        },
    )
    p.wait_for(
        display_name=f'Waiting for box-8080 to be ready…',
        host='localhost', port='8080', state='started',
        delay=2, timeout=120,
    )
        
        


## Generate traces

seed(SEED)

def getArgs ():
    isLeft = randint(0,1)
    if (isLeft == 1):    
        return randint(51, 100) ## 1s + (0.5 to 1)s
    else :
        return randint(301, 350) ## 1s + (3 to 3.5)s

for i in range(0, NB_QUERY):
    url = 'http://{}:80?args={}'.format(front_address, getArgs())
    print ('({}) Calling url: {}'.format(i, url))
    
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.HTTPHEADER, ['objective: 10000'])
    c.perform()
    c.close()



## Export file of traces

URL = 'http://{}:16686/api/traces?service=box-8080&limit={}'.format(
    jaeger_address,
    NB_QUERY)

buffer = BytesIO()
c = pycurl.Curl()
c.setopt(c.URL, URL)
c.setopt(c.WRITEDATA, buffer)
c.perform()
c.close()

results = json.loads(buffer.getvalue())
with EXPORT_TRACES_FILE.open('w') as f:
    json.dump(results, f)
