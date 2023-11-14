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

Or, use this for reference: [Kubernetes Docs](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/#create-a-secret-by-providing-credentials-on-the-command-line).

After that, make sure that the NGINX Ingress Controller is installed. Do that by following the
[NGINX Docs](https://kubernetes.github.io/ingress-nginx/deploy/)

Finally, with the secret and ingress controller in place, run the helm install

1. helm install architect architect/
