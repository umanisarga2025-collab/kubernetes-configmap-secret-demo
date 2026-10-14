# Kubernetes ConfigMap and Secret Demo

## 1. Objective

Demonstrate how Kubernetes stores application configuration and sensitive
credentials, connects them to a Pod, and allows a container to retrieve
the values through environment variables and mounted files.

## 2. Environment

- Local cluster: Docker Desktop Kubernetes
- Kubernetes version: v1.36.1
- Container image: busybox:1.36
- Namespace: default

## 3. Architecture

The demo contains three main resources:

1. ConfigMap: app-config
2. Secret: app-secret
3. Deployment: config-secret-demo

The Deployment references both resources. Kubernetes provides their
values to the container as environment variables and mounted files.

## 4. ConfigMap

The ConfigMap stores non-sensitive configuration:

- APP_ENV: development
- APP_PORT: 8080
- APP_COLOR: blue (initial value; updated during the experiments)

Create and inspect it:

    kubectl apply -f configmap.yaml
    kubectl get configmap app-config
    kubectl describe configmap app-config
    kubectl get configmap app-config -o yaml

## 5. Secret

The Secret stores demonstration credentials:

- DB_USERNAME
- DB_PASSWORD

For this demo, the Secret was created using fake credentials:

    kubectl create secret generic app-secret \
      --from-literal=DB_USERNAME=demo_user \
      --from-literal=DB_PASSWORD='REPLACE_WITH_DEMO_VALUE'

Inspect the Secret without printing its values:

    kubectl get secret app-secret
    kubectl describe secret app-secret

Security note: Never commit real credentials to Git. Base64 encoding
is not encryption. Production environments should use least-privilege
RBAC and appropriate encryption at rest.

## 6. Connecting Resources to the Pod

The Deployment uses:

- envFrom.configMapRef to inject ConfigMap entries as environment variables.
- envFrom.secretRef to inject Secret entries as environment variables.
- ConfigMap volumes and volumeMounts to expose configuration as files.
- Secret volumes and volumeMounts to expose credentials as files.

Apply and validate the Deployment:

    kubectl apply -f deployment.yaml
    kubectl rollout status deployment/config-secret-demo
    kubectl get pods -l app=config-secret-demo

## 7. Fetching Configuration

Get the Pod name:

    POD=$(kubectl get pods \
      -l app=config-secret-demo \
      -o jsonpath='{.items[0].metadata.name}')

Read environment variables:

    kubectl exec "$POD" -- printenv APP_ENV
    kubectl exec "$POD" -- printenv APP_COLOR

Read mounted ConfigMap files:

    MSYS_NO_PATHCONV=1 kubectl exec "$POD" -- \
      cat /etc/app-config/APP_ENV

Read the mounted Secret username:

    MSYS_NO_PATHCONV=1 kubectl exec "$POD" -- \
      cat /etc/app-secret/DB_USERNAME

Verify that Secret environment variables exist without printing
the sensitive values:

    kubectl exec "$POD" -- sh -c '
    test -n "$DB_USERNAME" && echo "DB_USERNAME is available"
    test -n "$DB_PASSWORD" && echo "DB_PASSWORD is available"
    '

MSYS_NO_PATHCONV=1 prevents Git Bash from converting Linux paths
into Windows paths.

## 8. ConfigMap Update Experiment

Update APP_COLOR from blue to green in the original BusyBox demo:

    kubectl patch configmap app-config \
      --type merge \
      -p '{"data":{"APP_COLOR":"green"}}'

Verify the cluster value:

    kubectl get configmap app-config \
      -o jsonpath='{.data.APP_COLOR}'
    echo

The existing container environment variable remained blue, while the
mounted ConfigMap file updated to green after propagation.

Restart the Deployment:

    kubectl rollout restart deployment/config-secret-demo
    kubectl rollout status deployment/config-secret-demo

Refresh the Pod name and verify:

    POD=$(kubectl get pods \
      -l app=config-secret-demo \
      -o jsonpath='{.items[0].metadata.name}')

    kubectl exec "$POD" -- printenv APP_COLOR

Expected final value: green.

Environment variables do not automatically change in an already-running
container. Mounted ConfigMap volumes normally receive updates eventually,
except when mounted using subPath. Applications may need to reread files
to use updated values.

## 9. Final Validation

    kubectl get configmap app-config
    kubectl get secret app-secret
    kubectl get deployment config-secret-demo
    kubectl get pods -l app=config-secret-demo

Observed result:

- ConfigMap exists with three keys.
- Secret exists with two keys.
- Deployment has one ready replica.
- Pod is Running with one ready container.
- Final APP_COLOR value in the original BusyBox experiment was green.

## 10. Security Best Practices

- Store non-sensitive settings in ConfigMaps.
- Store sensitive credentials in Secrets or an appropriate external
  secret-management system.
- Apply least-privilege RBAC.
- Enable encryption at rest for Secrets.
- Do not expose passwords through logs, screenshots, or API responses.
- Do not commit real credentials or credential-bearing manifests to Git.
- Use an application-specific identity and restricted permissions in
  production.

## 11. Cleanup

Delete the demo resources when testing is complete:

    kubectl delete deployment config-secret-demo
    kubectl delete configmap app-config
    kubectl delete secret app-secret

## 12. Conclusion

This practical demonstrates how to create and inspect ConfigMaps and
Secrets, connect them to a Deployment, retrieve values from a container,
and observe configuration-update behavior in Kubernetes.

## 13. Real Flask Application

This project also includes a Python Flask application that reads
configuration supplied by Kubernetes.

Files:
- app/app.py: Flask application with /health and /config endpoints.
- app/requirements.txt: Python dependencies.
- app/Dockerfile: Container image build instructions.
- web-deployment.yaml: Kubernetes Deployment for the Flask app.

### Security configuration

The Flask Deployment uses several Kubernetes security controls:

- **Non-root user and group:** `runAsUser: 10001` and `runAsGroup: 10001`.
- **Privilege escalation disabled:** `allowPrivilegeEscalation: false`.
- **Linux capabilities dropped:** `capabilities.drop: ["ALL"]`.
- **Resource requests:** CPU `100m`, memory `64Mi`.
- **Resource limits:** CPU `500m`, memory `128Mi`.
- **ServiceAccount:** Uses the dedicated `config-secret-web` ServiceAccount.
- **Token automount disabled:** `automountServiceAccountToken: false`, because this application does not need to call the Kubernetes API.

Verify the container identity:

    kubectl exec deployment/config-secret-web -- id

Expected output:

    uid=10001 gid=10001 groups=10001

Inspect the Deployment's security configuration:

    kubectl get deployment config-secret-web -o yaml

These settings reduce unnecessary privileges and help limit resource consumption. They do not replace RBAC, Secret protection, network controls, or other production security measures.
### Build the image

Run from the project root:

    docker build -t config-secret-app:1.0 ./app

### Deploy the application

    kubectl apply -f web-deployment.yaml
    kubectl rollout status deployment/config-secret-web --timeout=120s
    kubectl get pods -l app=config-secret-web

### Access the application

Start port forwarding in one terminal:

    kubectl port-forward deployment/config-secret-web 8081:8080

Keep that terminal open. In a second terminal, run:

    curl http://localhost:8081/health
    curl http://localhost:8081/config

The health endpoint reports whether the application is healthy.
The configuration endpoint displays non-sensitive settings and indicates
whether the database username and password are configured. It does not
return the password.

### ConfigMap update experiment

The ConfigMap APP_COLOR was changed to orange:

    kubectl patch configmap app-config --type merge -p '{"data":{"APP_COLOR":"orange"}}'

Verify the stored value:

    kubectl get configmap app-config -o jsonpath='{.data.APP_COLOR}'
    echo

An existing container that receives APP_COLOR as an environment variable
continues to use its original value after a ConfigMap update. Restart the
Deployment to create a container with the updated value:

    kubectl rollout restart deployment/config-secret-web
    kubectl rollout status deployment/config-secret-web --timeout=120s
    kubectl exec deployment/config-secret-web -- printenv APP_COLOR

Expected value after the restart: orange.

### Security notes

- Never commit real passwords or credentials to Git.
- Base64 encoding in a Kubernetes Secret is not encryption.
- Apply least-privilege RBAC and protect access to Secrets.
- Configure encryption at rest for production clusters.
- Consider an appropriate external secret-management solution for production.
- This exercise uses demonstration credentials and Docker Desktop Kubernetes.
