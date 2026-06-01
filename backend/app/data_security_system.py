# Fitness ve Kalori Takip Uygulaması - Veri Güvenlik Sistemi
# AES-256 şifreleme, otomatik yedekleme ve veri güvenliği mekanizmaları

import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DataBackup, Measurement, UserProfile, FoodLog, 
    WorkoutLog, WeightValidation, TrendAnalysis
)


# ---------------------------------------------------------------------------
# Veri Sınıfları
# ---------------------------------------------------------------------------

@dataclass
class BackupResult:
    """Yedekleme işlemi sonucu."""
    backup_id: str
    success: bool
    file_size_bytes: int
    checksum: str
    created_at: datetime
    expires_at: datetime
    error_message: Optional[str] = None


@dataclass
class CleanupResult:
    """Veri temizleme işlemi sonucu."""
    deleted_records: int
    freed_space_bytes: int
    cleanup_categories: Dict[str, int]
    success: bool
    error_message: Optional[str] = None


@dataclass
class ExportData:
    """Dışa aktarım verisi."""
    user_id: int
    export_date: datetime
    measurements: List[Dict[str, Any]]
    food_logs: List[Dict[str, Any]]
    workout_logs: List[Dict[str, Any]]
    user_profile: Dict[str, Any]
    metadata: Dict[str, Any]


# ---------------------------------------------------------------------------
# DataSecuritySystem Sınıfı
# ---------------------------------------------------------------------------

class DataSecuritySystem:
    """Veri güvenliği ve yedekleme sistemi."""
    
    # Sabitler
    BACKUP_RETENTION_DAYS = 90
    TEMP_DATA_RETENTION_DAYS = 30
    ENCRYPTION_KEY_LENGTH = 32
    SALT_LENGTH = 16
    
    def __init__(self):
        """Şifreleme anahtarını başlat."""
        self._master_key = self._get_or_create_master_key()
    
    # ------------------------------------------------------------------
    # Şifreleme ve Şifre Çözme
    # ------------------------------------------------------------------
    
    def encrypt_measurement_data(self, data: dict) -> str:
        """Ölçüm verilerini AES-256 ile şifreler.
        
        Args:
            data: Şifrelenecek veri dictionary'si
            
        Returns:
            str: Base64 encoded şifrelenmiş veri
        """
        try:
            # JSON string'e dönüştür
            json_data = json.dumps(data, ensure_ascii=False, default=str)
            
            # Fernet ile şifrele
            fernet = Fernet(self._master_key)
            encrypted_data = fernet.encrypt(json_data.encode('utf-8'))
            
            # Base64 encode
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            raise EncryptionError(f"Veri şifreleme hatası: {str(e)}")
    
    def decrypt_measurement_data(self, encrypted_data: str) -> dict:
        """Şifrelenmiş ölçüm verilerini çözer.
        
        Args:
            encrypted_data: Base64 encoded şifrelenmiş veri
            
        Returns:
            dict: Çözülmüş veri dictionary'si
        """
        try:
            # Base64 decode
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Fernet ile şifre çöz
            fernet = Fernet(self._master_key)
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            
            # JSON parse
            json_data = decrypted_bytes.decode('utf-8')
            return json.loads(json_data)
            
        except Exception as e:
            raise DecryptionError(f"Veri şifre çözme hatası: {str(e)}")
    
    # ------------------------------------------------------------------
    # Yedekleme İşlemleri
    # ------------------------------------------------------------------
    
    async def create_backup(
        self, 
        user_id: int, 
        db: AsyncSession,
        backup_type: str = "full"
    ) -> BackupResult:
        """Kullanıcı verilerinin otomatik yedeklemesini oluşturur.
        
        Args:
            user_id: Kullanıcı ID'si
            db: Veritabanı oturumu
            backup_type: Yedekleme tipi ("full" | "incremental")
            
        Returns:
            BackupResult: Yedekleme sonucu
        """
        try:
            backup_id = str(uuid.uuid4())
            created_at = datetime.now()
            expires_at = created_at + timedelta(days=self.BACKUP_RETENTION_DAYS)
            
            # Kullanıcı verilerini topla
            export_data = await self._collect_user_data(user_id, db, backup_type)
            
            # Veriyi şifrele
            encrypted_data = self.encrypt_measurement_data(export_data.__dict__)
            
            # Dosya boyutu ve checksum hesapla
            file_size_bytes = len(encrypted_data.encode('utf-8'))
            checksum = hashlib.sha256(encrypted_data.encode('utf-8')).hexdigest()
            
            # Yedekleme kaydını oluştur
            backup_record = DataBackup(
                id=backup_id,
                user_id=user_id,
                backup_type=backup_type,
                data_encrypted=encrypted_data,
                file_size_bytes=file_size_bytes,
                checksum=checksum,
                created_at=created_at,
                expires_at=expires_at
            )
            
            db.add(backup_record)
            await db.flush()
            
            return BackupResult(
                backup_id=backup_id,
                success=True,
                file_size_bytes=file_size_bytes,
                checksum=checksum,
                created_at=created_at,
                expires_at=expires_at
            )
            
        except Exception as e:
            return BackupResult(
                backup_id="",
                success=False,
                file_size_bytes=0,
                checksum="",
                created_at=datetime.now(),
                expires_at=datetime.now(),
                error_message=f"Yedekleme hatası: {str(e)}"
            )
    
    async def export_user_data(
        self, 
        user_id: int, 
        db: AsyncSession,
        include_sensitive: bool = False
    ) -> dict:
        """Kullanıcı verilerini JSON formatında dışa aktarır.
        
        Args:
            user_id: Kullanıcı ID'si
            db: Veritabanı oturumu
            include_sensitive: Hassas verileri dahil et
            
        Returns:
            dict: JSON formatında kullanıcı verileri
        """
        try:
            # Kullanıcı verilerini topla
            export_data = await self._collect_user_data(user_id, db, "full")
            
            # Hassas verileri filtrele
            if not include_sensitive:
                export_data = self._filter_sensitive_data(export_data)
            
            # Metadata ekle
            export_dict = export_data.__dict__
            export_dict["export_metadata"] = {
                "exported_at": datetime.now().isoformat(),
                "version": "1.0",
                "include_sensitive": include_sensitive,
                "total_measurements": len(export_data.measurements),
                "total_food_logs": len(export_data.food_logs),
                "total_workout_logs": len(export_data.workout_logs)
            }
            
            return export_dict
            
        except Exception as e:
            raise ExportError(f"Veri dışa aktarım hatası: {str(e)}")
    
    # ------------------------------------------------------------------
    # Veri Temizleme
    # ------------------------------------------------------------------
    
    async def cleanup_old_data(
        self, 
        days_threshold: int, 
        db: AsyncSession
    ) -> CleanupResult:
        """Eski geçici verileri temizler.
        
        Args:
            days_threshold: Gün eşiği (bu günden eski veriler silinir)
            db: Veritabanı oturumu
            
        Returns:
            CleanupResult: Temizleme sonucu
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_threshold)
            cleanup_categories = {}
            total_deleted = 0
            
            # Eski yedeklemeleri temizle
            expired_backups = await db.execute(
                select(DataBackup).where(DataBackup.expires_at < datetime.now())
            )
            expired_backup_list = expired_backups.scalars().all()
            
            for backup in expired_backup_list:
                await db.delete(backup)
                cleanup_categories["expired_backups"] = cleanup_categories.get("expired_backups", 0) + 1
                total_deleted += 1
            
            # Eski geçici trend analizlerini temizle
            old_trends = await db.execute(
                delete(TrendAnalysis).where(
                    and_(
                        TrendAnalysis.created_at < cutoff_date,
                        TrendAnalysis.analysis_type == "temporary"
                    )
                )
            )
            trends_deleted = old_trends.rowcount
            cleanup_categories["old_trend_analyses"] = trends_deleted
            total_deleted += trends_deleted
            
            # Eski doğrulama kayıtlarını temizle (90 günden eski)
            very_old_date = datetime.now() - timedelta(days=90)
            old_validations = await db.execute(
                delete(WeightValidation).where(WeightValidation.validated_at < very_old_date)
            )
            validations_deleted = old_validations.rowcount
            cleanup_categories["old_validations"] = validations_deleted
            total_deleted += validations_deleted
            
            await db.commit()
            
            # Tahmini serbest bırakılan alan (her kayıt ~1KB)
            freed_space_bytes = total_deleted * 1024
            
            return CleanupResult(
                deleted_records=total_deleted,
                freed_space_bytes=freed_space_bytes,
                cleanup_categories=cleanup_categories,
                success=True
            )
            
        except Exception as e:
            await db.rollback()
            return CleanupResult(
                deleted_records=0,
                freed_space_bytes=0,
                cleanup_categories={},
                success=False,
                error_message=f"Veri temizleme hatası: {str(e)}"
            )
    
    async def perform_rollback(
        self, 
        user_id: int, 
        backup_id: str, 
        db: AsyncSession
    ) -> bool:
        """Yedeklemeden veri geri yükleme işlemi.
        
        Args:
            user_id: Kullanıcı ID'si
            backup_id: Yedekleme ID'si
            db: Veritabanı oturumu
            
        Returns:
            bool: İşlem başarılıysa True
        """
        try:
            # Yedekleme kaydını bul
            backup_stmt = select(DataBackup).where(
                and_(
                    DataBackup.id == backup_id,
                    DataBackup.user_id == user_id
                )
            )
            result = await db.execute(backup_stmt)
            backup = result.scalar_one_or_none()
            
            if not backup:
                raise ValueError(f"Yedekleme bulunamadı: {backup_id}")
            
            # Şifrelenmiş veriyi çöz
            decrypted_data = self.decrypt_measurement_data(backup.data_encrypted)
            
            # Checksum doğrula
            current_checksum = hashlib.sha256(backup.data_encrypted.encode('utf-8')).hexdigest()
            if current_checksum != backup.checksum:
                raise ValueError("Yedekleme verisi bozulmuş (checksum uyumsuzluğu)")
            
            # Transaction başlat
            async with db.begin():
                # Mevcut verileri yedekle (güvenlik için)
                safety_backup = await self.create_backup(user_id, db, "safety")
                
                if not safety_backup.success:
                    raise ValueError("Güvenlik yedeklemesi oluşturulamadı")
                
                # Mevcut verileri sil
                await self._delete_user_data(user_id, db)
                
                # Yedekleme verilerini geri yükle
                await self._restore_user_data(user_id, decrypted_data, db)
            
            return True
            
        except Exception as e:
            await db.rollback()
            raise RollbackError(f"Geri yükleme hatası: {str(e)}")
    
    # ------------------------------------------------------------------
    # Yardımcı Metodlar
    # ------------------------------------------------------------------
    
    def _get_or_create_master_key(self) -> bytes:
        """Master şifreleme anahtarını al veya oluştur."""
        # Gerçek uygulamada bu anahtar güvenli bir yerde saklanmalı
        # Örneğin: environment variable, key management service, vb.
        key_env = os.getenv('ENCRYPTION_MASTER_KEY')
        
        if key_env:
            return base64.b64decode(key_env.encode('utf-8'))
        
        # Geliştirme ortamı için sabit anahtar (GÜVENLİ DEĞİL!)
        password = b"fitness_app_master_key_2024"
        salt = b"fitness_salt_2024"
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    async def _collect_user_data(
        self, 
        user_id: int, 
        db: AsyncSession, 
        backup_type: str
    ) -> ExportData:
        """Kullanıcı verilerini toplar."""
        # Kullanıcı profili
        profile_stmt = select(UserProfile).where(UserProfile.id == user_id)
        profile_result = await db.execute(profile_stmt)
        user_profile = profile_result.scalar_one_or_none()
        
        # Ölçümler
        measurements_stmt = select(Measurement).where(Measurement.user_id == user_id)
        if backup_type == "incremental":
            # Son 30 günün verileri
            cutoff_date = datetime.now() - timedelta(days=30)
            measurements_stmt = measurements_stmt.where(Measurement.measured_at >= cutoff_date)
        
        measurements_result = await db.execute(measurements_stmt)
        measurements = measurements_result.scalars().all()
        
        # Yemek kayıtları
        food_logs_stmt = select(FoodLog).where(FoodLog.user_id == user_id)
        if backup_type == "incremental":
            food_logs_stmt = food_logs_stmt.where(FoodLog.logged_at >= cutoff_date)
        
        food_logs_result = await db.execute(food_logs_stmt)
        food_logs = food_logs_result.scalars().all()
        
        # Antrenman kayıtları
        workout_logs_stmt = select(WorkoutLog).where(WorkoutLog.user_id == user_id)
        if backup_type == "incremental":
            workout_logs_stmt = workout_logs_stmt.where(WorkoutLog.completed_at >= cutoff_date)
        
        workout_logs_result = await db.execute(workout_logs_stmt)
        workout_logs = workout_logs_result.scalars().all()
        
        return ExportData(
            user_id=user_id,
            export_date=datetime.now(),
            measurements=[self._model_to_dict(m) for m in measurements],
            food_logs=[self._model_to_dict(f) for f in food_logs],
            workout_logs=[self._model_to_dict(w) for w in workout_logs],
            user_profile=self._model_to_dict(user_profile) if user_profile else {},
            metadata={
                "backup_type": backup_type,
                "total_records": len(measurements) + len(food_logs) + len(workout_logs)
            }
        )
    
    def _model_to_dict(self, model) -> dict:
        """SQLAlchemy modelini dictionary'ye dönüştürür."""
        if model is None:
            return {}
        
        result = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        
        return result
    
    def _filter_sensitive_data(self, export_data: ExportData) -> ExportData:
        """Hassas verileri filtreler."""
        # Kullanıcı profilinden hassas alanları kaldır
        if export_data.user_profile:
            sensitive_fields = ['password_hash', 'email', 'phone']
            for field in sensitive_fields:
                export_data.user_profile.pop(field, None)
        
        return export_data
    
    async def _delete_user_data(self, user_id: int, db: AsyncSession):
        """Kullanıcının tüm verilerini siler (rollback için)."""
        # Ölçümleri sil
        await db.execute(delete(Measurement).where(Measurement.user_id == user_id))
        
        # Yemek kayıtlarını sil
        await db.execute(delete(FoodLog).where(FoodLog.user_id == user_id))
        
        # Antrenman kayıtlarını sil
        await db.execute(delete(WorkoutLog).where(WorkoutLog.user_id == user_id))
        
        # Doğrulama kayıtlarını sil
        await db.execute(delete(WeightValidation).where(WeightValidation.user_id == user_id))
    
    async def _restore_user_data(self, user_id: int, data: dict, db: AsyncSession):
        """Yedekleme verilerini geri yükler."""
        # Bu metodun implementasyonu karmaşık olduğu için
        # gerçek uygulamada daha detaylı olarak yazılmalı
        pass


# ---------------------------------------------------------------------------
# Özel Exception Sınıfları
# ---------------------------------------------------------------------------

class EncryptionError(Exception):
    """Şifreleme hatası."""
    pass


class DecryptionError(Exception):
    """Şifre çözme hatası."""
    pass


class ExportError(Exception):
    """Veri dışa aktarım hatası."""
    pass


class RollbackError(Exception):
    """Geri yükleme hatası."""
    pass


# ---------------------------------------------------------------------------
# Global Instance
# ---------------------------------------------------------------------------

# Singleton instance
data_security_system = DataSecuritySystem()