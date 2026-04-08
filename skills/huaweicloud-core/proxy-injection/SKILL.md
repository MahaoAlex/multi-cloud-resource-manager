---
name: proxy-injection
description: Interactive proxy configuration for Huawei Cloud CLI (KooCLI). Configures HTTP_PROXY, HTTPS_PROXY, and NO_PROXY environment variables for the current session with user confirmation.
disable-model-invocation: true
---

# Proxy Injection Skill

Configure proxy settings for Huawei Cloud CLI (KooCLI / hcloud) in the current session.

## Usage

Invoke with `/proxy-injection` to start interactive proxy configuration.

## Configuration Flow

1. **Check for existing proxy configuration**
   - If proxy is already configured, ask user if they want to reconfigure
   - If no proxy is configured, ask user if they need proxy

2. **User confirmation**
   - Prompts user with yes/no question before proceeding
   - Allows user to skip configuration if not needed

3. **Configure proxy settings** (if user confirms)
   - Prompt for HTTP_PROXY (optional)
   - Prompt for HTTPS_PROXY (optional)
   - Prompt for NO_PROXY (optional)

4. **Export variables to current session environment**

## Security

- Proxy credentials in URLs are masked in output
- No persistent storage of proxy settings
- Only affects current session
- User must explicitly confirm before any changes are made

## Example

```
/proxy-injection

============================================================
Huawei Cloud CLI Proxy Configuration
============================================================

Proxy configuration allows Huawei Cloud CLI to connect through
a corporate or network proxy server.

Do you need to configure a proxy? [Y/n]: y

Configure proxy settings for hcloud CLI.
Leave blank and press Enter to skip any setting.

HTTP_PROXY (e.g., http://proxy.company.com:8080): http://proxy.company.com:8080
HTTPS_PROXY (e.g., http://proxy.company.com:8080): http://proxy.company.com:8080
NO_PROXY (e.g., localhost,127.0.0.1,.internal.com): localhost,127.0.0.1

Proxy configuration applied successfully.

Configured variables:
  HTTP_PROXY=http://proxy.company.com:8080
  HTTPS_PROXY=http://proxy.company.com:8080
  NO_PROXY=localhost,127.0.0.1

Note: These settings are only valid for the current session.
============================================================
```

## Skipping Configuration

If you already have proxy configured or don't need it:

```
/proxy-injection

============================================================
Huawei Cloud CLI Proxy Configuration
============================================================

Proxy configuration allows Huawei Cloud CLI to connect through
a corporate or network proxy server.

Do you need to configure a proxy? [Y/n]: n

No proxy will be configured.
============================================================
```
