import os
import subprocess
import sys
import json

from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table

# --- Configuration ---
LOG_FILE = "argocd_cli.log"
ENV_FILE = ".env"

# --- Initialize Libraries ---
console = Console()
logger.add(LOG_FILE, rotation="500 MB")


def login_to_argocd() -> bool:
    """
    Initial login attempt. Tries to use .env variables first, then prompts if they are missing.
    """
    load_dotenv(dotenv_path=ENV_FILE)

    argo_host = os.getenv("ARGO_HOST") or Prompt.ask("Enter ArgoCD host", default="localhost")
    argo_port = os.getenv("ARGO_PORT") or Prompt.ask("Enter ArgoCD port", default="8080")
    
    argo_username = os.getenv("ARGO_USERNAME") or Prompt.ask("Enter ArgoCD username")
    argo_password = os.getenv("ARGO_PASSWORD") or Prompt.ask(
        "Enter ArgoCD password", password=True
    )
    
    skip_verify_str = os.getenv("ARGO_INSECURE_SKIP_VERIFY", "false").lower()
    insecure = skip_verify_str in ("true", "1", "yes")

    server_address = f"{argo_host}:{argo_port}"

    console.print(f"Attempting to log in to [cyan]{server_address}[/cyan]...")

    command = [
        "argocd", "login", server_address,
        "--username", argo_username,
        "--password", argo_password
    ]
    if insecure:
        command.append("--insecure")

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(f"Successfully logged in: {result.stdout}")
        console.print("[green]Authentication successful.[/green]")
        return True
    except FileNotFoundError:
        logger.error("The 'argocd' command was not found.")
        console.print("[bold red]Error: The 'argocd' CLI is not installed or not in your system's PATH.[/bold red]")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to log in. Stderr: {e.stderr}")
        console.print(f"[red]Error: Authentication failed. Check credentials and connection details.[/red]")
        console.print(f"[dim]{e.stderr}[/dim]")
        return False


def prompt_and_login() -> bool:
    """
    Always prompts the user for new credentials and attempts to log in. Used for retries.
    """
    console.print("\n[bold]Enter ArgoCD Credentials[/bold]")
    argo_host = Prompt.ask("Enter ArgoCD host", default="localhost")
    argo_port = Prompt.ask("Enter ArgoCD port", default="8080")
    argo_username = Prompt.ask("Enter ArgoCD username")
    argo_password = Prompt.ask("Enter ArgoCD password", password=True)
    insecure = Confirm.ask("Skip TLS certificate verification (insecure)?", default=True)

    server_address = f"{argo_host}:{argo_port}"
    console.print(f"Attempting to log in to [cyan]{server_address}[/cyan]...")

    command = [
        "argocd", "login", server_address,
        "--username", argo_username,
        "--password", argo_password
    ]
    if insecure:
        command.append("--insecure")

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(f"Successfully logged in: {result.stdout}")
        console.print("[green]Authentication successful.[/green]")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to log in. Stderr: {e.stderr}")
        console.print(f"[red]Error: Authentication failed.[/red]")
        console.print(f"[dim]{e.stderr}[/dim]")
        return False


def install_argocd():
    """
    Installs ArgoCD into a Kubernetes cluster using kubectl.
    """
    console.print("\n[bold]Install ArgoCD into a Kubernetes Cluster[/bold]")
    console.print("This requires `kubectl` to be installed and configured to access your cluster.")
    
    namespace = Prompt.ask("Enter the namespace for ArgoCD installation", default="argocd")
    
    try:
        console.print(f"Attempting to create namespace '[cyan]{namespace}[/cyan]'...")
        create_ns_command = ["kubectl", "create", "namespace", namespace]
        result = subprocess.run(create_ns_command, capture_output=True, text=True)
        if result.returncode == 0:
            console.print(f"[green]Namespace '{namespace}' created.[/green]")
        elif "already exists" in result.stderr:
            console.print(f"[yellow]Namespace '{namespace}' already exists. Continuing.[/yellow]")
        else:
            raise subprocess.CalledProcessError(result.returncode, create_ns_command, output=result.stdout, stderr=result.stderr)

        console.print("Applying ArgoCD installation manifest...")
        install_command = ["kubectl", "apply", "-n", namespace, "-f", "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"]
        subprocess.run(install_command, check=True)
        
        logger.info(f"Successfully applied ArgoCD manifests to namespace '{namespace}'.")
        console.print(f"\n[green]ArgoCD installation manifest applied successfully to namespace '{namespace}'.[/green]")
        console.print("Run 'Check ArgoCD Installation Status' to see the pods start up.")

    except FileNotFoundError:
        logger.error("The 'kubectl' command was not found.")
        console.print("[bold red]Error: The 'kubectl' CLI is not installed or not in your system's PATH.[/bold red]")
    except subprocess.CalledProcessError as e:
        logger.error(f"An error occurred during installation. Stderr: {e.stderr}")
        console.print(f"[bold red]An error occurred during the installation process.[/bold red]")
        console.print(f"[dim]{e.stderr}[/dim]")


def check_installation_status():
    """
    Checks the status of ArgoCD pods in a given namespace using kubectl.
    """
    console.print("\n[bold]Check ArgoCD Installation Status[/bold]")
    namespace = Prompt.ask("Enter the namespace where ArgoCD is installed", default="argocd")
    
    command = ["kubectl", "get", "pods", "-n", namespace]
    
    try:
        console.print(f"Fetching pod status in namespace '[cyan]{namespace}[/cyan]'...")
        subprocess.run(command, check=True)
    except FileNotFoundError:
        logger.error("The 'kubectl' command was not found.")
        console.print("[bold red]Error: The 'kubectl' CLI is not installed or not in your system's PATH.[/bold red]")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get pod status. Stderr: {e.stderr}")
        console.print(f"[bold red]An error occurred while fetching pod status.[/bold red]")
        console.print(f"[dim]{e.stderr}[/dim]")


def delete_argocd_installation():
    """
    Deletes an ArgoCD installation from a Kubernetes cluster.
    """
    console.print("\n[bold red]Uninstall ArgoCD from a Kubernetes Cluster[/bold red]")
    namespace = Prompt.ask("Enter the namespace where ArgoCD is installed", default="argocd")

    console.print(f"\n[bold yellow]Warning:[/bold yellow] This is a destructive action that will remove all ArgoCD resources from the '{namespace}' namespace.")
    if not Confirm.ask(f"Are you sure you want to proceed with uninstalling ArgoCD from namespace '[cyan]{namespace}[/cyan]'?"):
        console.print("Uninstallation cancelled.")
        return

    try:
        console.print(f"Deleting ArgoCD resources from namespace '[cyan]{namespace}[/cyan]'...")
        delete_command = ["kubectl", "delete", "-n", namespace, "-f", "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"]
        subprocess.run(delete_command, check=True)
        logger.info(f"Successfully deleted ArgoCD resources from namespace '{namespace}'.")
        console.print(f"[green]ArgoCD resources have been deleted.[/green]")

        if Confirm.ask(f"\nDo you also want to delete the entire '[cyan]{namespace}[/cyan]' namespace?"):
            console.print(f"Deleting namespace '{namespace}'...")
            delete_ns_command = ["kubectl", "delete", "namespace", namespace]
            subprocess.run(delete_ns_command, check=True)
            logger.info(f"Successfully deleted namespace '{namespace}'.")
            console.print(f"[green]Namespace '{namespace}' has been deleted.[/green]")

    except FileNotFoundError:
        logger.error("The 'kubectl' command was not found.")
        console.print("[bold red]Error: The 'kubectl' CLI is not installed or not in your system's PATH.[/bold red]")
    except subprocess.CalledProcessError as e:
        logger.error(f"An error occurred during uninstallation. Stderr: {e.stderr}")
        console.print(f"[bold red]An error occurred during the uninstallation process.[/bold red]")
        console.print(f"[dim]{e.stderr}[/dim]")


def list_repositories():
    """
    Fetches and displays a list of all repositories in ArgoCD using JSON output.
    """
    console.print("\n[bold]Fetching Repositories...[/bold]")
    command = ["argocd", "repo", "list", "-o", "json"]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        repos = json.loads(result.stdout)
        
        if not repos:
            console.print("No repositories found.")
            return

        table = Table(title="ArgoCD Repositories", show_header=True, header_style="bold magenta")
        headers = ["REPO", "NAME", "STATUS", "CONNECTION", "PROJECT"]
        for header in headers:
            table.add_column(header)
        
        for repo in repos:
            table.add_row(
                repo.get("repo", ""),
                repo.get("name", ""),
                repo.get("status", ""),
                repo.get("connectionState", {}).get("status", ""),
                repo.get("project", "")
            )
            
        console.print(table)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON from argocd CLI output.")
        console.print("[red]Error: Could not parse the data received from the ArgoCD CLI.[/red]")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to list repositories. Stderr: {e.stderr}")
        console.print("[red]Error: Failed to list repositories.[/red]")
        console.print(f"[dim]{e.stderr}[/dim]")


def add_credential_template():
    """
    Adds repository credentials that can be used for any repo matching the URL.
    """
    console.print("\n[bold]Add Repository Credential Template[/bold]")
    console.print("This will store credentials for a URL prefix (e.g., 'https://github.com/my-org').")
    
    url_prefix = Prompt.ask("Enter Repository URL Prefix")
    username = Prompt.ask("Enter repository username")
    password = Prompt.ask("Enter repository password or PAT", password=True)
    
    command = [
        "argocd", "repocreds", "add", url_prefix,
        "--username", username,
        "--password", password
    ]

    try:
        console.print(f"Adding credentials for [cyan]{url_prefix}[/cyan]...")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(f"Successfully added credential template: {result.stdout}")
        console.print(f"[green]Successfully added credential template.[/green]")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to add credential template. Stderr: {e.stderr}")
        console.print("[red]Error: Failed to add credential template.[/red]")
        console.print(f"[dim]{e.stderr}[/dim]")


def add_repository():
    """
    Adds a single repository, relying on pre-configured credential templates.
    """
    console.print("\n[bold]Add a new Repository to ArgoCD[/bold]")
    console.print("Note: If this is a private repository, ensure you have added a matching credential template first.")
    
    repo_url = Prompt.ask("Enter the full Repository URL (e.g., https://github.com/my-org/my-repo.git)")
    
    command = ["argocd", "repo", "add", repo_url]

    try:
        console.print("Registering repository...")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(f"Successfully added repository: {result.stdout}")
        console.print(f"[green]Successfully registered repository {repo_url}.[/green]")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to add repository. Stderr: {e.stderr}")
        console.print("[red]Error: Failed to register repository. Ensure the URL is correct and credentials have been added.[/red]")
        console.print(f"[dim]{e.stderr}[/dim]")


def create_application():
    """
    Creates a new ArgoCD application using the 'argocd app create' command.
    """
    console.print("\n[bold]Create a new ArgoCD Application[/bold]")

    app_name = Prompt.ask("Application Name")
    repo_url = Prompt.ask("Repository URL")
    revision = Prompt.ask("Target branch/revision", default="HEAD")
    path = Prompt.ask("Path to manifests in repository")
    dest_server = Prompt.ask("Destination cluster URL", default="https://kubernetes.default.svc")
    dest_namespace = Prompt.ask("Destination namespace")
    project = Prompt.ask("ArgoCD Project", default="default")

    command = [
        "argocd", "app", "create", app_name,
        "--repo", repo_url,
        "--revision", revision,
        "--path", path,
        "--dest-server", dest_server,
        "--dest-namespace", dest_namespace,
        "--project", project
    ]

    enable_auto_sync = Prompt.ask("Enable automated sync?", choices=["y", "n"], default="n")
    if enable_auto_sync == 'y':
        command.extend(["--sync-policy", "automated"])
        
        enable_prune = Prompt.ask("Enable auto-pruning?", choices=["y", "n"], default="n")
        if enable_prune == 'y':
            command.append("--auto-prune")
            
        enable_self_heal = Prompt.ask("Enable self-healing?", choices=["y", "n"], default="n")
        if enable_self_heal == 'y':
            command.append("--self-heal")

    try:
        console.print(f"Creating application [cyan]{app_name}[/cyan]...")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(f"Successfully created application: {result.stdout}")
        console.print(f"[green]Successfully created application '{app_name}'.[/green]")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create application. Stderr: {e.stderr}")
        console.print("[red]Error: Failed to create application.[/red]")
        console.print(f"[dim]{e.stderr}[/dim]")


def list_applications():
    """
    Fetches and displays a list of all applications in ArgoCD using JSON output.
    """
    console.print("\n[bold]Fetching Applications...[/bold]")
    command = ["argocd", "app", "list", "-o", "json"]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        apps = json.loads(result.stdout)
        
        if not apps:
            console.print("No applications found.")
            return

        table = Table(title="ArgoCD Applications", show_header=True, header_style="bold magenta")
        headers = ["NAME", "PROJECT", "SERVER", "NAMESPACE", "SYNC STATUS", "HEALTH STATUS"]
        for header in headers:
            table.add_column(header)
        
        for app in apps:
            status = app.get("status", {})
            spec = app.get("spec", {})
            destination = spec.get("destination", {})
            metadata = app.get("metadata", {})
            
            table.add_row(
                metadata.get("name", ""),
                spec.get("project", ""),
                destination.get("server", ""),
                destination.get("namespace", ""),
                status.get("sync", {}).get("status", ""),
                status.get("health", {}).get("status", "")
            )
            
        console.print(table)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON from argocd CLI output.")
        console.print("[red]Error: Could not parse the data received from the ArgoCD CLI.[/red]")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to list applications. Stderr: {e.stderr}")
        console.print("[red]Error: Failed to list applications.[/red]")
        console.print(f"[dim]{e.stderr}[/dim]")


def delete_application():
    """
    Deletes an ArgoCD application after asking for confirmation.
    """
    console.print("\n[bold]Delete an ArgoCD Application[/bold]")
    app_name = Prompt.ask("Enter the name of the application to delete")

    if not app_name:
        console.print("[yellow]No application name entered. Aborting.[/yellow]")
        return
    
    confirmed = Confirm.ask(f"[bold red]Are you sure you want to delete the application '{app_name}'?[/bold red]")

    if not confirmed:
        console.print("Deletion cancelled.")
        return

    command = ["argocd", "app", "delete", app_name, "--yes"]

    try:
        console.print(f"Deleting application [cyan]{app_name}[/cyan]...")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(f"Successfully deleted application: {result.stdout}")
        console.print(f"[green]Successfully deleted application '{app_name}'.[/green]")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to delete application. Stderr: {e.stderr}")
        console.print("[red]Error: Failed to delete application. It may not exist.[/red]")
        console.print(f"[dim]{e.stderr}[/dim]")


def create_application_batch():
    """
    Creates a batch of ArgoCD applications with shared properties and detailed error handling.
    """
    console.print("\n[bold]Create a Batch of ArgoCD Applications[/bold]")
    
    app_names_str = Prompt.ask("Enter application names (comma-separated)")
    app_names = [name.strip() for name in app_names_str.split(',') if name.strip()]

    if not app_names:
        console.print("[yellow]No application names entered. Aborting.[/yellow]")
        return
    
    console.print("\n[bold]Enter shared configuration for the batch:[/bold]")
    repo_url = Prompt.ask("Repository URL")
    revision = Prompt.ask("Target branch/revision", default="HEAD")
    environment = Prompt.ask("Environment (e.g., dev, test, uat, prod)")
    dest_server = Prompt.ask("Destination cluster URL", default="https://kubernetes.default.svc")
    dest_namespace = Prompt.ask("Destination namespace")
    project = Prompt.ask("ArgoCD Project", default="default")

    base_command = []
    enable_auto_sync = Prompt.ask("Enable automated sync for all apps?", choices=["y", "n"], default="n")
    if enable_auto_sync == 'y':
        base_command.extend(["--sync-policy", "automated"])
        
        enable_prune = Prompt.ask("Enable auto-pruning for all apps?", choices=["y", "n"], default="n")
        if enable_prune == 'y':
            base_command.append("--auto-prune")
            
        enable_self_heal = Prompt.ask("Enable self-healing for all apps?", choices=["y", "n"], default="n")
        if enable_self_heal == 'y':
            base_command.append("--self-heal")

    successful_apps = []
    failed_apps = []

    console.print("\n[bold]Starting batch creation...[/bold]")
    for app_name in app_names:
        path = f"{app_name}/overlay/{environment}"
        
        command = [
            "argocd", "app", "create", app_name,
            "--repo", repo_url,
            "--revision", revision,
            "--path", path,
            "--dest-server", dest_server,
            "--dest-namespace", dest_namespace,
            "--project", project
        ]
        command.extend(base_command)

        try:
            console.print(f"Creating application [cyan]{app_name}[/cyan] with path [dim]'{path}'[/dim]...")
            subprocess.run(command, capture_output=True, text=True, check=True)
            successful_apps.append(app_name)
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.strip()
            logger.error(f"Failed to create application '{app_name}'. Stderr: {error_message}")
            failed_apps.append((app_name, error_message))
            console.print(f"[bold red]  -> Error creating '{app_name}'.[/bold red]")
            
            if not Confirm.ask("An error occurred. Continue with the next application?"):
                console.print("[yellow]Batch creation aborted by user.[/yellow]")
                break
    
    console.print("\n[bold]Batch Creation Summary[/bold]")
    summary_table = Table(show_header=True, header_style="bold blue")
    summary_table.add_column("Application Name", style="cyan")
    summary_table.add_column("Status", style="magenta")
    summary_table.add_column("Details / Error Message")

    for app_name in successful_apps:
        summary_table.add_row(app_name, "[green]Success[/green]", "Application created.")
    
    for app_name, error in failed_apps:
        summary_table.add_row(app_name, "[red]Failed[/red]", error)

    console.print(summary_table)
    console.print("\n[bold]Batch processing finished.[/bold]")


def main():
    """
    Main interactive loop for the ArgoCD CLI.
    """
    console.print("[bold cyan]Welcome to the ArgoCD Interactive CLI[/bold cyan]")
    
    management_options = {
        "Add Credential Template": add_credential_template,
        "Add Repository": add_repository,
        "Create Application": create_application,
        "Create Application Batch": create_application_batch,
        "Delete Application": delete_application,
        "List Applications": list_applications,
        "List Repositories": list_repositories,
    }
    
    setup_options = {
        "Check ArgoCD Installation Status": check_installation_status,
        "Install ArgoCD": install_argocd,
        "Uninstall ArgoCD": delete_argocd_installation,
    }

    logged_in = login_to_argocd()
    
    try:
        while True:
            console.print("\n[bold]Main Menu[/bold]")
            
            current_menu_text = {**setup_options}
            if logged_in:
                current_menu_text.update(management_options)
            else:
                current_menu_text["Login to ArgoCD"] = "login_retry"

            sorted_menu_items = sorted(current_menu_text.keys())
            
            for i, item_text in enumerate(sorted_menu_items, 1):
                console.print(f"[bold]{i}:[/bold] {item_text}")
            
            exit_option_number = len(sorted_menu_items) + 1
            console.print(f"[bold]{exit_option_number}:[/bold] Exit")

            valid_choices = [str(i) for i in range(1, exit_option_number + 1)]

            choice = Prompt.ask(
                "Choose an action",
                choices=valid_choices,
                default=str(exit_option_number)
            )
            
            if choice == str(exit_option_number):
                console.print("\nExiting.")
                break
            
            selected_item_text = sorted_menu_items[int(choice) - 1]
            selected_action = current_menu_text[selected_item_text]

            if selected_action == "login_retry":
                # Start the login retry loop
                while True:
                    success = prompt_and_login()
                    if success:
                        logged_in = True
                        break 
                    
                    if not Confirm.ask("[yellow]Login failed. Do you want to try again with different credentials?[/yellow]"):
                        break
            else:
                selected_action()

    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]Interrupted by user. Exiting gracefully.[/bold yellow]")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An unexpected error occurred in the main loop: {e}")
        console.print(f"\n[bold red]An unexpected error occurred: {e}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()