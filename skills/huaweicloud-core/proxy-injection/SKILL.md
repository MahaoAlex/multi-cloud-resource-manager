---
name: proxy-injection
description: Interactive proxy configuration for Huawei Cloud CLI (KooCLI). Configures HTTP_PROXY, HTTPS_PROXY, and NO_PROXY environment variables for the current session.
disable-model-invocation: true
---

# Proxy Injection Skill

Configure proxy settings for Huawei Cloud CLI (KooCLI / hcloud) in the current session.

## Usage

Invoke with `/proxy-injection` to start interactive proxy configuration.

## Configuration Steps

1. Prompt for HTTP_PROXY (optional)
2. Prompt for HTTPS_PROXY (optional)
3. Prompt for NO_PROXY (optional)
4. Export variables to current session environment

## Security

- Proxy credentials in URLs are masked in output
- No persistent storage of proxy settings
- Only affects current session

## Example

```
/proxy-injection

HTTP_PROXY: http://proxy.company.com:8080
HTTPS_PROXY: http://proxy.company.com:8080
NO_PROXY: localhost,127.0.0.1,.internal.company.com
```
