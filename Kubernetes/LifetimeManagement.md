# Lifetime Management

## Rollout
- `k rollout status <deployment/myapp-deployment>`
- `k rollout history <deployment/myapp-deployment>`
- `k rollout undo <deployment/myapp-deployment>`: rollback.

## ENV Variables
```yaml
spec:
  containers:
    - name: myname
      image: myimage
      ports:
      	- containerPort: 8080
      env:
      	- name: VARNAME
      	  value: value
```

### Using ConfigMaps:
```yaml
envFrom:
  - configMapRef:
  	  name: app-config
  - configMapRef:
  	  name: other-app-config
```

In the config file:
```
VAR1: value1
VAR2: value2
```

- Imperative from CLI: `k create configmap <config-name> --from-literal=<key>=<value> 
--from-literal=<key2>=<value2>`.
- Imperative from file: `k create configmap <config-name> --from-file=<path-to-file>`, usually 
app_config.properties.
- Declarative: `k create -f <config-map.yaml>`.

- `k get configmaps`
- `k describe configmap`
- `k edit configmap`

Selecting only a few keys:

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    name: webapp-color
  name: webapp-color
  namespace: default
spec:
  containers:
  - env:
    - name: APP_COLOR
      valueFrom:
       configMapKeyRef:
         name: webapp-config-map
         key: APP_COLOR
    image: bob/webapp-color
    name: webapp-color
```

### Secrets 
- `k get secrets`
- `k describe secret`: Encode into base64 so there aren't displayed here.
- `k create secret generic <secret-name> --from-literal=<key>=<value>`

```yaml
envFrom:
  - secretRef:
  	  name: app-config 
```

Single ENV:
```yaml
env:
  - name: DB_Password
    valueFrom:
      secretKeyRef:
      	name: app-secret
      	key: DB_Password
```

Volume:
```yaml
volumes:
  - name: app-secret-volume
    secret:
      secretName: app-secret 
```

[Encrypt secrets](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data)
&rarr; Enable encryption at rest
&rarr; Configure least-privilege access to Secrets - RBAC
[Risks](https://kubernetes.io/docs/concepts/configuration/secret/#risks)