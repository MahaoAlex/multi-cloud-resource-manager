---
name: auth-manager
description: Huawei Cloud authentication setup. Configures Access Key, Secret Key, Project ID, and regions for Huawei Cloud CLI (KooCLI) with validation. Supports both main accounts and IAM sub-users. Project ID selection from available projects.
disable-model-invocation: true
---

# Auth Manager Skill

Configure Huawei Cloud authentication credentials for Huawei Cloud CLI (KooCLI).

The CLI tool (hcloud) is part of KooCLI. Download from: https://support.huaweicloud.com/intl/en-us/qs-hcli/hcli_02_003.html

## Usage

Invoke with `/auth-manager` to start interactive authentication setup.

## Configuration Steps

1. Prompt for Access Key ID (masked input)
2. Prompt for Secret Access Key (masked input)
3. Prompt for regions (comma-separated or 'all')
4. **Query and display available projects from IAM API**
5. **Select Project ID from list or enter manually**
6. Validate credentials with hcloud VPC ListVpcs
7. Export environment variables on success

## Project ID Selection

The skill will automatically query and display available projects:

```
Querying available projects for region 'cn-north-4'...
Found 3 project(s).

Available projects:
----------------------------------------------------------------------
No.  Project Name              Project ID
----------------------------------------------------------------------
1    cn-north-4                b6c0fd8b...f2f39227
2    cn-south-1                cce11cb6...b8e606b9
3    cn-east-3                 066a1343...1a5b6d28ed
----------------------------------------------------------------------
Options:
  1-3 : Select a project from the list
  0   : Enter Project ID manually
  s   : Skip Project ID configuration

Select option [0/s/1-3]: 1
Selected: cn-north-4 (b6c0fd8b...)
```

### Selection Options

| Option | Description |
|--------|-------------|
| `1-N` | Select project by number from the list |
| `0` | Enter Project ID manually (for projects not shown) |
| `s` or Enter | Skip Project ID configuration |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HWCLOUD_ACCESS_KEY` | **Yes** | Huawei Cloud Access Key ID |
| `HWCLOUD_SECRET_KEY` | **Yes** | Huawei Cloud Secret Access Key |
| `HWCLOUD_REGIONS` | **Yes** | Comma-separated list of regions |
| `HWCLOUD_PROJECT_ID` | *Recommended* | Project ID (required for IAM sub-users) |

## Account Types

### Main Account Users
- Can work without Project ID
- System will discover and list available projects
- Can select from discovered projects

### IAM Sub-Users
- **Must select a Project ID**
- Access is limited to the selected project
- Cannot access resources outside the selected project

## Multi-Region Support

- Enter comma-separated regions: `cn-north-4,cn-south-1,cn-east-2`
- Enter `all` to discover and validate all available regions
- Each region is validated before being added

## Security

- Sensitive input is masked during entry
- Project IDs are masked in output (showing first/last 8 chars only)
- Credentials are never logged or stored to disk
- Only exported to current session environment
- Validation ensures credentials work before completing

## Example

```
/auth-manager

============================================================
Huawei Cloud Authentication Configuration
============================================================

Configure authentication credentials for hcloud CLI.
Your credentials will be validated before being applied.

Enter your Huawei Cloud credentials:

Access Key ID: ********************
Secret Access Key: ********************************

Available regions:
  cn-north-1, cn-north-4, cn-north-9, cn-south-1, cn-south-4, ...

Enter regions to use (comma-separated) or 'all' for all regions:
Regions [default: cn-north-4]: cn-north-4

Project ID Configuration:
  - Required for IAM sub-users
  - Optional for main account users

Querying available projects for region 'cn-north-4'...
Found 3 project(s).

Available projects:
----------------------------------------------------------------------
No.  Project Name              Project ID
----------------------------------------------------------------------
1    cn-north-4                b6c0fd8b...f2f39227
2    cn-south-1                cce11cb6...b8e606b9
3    cn-east-3                 066a1343...1a5b6d28ed
----------------------------------------------------------------------
Options:
  1-3 : Select a project from the list
  0   : Enter Project ID manually
  s   : Skip Project ID configuration

Select option [0/s/1-3]: 1
Selected: cn-north-4 (b6c0fd8b...)

Validating credentials...
  Region cn-north-4: OK

Authentication configured successfully.

Environment variables set:
  HWCLOUD_ACCESS_KEY=************27178
  HWCLOUD_SECRET_KEY=****************
  HWCLOUD_REGIONS=cn-north-4
  HWCLOUD_PROJECT_ID=b6c0fd8b...f2f39227

Validated regions (1):
  - cn-north-4

Note: These settings are only valid for the current session.
============================================================
```

## Troubleshooting

### "Project ID required" Error
If you see this error after skipping Project ID selection:
1. Re-run `/auth-manager`
2. Select a project from the list or enter Project ID manually

### "Could not retrieve project list"
If automatic project discovery fails:
1. You can still enter Project ID manually (option `0`)
2. Find your Project ID in Huawei Cloud Console → My Credentials → Projects

### No Domain or User Information Required
Unlike some other cloud providers, Huawei Cloud CLI authentication does **not** require:
- Domain ID/Name
- Username
- Account ID

The Access Key and Secret Key already encode your identity.
