#!/usr/bin/env python3
"""
Proxy injection module for Huawei Cloud CLI.
Handles interactive proxy configuration and environment variable export.
"""

import os
import re
from urllib.parse import urlparse


def mask_proxy_url(url):
    """
    Mask sensitive information in proxy URL.
    Hides username/password if present in URL.
    """
    if not url:
        return ""

    try:
        parsed = urlparse(url)
        if parsed.username or parsed.password:
            # Mask credentials in URL
            masked_url = f"{parsed.scheme}://***:***@{parsed.hostname}"
            if parsed.port:
                masked_url += f":{parsed.port}"
            if parsed.path:
                masked_url += parsed.path
            return masked_url
        return url
    except Exception:
        # If parsing fails, return masked version
        return "[masked]"


def validate_proxy_url(url):
    """
    Validate proxy URL format.
    Returns (is_valid, error_message).
    """
    if not url:
        return True, None

    # Basic URL validation
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https', 'socks4', 'socks5'):
            return False, f"Invalid proxy scheme: {parsed.scheme}. Use http, https, socks4, or socks5."

        if not parsed.hostname:
            return False, "Proxy URL must include a hostname."

        return True, None
    except Exception as e:
        return False, f"Invalid proxy URL format: {str(e)}"


def configure_proxy(http_proxy=None, https_proxy=None, no_proxy=None):
    """
    Configure proxy environment variables.

    Args:
        http_proxy: HTTP proxy URL
        https_proxy: HTTPS proxy URL
        no_proxy: Comma-separated list of hosts to exclude from proxy

    Returns:
        dict: Configuration result with status and masked values
    """
    result = {
        "success": True,
        "configured": [],
        "errors": [],
        "masked_values": {}
    }

    # Validate and set HTTP_PROXY
    if http_proxy:
        is_valid, error = validate_proxy_url(http_proxy)
        if is_valid:
            os.environ['HTTP_PROXY'] = http_proxy
            os.environ['http_proxy'] = http_proxy
            result["configured"].append("HTTP_PROXY")
            result["masked_values"]["HTTP_PROXY"] = mask_proxy_url(http_proxy)
        else:
            result["errors"].append(f"HTTP_PROXY: {error}")
            result["success"] = False

    # Validate and set HTTPS_PROXY
    if https_proxy:
        is_valid, error = validate_proxy_url(https_proxy)
        if is_valid:
            os.environ['HTTPS_PROXY'] = https_proxy
            os.environ['https_proxy'] = https_proxy
            result["configured"].append("HTTPS_PROXY")
            result["masked_values"]["HTTPS_PROXY"] = mask_proxy_url(https_proxy)
        else:
            result["errors"].append(f"HTTPS_PROXY: {error}")
            result["success"] = False

    # Set NO_PROXY
    if no_proxy:
        os.environ['NO_PROXY'] = no_proxy
        os.environ['no_proxy'] = no_proxy
        result["configured"].append("NO_PROXY")
        result["masked_values"]["NO_PROXY"] = no_proxy

    return result


def get_current_proxy_config():
    """
    Get current proxy configuration from environment.

    Returns:
        dict: Current proxy settings with masked values
    """
    return {
        "HTTP_PROXY": mask_proxy_url(os.environ.get('HTTP_PROXY', '')),
        "HTTPS_PROXY": mask_proxy_url(os.environ.get('HTTPS_PROXY', '')),
        "NO_PROXY": os.environ.get('NO_PROXY', '')
    }


def interactive_proxy_setup():
    """
    Run interactive proxy configuration.
    Prompts user for proxy settings and applies them.

    Returns:
        dict: Configuration result
    """
    print("=" * 60)
    print("Huawei Cloud CLI Proxy Configuration")
    print("=" * 60)
    print()
    print("Configure proxy settings for hcloud CLI.")
    print("Leave blank and press Enter to skip any setting.")
    print()

    # Show current configuration
    current = get_current_proxy_config()
    if any(current.values()):
        print("Current configuration:")
        for key, value in current.items():
            if value:
                print(f"  {key}: {value}")
        print()

    # Prompt for proxy settings
    http_proxy = input("HTTP_PROXY (e.g., http://proxy.company.com:8080): ").strip()
    https_proxy = input("HTTPS_PROXY (e.g., http://proxy.company.com:8080): ").strip()
    no_proxy = input("NO_PROXY (e.g., localhost,127.0.0.1,.internal.com): ").strip()

    print()

    # Configure proxies
    result = configure_proxy(
        http_proxy=http_proxy if http_proxy else None,
        https_proxy=https_proxy if https_proxy else None,
        no_proxy=no_proxy if no_proxy else None
    )

    # Display results
    if result["success"] and result["configured"]:
        print("Proxy configuration applied successfully.")
        print()
        print("Configured variables:")
        for var in result["configured"]:
            masked_value = result["masked_values"].get(var, "[masked]")
            print(f"  {var}={masked_value}")
    elif result["errors"]:
        print("Configuration failed with errors:")
        for error in result["errors"]:
            print(f"  - {error}")
    else:
        print("No proxy settings configured.")

    print()
    print("Note: These settings are only valid for the current session.")
    print("=" * 60)

    return result


if __name__ == "__main__":
    interactive_proxy_setup()
