# Deploy Boxes

[Enoslib](https://gitlab.inria.fr/discovery/enoslib) deployment of an
[energy monitoring
stack](https://github.com/Chat-Wane/deploy-boxes/tree/master/energyservice)
(optional) along with [working box
services](https://github.com/Chat-Wane/working-box) that consumes
energy during a configurable time.  In addition to these services,
this project deploys a [Jaeger tracing
service](https://www.jaegertracing.io/) and an [envoy proxy
service](https://www.envoyproxy.io/).  The former allows us to reason
about the workflow at runtime or post mortem (for now this is the
all-in-one version but could be changed to a more scalable
distribution if need be); while the latter automatically adds metadata
for Jaeger to work (we could do this in working boxes or
[istio](https://istio.io/)).

## Usage

To start the deployment on Grid5000, make sure that the
[working-box](https://github.com/Chat-Wane/working-box) image exists
in your home directory. Then, go to the evaluation folder and select
your evaluation. It includes convergence speed, resilience to crashes,
fairness trade-off, and scalability.

```
$ cd ./src/evaluations
$ python3 <name_of_the_eval_file>.py
```

In a web browser, connect to ```<collector_ip>:16686``` to look at
traces; and ```<collector_ip>:3000``` to look at energy monitoring
data per container.


## Results

Results of executions are already in directory ```results``` except
for larger scale experiments where the size of the file is too large
for Github.

```
$ cd ./results/
$ python3 ./<name_of_the_result_python_file>.py
```

This should create additional files containing data easily printable
by [gnuplot](http://www.gnuplot.info/).
