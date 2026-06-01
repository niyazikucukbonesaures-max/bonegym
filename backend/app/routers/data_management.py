# Veri Yönetimi Router'ı
# GET    /export              → Veri dışa aktarım
# POST   /backup              → Yedekleme oluştur
# GET    /backups             → Yedekleme listesi
# POST   /restore/{backup_id} → Yedeklemeden geri yükle
# POST   /cleanup             → Eski veri temizleme
# GET    /security-status     → Güvenlik durumu

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models import DataBackup
from app.data_security_system import data_security_system

router = APIRouter()


@router.get("/export")
async def export_user_data(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    include_sensitive: bool = Query(False, description="Hassas verileri dahil et"),
    format: str = Query("json", description="Dışa aktarım formatı"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Kullanıcı verilerini JSON formatında dışa aktarır."""
    try:
        if format.lower() != "json":
            raise HTTPException(status_code=400, detail="Şu anda sadece JSON formatı desteklenmektedir")
        
        # Veri dışa aktarım
        export_data = await data_security_system.export_user_data(
            user_id=user_id,
            db=db,
            include_sensitive=include_sensitive
        )
        
        # Dosya boyutu hesapla
        import json
        json_str = json.dumps(export_data, ensure_ascii=False, default=str)
        file_size_bytes = len(json_str.encode('utf-8'))
        
        return {
            "export_successful": True,
            "user_id": user_id,
            "export_metadata": export_data.get("export_metadata", {}),
            "file_info": {
                "format": "json",
                "size_bytes": file_size_bytes,
                "size_mb": round(file_size_bytes / 1024 / 1024, 2),
                "include_sensitive": include_sensitive
            },
            "data": export_data,
            "download_info": {
                "filename": f"fitness_data_user_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "content_type": "application/json"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veri dışa aktarım hatası: {str(e)}")


@router.post("/backup")
async def create_backup(
    user_id: int = Body(..., description="Kullanıcı ID'si"),
    backup_type: str = Body("full", description="Yedekleme tipi (full/incremental)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Kullanıcı verilerinin yedeklemesini oluşturur."""
    try:
        if backup_type not in ["full", "incremental"]:
            raise HTTPException(status_code=400, detail="Geçersiz yedekleme tipi. 'full' veya 'incremental' olmalıdır")
        
        # Yedekleme oluştur
        backup_result = await data_security_system.create_backup(
            user_id=user_id,
            db=db,
            backup_type=backup_type
        )
        
        if not backup_result.success:
            raise HTTPException(status_code=500, detail=backup_result.error_message or "Yedekleme oluşturulamadı")
        
        return {
            "backup_successful": True,
            "backup_id": backup_result.backup_id,
            "user_id": user_id,
            "backup_type": backup_type,
            "file_info": {
                "size_bytes": backup_result.file_size_bytes,
                "size_mb": round(backup_result.file_size_bytes / 1024 / 1024, 2),
                "checksum": backup_result.checksum
            },
            "timestamps": {
                "created_at": backup_result.created_at.isoformat(),
                "expires_at": backup_result.expires_at.isoformat()
            },
            "retention_days": (backup_result.expires_at - backup_result.created_at).days
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Yedekleme oluşturma hatası: {str(e)}")


@router.get("/backups")
async def list_backups(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    limit: int = Query(10, ge=1, le=50, description="Maksimum kayıt sayısı"),
    backup_type: Optional[str] = Query(None, description="Yedekleme tipi filtresi"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Kullanıcının yedekleme listesini getirir."""
    try:
        # Yedekleme kayıtlarını sorgula
        stmt = (
            select(DataBackup)
            .where(DataBackup.user_id == user_id)
            .order_by(desc(DataBackup.created_at))
            .limit(limit)
        )
        
        if backup_type:
            stmt = stmt.where(DataBackup.backup_type == backup_type)
        
        result = await db.execute(stmt)
        backups = result.scalars().all()
        
        backup_list = []
        total_size_bytes = 0
        
        for backup in backups:
            backup_info = {
                "backup_id": backup.id,
                "backup_type": backup.backup_type,
                "file_size_bytes": backup.file_size_bytes,
                "file_size_mb": round(backup.file_size_bytes / 1024 / 1024, 2),
                "checksum": backup.checksum,
                "created_at": backup.created_at.isoformat(),
                "expires_at": backup.expires_at.isoformat(),
                "is_expired": backup.expires_at < datetime.now(),
                "days_until_expiry": (backup.expires_at - datetime.now()).days
            }
            backup_list.append(backup_info)
            total_size_bytes += backup.file_size_bytes
        
        return {
            "user_id": user_id,
            "backups": backup_list,
            "summary": {
                "total_backups": len(backup_list),
                "total_size_bytes": total_size_bytes,
                "total_size_mb": round(total_size_bytes / 1024 / 1024, 2),
                "active_backups": sum(1 for b in backup_list if not b["is_expired"]),
                "expired_backups": sum(1 for b in backup_list if b["is_expired"])
            },
            "backup_types": {
                "full": sum(1 for b in backup_list if b["backup_type"] == "full"),
                "incremental": sum(1 for b in backup_list if b["backup_type"] == "incremental")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Yedekleme listesi hatası: {str(e)}")


@router.post("/restore/{backup_id}")
async def restore_from_backup(
    backup_id: str = Path(..., description="Yedekleme ID'si"),
    user_id: int = Body(..., description="Kullanıcı ID'si"),
    confirm: bool = Body(False, description="Geri yükleme onayı"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Yedeklemeden veri geri yükleme işlemi."""
    try:
        if not confirm:
            # Önce onay iste
            stmt = select(DataBackup).where(
                DataBackup.id == backup_id,
                DataBackup.user_id == user_id
            )
            result = await db.execute(stmt)
            backup = result.scalar_one_or_none()
            
            if not backup:
                raise HTTPException(status_code=404, detail="Yedekleme bulunamadı")
            
            return {
                "restore_ready": True,
                "backup_info": {
                    "backup_id": backup.id,
                    "backup_type": backup.backup_type,
                    "created_at": backup.created_at.isoformat(),
                    "file_size_mb": round(backup.file_size_bytes / 1024 / 1024, 2)
                },
                "warning": "Bu işlem mevcut verilerinizi yedekleme tarihindeki duruma geri döndürecektir.",
                "confirmation_required": True,
                "next_step": "confirm=true parametresi ile tekrar çağırın"
            }
        
        # Geri yükleme işlemini gerçekleştir
        success = await data_security_system.perform_rollback(
            user_id=user_id,
            backup_id=backup_id,
            db=db
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Geri yükleme işlemi başarısız")
        
        return {
            "restore_successful": True,
            "backup_id": backup_id,
            "user_id": user_id,
            "restored_at": datetime.now().isoformat(),
            "message": "Veriler başarıyla geri yüklendi",
            "next_steps": [
                "Uygulamayı yeniden başlatın",
                "Verilerinizi kontrol edin",
                "Gerekirse yeni ölçümler ekleyin"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geri yükleme hatası: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_data(
    days_threshold: int = Body(30, description="Temizlenecek veri yaşı (gün)"),
    dry_run: bool = Body(True, description="Sadece analiz yap, silme işlemi yapma"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Eski geçici verileri temizler."""
    try:
        if days_threshold < 7:
            raise HTTPException(status_code=400, detail="Minimum 7 gün eşiği gereklidir")
        
        if dry_run:
            # Sadece analiz yap
            return {
                "dry_run": True,
                "analysis": {
                    "days_threshold": days_threshold,
                    "estimated_cleanup": "Gerçek temizleme işlemi için dry_run=false kullanın",
                    "categories_to_clean": [
                        "Süresi dolmuş yedeklemeler",
                        "Eski geçici trend analizleri",
                        "90 günden eski doğrulama kayıtları"
                    ]
                },
                "warning": "Bu işlem geri alınamaz. Önce yedekleme yapmanız önerilir."
            }
        
        # Gerçek temizleme işlemi
        cleanup_result = await data_security_system.cleanup_old_data(
            days_threshold=days_threshold,
            db=db
        )
        
        if not cleanup_result.success:
            raise HTTPException(status_code=500, detail=cleanup_result.error_message or "Temizleme işlemi başarısız")
        
        return {
            "cleanup_successful": True,
            "days_threshold": days_threshold,
            "results": {
                "deleted_records": cleanup_result.deleted_records,
                "freed_space_bytes": cleanup_result.freed_space_bytes,
                "freed_space_mb": round(cleanup_result.freed_space_bytes / 1024 / 1024, 2),
                "cleanup_categories": cleanup_result.cleanup_categories
            },
            "cleaned_at": datetime.now().isoformat(),
            "next_cleanup_recommended": (datetime.now().replace(day=1) + 
                                       datetime.timedelta(days=32)).replace(day=1).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veri temizleme hatası: {str(e)}")


@router.get("/security-status")
async def get_security_status(
    user_id: int = Query(1, description="Kullanıcı ID'si"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Veri güvenliği durumunu kontrol eder."""
    try:
        # Son yedekleme bilgisi
        stmt = (
            select(DataBackup)
            .where(DataBackup.user_id == user_id)
            .order_by(desc(DataBackup.created_at))
            .limit(1)
        )
        result = await db.execute(stmt)
        last_backup = result.scalar_one_or_none()
        
        # Toplam yedekleme sayısı
        stmt = select(DataBackup).where(DataBackup.user_id == user_id)
        result = await db.execute(stmt)
        all_backups = result.scalars().all()
        
        # Güvenlik skorunu hesapla
        security_score = 0
        security_issues = []
        
        # Yedekleme kontrolü
        if last_backup:
            days_since_backup = (datetime.now() - last_backup.created_at).days
            if days_since_backup <= 7:
                security_score += 40
            elif days_since_backup <= 30:
                security_score += 20
            else:
                security_issues.append("Son yedekleme 30 günden eski")
        else:
            security_issues.append("Hiç yedekleme yapılmamış")
        
        # Yedekleme çeşitliliği
        backup_types = set(b.backup_type for b in all_backups)
        if "full" in backup_types:
            security_score += 20
        if "incremental" in backup_types:
            security_score += 10
        
        # Veri şifreleme (her zaman aktif)
        security_score += 30
        
        # Güvenlik seviyesi
        if security_score >= 80:
            security_level = "Yüksek"
        elif security_score >= 60:
            security_level = "Orta"
        else:
            security_level = "Düşük"
        
        return {
            "user_id": user_id,
            "security_status": {
                "overall_score": security_score,
                "security_level": security_level,
                "last_assessment": datetime.now().isoformat()
            },
            "backup_status": {
                "total_backups": len(all_backups),
                "last_backup_date": last_backup.created_at.isoformat() if last_backup else None,
                "days_since_last_backup": (datetime.now() - last_backup.created_at).days if last_backup else None,
                "backup_types_used": list(backup_types),
                "active_backups": sum(1 for b in all_backups if b.expires_at > datetime.now())
            },
            "encryption_status": {
                "data_encrypted": True,
                "encryption_algorithm": "AES-256",
                "key_rotation": "Aktif"
            },
            "security_recommendations": [
                "Haftalık otomatik yedekleme ayarlayın" if not last_backup or (datetime.now() - last_backup.created_at).days > 7 else None,
                "Hem full hem incremental yedekleme kullanın" if len(backup_types) < 2 else None,
                "Eski yedeklemeleri temizleyin" if len(all_backups) > 10 else None
            ],
            "security_issues": security_issues,
            "compliance_status": {
                "data_retention": "Uyumlu",
                "encryption_standards": "Uyumlu",
                "backup_policy": "Uyumlu" if last_backup and (datetime.now() - last_backup.created_at).days <= 30 else "Uyumsuz"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Güvenlik durumu kontrolü hatası: {str(e)}")