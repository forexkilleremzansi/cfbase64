#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Subscription Content Converter

Author: cndaqiang
Update: 2025-12-03
Description: Download and convert subscription provider content to proxies
"""

import base64
import json
import re
import yaml
import requests
from urllib.parse import parse_qs, unquote


def download_and_convert_provider(url):
    """
    Download provider URL and convert to proxies list

    Args:
        url: Provider subscription URL

    Returns:
        List of proxy configurations
    """
    # Download content
    try:
        headers = {
            'User-Agent': 'mihomo/1.19.7'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.text
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return []

    # Determine content type and parse
    proxies = []

    # Find first non-comment line
    first_line = None
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            first_line = line
            break

    # Check if it's YAML format first (before base64 detection)
    # Support both 'proxies:' and 'port:' (or 'mixed-port:') as YAML indicators
    if first_line and (first_line.startswith('proxies:') or 'port:' in first_line):
        # It's YAML format
        print(f"Parsing YAML format from {url}")
        try:
            yaml_data = yaml.safe_load(content)
            if isinstance(yaml_data, dict) and 'proxies' in yaml_data:
                proxies = yaml_data['proxies']
                print(f"✓ Extracted {len(proxies)} proxies from YAML")
        except Exception as e:
            print(f"Error parsing YAML: {e}")
        return proxies

    # Check if content is base64 encoded
    decoded_content = content
    is_base64 = False

    if content:
        # Try to detect if content is base64 encoded
        # Base64 encoded content should be decodable and result in valid text
        try:
            # Check if content looks like base64 (contains only base64 chars and padding)
            # Remove whitespace and newlines
            cleaned_content = content.strip()
            # Base64 strings should have length multiple of 4
            if len(cleaned_content) % 4 == 0 and len(cleaned_content) > 100:
                # Try to decode
                decoded = base64.b64decode(cleaned_content)
                # Check if decoded content is valid UTF-8 and contains meaningful data
                decoded_str = decoded.decode('utf-8')
                if decoded_str and len(decoded_str.strip()) > 0:
                    # Check if it looks like YAML or URIs
                    decoded_content = decoded_str
                    is_base64 = True
                    print(f"Detected base64 encoded content from {url}")
        except Exception:
            # Not base64, use original content
            is_base64 = False

    # Now check decoded content if it was base64
    if is_base64:
        # Check if decoded content is YAML
        # Find first non-comment line in decoded content
        decoded_first_line = None
        for line in decoded_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                decoded_first_line = line
                break

        if decoded_first_line and (decoded_first_line.startswith('proxies:') or decoded_first_line.startswith('port:')):
            print(f"Parsing YAML format (base64 decoded) from {url}")
            try:
                yaml_data = yaml.safe_load(decoded_content)
                if isinstance(yaml_data, dict) and 'proxies' in yaml_data:
                    proxies = yaml_data['proxies']
            except Exception as e:
                print(f"Error parsing YAML: {e}")
        else:
            # It's URI list format
            print(f"Parsing URI list format from {url}")
            proxies = parse_uri_list(decoded_content)
    else:
        # Not base64, treat as URI list
        print(f"Parsing URI list format from {url}")
        proxies = parse_uri_list(content)

    return proxies


def parse_uri_list(content):
    """
    Parse URI list content and convert to proxies

    Args:
        content: Text content with one URI per line

    Returns:
        List of proxy configurations
    """
    proxies = []
    lines = content.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Parse different URI types
        if line.startswith('vmess://'):
            proxy = parse_vmess_uri(line)
            if proxy:
                proxies.append(proxy)
        elif line.startswith('vless://'):
            proxy = parse_vless_uri(line)
            if proxy:
                proxies.append(proxy)
        elif line.startswith('trojan://'):
            proxy = parse_trojan_uri(line)
            if proxy:
                proxies.append(proxy)
        elif line.startswith('ss://'):
            proxy = parse_ss_uri(line)
            if proxy:
                proxies.append(proxy)
        elif line.startswith('hysteria2://'):
            proxy = parse_hysteria2_uri(line)
            if proxy:
                proxies.append(proxy)
        elif line.startswith('anytls://'):
            proxy = parse_anytls_uri(line)
            if proxy:
                proxies.append(proxy)

    return proxies


def parse_vmess_uri(uri):
    """
    Parse VMess URI and convert to proxy config

    Args:
        uri: VMess URI string (vmess://...)

    Returns:
        Proxy configuration dict or None
    """
    try:
        # Decode base64 encoded part after vmess://
        encoded_data = uri[8:]  # Remove vmess:// prefix
        decoded = base64.b64decode(encoded_data)
        data = json.loads(decoded.decode('utf-8'))

        proxy = {
            'name': data.get('ps', data.get('remarks', 'VMess')),
            'type': 'vmess',
            'server': data.get('add', ''),
            'port': int(data.get('port', 0)),
            'uuid': data.get('id', ''),
            'alterId': int(data.get('aid', 0)),
            'cipher': data.get('scy', 'auto'),
            'udp': True
        }

        # Add optional fields if present
        if 'net' in data and data['net']:
            proxy['network'] = data['net']
        # Note: VMess JSON 'type' field is header type (none/http/srtp/etc), not proxy type
        # Do not overwrite proxy['type'] which should remain 'vmess'
        if 'host' in data and data['host']:
            proxy['servername'] = data['host']
        if 'path' in data and data['path']:
            proxy['ws-path'] = data['path']
            proxy['ws-opts'] = {
                'path': data['path']
            }
            if proxy.get('servername'):
                proxy['ws-opts']['headers'] = {'Host': proxy['servername']}

        return proxy
    except Exception as e:
        print(f"Error parsing VMess URI: {e}")
        return None


def parse_vless_uri(uri):
    """
    Parse VLESS URI and convert to proxy config

    Args:
        uri: VLESS URI string (vless://...)

    Returns:
        Proxy configuration dict or None
    """
    try:
        # Extract UUID and parameters
        # Format: vless://uuid@server:port?params#name
        if '://' in uri:
            _, rest = uri.split('://', 1)
        else:
            return None

        # Find the first @ which separates UUID from server:port
        if '@' in rest:
            uuid_part, server_part = rest.split('@', 1)
            uuid = uuid_part
        else:
            # Handle case where there's no @ (shouldn't happen for vless)
            return None

        # Parse server:port
        if ':' in server_part:
            server, rest = server_part.split(':', 1)
            # Extract port number (before any ? or / or #)
            port = rest
            for delimiter in ['/', '?', '#']:
                if delimiter in port:
                    port = port.split(delimiter, 1)[0]
        else:
            return None

        if port == '':
            return None

        # Parse query parameters from the rest of the string
        params = {}
        if '?' in rest:
            query = rest.split('?', 1)[1]
            if '#' in query:
                query = query.split('#', 1)[0]
            params = {k: v for k, v in [p.split('=', 1) for p in query.split('&') if '=' in p]}

        # Extract name from fragment
        name = 'VLESS'
        if '#' in uri:
            name = unquote(uri.split('#', 1)[1])

        proxy = {
            'name': name,
            'type': 'vless',
            'server': server,
            'port': int(port),
            'uuid': uuid,
            'udp': True
        }

        # Add optional fields from params
        if 'security' in params:
            proxy['tls'] = params['security'] == 'tls'
        if 'flow' in params:
            proxy['flow'] = params['flow']
        if 'type' in params:
            proxy['network'] = params['type']
        if 'path' in params:
            proxy['ws-path'] = params['path']
            if 'host' in params:
                proxy['ws-opts'] = {
                    'path': params['path'],
                    'headers': {'Host': params['host']}
                }
        if 'sni' in params:
            proxy['sni'] = params['sni']
        if 'fp' in params:
            proxy['fingerprint'] = params['fp']

        return proxy
    except Exception as e:
        print(f"Error parsing VLESS URI: {e}")
        return None


def parse_trojan_uri(uri):
    """
    Parse Trojan URI and convert to proxy config

    Args:
        uri: Trojan URI string (trojan://...)

    Returns:
        Proxy configuration dict or None
    """
    try:
        # Format: trojan://password@server:port?params#name
        if '://' in uri:
            _, rest = uri.split('://', 1)
        else:
            return None

        # Find the first @ which separates password from server:port
        if '@' in rest:
            password, server_part = rest.split('@', 1)
        else:
            return None

        # Parse server:port
        if ':' in server_part:
            server, rest = server_part.split(':', 1)
            # Extract port number (before any ? or / or #)
            port = rest
            for delimiter in ['/', '?', '#']:
                if delimiter in port:
                    port = port.split(delimiter, 1)[0]
        else:
            return None

        if port == '':
            return None

        # Parse query parameters from the rest of the string
        params = {}
        if '?' in rest:
            query = rest.split('?', 1)[1]
            if '#' in query:
                query = query.split('#', 1)[0]
            params = {k: v for k, v in [p.split('=', 1) for p in query.split('&') if '=' in p]}

        # Extract name from fragment
        name = 'Trojan'
        if '#' in uri:
            name = unquote(uri.split('#', 1)[1])

        proxy = {
            'name': name,
            'type': 'trojan',
            'server': server,
            'port': int(port),
            'password': password,
            'udp': True
        }

        # Add optional fields from params
        if 'security' in params:
            proxy['tls'] = params['security'] == 'tls'
        if 'sni' in params:
            proxy['sni'] = params['sni']
        if 'fp' in params:
            proxy['fingerprint'] = params['fp']
        if 'type' in params:
            proxy['network'] = params['type']
        if 'path' in params:
            proxy['ws-path'] = params['path']
        if 'host' in params:
            proxy['ws-opts'] = {
                'headers': {'Host': params['host']}
            }
        if 'serviceName' in params:
            proxy['grpc-opts'] = {
                'grpc-service-name': params['serviceName']
            }

        return proxy
    except Exception as e:
        print(f"Error parsing Trojan URI: {e}")
        return None


def parse_ss_uri(uri):
    """
    Parse Shadowsocks URI and convert to proxy config

    Args:
        uri: Shadowsocks URI string (ss://...)

    Returns:
        Proxy configuration dict or None

    Note:
        For SS2022 ciphers (e.g., 2022-blake3-aes-128-gcm), the password
        remains in base64 format and may contain multiple keys separated
        by colons (e.g., "base64key1:base64key2").
    """
    try:
        # Format: ss://base64(method:password)@server:port#name
        # or ss://method:password@server:port#name
        if '://' in uri:
            _, rest = uri.split('://', 1)
        else:
            return None

        # Extract name first
        name = 'Shadowsocks'
        if '#' in rest:
            name = unquote(rest.split('#', 1)[1])
            rest = rest.split('#', 1)[0]

        # Find the last @ which separates auth from server:port
        if '@' in rest:
            auth_part, server_part = rest.rsplit('@', 1)
        else:
            return None

        # Parse auth (can be base64 or plain text)
        if ':' in auth_part:
            # Split only on first colon to preserve SS2022 multi-key passwords
            # e.g., "2022-blake3-aes-128-gcm:key1base64:key2base64"
            method, password = auth_part.split(':', 1)
        else:
            # Try base64 decode (add padding if needed)
            try:
                # Add padding to make length multiple of 4
                padded = auth_part + '=' * (4 - len(auth_part) % 4) if len(auth_part) % 4 else auth_part
                decoded = base64.b64decode(padded).decode('utf-8')
                if ':' in decoded:
                    # Split only on first colon to preserve SS2022 multi-key passwords
                    method, password = decoded.split(':', 1)
                else:
                    return None
            except:
                return None

        # Parse server:port
        if ':' in server_part:
            server, port = server_part.split(':', 1)
        else:
            return None

        proxy = {
            'name': name,
            'type': 'ss',
            'server': server,
            'port': int(port),
            'cipher': method,
            'password': password
        }

        return proxy
    except Exception as e:
        print(f"Error parsing SS URI: {e}")
        return None


def parse_hysteria2_uri(uri):
    """
    Parse Hysteria2 URI and convert to proxy config

    Args:
        uri: Hysteria2 URI string (hysteria2://...)

    Returns:
        Proxy configuration dict or None
    """
    try:
        # Format: hysteria2://password@server:port?params#name
        if '://' in uri:
            _, rest = uri.split('://', 1)
        else:
            return None

        # Find the first @ which separates password from server:port
        if '@' in rest:
            password, server_part = rest.split('@', 1)
        else:
            return None

        # Parse server:port
        port = None
        if ':' in server_part:
            # Handle IPv6 addresses like [::1]:5021
            if '[' in server_part:
                # IPv6
                end_bracket = server_part.index(']')
                server = server_part[1:end_bracket]
                rest = server_part[end_bracket+2:]  # Skip ]:
                if ':' in rest:
                    port = rest[1:]  # Skip the : after ]
            else:
                server, rest = server_part.split(':', 1)
                # Extract port number (before any ? or / or #)
                # Find the earliest delimiter position
                port = rest
                for delimiter in ['/', '?', '#']:
                    if delimiter in port:
                        port = port.split(delimiter, 1)[0]

        if port is None or port == '':
            return None

        # Parse query parameters from the rest of the string
        params = {}
        if '?' in rest:
            query = rest.split('?', 1)[1]
            if '#' in query:
                query = query.split('#', 0)[0]
            params = {k: v for k, v in [p.split('=', 1) for p in query.split('&') if '=' in p]}

        # Extract name from fragment
        name = 'Hysteria2'
        if '#' in uri:
            name = unquote(uri.split('#', 1)[1])

        proxy = {
            'name': name,
            'type': 'hysteria2',
            'server': server,
            'port': int(port),
            'password': password,
            'udp': True
        }

        # Add optional fields from params
        if 'sni' in params:
            proxy['sni'] = params['sni']
        if 'fp' in params:
            proxy['fingerprint'] = params['fp']
        if 'insecure' in params:
            proxy['insecure'] = params['insecure'] == '1'

        return proxy
    except Exception as e:
        print(f"Error parsing Hysteria2 URI: {e}")
        return None


def parse_anytls_uri(uri):
    """
    Parse AnyTLS URI and convert to proxy config

    Args:
        uri: AnyTLS URI string (anytls://...)

    Returns:
        Proxy configuration dict or None
    """
    try:
        # Format: anytls://password@server:port?params#name
        if '://' in uri:
            _, rest = uri.split('://', 1)
        else:
            return None

        # Find the first @ which separates password from server:port
        if '@' in rest:
            password, server_part = rest.split('@', 1)
        else:
            return None

        # Parse server:port
        if ':' in server_part:
            server, rest = server_part.split(':', 1)
            # Extract port number (before any ? or / or #)
            port = rest
            for delimiter in ['/', '?', '#']:
                if delimiter in port:
                    port = port.split(delimiter, 1)[0]
        else:
            return None

        if port == '':
            return None

        # Parse query parameters from the rest of the string
        params = {}
        if '?' in rest:
            query = rest.split('?', 1)[1]
            if '#' in query:
                query = query.split('#', 1)[0]
            params = {k: v for k, v in [p.split('=', 1) for p in query.split('&') if '=' in p]}

        # Extract name from fragment
        name = 'AnyTLS'
        if '#' in uri:
            name = unquote(uri.split('#', 1)[1])

        proxy = {
            'name': name,
            'type': 'anytls',
            'server': server,
            'port': int(port),
            'password': password,
            'udp': True
        }

        # Add optional fields from params
        if 'sni' in params:
            proxy['sni'] = params['sni']
        if 'fp' in params:
            proxy['fingerprint'] = params['fp']
        if 'insecure' in params:
            proxy['insecure'] = params['insecure'] == '1'

        return proxy
    except Exception as e:
        print(f"Error parsing AnyTLS URI: {e}")
        return None
