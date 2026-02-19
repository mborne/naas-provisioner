# naas-provisioner

An **experimental** *Namespace as service* operator provisioning K8S namespaces according to a list of applications provided by an URL.

## Motivation

- Provisioning namespaces for students.
- Dynamic provisioning from an external application catalog (ex : naas-manager, k8slab, betalab,...).

## Features

Given a collection of applications provided as an URL (see [docs/samples-applications.yaml](docs/samples-applications.yaml)) this tool run a loop to :

- Create, update or remove the corresponding namespaces with `app.name` == `namespace.name`
- Configure a `"naas-providers-admins"` RoleBinding with the `"admin"` ClusterRole on the namespace for the `app.admins`.

Note that :

- A `managed-by=naas-provisioner` label is configured on the resources (existing namespace without this label are ignored)
- It might be extended in the futur to configure Quotas, NetworkPolicies,...

## Architecture

![Architecture](docs/architecture.drawio.png)

## Parameters

| Name                         | Description                                             | Default             |
| ---------------------------- | ------------------------------------------------------- | ------------------- |
| `NAAS_APPLICATIONS_URL`      | The URL of the YAML files defining the applications (1) | None (**required**) |
| `NAAS_ADMINS_CLUSTER_ROLE`   | The ClusterRole assigned to the app admins              | "admin"             |
| `NAAS_DRY_RUN`               | Set to 1 to display operations                          | 0                   |
| `NAAS_POLL_INTERVAL_SECONDS` | Update loop frequency                                   | 30                  |

> (1) A path like examples/applications.yaml is allowed for development purpose.

## Usage

### For development purpose

```bash
# Configure applications source
export NAAS_APPLICATION_URL=docs/sample-applications.yaml

# WARNING : it will use the current context in your KUBECONFIG
export NAAS_DRY_RUN=0

# Run synchronize loop
uv run naas-provisioner --loop
```

### Deploying in Kubernetes

> Kustomize manifests coming soon...


## License

[MIT](LICENSE)

