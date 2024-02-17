# Scheduler

## Issues
### Check the statut of the scheduler
- `k get pods --namespace kube-system`: to check if the scheduler is running

### Common issues
- No scheduler means nothing to assign a pod to a node -> pod status is 'Pending'. To fix that, delete the pod and add 
the field 
```yaml
spec:
  nodeName: <node01>
```
then recreate the pod.

## Taints
Restraining nodes from accepting certain pods.
- `k taint nodes <node-name> <key>=<value>:<taint-effect>`

Taint-effect: 
- NoSchedule &rarr; skip to next node.
- PrefetNoSchedule &rarr; tries not to schedule.
- NoExecute &rarr; remove pods already placed in the node if they don't have the tolerance.

Apply tolerance to pod:
```yaml
spec:
  tolerations:
  - effect: "NoSchedule"
    key: "app"
    operator: "Equal"
    value: "blue"
```
> :warning: Every value should be placed inside "double quotes"! 

- Check on which node is a pod: `k describe pod <pod-name> | grep Node:`.
- Check if a node has taint: `k describe node <node-name> | grep Taint`.


The master node is created with a special taint that rejects all the pods 
(`k describe node kubemaster | grep Taint`).

## Node Selector
- First label a node: `k label nodes <node-name> <label-key>=<label-value>`.

```yaml
spec:
  nodeSelector:
    size: Large
```

Limitations: Large OR Medium ? NOT Small ? &rarr; Node Affinity.

## Node Affinity
To assign a pod to a "Large" node: 
```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoreDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: size
            operator: In
            values:
            - Large
```

Node affinity types:
- requiredDuringSchedulingIgnoredDuringExecution
- preferredDuringSchedulingIgnoredDuringExecution
- ~requiredDuringSchedulingRequiredDuringExecution~ (planned but not yet available)

OR expression
```yaml
operator: In
values:
- Large
- Medium
```

NOT expression
```yaml
operator: NotIn
values:
- Small
```

EXISTS expression: check if the key exists on the node
```yaml
operator: Exists
```

## Resources
[Docs](https://kubernetes.io/docs/tasks/administer-cluster/manage-resources)
### Resource Requests
Change the pod definition file:
```yaml
spec:
  resources:
    requests:
      memory: "4Gi"
      cpu: 2
```

Values for CPU:
- in CPU: 0.1 to infty.
- in mCPU: 1 to infty.

Values for memory: G/M/K, Gi/Mi/Ki (1K = 1000bytes whereas 1Ki = 1024bytes).

### Resource Limits
Change the pod definition file:
```yaml
spec:
  resources:
    limits:
      memory: "8Gi"
      cpu: 4
```
If the pod tries to get more cpu it will be throttled. However, it can take more memory than the limit, it will then be 
terminated with OOM error (Out Of Memory).
> Useful for labs: admin doesn't want user to mine crypto.

### Ideal scenario: requests and no limits
It will automatically limit the other pods to garantee the requested amount of ressources.
> Make sure every pod have requested resources in this case.

### Define resource consumption at namespace level
Create a 'default' with a LimitRange file: [limit-range-cpu](examples/limit-range-cpu.yaml). Same goes for memory: [limit-range-memory](examples/limit-range-memory.yaml).

### Resources Quotas 
At namespace level, quotas can be created: [resource-quota](examples/resource-quota.yaml).

## Multiple Schedulers
Check the docs.

[my-scheduler-config.yaml](Exemples/my-scheduler-config.yaml) [my-custom-scheduler.yaml](Exemples/my-custom-scheduler.yaml)

Then modify the POD's definition file:
```yaml
# pod-definition.yaml
spec:
  schedulerName: my-custom-scheduler
```
