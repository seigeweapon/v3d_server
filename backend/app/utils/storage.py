from pathlib import Path
from typing import BinaryIO, Optional

import tos
from tos.models2 import PolicySignatureCondition

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


def generate_tos_download_url(object_key: str, expires: Optional[int] = None) -> str:
    """为指定对象 key 生成 TOS 预签名下载 URL（GET）。"""
    client = get_tos_client()
    bucket = settings.tos_bucket
    if not bucket:
        raise RuntimeError("TOS_BUCKET 未配置")
    
    # 使用传入的过期时间，如果没有则使用默认值 3600 秒
    if expires is None:
        expires = 3600

    # 按照官方文档推荐的 TosClientV2.pre_signed_url 用法生成预签名 URL
    # 参考文档：https://www.volcengine.com/docs/6349/135725?lang=zh
    out = client.pre_signed_url(
        tos.HttpMethodType.Http_Method_Get,
        bucket,
        object_key,
        expires=expires,
    )
    return out.signed_url


def set_tos_object_content_type(object_key: str, content_type: str) -> None:
    """
    设置 TOS 对象的 Content-Type 元数据。
    注意：需要在对象上传后调用此函数。
    """
    client = get_tos_client()
    bucket = settings.tos_bucket
    if not bucket:
        raise RuntimeError("TOS_BUCKET 未配置")
    
    try:
        # 使用 set_object_meta 设置对象的 Content-Type
        client.set_object_meta(
            bucket=bucket,
            key=object_key,
            content_type=content_type,
        )
    except Exception as e:
        # 如果设置失败，记录错误但不抛出异常（避免影响主流程）
        import logging
        logging.warning(f"设置对象 {object_key} 的 Content-Type 失败: {e}")


def list_tos_objects(prefix: str) -> list[str]:
    """
    列出 TOS 中指定前缀下的所有对象 key。
    
    参考文档：https://www.volcengine.com/docs/6349/173820?lang=zh
    
    Args:
        prefix: 对象 key 的前缀（例如 "fv-data/tests/background/uuid/"）
    
    Returns:
        对象 key 列表
    """
    client = get_tos_client()
    bucket = settings.tos_bucket
    if not bucket:
        raise RuntimeError("TOS_BUCKET 未配置")
    
    object_keys = []
    try:
        # 使用 list_objects_type2 列出对象
        # 参考文档：https://www.volcengine.com/docs/6349/173820?lang=zh
        # 注意：TOS 一次最多返回 1000 个对象，如果超过需要分页处理
        is_truncated = True
        next_continuation_token = None
        
        while is_truncated:
            # 第一次调用不使用 continuation_token，后续调用使用 token 进行分页
            if next_continuation_token:
                result = client.list_objects_type2(
                    bucket=bucket,
                    prefix=prefix,
                    continuation_token=next_continuation_token,
                )
            else:
                result = client.list_objects_type2(
                    bucket=bucket,
                    prefix=prefix,
                )
            
            # 提取对象 key
            # contents 中返回了指定前缀下的对象
            if hasattr(result, 'contents') and result.contents:
                for content in result.contents:
                    if hasattr(content, 'key'):
                        object_keys.append(content.key)
            
            # 检查是否还有更多对象需要分页获取
            is_truncated = getattr(result, 'is_truncated', False)
            if is_truncated:
                # 如果还有更多对象，获取 continuation_token 用于下次请求
                next_continuation_token = getattr(result, 'next_continuation_token', None)
                if not next_continuation_token:
                    # 如果 is_truncated 为 True 但没有 continuation_token，记录警告
                    import logging
                    logging.warning(
                        f"TOS 返回 is_truncated=True 但未提供 next_continuation_token "
                        f"(prefix={prefix})，可能无法获取所有对象"
                    )
                    break
            else:
                # 没有更多对象了，退出循环
                break
    except Exception as e:
        import logging
        logging.error(f"列出 TOS 对象失败 (prefix={prefix}): {e}")
        raise
    
    return object_keys


def delete_tos_object(object_key: str) -> None:
    """
    删除 TOS 中的指定对象。
    
    Args:
        object_key: 要删除的对象 key
    """
    client = get_tos_client()
    bucket = settings.tos_bucket
    if not bucket:
        raise RuntimeError("TOS_BUCKET 未配置")
    
    try:
        client.delete_object(bucket=bucket, key=object_key)
    except Exception as e:
        import logging
        logging.error(f"删除 TOS 对象失败 (key={object_key}): {e}")
        raise


def delete_tos_objects_by_prefix(prefix: str) -> None:
    """
    删除 TOS 中指定前缀下的所有对象。
    
    Args:
        prefix: 对象 key 的前缀（例如 "fv-data/tests/background/uuid/"）
    
    Raises:
        RuntimeError: 如果列出对象失败或任何对象删除失败，抛出异常以确保数据一致性
    """
    # 先列出所有对象
    # 如果列出失败，捕获异常并重新抛出为 RuntimeError，确保调用者能正确识别为 TOS 操作失败
    try:
        object_keys = list_tos_objects(prefix)
    except Exception as e:
        import logging
        logging.error(f"列出 TOS 对象失败 (prefix={prefix}): {e}")
        # 重新抛出为 RuntimeError，确保调用者能正确识别为 TOS 操作失败
        raise RuntimeError(f"列出 TOS 对象失败: {str(e)}") from e
    
    # 逐个删除，跟踪失败的对象
    failed_keys = []
    for object_key in object_keys:
        try:
            delete_tos_object(object_key)
        except Exception as e:
            import logging
            logging.error(f"删除对象 {object_key} 失败: {e}")
            failed_keys.append(object_key)
            # 继续删除其他对象，但记录失败
    
    # 如果有任何对象删除失败，抛出异常以确保数据一致性
    # 这样调用者可以阻止数据库记录的删除，避免产生孤儿文件
    if failed_keys:
        import logging
        error_msg = (
            f"删除 TOS 对象失败: 共 {len(failed_keys)} 个对象删除失败 "
            f"(总共 {len(object_keys)} 个对象)。失败的对象: {failed_keys[:10]}"  # 只显示前10个
            + (f" 等共 {len(failed_keys)} 个" if len(failed_keys) > 10 else "")
        )
        logging.error(error_msg)
        raise RuntimeError(error_msg)


def upload_file_to_tos(file_data: bytes, object_key: str, content_type: Optional[str] = None) -> None:
    """
    将文件数据直接上传到 TOS。
    
    Args:
        file_data: 文件的二进制数据
        object_key: TOS 对象 key
        content_type: MIME 类型（可选）
    
    Raises:
        RuntimeError: 如果上传失败
    """
    import io
    client = get_tos_client()
    bucket = settings.tos_bucket
    if not bucket:
        raise RuntimeError("TOS_BUCKET 未配置")
    
    try:
        # 使用 put_object 上传文件
        # TOS SDK 可能需要直接传递字节数据
        # 参考文档：https://www.volcengine.com/docs/6349/129225?lang=zh
        # 尝试直接传递字节数据，不使用 BytesIO
        if content_type:
            client.put_object(
                bucket=bucket,
                key=object_key,
                content=file_data,  # 直接传递字节数据
                content_type=content_type
            )
        else:
            client.put_object(
                bucket=bucket,
                key=object_key,
                content=file_data  # 直接传递字节数据
            )
    except Exception as e:
        import logging
        logging.error(f"上传文件到 TOS 失败 (key={object_key}): {e}")
        raise RuntimeError(f"上传文件到 TOS 失败: {str(e)}") from e


def generate_tos_post_form_data(object_key: str, content_type: Optional[str] = None, expires: int = 3600) -> dict:
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
    # 如需在上传时写入 Content-Type，必须在 policy.conditions 中声明同样的字段。
    # TOS SDK 期望 conditions 为字典列表，例如 {"Content-Type": "image/png"}。
    conditions = []
    if content_type:
        conditions.append(PolicySignatureCondition(key="Content-Type", value=content_type))

    result = client.pre_signed_post_signature(
        conditions=conditions,
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

    # 构建表单字段
    fields = {
        "key": object_key,
        "policy": result.policy,
        "x-tos-algorithm": result.algorithm,
        "x-tos-credential": result.credential,
        "x-tos-date": result.date,
        "x-tos-signature": result.signature,
    }

    # 携带 Content-Type，使对象在上传时即写入正确元数据
    if content_type:
        fields["Content-Type"] = content_type

    # 返回表单数据
    return {
        "action": action_url,
        "fields": fields,
    }