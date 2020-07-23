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
import portion as I
from random import seed
from random import randint
from io import BytesIO
from pathlib import Path

from utils import _get_address
from box import Box
from boxes import Boxes, BoxesType

## Experiment on a small unbalanced tree of working-boxes with small
## parameters

## (TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)
## (TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)(TODO)



CLUSTER = "econome"
SITE = "nantes"

conf = Configuration.from_settings(job_type='allow_classic_ssh',
                                   job_name=f'working-boxes eval_fairness_1.py',
                                   walltime='02:00:00')
network = NetworkConfiguration(id='n1',
                               type='prod',
                               roles=['my_network'],
                               site=SITE)
conf.add_network_conf(network)\
    .add_machine(roles=['collector', 'front', 'working'],
                 cluster=CLUSTER,
                 nodes=1,
                 primary_network=network)\
    .finalize()
                 


SEED = 2
NB_QUERY = 1500
FAIRNESS = 0.4
EXPORT_TRACES_FILE = Path(f'../../results/result_fairness_2_s{SEED}.json')

boxes = Boxes(depth=3, arity=2, kind=BoxesType.WORST)
boxes.print()
longestTimeOfLongest = boxes.getMaxTime()
logging.debug(f"Longest possible task takes {longestTimeOfLongest}ms.")

seed(SEED)



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


i = 0
workings = roles['working']
boxNameToAddress = {}
for box in reversed(boxes.boxes):
    with play_on(pattern_hosts=
                 _get_address(workings[i%len(workings)]),
                 roles=roles) as p:
        box_address = _get_address(workings[i%len(workings)])
        boxNameToAddress[box.SPRING_APPLICATION_NAME] = box_address
        i = i + 1
        p.docker_container(
            display_name=f'Installing box {box.SPRING_APPLICATION_NAME} service…',
            name=f'{box.SPRING_APPLICATION_NAME}', ## be careful with uniqu names
            image='working-box:latest',
            detach=True, network_mode='host', state='started',
            recreate=True,
            published_ports=[f'{box.SERVER_PORT}:{box.SERVER_PORT}'],
            env={
                'JAEGER_ENDPOINT': f'http://{jaeger_address}:14268/api/traces',
                'SPRING_APPLICATION_NAME': f'{box.SPRING_APPLICATION_NAME}',
                'SERVER_PORT': f'{box.SERVER_PORT}',
                'BOX_POLYNOMES_COEFFICIENTS': f'{box.POLYNOME()}',
                'BOX_REMOTE_CALLS': f'{box.REMOTE_CALLS(boxNameToAddress)}',
                'BOX_ENERGY_FAIRNESS_FACTOR': f'{FAIRNESS}', ## THIS IS THE DIFFERENCE
                'BOX_ENERGY_THRESHOLD_BEFORE_SELF_TUNING_ARGS':
                f'{box.BOX_ENERGY_THRESHOLD_BEFORE_SELF_TUNING_ARGS}',
	        'BOX_ENERGY_MAX_LOCAL_DATA':
                f'{box.BOX_ENERGY_MAX_LOCAL_DATA}',
	        'BOX_ENERGY_FACTOR_LOCALDATAKEPT_DIFFERENTDATAMONITORED':
                f'{box.BOX_ENERGY_FACTOR_LOCALDATAKEPT_DIFFERENTDATAMONITORED}',
            },
        )
        p.wait_for(
            display_name=f'Waiting for box {box.SPRING_APPLICATION_NAME} to be ready…',
            host='localhost', port=f'{box.SERVER_PORT}', state='started',
            delay=2, timeout=120,
        )
        
        


## Generate traces
nb_crashes = 0
for i in range(0, NB_QUERY):
    ## #1 get possible objective
    urlIntervals = f'http://{front_address}:80/getEnergyIntervals'
    logging.debug(f'({i}) Calling url: {urlIntervals}')
    buffer = BytesIO()    
    c = pycurl.Curl()
    c.setopt(c.URL, urlIntervals)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()

    value = buffer.getvalue().decode("utf-8")
    intervalsAsArray = []
    if value != "EMPTY":
        value = value.replace("‥", ",")
        intervalsAsArray = json.loads('[' + value + ']')
        logging.debug(f'intervals {intervalsAsArray}')
        intervals = I.empty()
        for interval in intervalsAsArray:
            intervals = intervals | I.closed(int(interval[0]), int(interval[1]))
            
        objective = boxes.getInput(intervals)
    else:
        objective = -1


    logging.debug(f'objective {objective}')
    ## #2 call the application
    inputs  = boxes.getInputs() ## (TODO) write input ranges
    inputsString = ','.join([str(i) for i in inputs])    
    url = f'http://{front_address}:80?args={inputsString}'
    logging.debug(f'''({i}) Calling url: {url} \
    ETA {boxes.getTimeForInputs(inputs)}, max {boxes.getMaxTime()}''')

    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.HTTPHEADER, [f'objective: {objective}'])
    c.perform()
    c.close()
    


## Export file of traces

## 2*NB_QUERY because of getIntervalEnergy now
URL = f'http://{jaeger_address}:16686/api/traces?service={boxes.entryPoint.SPRING_APPLICATION_NAME}&limit={2*NB_QUERY}'

buffer = BytesIO()
c = pycurl.Curl()
c.setopt(c.URL, URL)
c.setopt(c.WRITEDATA, buffer)
c.perform()
c.close()

logging.debug(f"Exporting traces to {EXPORT_TRACES_FILE}.")
results = json.loads(buffer.getvalue())
with EXPORT_TRACES_FILE.open('w') as f:
    json.dump(results, f)
