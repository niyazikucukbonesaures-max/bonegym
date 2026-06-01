# AI Besin Asistanı Router'ı
# POST /chat          → AI ile sohbet et
# GET /session/{id}   → Oturum geçmişini al
# DELETE /session/{id} → Oturumu temizle

import uuid
import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AIChatSession, AIChatMessage, AIGeneratedFood
from app.schemas import (
    ChatRequest, 
    ChatResponse, 
    SessionHistory, 
    StatusResponse,
    ChatMessageSchema,
    NutritionData
)
from app.ai_service import get_ai_assistant_service, AIAssistantService

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    ai_service: AIAssistantService = Depends(get_ai_assistant_service)
) -> ChatResponse:
    """AI besin asistanı ile sohbet et."""
    
    try:
        # Oturumu kontrol et/oluştur
        session = await _get_or_create_session(db, request.session_id, request.user_id)
        
        # Kullanıcı mesajını kaydet
        user_message = await _save_message(
            db, 
            session.id, 
            "user", 
            request.message
        )

        # ── Gemini ile yanıt üret ──────────────────────────────────────────
        ai_result = None
        try:
            from app.gemini_service import ask_nutrition_assistant, is_gemini_available
            if is_gemini_available():
                # Oturum geçmişini al (son 10 mesaj)
                messages_stmt = (
                    select(AIChatMessage)
                    .where(AIChatMessage.session_id == request.session_id)
                    .order_by(AIChatMessage.timestamp.desc())
                    .limit(10)
                )
                msgs_result = await db.execute(messages_stmt)
                recent_msgs = list(reversed(msgs_result.scalars().all()))

                # Gemini formatına çevir
                gemini_history = []
                for msg in recent_msgs[:-1]:  # Son mesaj (yeni kullanıcı mesajı) hariç
                    role = "user" if msg.message_type == "user" else "model"
                    gemini_history.append({"role": role, "parts": [msg.content]})

                gemini_result = await ask_nutrition_assistant(request.message, gemini_history, user_id=request.user_id)
                if gemini_result["error"] is None:
                    # NutritionData schema'sına çevir
                    nutrition_data = None
                    if gemini_result["nutrition_data"]:
                        try:
                            nd = gemini_result["nutrition_data"]
                            nutrition_data = NutritionData(
                                food_name=nd["food_name"],
                                calories_per_100g=min(float(nd["calories_per_100g"]), 900),
                                protein_per_100g=min(float(nd["protein_per_100g"]), 100),
                                carbs_per_100g=min(float(nd["carbs_per_100g"]), 100),
                                fat_per_100g=min(float(nd["fat_per_100g"]), 100),
                                confidence=nd.get("confidence", "medium"),
                                source="gemini_ai"
                            )
                        except Exception:
                            pass
                    ai_result = {
                        "response": gemini_result["response"],
                        "nutrition_data": nutrition_data,
                        "error": None
                    }
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Gemini hatası, fallback kullanılıyor: {e}")

        # ── Fallback: Mevcut web scraping sistemi ─────────────────────────
        if ai_result is None:
            ai_result = await ai_service.process_nutrition_query(
                request.message,
                request.session_id,
                request.user_id
            )
        
        # AI mesajını kaydet
        nutrition_json = None
        if ai_result["nutrition_data"]:
            nutrition_json = ai_result["nutrition_data"].model_dump_json()
            
            # AI besin verisini ayrı tabloya kaydet
            await _save_ai_generated_food(
                db,
                session.id,
                user_message.id,
                ai_result["nutrition_data"]
            )
        
        assistant_message = await _save_message(
            db,
            session.id,
            "assistant",
            ai_result["response"],
            nutrition_json
        )
        
        # Oturum istatistiklerini güncelle
        await _update_session_stats(db, session.id)
        
        return ChatResponse(
            response=ai_result["response"],
            nutrition_data=ai_result["nutrition_data"],
            session_id=request.session_id,
            timestamp=assistant_message.timestamp,
            error=ai_result["error"]
        )
        
    except Exception as e:
        error_message = "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."
        
        return ChatResponse(
            response=error_message,
            nutrition_data=None,
            session_id=request.session_id,
            timestamp=datetime.now(timezone.utc),
            error=str(e)
        )


@router.get("/session/{session_id}", response_model=SessionHistory)
async def get_session_history(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> SessionHistory:
    """Oturum geçmişini al."""
    
    # Oturumu bul
    stmt = select(AIChatSession).where(AIChatSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Oturum bulunamadı"
        )
    
    # Mesajları al (son 50 mesaj)
    messages_stmt = (
        select(AIChatMessage)
        .where(AIChatMessage.session_id == session_id)
        .order_by(AIChatMessage.timestamp.desc())
        .limit(50)
    )
    messages_result = await db.execute(messages_stmt)
    messages = messages_result.scalars().all()
    
    # Mesajları ters çevir (eskiden yeniye)
    messages = list(reversed(messages))
    
    # ChatMessageSchema'ya dönüştür
    chat_messages = []
    for msg in messages:
        nutrition_data = None
        if msg.nutrition_data:
            try:
                nutrition_dict = json.loads(msg.nutrition_data)
                nutrition_data = NutritionData(**nutrition_dict)
            except (json.JSONDecodeError, ValueError):
                pass
        
        chat_messages.append(ChatMessageSchema(
            id=msg.id,
            type=msg.message_type,
            content=msg.content,
            timestamp=msg.timestamp,
            nutrition_data=nutrition_data
        ))
    
    return SessionHistory(
        session_id=session.id,
        messages=chat_messages,
        created_at=session.created_at,
        last_activity=session.last_activity,
        message_count=session.message_count
    )


@router.delete("/session/{session_id}", response_model=StatusResponse)
async def clear_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    ai_service: AIAssistantService = Depends(get_ai_assistant_service)
) -> StatusResponse:
    """Oturumu temizle."""
    
    try:
        # Oturumu ve tüm mesajlarını sil (CASCADE ile otomatik silinir)
        stmt = delete(AIChatSession).where(AIChatSession.id == session_id)
        result = await db.execute(stmt)
        await db.commit()
        
        # AI servisinden de bağlamı temizle
        ai_service.clear_session_context(session_id)
        
        if result.rowcount == 0:
            return StatusResponse(
                success=False,
                message="Oturum bulunamadı"
            )
        
        return StatusResponse(
            success=True,
            message="Oturum başarıyla temizlendi"
        )
        
    except Exception as e:
        await db.rollback()
        return StatusResponse(
            success=False,
            message=f"Oturum temizlenirken hata oluştu: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Yardımcı Fonksiyonlar
# ---------------------------------------------------------------------------

async def _get_or_create_session(
    db: AsyncSession, 
    session_id: str, 
    user_id: int
) -> AIChatSession:
    """Oturumu al veya oluştur."""
    
    # Mevcut oturumu kontrol et
    stmt = select(AIChatSession).where(AIChatSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if session:
        # Mevcut oturumun son aktivitesini güncelle
        session.last_activity = datetime.now(timezone.utc)
        await db.commit()
        return session
    
    # Yeni oturum oluştur
    new_session = AIChatSession(
        id=session_id,
        user_id=user_id,
        created_at=datetime.now(timezone.utc),
        last_activity=datetime.now(timezone.utc),
        message_count=0
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return new_session


async def _save_message(
    db: AsyncSession,
    session_id: str,
    message_type: str,
    content: str,
    nutrition_data: Optional[str] = None
) -> AIChatMessage:
    """Mesajı veritabanına kaydet."""
    
    message = AIChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        message_type=message_type,
        content=content,
        nutrition_data=nutrition_data,
        timestamp=datetime.now(timezone.utc)
    )
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return message


async def _save_ai_generated_food(
    db: AsyncSession,
    session_id: str,
    message_id: str,
    nutrition_data: NutritionData
) -> AIGeneratedFood:
    """AI tarafından üretilen besin verisini kaydet."""
    
    ai_food = AIGeneratedFood(
        session_id=session_id,
        message_id=message_id,
        food_name=nutrition_data.food_name,
        calories_per_100g=nutrition_data.calories_per_100g,
        protein_per_100g=nutrition_data.protein_per_100g,
        carbs_per_100g=nutrition_data.carbs_per_100g,
        fat_per_100g=nutrition_data.fat_per_100g,
        confidence=nutrition_data.confidence,
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(ai_food)
    await db.commit()
    await db.refresh(ai_food)
    
    return ai_food


async def _update_session_stats(db: AsyncSession, session_id: str):
    """Oturum istatistiklerini güncelle."""
    
    # Mesaj sayısını hesapla
    count_stmt = select(AIChatMessage).where(AIChatMessage.session_id == session_id)
    count_result = await db.execute(count_stmt)
    message_count = len(count_result.scalars().all())
    
    # Oturumu güncelle
    session_stmt = select(AIChatSession).where(AIChatSession.id == session_id)
    session_result = await db.execute(session_stmt)
    session = session_result.scalar_one()
    
    session.message_count = message_count
    session.last_activity = datetime.now(timezone.utc)
    
    await db.commit()