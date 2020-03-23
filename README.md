# Deploy Boxes

Enoslib deployment of an [energy monitoring
stack](https://github.com/Chat-Wane/deploy-boxes/tree/master/energyservice)
along with [working box
services](https://github.com/Chat-Wane/working-box) that consumes
energy during a configurable time.  In addition to these services,
this project deploys a [Jaeger tracing
service](https://www.jaegertracing.io/) and an envoy front service.
The former allows us to reason about the workflow at runtime or post
mortem (for now this is the all-in-one version but could be changed to
a more scalable distribution if need be); while the latter
automatically adds metadata for Jaeger to work (we could do this in
working boxes but w/e).
