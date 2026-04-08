---
name: auth-manager
description: Huawei Cloud authentication setup. Configures Access Key, Secret Key, and regions for Huawei Cloud CLI (KooCLI) with validation.
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
4. Validate credentials with hcloud vpc ListVpcs
5. Export environment variables on success

## Environment Variables

- `HWCLOUD_ACCESS_KEY`: Huawei Cloud Access Key ID
- `HWCLOUD_SECRET_KEY`: Huawei Cloud Secret Access Key
- `HWCLOUD_REGIONS`: Comma-separated list of regions
- `HWCLOUD_PROJECT_ID`: Project ID (optional)

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

```
/auth-manager

Huawei Cloud Access Key ID: ********************
Huawei Cloud Secret Access Key: ********************************
Regions (comma-separated or 'all'): cn-north-4,cn-south-1

Validating credentials...
Region cn-north-4: OK
Region cn-south-1: OK

Authentication configured successfully.
```
