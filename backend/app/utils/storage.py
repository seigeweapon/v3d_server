from pathlib import Path
from typing import BinaryIO

import tos

from app.core.config import settings

UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 使用新版 TOS 客户端 TosClientV2
_tos_client: tos.TosClientV2 | None = None


def save_file(filename: str, file_data: BinaryIO) -> str:
    """本地文件保存（开发环境占位实现）。"""
    destination = UPLOAD_DIR / filename
    with open(destination, "wb") as f:
        f.write(file_data.read())
    return str(destination)


def get_tos_client() -> tos.TosClientV2:
    """懒加载 TOS 客户端，用于生成预签名 URL 或后续上传等操作。"""
    global _tos_client
    if _tos_client is None:
        if not (
            settings.tos_access_key
            and settings.tos_secret_key
            and settings.tos_region
            and settings.tos_endpoint
        ):
            raise RuntimeError(
                "TOS 配置不完整，请在 .env 中设置 TOS_ACCESS_KEY / TOS_SECRET_KEY / TOS_REGION / TOS_ENDPOINT"
            )

        # 按照 TosClientV2 的推荐用法，直接传入 ak/sk + endpoint + region
        # 参考文档：https://www.volcengine.com/docs/6349/135725?lang=zh
        _tos_client = tos.TosClientV2(
            settings.tos_access_key,
            settings.tos_secret_key,
            settings.tos_endpoint,
            settings.tos_region,
        )
    return _tos_client


def generate_tos_upload_url(object_key: str, expires: int = 3600) -> str:
    """为指定对象 key 生成 TOS 预签名上传 URL（PUT）。"""
    client = get_tos_client()
    bucket = settings.tos_bucket
    if not bucket:
        raise RuntimeError("TOS_BUCKET 未配置")

    # 按照官方文档推荐的 TosClientV2.pre_signed_url 用法生成预签名 URL
    # 参考文档：https://www.volcengine.com/docs/6349/135725?lang=zh
    out = client.pre_signed_url(
        tos.HttpMethodType.Http_Method_Put,
        bucket,
        object_key,
        expires=expires,
    )
    return out.signed_url


def generate_tos_post_form_data(object_key: str, expires: int = 3600) -> dict:
    """
    为指定对象 key 生成 TOS PostObject 表单数据（用于浏览器表单上传，可绕过 CORS）。
    参考文档：https://www.volcengine.com/docs/6349/129225?lang=zh
    
    返回包含以下字段的字典：
    - action: 表单提交的 URL
    - fields: 表单字段字典，包含 policy, signature, key 等
    """
    client = get_tos_client()
    bucket = settings.tos_bucket
    if not bucket:
        raise RuntimeError("TOS_BUCKET 未配置")

    # 生成 PostObject 预签名
    # 注意：conditions 需要是特定结构，这里不额外添加限制条件，直接传空列表即可，
    # bucket 和 key 通过参数单独传入即可由 SDK 生成合法的 policy。
    result = client.pre_signed_post_signature(
        conditions=[],
        bucket=bucket,
        key=object_key,
        expires=expires,
    )

    # 构建表单提交 URL
    # TOS PostObject 的 action URL 格式：https://{bucket}.{endpoint}/ 或 https://{endpoint}/{bucket}/
    endpoint = settings.tos_endpoint
    if not endpoint:
        raise RuntimeError("TOS_ENDPOINT 未配置")
    
    # 移除可能的 https:// 前缀
    endpoint = endpoint.replace("https://", "").replace("http://", "")
    action_url = f"https://{bucket}.{endpoint}/"

    # 返回表单数据
    return {
        "action": action_url,
        "fields": {
            "key": object_key,
            "policy": result.policy,
            "x-tos-algorithm": result.algorithm,
            "x-tos-credential": result.credential,
            "x-tos-date": result.date,
            "x-tos-signature": result.signature,
        },
    }
