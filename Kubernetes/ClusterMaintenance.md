# Cluster Maintenance

## Updating OS
- `k drain <node>`: Schedules all the pods of the node on other nodes and prevents new pods to be scheduled on the
pod.
- `k cordon <node>`: Prevents new pods to be scheduled on the node.
- `k uncordon <node>`: The node is schedulable again.
- `k drain <node> --ignore-daemonsets`
- `k drain <node> --ignore-daemonsets --force`: Kill all the pods on the node even if they aren't part of a
replica set.

## Upgrading Kube
https://kubernetes.io/docs/concepts/overview/kubernetes-api/

https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md

https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api_changes.md
### Example
- `kubeadm upgrade plan`
- `kubeadm upgrade plan | grep "remote version"`
> :warning: Upgrade one version at a time!

- `apt-get upgrade -y kubeadm=1.12.0-00`
- `kubeadm upgrade apply v1.12.0`
- `apt-get upgrade -y kubelet=1.12.0-00`: Manually upgrade Kubelet on each node.
- `systemctl restart kubelet`

First, upgrade the Kubelet on the master node, then upgrade the worker nodes with:
- `k drain <node>`
- `apt-get upgrade -y kubeadm=1.12.0-00`
- `apt-get upgrade -y kubelet=1.12.0-00`
- `kubeadm upgrade node config --kubelet-version v1.12.0`
- `systemctl restart kubelet`
- `kubectl uncordon <node>`

Get the version of the cluster:
- `k get nodes`

### Updating the Controlplane node
- `apt-get update`
- `apt-get install kubeadm=1.27.0-00`
- `kubeadm upgrade apply v1.27.0`: This will upgrade Kubernetes controlplane node.
- `apt-get install kubelet=1.27.0-00`: This will update the kubelet with the version 1.27.0.
- `systemctl daemon-reload && systemctl restart kubelet`: You may need to reload the daemon and restart kubelet service 
after it has been upgraded.
Then update the worker nodes:
- `apt-get update`
- `apt-get install kubeadm=1.27.0-00`
- `kubeadm upgrade node`
- `apt-get install kubelet=1.27.0-00`
- `systemctl daemon-reload && systemctl restart kubelet`


## Backups
- `k get all --all-namespaces -o yaml > all-deploy-services.yaml`
### Backup directly ETCD
- View `etcd.service` options: `kubectl describe pod etcd-controlplane -n kube-system`: 
```
# etcd.service
ExecStart=/usr/local/bin/etcd \\
...
--data-dir=/var/lib/etcd
```
- Taking a snapshot: `ETCDCTL_API=3 etcdctl snapshot save snapshot.db`.
> :warning: There are 3 mandatory flags `--cacert` `--cert` `--key` (each could be find using 
> `k describe pod etcd-controlplane -n kube-system`). For example `etcdctl snapshot save /opt/snapshot-pre-boot.db 
> --endpoints=127.0.0.1:2379 --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt 
> --key=/etc/kubernetes/pki/etcd/server.key`.
- Status of snapshot: `ETCDCTL_API=3 etcdctl snapshot status snapshot.db`.

Restore:
- Stop the API: `service kube-apiserver stop`.
- `ETCDCTL_API=3 etcdctl snapshot restore snapshot.db --data-dir=/var/lib/etcd-from-backup`.
- Configure the ETCD service to use the new data directory in the `etcd.service`: you can vim directly in the YAML.
configuration file and change:
```yaml
# /etc/kubernetes/manifests/etcd.yaml
- volumes
  - hostPath : 
      path: /var/lib/etcd-from-backup
      type: DirectoryOrCreate
    name: etcd-data
``` 
> With this change in the /manifests folder, a pod is automatically re-created as this is a static pod. If the pod 
> isn't getting ready, force it by doing `k delete pod -n kube-system etcd-controlplane`.
- `systemctl daemon-reload`
- `service etcd restart`
- `service kube-apiserver start`

## ETCD 
- `k describe pod etcd-controlplane -n kube-system` in `--listen-client-urls`: the etcd is accessible via url.
- Stacked ETCD: ETCD running on the controlplane (there is a pod, or a static manifest on the controlplane's node).
- External ETCD: ETCD running elsewhere, on a separate server. The location of the ETCD is written in the Kube-API 
config.

## Cluster
- `k config view`: Cluster infos.
- `kubectl config use-context <cluster name>`: Switch context to a cluster .
- Ssh to a node: `k get nodes`, `ssh <node name>`.








