# Deploy Boxes

Enoslib deployment of an [energy monitoring
stack](https://github.com/Chat-Wane/deploy-boxes/tree/master/energyservice)
along with [working box
services](https://github.com/Chat-Wane/working-box) that consumes
energy during a configurable time.  In addition to these services,
this project deploys a [Jaeger tracing
service](https://www.jaegertracing.io/) and an [envoy proxy
service](https://www.envoyproxy.io/).  The former allows us to reason
about the workflow at runtime or post mortem (for now this is the
all-in-one version but could be changed to a more scalable
distribution if need be); while the latter automatically adds metadata
for Jaeger to work (we could do this in working boxes but w/e).

## Usage

To start the deployement on Grid5000, type: ```python3 main.py```

In a web browser, connect to ```<collector_ip>:16686``` to look at
traces; and ```<collector_ip>:3000``` to look at energy monitoring
data per container.
