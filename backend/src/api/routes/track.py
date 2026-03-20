"""
轨迹分析路由
============

POST /api/v1/track/analyze - 轨迹解析
"""

from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from src.schemas.track import TrackAnalysisResult
from src.services.track_parser import TrackParser

router = APIRouter(prefix="/track", tags=["轨迹分析"])

# 常量
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.gpx', '.kml'}


class TrackAnalyzeResponse(BaseModel):
    """轨迹分析响应"""
    success: bool = Field(True, description="请求是否成功")
    data: Optional[TrackAnalysisResult] = Field(None, description="轨迹分析结果")
    track_id: str = Field(..., description="轨迹ID（用于后续请求）")
    message: Optional[str] = Field(None, description="附加消息")


@router.post("/analyze", response_model=TrackAnalyzeResponse)
async def analyze_track(
    file: UploadFile = File(..., description="GPX/KML 轨迹文件")
) -> TrackAnalyzeResponse:
    """
    解析轨迹文件

    接收 GPX/KML 轨迹文件，返回轨迹分析结果。

    - **file**: GPX/KML 轨迹文件（必填）
    """
    # 验证文件后缀
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}，仅支持 .gpx 和 .kml"
        )

    # 读取文件内容
    content = await file.read()

    # 文件大小检查
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）"
        )

    # 保存临时文件
    track_id = f"track_{uuid4().hex}"
    temp_dir = Path("temp_tracks")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / f"{track_id}{file_ext}"

    try:
        with open(temp_path, "wb") as f:
            f.write(content)

        # 解析轨迹
        parser = TrackParser()
        result = parser.parse_file(str(temp_path))

        return TrackAnalyzeResponse(
            success=True,
            data=result,
            track_id=track_id,
            message="轨迹解析成功"
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"轨迹解析失败: {str(e)}"
        )
    finally:
        # 清理临时文件
        if temp_path.exists():
            temp_path.unlink()
