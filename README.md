# naas-provisioner

An **experimental** operator aiming at synchronization K8S namespaces according to a list of applications provided by an URL.

## Motivation

- Provisioning namespaces for students.
- Allow app managment in a side app (naas-manager) providing the application list.

## Parameters

| Name                         | Description                                              | Default             |
| ---------------------------- | -------------------------------------------------------- | ------------------- |
| `NAAS_APPLICATIONS_URL`      | The URL of the YAML files defining the applications [^1] | None (**required**) |
| `NAAS_DRY_RUN`               | Set to 1 to display operations                           | 0                   |
| `NAAS_POLL_INTERVAL_SECONDS` | Update loop frequency                                    | 30                  |

[^1]: Path allowed for development purpose.

## Development

```bash
uv run naas-provisioner
```

