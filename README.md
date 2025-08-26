# ArgoCD Manager CLI

A rich, interactive Python CLI for managing ArgoCD installations, repositories, and applications. This tool wraps the `argocd` and `kubectl` CLIs, providing a user-friendly interface for common ArgoCD operations.

---

## Features

- **Interactive Login**: Authenticate to ArgoCD using environment variables or prompts.
- **ArgoCD Installation**: Install or uninstall ArgoCD in a Kubernetes cluster.
- **Status Checks**: View the status of ArgoCD pods in your cluster.
- **Repository Management**:
  - Add repository credential templates
  - Register new repositories
  - List all repositories
- **Application Management**:
  - Create single or batch applications
  - List all applications
  - Delete applications
- **Batch Operations**: Create multiple applications with shared settings in one go.
- **Rich UI**: Uses [rich](https://github.com/Textualize/rich) for beautiful tables and prompts.
- **Logging**: All actions are logged to `argocd_cli.log`.

---

## Requirements

- Python 3.7+
- [ArgoCD CLI](https://argo-cd.readthedocs.io/en/stable/cli_installation/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- Access to a Kubernetes cluster

### Python Dependencies

Install with pip:

```bash
pip install -r requirements.txt
```

---

## Usage

1. **Set up your environment variables (optional):**
   - Create a `.env` file in the project root:
     ```env
     ARGO_HOST=your-argocd-server
     ARGO_PORT=443
     ARGO_USERNAME=admin
     ARGO_PASSWORD=yourpassword
     ARGO_INSECURE_SKIP_VERIFY=true
     ```
   - Or, enter credentials interactively at startup.

2. **Run the CLI:**
   ```bash
   python main.py
   ```

3. **Follow the interactive menu** to perform actions like installing ArgoCD, managing repositories, or creating applications.

---

## Main Menu Options

- **Check ArgoCD Installation Status**: View pod status in a namespace.
- **Install ArgoCD**: Deploy ArgoCD to your cluster.
- **Uninstall ArgoCD**: Remove ArgoCD and optionally the namespace.
- **Add Credential Template**: Store credentials for repository URL prefixes.
- **Add Repository**: Register a new repository with ArgoCD.
- **Create Application**: Create a new ArgoCD application.
- **Create Application Batch**: Create multiple applications at once.
- **Delete Application**: Remove an application from ArgoCD.
- **List Applications**: View all ArgoCD applications.
- **List Repositories**: View all registered repositories.

---

## Logging

All actions and errors are logged to `argocd_cli.log` in the project directory.

---

## Troubleshooting

- Ensure `argocd` and `kubectl` are installed and in your PATH.
- For authentication issues, check your credentials and network connectivity.
- For Kubernetes errors, ensure your kubeconfig is set up and you have cluster access.

---

## Contributing

Pull requests and issues are welcome! Please open an issue to discuss your ideas or report bugs.

---

## License

MIT License
