# Deployment

## Local Development

Use docker compose and see [README](../README.md)

## Local Helm Install

The image for this application must be built and stored in a registry.

1. docker compose build
2. tag the image accordingly
3. docker push [image registry]

Unless the image is public, an image pull secret is required.  This example will use dockerhub.

1. log into docker hub; docker login
2. Create a kubectl secret (see example)

Or, use this for reference: [Kubernetes Docs](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/).

Next, with the secret in place, run the helm install


### Kubectl secret for dockerhub

```
kubectl create secret generic regcred \
    --from-file=.dockerconfigjson=$HOME/.docker/config.json \
    --type=kubernetes.io/dockerconfigjson
```

