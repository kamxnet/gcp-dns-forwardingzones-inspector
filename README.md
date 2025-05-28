# Cloud DNS Forwarding Inspector

## Overview

The **Cloud DNS Forwarding Inspector** is a Python-based internal diagnostic tool designed for **GCP support engineers** and **network administrators**. It helps identify how DNS queries are resolved via **private forwarding zones**, especially in **cross-project VPC bindings**, which can often lead to DNS anomalies like `SERVFAIL`, `NXDOMAIN`, or unexpected query routing.

---

## Key Features

* Scans **all Cloud DNS private forwarding zones** across multiple projects.
* Automatically detects if a DNS forwarding zone is **bound to the VM's VPC**.
* Identifies **source project** (zone origin) and **target project** (zone binding).
* Detects **cross-project DNS bindings** and **reverse DNS delegation paths**.
* Flags misconfigurations such as:

  * Duplicate DNS names across zones
  * Multiple forwarding targets
* Provides a **clear, readable report** summarizing all DNS zones affecting the VM.

---

## Architecture

The tool utilizes the `gcloud` CLI to:

1. Retrieve the VPC network associated with a VM.
2. Enumerate all Cloud DNS forwarding zones in a set of GCP projects.
3. Check if each zone is bound to the VM's VPC.
4. Identify source and target projects using parsing logic from DNS zone metadata.
5. Output a human-readable inspection report.

---

## Requirements

* Python 3.6+
* `gcloud` CLI must be installed and authenticated.
* The authenticated identity must have `viewer` or `dns.reader` and `compute.viewer` roles in all specified projects.

---

## Usage

```bash
python3 cloud_dns_forwarding_inspector_standalone.py \
  --vm test-vm \
  --project kamsbtest \
  --zone us-central1-a \
  --extra_projects kamsbtest1 other-project \
  --debug
```

### Arguments

| Argument           | Description                                                     |
| ------------------ | --------------------------------------------------------------- |
| `--vm`             | Name of the VM to inspect                                       |
| `--project`        | GCP project ID where the VM resides                             |
| `--zone`           | GCP zone of the VM                                              |
| `--extra_projects` | Optional list of other projects to inspect for forwarding zones |
| `--debug`          | Optional flag to print full stack trace on error                |

---

## Example Output

```text
================ DNS Forwarding Inspection Report ================
VM: test-vm
Project: kamsbtest
VPC: default

Forwarding Zone: reverse-fwd-zone (Cross-project)
   DNS Name: devops.internal.
   Source Project: kamsbtest
   Target Project: kamsbtest1
   Cross Binding: kamsbtest → kamsbtest1
   VPC Bindings: default
   Target IPs: 1.1.1.1
...
Total forwarding zones scanned: 5
```
```
/ (root)
├── cloud_dns_forwarding_inspector_standalone.py    # Main Python script
├── README.md              # Documentation for the project
├── LICENSE                # Open source license (MIT)
├── sample_output.txt      # Example output file from Cloud Shell
├── Screenshots.zip        # Project Overview from GCP Console

```
---

## Screenshots

- Refer to the screenshot directory for overview of different DNS forwarding zones in the sampele project. 

---

## Benefits

* **Saves hours of manual investigation** in DNS escalation cases.
* Provides **visibility into cross-project forwarding** which is not evident from within a single project.
* Accelerates **root cause analysis** during `dnsPolicy` misconfigurations.
* Ideal for debugging **metadata DNS** anomalies in GKE or Compute Engine.


## Owner

Kamal Bawa [ksbnetworks@gmail.com](mailto:ksbnetworks@gmail.com.com)
