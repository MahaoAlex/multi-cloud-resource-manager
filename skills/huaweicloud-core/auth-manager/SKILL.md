---
name: auth-manager
description: Huawei Cloud authentication setup. Configures Access Key, Secret Key, Project ID, and regions for Huawei Cloud CLI (KooCLI) with validation. Supports both main accounts and IAM sub-users.
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
4. Prompt for Project ID (optional for main accounts, **required for IAM sub-users**)
5. Validate credentials with hcloud VPC ListVpcs
6. Export environment variables on success

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HWCLOUD_ACCESS_KEY` | **Yes** | Huawei Cloud Access Key ID |
| `HWCLOUD_SECRET_KEY` | **Yes** | Huawei Cloud Secret Access Key |
| `HWCLOUD_REGIONS` | **Yes** | Comma-separated list of regions |
| `HWCLOUD_PROJECT_ID` | *Recommended* | Project ID (required for IAM sub-users) |

## Account Types

### Main Account Users
- Can use Access Key without Project ID
- System will attempt to auto-discover Project ID
- Can access resources across multiple projects

### IAM Sub-Users
- **Must provide Project ID**
- Access is limited to the specified project
- Project ID format: 32-character hex string (e.g., `b6c0fd8b70114e2fad507fb0f2f39227`)

## Finding Your Project ID

1. Log in to Huawei Cloud Console
2. Click your username (top right) → "My Credentials"
3. Select "Projects" tab
4. Copy the Project ID for your region

Or use the CLI:
```bash
hcloud IAM KeystoneListAuthProjects --cli-region=cn-north-4
```

## Multi-Region Support

- Enter comma-separated regions: `cn-north-4,cn-south-1,cn-east-2`
- Enter `all` to discover and validate all available regions
- Each region is validated before being added

## Security

- Sensitive input is masked during entry
- Credentials are never logged or stored to disk
- Only exported to current session environment
- Validation ensures credentials work before completing

## Example

### Main Account User
```
/auth-manager

============================================================
Huawei Cloud Authentication Configuration
============================================================

Configure authentication credentials for hcloud CLI.
Your credentials will be validated before being applied.

NOTE: For IAM sub-users, Project ID is required.
      Main account users can leave Project ID blank.

Enter your Huawei Cloud credentials:

Access Key ID: ********************
Secret Access Key: ********************************

Available regions:
  cn-north-1, cn-north-4, cn-north-9, cn-south-1, cn-south-4, ...

Enter regions to use (comma-separated) or 'all' for all regions:
Regions [default: cn-north-4]: cn-north-4,cn-south-1

Project ID:
  - Required for IAM sub-users
  - Optional for main account users
  - Format: 32-character hex string
Project ID (press Enter to skip):

Attempting to discover Project ID...
Discovered Project ID: b6c0fd8b70114e2fad507fb0f2f39227

Validating credentials...
  Region cn-north-4: OK
  Region cn-south-1: OK

Authentication configured successfully.

Environment variables set:
  HWCLOUD_ACCESS_KEY=************27178
  HWCLOUD_SECRET_KEY=****************
  HWCLOUD_REGIONS=cn-north-4,cn-south-1
  HWCLOUD_PROJECT_ID=b6c0fd8b70114e2fad507fb0f2f39227

Validated regions (2):
  - cn-north-4
  - cn-south-1

Note: These settings are only valid for the current session.
============================================================
```

### IAM Sub-User
```
/auth-manager

Access Key ID: ********************
Secret Access Key: ********************************
Regions [default: cn-north-4]: cn-north-4

Project ID:
  - Required for IAM sub-users
  - Optional for main account users
Project ID (press Enter to skip): b6c0fd8b70114e2fad507fb0f2f39227

Validating credentials...
  Region cn-north-4: OK

Authentication configured successfully.
```

## Troubleshooting

### "Project ID required" Error
If you see this error, you are likely an IAM sub-user. You must provide a Project ID:
1. Log in to Huawei Cloud Console
2. Navigate to "My Credentials" → "Projects"
3. Copy the Project ID for your region
4. Run `/auth-manager` again and enter the Project ID

### "Authentication failed" Error
- Check that your Access Key and Secret Key are correct
- Ensure the keys are active (not expired or disabled)
- Verify you have permissions to access the specified regions

### No Domain or User Information Required
Unlike some other cloud providers, Huawei Cloud CLI authentication does **not** require:
- Domain ID/Name
- Username
- Account ID

The Access Key and Secret Key already encode your identity.
