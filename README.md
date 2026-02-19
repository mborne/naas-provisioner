# naas-provisioner

This experimental operator aims at synchronization K8S namespaces according to a list of applications provided by an URL.

## Parameters

| Name                    | Description                                         |
| ----------------------- | --------------------------------------------------- |
| `APPLICATIONS_URL`      | The URL of the YAML files defining the applications |
| `DRY_RUN`               | Only display actions                                |

## Development

```bash
uv run main.py
```

