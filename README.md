# Cloud DNS Forwarding Inspector

## Overview

The **Cloud DNS Forwarding Inspector** is a Python-based diagnostic tool designed to help GCP support engineers and network administrators troubleshoot DNS resolution issues involving **Cloud DNS private forwarding zones**. It detects forwarding zones across projects that are bound to a specific VM's VPC and surfaces any DNS routing behavior that might not be visible from a single project view.

---

## Key Features

* Detects all Cloud DNS private forwarding zones across projects
* Identifies:

  * Source project (where the DNS zone is defined)
  * Target project (where the VPC is bound)
  * Target IP addresses for outbound forwarding
  * Cross-project forwarding relationships
  * Duplicate DNS names or multiple targets
* Outputs a clean, readable report for debugging

---

## Requirements

* Python 3.6+
* Google Cloud SDK (`gcloud`) must be installed and authenticated
* Required IAM roles:

  * `roles/dns.reader`
  * `roles/compute.viewer`

---

## Usage

```bash
python3 cloud_dns_forwarding_inspector_standalone.py \
  --vm test-vm \
  --project kamsbtest \
  --zone us-central1-a \
  --extra_projects kamsbtest1 \
  --debug
```

### Arguments

| Argument           | Description                                                 |
| ------------------ | ----------------------------------------------------------- |
| `--vm`             | VM instance name to inspect                                 |
| `--project`        | Project ID where the VM is located                          |
| `--zone`           | Zone of the VM                                              |
| `--extra_projects` | List of additional projects to inspect for forwarding zones |
| `--debug`          | Print detailed error traceback if an exception is raised    |

---

## Sample Output

```txt
================ DNS Forwarding Inspection Report ================
VM: test-vm
Project: kamsbtest
VPC: default

Forwarding Zone: cross-fwd-zone (Cross-project)
   DNS Name: factory.internal.
   Source Project: kamsbtest1
   Target Project: kamsbtest
   Cross Binding: kamsbtest1 → kamsbtest
   VPC Bindings: default
   Target IPs: 192.168.100.10
...
Total forwarding zones scanned: 5
```

---

## Project Structure

```bash
/root
├── cloud_dns_forwarding_inspector_standalone.py   # Main Python script
├── README.md                                       # Documentation for the project
├── LICENSE                                         # Open source License (MIT)
├── sample_output.txt                               # Example output file from Cloud Shell
├── Screenshots.zip                                 # Screenshot archive (or individual .png files below)
├── screenshots/                                    # Optional extracted directory
│   ├── kamsbtest_zones.png
│   ├── cross_fwd_zone_summary.png
│   ├── cross_fwd_zone_outbound.png
│   ├── cross_fwd_zone_inuseby.png
│   ├── reverse_fwd_zone_outbound.png
│   ├── reverse_fwd_zone_inuseby.png
```

---

## Benefits

* Saves hours of debugging when DNS queries return `SERVFAIL` or `NXDOMAIN`
* Detects forwarding zones outside of the current project scope
* Clarifies DNS resolution behavior at the network level
* Reduces engineering escalations and back-and-forth with customers

---

## Author

Kamal Bawa — [ksbnetworks@gmail.com](mailto:ksbnetworks@gmail.com)

---

## Reference

* [Google Cloud DNS Zone Binding Docs](https://cloud.google.com/dns/docs/zones/zones-overview#cross-project_binding)
