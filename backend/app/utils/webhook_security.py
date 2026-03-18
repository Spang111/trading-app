"""
Webhook 安全相关工具函数
"""
import secrets
import hashlib
from ipaddress import ip_address, ip_network
from typing import List
from app.config import settings


def generate_secret_key() -> str:
    """生成 Secret Key"""
    return secrets.token_urlsafe(32)


def verify_webhook_ip(client_ip: str, allowed_ips: List[str] = None) -> bool:
    """
    验证 IP 是否在白名单中
    
    Args:
        client_ip: 客户端 IP 地址
        allowed_ips: 允许的 IP 列表（支持 CIDR 格式）
    
    Returns:
        bool: 是否允许
    """
    if not allowed_ips:
        allowed_ips = settings.tradingview_ips
    
    try:
        client_ip_obj = ip_address(client_ip)
        
        for allowed_ip in allowed_ips:
            if "/" in allowed_ip:
                # CIDR 格式
                if client_ip_obj in ip_network(allowed_ip, strict=False):
                    return True
            else:
                # 单个 IP
                if client_ip_obj == ip_address(allowed_ip):
                    return True
        
        return False
    except ValueError:
        return False


def verify_webhook_signature(payload: str, secret_key: str, signature: str) -> bool:
    """
    验证 Webhook 签名
    
    Args:
        payload: 原始 payload 字符串
        secret_key: Secret Key
        signature: 传来的签名
    
    Returns:
        bool: 签名是否有效
    """
    expected_signature = hashlib.sha256(
        f"{payload}{secret_key}".encode()
    ).hexdigest()
    
    return secrets.compare_digest(expected_signature, signature)
