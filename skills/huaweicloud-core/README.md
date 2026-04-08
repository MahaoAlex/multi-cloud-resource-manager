# Huawei Cloud Core Skills

Infrastructure skills providing reusable capabilities for Huawei Cloud CLI authentication and proxy configuration.

## Skills

### proxy-injection

Configure proxy settings for Huawei Cloud CLI (KooCLI / hcloud) in the current session.

**Usage:**
```
/proxy-injection
```

**Features:**
- Interactive configuration of HTTP_PROXY, HTTPS_PROXY, and NO_PROXY
- URL validation with support for http, https, socks4, socks5 schemes
- Credential masking in proxy URLs
- Session-only configuration (no persistent storage)

**Environment Variables Set:**
- `HTTP_PROXY` / `http_proxy`
- `HTTPS_PROXY` / `https_proxy`
- `NO_PROXY` / `no_proxy`

**Example:**
```
/proxy-injection

HTTP_PROXY (e.g., http://proxy.company.com:8080): http://proxy.company.com:8080
HTTPS_PROXY (e.g., http://proxy.company.com:8080): http://proxy.company.com:8080
NO_PROXY (e.g., localhost,127.0.0.1,.internal.com): localhost,127.0.0.1

Proxy configuration applied successfully.
Configured variables:
  HTTP_PROXY=http://proxy.company.com:8080
  HTTPS_PROXY=http://proxy.company.com:8080
  NO_PROXY=localhost,127.0.0.1

Note: These settings are only valid for the current session.
```

### auth-manager

Configure Huawei Cloud authentication credentials for Huawei Cloud CLI (KooCLI / hcloud).

**Usage:**
```
/auth-manager
```

**Features:**
- Masked input for Access Key ID and Secret Access Key
- Multi-region support (comma-separated or 'all')
- Credential validation with `hcloud vpc ListVpcs` (KooCLI) for each region
- Per-region validation results

**Environment Variables Set:**
- `HWCLOUD_ACCESS_KEY` - Huawei Cloud Access Key ID
- `HWCLOUD_SECRET_KEY` - Huawei Cloud Secret Access Key
- `HWCLOUD_REGIONS` - Comma-separated list of validated regions
- `HWCLOUD_PROJECT_ID` - Project ID (optional)

**Supported Regions:**
- cn-north-1, cn-north-4, cn-north-9 (China North)
- cn-south-1, cn-south-4 (China South)
- cn-east-2, cn-east-3 (China East)
- cn-southwest-2 (China Southwest)
- ap-southeast-1, ap-southeast-2, ap-southeast-3 (Asia Pacific)
- af-south-1 (Africa)
- sa-brazil-1 (South America)
- na-mexico-1 (North America)
- la-south-2 (Latin America)

**Example:**
```
/auth-manager

Enter your Huawei Cloud credentials:

Access Key ID: ********************
Secret Access Key: ********************************

Available regions:
  cn-north-4, cn-north-1, cn-south-1, cn-east-2, cn-east-3...

Enter regions to use (comma-separated) or 'all' for all regions:
Regions [default: cn-north-4]: cn-north-4,cn-south-1

Validating credentials...
  Region cn-north-4: OK
  Region cn-south-1: OK

Authentication configured successfully.
Environment variables set:
  HWCLOUD_ACCESS_KEY=********************ABCD
  HWCLOUD_SECRET_KEY=****************
  HWCLOUD_REGIONS=cn-north-4,cn-south-1

Validated regions (2):
  - cn-north-4
  - cn-south-1

Note: These settings are only valid for the current session.
```

## Security Considerations

- All sensitive input is masked during entry
- Credentials are never logged or stored to disk
- Only exported to current session environment
- Proxy URLs with credentials are masked in output

## Prerequisites

- Python 3.8 or higher
- Huawei Cloud CLI (KooCLI / hcloud) installed (for auth-manager validation)

## File Structure

```
huaweicloud-core/
├── proxy-injection/
│   ├── SKILL.md
│   ├── skill.yaml
│   └── proxy_injection.py
├── auth-manager/
│   ├── SKILL.md
│   ├── skill.yaml
│   └── auth_manager.py
└── README.md
```
