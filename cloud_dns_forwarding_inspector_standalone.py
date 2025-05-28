# cloud_dns_forwarding_inspector_standalone.py

"""
This tool inspects Google Cloud DNS private forwarding zones
that are bound to the same VPC network as a specified VM.
It supports cross-project zone discovery and reports key details
such as source and target projects, target IPs, and conflict warnings.

Requirements:
- gcloud CLI must be installed and authenticated
- The user must have read access to DNS and Compute Engine APIs in all relevant projects
"""

import subprocess
import json
import argparse
from typing import List, Dict

# ============================
# Helper Function: Run shell command and return output
# ============================
def run_cmd(cmd: List[str]) -> Dict:
    """
    Runs a shell command using subprocess and returns the JSON-parsed output.
    Raises an exception if the command fails.
    """
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise Exception(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return json.loads(result.stdout)

# ============================
# Class: VMInspector
# ============================
class VMInspector:
    def __init__(self, project: str, zone: str, vm_name: str):
        self.project = project
        self.zone = zone
        self.vm_name = vm_name

    def get_vpc_network(self) -> str:
        """
        Fetch the VPC network name associated with the given VM instance
        by calling gcloud compute instance describe.
        """
        cmd = [
            "gcloud", "compute", "instances", "describe", self.vm_name,
            "--zone", self.zone,
            "--project", self.project,
            "--format=json"
        ]
        data = run_cmd(cmd)
        network_url = data['networkInterfaces'][0]['network']
        return network_url.split('/')[-1]  # Extract network name from URL

# ============================
# Class: DNSZoneInspector
# ============================
class DNSZoneInspector:
    def __init__(self, project: str):
        self.project = project

    def list_forwarding_zones(self) -> List[Dict]:
        """
        Retrieve all forwarding DNS zones in a given project
        using gcloud dns managed-zones list.
        """
        cmd = [
            "gcloud", "dns", "managed-zones", "list",
            "--project", self.project,
            "--format=json"
        ]
        zones = run_cmd(cmd)
        return [zone for zone in zones if zone.get("forwardingConfig")]

# ============================
# Function: analyze_forwarding_zones
# ============================
def analyze_forwarding_zones(vm_project: str, vm_vpc: str, all_projects: List[str]) -> List[Dict]:
    """
    Analyze all forwarding zones across specified projects.
    Filters zones that are bound to the VM's VPC.
    Identifies:
        - Source project of the zone
        - Target VPC and project (derived from network URL)
        - Duplicate DNS names
        - Multiple target IPs
        - Cross-project direction (e.g., from kamsbtest1 → kamsbtest)
    """
    output = []
    dns_names_seen = set()

    for project in all_projects:
        inspector = DNSZoneInspector(project)
        try:
            zones = inspector.list_forwarding_zones()
        except Exception as e:
            print(f"Failed to retrieve zones from project {project}: {e}")
            continue

        for zone in zones:
            networks = zone.get("privateVisibilityConfig", {}).get("networks", [])
            for net in networks:
                network_url = net.get('networkUrl') if isinstance(net, dict) else net
                bound_vpc = network_url.split('/')[-1]
                bound_project = network_url.split('/')[6] if "/projects/" in network_url else vm_project

                if bound_vpc == vm_vpc:
                    target_ips = zone.get("forwardingConfig", {}).get("targetNameServers", [])
                    ip_list = [ip['ipv4Address'] for ip in target_ips]

                    record = {
                        "zone_name": zone["name"],
                        "dns_name": zone["dnsName"],
                        "source_project": project,
                        "target_project": bound_project,
                        "vpc_bindings": bound_vpc,
                        "target_ips": ', '.join(ip_list),
                        "is_cross_project": project != bound_project,
                        "cross_direction": f"{project} → {bound_project}" if project != bound_project else None,
                        "is_duplicate_dns": zone["dnsName"] in dns_names_seen,
                        "has_multiple_targets": len(ip_list) > 1
                    }
                    output.append(record)
                    dns_names_seen.add(zone["dnsName"])

    return output

# ============================
# Function: print_report
# ============================
def print_report(vm_name: str, vm_project: str, vm_vpc: str, zones: List[Dict]):
    """
    Display a readable report of all relevant DNS forwarding zones.
    Includes details about:
        - Cross-project bindings
        - Source and target project
        - VPC attached
        - Target IPs used by metadata DNS
    """
    print("\n================ DNS Forwarding Inspection Report ================")
    print(f"VM: {vm_name}")
    print(f"Project: {vm_project}")
    print(f"VPC: {vm_vpc}\n")

    if not zones:
        print("No forwarding zones found bound to this VM's VPC.\n")
        return

    for z in zones:
        location = "Cross-project" if z["is_cross_project"] else "Same project"
        print(f"Forwarding Zone: {z['zone_name']} ({location})")
        print(f"   DNS Name: {z['dns_name']}")
        print(f"   Source Project: {z['source_project']}")
        print(f"   Target Project: {z['target_project']}")
        if z.get("cross_direction"):
            print(f"   Cross Binding: {z['cross_direction']}")
        print(f"   VPC Bindings: {z['vpc_bindings']}")
        print(f"   Target IPs: {z['target_ips']}")
        if z["has_multiple_targets"]:
            print("   Warning: Multiple forwarding targets detected.")
        if z["is_duplicate_dns"]:
            print("   Warning: Duplicate DNS name across zones. This may cause resolution conflicts.")
        print("---")

    print(f"\nTotal forwarding zones scanned: {len(zones)}")
    print("\nNote: Metadata DNS may forward queries to the above targets due to these bindings.\n")

# ============================
# Main Function
# ============================
def main():
    """
    Entry point of the script. Parses CLI args and executes analysis.
    Note: Requires gcloud CLI to be installed and authenticated with access to all projects.
    """
    parser = argparse.ArgumentParser(description="Inspect Cloud DNS forwarding zones for a VM")
    parser.add_argument("--vm", required=True, help="VM instance name")
    parser.add_argument("--project", required=True, help="GCP project ID of the VM")
    parser.add_argument("--zone", required=True, help="Zone of the VM")
    parser.add_argument("--extra_projects", nargs='*', default=[], help="List of extra projects to inspect for DNS zones")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with full stack traces")
    args = parser.parse_args()

    try:
        projects = [args.project] + args.extra_projects
        vm = VMInspector(args.project, args.zone, args.vm)
        vpc_name = vm.get_vpc_network()
        zone_data = analyze_forwarding_zones(args.project, vpc_name, projects)
        print_report(args.vm, args.project, vpc_name, zone_data)
    except Exception as e:
        if args.debug:
            import traceback
            traceback.print_exc()
        else:
            print(f"Error: {e}")

# ============================
# Entry Point
# ============================
if __name__ == "__main__":
    main()
