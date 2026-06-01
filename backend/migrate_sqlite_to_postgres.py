"""
SQLite'tan PostgreSQL (Supabase)'e veri taşıma scripti.
Çalıştır: DATABASE_URL="postgresql://..." python migrate_sqlite_to_postgres.py
"""
import asyncio
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, '.')

from sqlalchemy import text
from app.database import engine, _IS_POSTGRES

SQLITE_PATH = Path("fitness.db")

# Migration sonuç sayaçları
_success = 0
_failed = 0


def parse_dt(val):
    """SQLite datetime string'ini timezone-aware datetime'a çevir."""
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(str(val), fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def safe_bool(row, key, default=False):
    """SQLite'tan güvenli bool okuma."""
    if key not in row.keys():
        return default
    return bool(row[key])


def safe_get(row, key, default=None):
    """SQLite'tan güvenli alan okuma."""
    if key not in row.keys():
        return default
    return row[key]


def safe_json(row, key, default=None):
    """SQLite'tan JSON alanı okuma — string veya None döner."""
    val = safe_get(row, key)
    if val is None:
        return json.dumps(default) if default is not None else None
    if isinstance(val, str):
        return val  # Zaten JSON string
    return json.dumps(val)


async def migrate_table(pg, cursor, table_name, migrate_fn):
    """Tek bir tabloyu hata toleransıyla migrate et."""
    global _success, _failed
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        print(f"  {table_name}: {len(rows)} kayıt")
        if rows:
            await migrate_fn(pg, rows)
        print(f"  ✅ {table_name} taşındı")
        _success += 1
    except Exception as e:
        print(f"  ❌ {table_name} HATA: {e}")
        _failed += 1


async def migrate():
    global _success, _failed
    if not _IS_POSTGRES:
        print("❌ PostgreSQL bağlantısı bulunamadı. DATABASE_URL env var'ını kontrol edin.")
        return

    if not SQLITE_PATH.exists():
        print(f"❌ SQLite dosyası bulunamadı: {SQLITE_PATH}")
        return

    print("📦 SQLite → PostgreSQL migration başlıyor...")
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    async with engine.begin() as pg:

        # ── food_items ──────────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM food_items")
            rows = cursor.fetchall()
            print(f"  food_items: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM food_items"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO food_items (id, name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, source_url, scraped_at)
                        VALUES (:id, :name, :cal, :prot, :carbs, :fat, :url, :scraped)
                    """), {
                        "id": row["id"], "name": row["name"],
                        "cal": row["calories_per_100g"], "prot": row["protein_per_100g"],
                        "carbs": row["carbs_per_100g"], "fat": row["fat_per_100g"],
                        "url": row["source_url"], "scraped": parse_dt(row["scraped_at"]),
                    })
                await pg.execute(text("SELECT setval('food_items_id_seq', (SELECT MAX(id) FROM food_items))"))
            print(f"  ✅ food_items taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ food_items HATA: {e}")
            _failed += 1

        # ── users (auth) ─────────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
            print(f"  users: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM user_sessions"))
                await pg.execute(text("DELETE FROM users"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO users (id, email, username, full_name, hashed_password, is_active, is_verified, created_at, last_login)
                        VALUES (:id, :email, :username, :full_name, :hashed_password, :is_active, :is_verified, :created_at, :last_login)
                    """), {
                        "id": row["id"], "email": row["email"],
                        "username": row["username"], "full_name": safe_get(row, "full_name", ""),
                        "hashed_password": row["hashed_password"],
                        "is_active": safe_bool(row, "is_active", True),
                        "is_verified": safe_bool(row, "is_verified", True),
                        "created_at": parse_dt(safe_get(row, "created_at")),
                        "last_login": parse_dt(safe_get(row, "last_login")),
                    })
                await pg.execute(text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))"))
            print(f"  ✅ users taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ users HATA: {e}")
            _failed += 1

        # ── user_sessions (auth) ──────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM user_sessions")
            rows = cursor.fetchall()
            print(f"  user_sessions: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM user_sessions"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO user_sessions (id, user_id, session_token, expires_at, created_at, user_agent, ip_address)
                        VALUES (:id, :user_id, :session_token, :expires_at, :created_at, :user_agent, :ip_address)
                    """), {
                        "id": row["id"], "user_id": row["user_id"],
                        "session_token": row["session_token"],
                        "expires_at": parse_dt(row["expires_at"]),
                        "created_at": parse_dt(safe_get(row, "created_at")),
                        "user_agent": safe_get(row, "user_agent"),
                        "ip_address": safe_get(row, "ip_address"),
                    })
                await pg.execute(text("SELECT setval('user_sessions_id_seq', (SELECT MAX(id) FROM user_sessions))"))
            print(f"  ✅ user_sessions taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ user_sessions HATA: {e}")
            _failed += 1

        # ── user_profile ─────────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM user_profile")
            rows = cursor.fetchall()
            print(f"  user_profile: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM user_profile"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO user_profile (id, weight_kg, height_cm, age, gender, activity_level, goal, weekly_workout_goal, daily_calorie_target, updated_at, is_athlete, preferred_measurement_time, data_retention_days, privacy_level)
                        VALUES (:id, :w, :h, :age, :gender, :act, :goal, :wg, :dct, :upd, :ath, :pmt, :drd, :pl)
                    """), {
                        "id": row["id"], "w": row["weight_kg"], "h": row["height_cm"],
                        "age": row["age"], "gender": row["gender"], "act": row["activity_level"],
                        "goal": row["goal"], "wg": row["weekly_workout_goal"],
                        "dct": row["daily_calorie_target"], "upd": parse_dt(row["updated_at"]),
                        "ath": safe_bool(row, "is_athlete"), "pmt": safe_get(row, "preferred_measurement_time"),
                        "drd": safe_get(row, "data_retention_days", 365), "pl": safe_get(row, "privacy_level", "standard"),
                    })
                await pg.execute(text("SELECT setval('user_profile_id_seq', (SELECT MAX(id) FROM user_profile))"))
            print(f"  ✅ user_profile taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ user_profile HATA: {e}")
            _failed += 1

        # ── food_log ─────────────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM food_log")
            rows = cursor.fetchall()
            print(f"  food_log: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM food_log"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO food_log (id, user_id, food_item_id, food_name, grams, calories, protein, carbs, fat, logged_at, meal_type)
                        VALUES (:id, :uid, :fid, :fname, :g, :cal, :prot, :carbs, :fat, :logged, :meal)
                    """), {
                        "id": row["id"], "uid": row["user_id"], "fid": row["food_item_id"],
                        "fname": row["food_name"], "g": row["grams"], "cal": row["calories"],
                        "prot": row["protein"], "carbs": row["carbs"], "fat": row["fat"],
                        "logged": parse_dt(row["logged_at"]), "meal": row["meal_type"],
                    })
                await pg.execute(text("SELECT setval('food_log_id_seq', (SELECT MAX(id) FROM food_log))"))
            print(f"  ✅ food_log taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ food_log HATA: {e}")
            _failed += 1

        # ── measurements ─────────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM measurements")
            rows = cursor.fetchall()
            print(f"  measurements: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM measurements"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO measurements (id, user_id, height_cm, weight_kg, waist_cm, hip_cm, chest_cm, arm_cm, leg_cm, measured_at, is_validated, validation_notes, measurement_method, confidence_score)
                        VALUES (:id, :uid, :h, :w, :waist, :hip, :chest, :arm, :leg, :meas, :iv, :vn, :mm, :cs)
                    """), {
                        "id": row["id"], "uid": row["user_id"], "h": row["height_cm"],
                        "w": row["weight_kg"], "waist": row["waist_cm"], "hip": row["hip_cm"],
                        "chest": row["chest_cm"], "arm": row["arm_cm"], "leg": row["leg_cm"],
                        "meas": parse_dt(row["measured_at"]), "iv": safe_bool(row, "is_validated", True),
                        "vn": safe_get(row, "validation_notes"), "mm": safe_get(row, "measurement_method", "manual"),
                        "cs": safe_get(row, "confidence_score", 1.0),
                    })
                await pg.execute(text("SELECT setval('measurements_id_seq', (SELECT MAX(id) FROM measurements))"))
            print(f"  ✅ measurements taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ measurements HATA: {e}")
            _failed += 1

        # ── water_logs ───────────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM water_logs")
            rows = cursor.fetchall()
            print(f"  water_logs: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM water_logs"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO water_logs (id, user_id, amount_ml, logged_at)
                        VALUES (:id, :uid, :amt, :logged)
                    """), {"id": row["id"], "uid": row["user_id"], "amt": row["amount_ml"], "logged": parse_dt(row["logged_at"])})
                await pg.execute(text("SELECT setval('water_logs_id_seq', (SELECT MAX(id) FROM water_logs))"))
            print(f"  ✅ water_logs taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ water_logs HATA: {e}")
            _failed += 1

        # ── creatine_doses ───────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM creatine_doses")
            rows = cursor.fetchall()
            print(f"  creatine_doses: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM creatine_doses"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO creatine_doses (id, user_id, dose_grams, phase, taken_at)
                        VALUES (:id, :uid, :dose, :phase, :taken)
                    """), {"id": row["id"], "uid": row["user_id"], "dose": row["dose_grams"], "phase": row["phase"], "taken": parse_dt(row["taken_at"])})
                await pg.execute(text("SELECT setval('creatine_doses_id_seq', (SELECT MAX(id) FROM creatine_doses))"))
            print(f"  ✅ creatine_doses taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ creatine_doses HATA: {e}")
            _failed += 1

        # ── workout_programs ─────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM workout_programs")
            rows = cursor.fetchall()
            print(f"  workout_programs: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM workout_programs"))
                for row in rows:
                    await pg.execute(text("INSERT INTO workout_programs (id, name, created_at) VALUES (:id, :name, :created)"),
                        {"id": row["id"], "name": row["name"], "created": parse_dt(row["created_at"])})
                await pg.execute(text("SELECT setval('workout_programs_id_seq', (SELECT MAX(id) FROM workout_programs))"))
            print(f"  ✅ workout_programs taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ workout_programs HATA: {e}")
            _failed += 1

        # ── exercises ────────────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM exercises")
            rows = cursor.fetchall()
            print(f"  exercises: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM exercises"))
                for row in rows:
                    await pg.execute(text("""INSERT INTO exercises (id, program_id, name, sets, reps, weight_kg, "order") VALUES (:id, :pid, :name, :sets, :reps, :w, :ord)"""),
                        {"id": row["id"], "pid": row["program_id"], "name": row["name"], "sets": row["sets"], "reps": row["reps"], "w": row["weight_kg"], "ord": row["order"]})
                await pg.execute(text("SELECT setval('exercises_id_seq', (SELECT MAX(id) FROM exercises))"))
            print(f"  ✅ exercises taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ exercises HATA: {e}")
            _failed += 1

        # ── workout_logs ─────────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM workout_logs")
            rows = cursor.fetchall()
            print(f"  workout_logs: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM exercise_logs"))
                await pg.execute(text("DELETE FROM workout_logs"))
                for row in rows:
                    await pg.execute(text("INSERT INTO workout_logs (id, program_id, program_name, completed_at, duration_minutes) VALUES (:id, :pid, :pname, :comp, :dur)"),
                        {"id": row["id"], "pid": row["program_id"], "pname": row["program_name"], "comp": parse_dt(row["completed_at"]), "dur": row["duration_minutes"]})
                await pg.execute(text("SELECT setval('workout_logs_id_seq', (SELECT MAX(id) FROM workout_logs))"))
            print(f"  ✅ workout_logs taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ workout_logs HATA: {e}")
            _failed += 1

        # ── exercise_logs ─────────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM exercise_logs")
            rows = cursor.fetchall()
            print(f"  exercise_logs: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM exercise_logs"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO exercise_logs (id, workout_log_id, exercise_name, sets_performed, reps_performed, weight_kg)
                        VALUES (:id, :wlid, :name, :sets, :reps, :w)
                    """), {
                        "id": row["id"], "wlid": row["workout_log_id"], "name": row["exercise_name"],
                        "sets": safe_get(row, "sets_performed", safe_get(row, "sets_completed", 0)),
                        "reps": safe_get(row, "reps_performed", safe_get(row, "reps_completed", 0)),
                        "w": row["weight_kg"],
                    })
                await pg.execute(text("SELECT setval('exercise_logs_id_seq', (SELECT MAX(id) FROM exercise_logs))"))
            print(f"  ✅ exercise_logs taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ exercise_logs HATA: {e}")
            _failed += 1

        # ── achievements ─────────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM achievements")
            rows = cursor.fetchall()
            print(f"  achievements: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM user_achievements"))
                await pg.execute(text("DELETE FROM achievements"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO achievements (id, name, description, icon, category, condition_type, condition_value, points, created_at)
                        VALUES (:id, :name, :desc, :icon, :cat, :ctype, :cval, :pts, :created)
                    """), {
                        "id": row["id"], "name": row["name"], "desc": row["description"],
                        "icon": row["icon"], "cat": row["category"],
                        "ctype": row["condition_type"], "cval": row["condition_value"],
                        "pts": safe_get(row, "points", 10), "created": parse_dt(safe_get(row, "created_at")),
                    })
                await pg.execute(text("SELECT setval('achievements_id_seq', (SELECT MAX(id) FROM achievements))"))
            print(f"  ✅ achievements taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ achievements HATA: {e}")
            _failed += 1

        # ── user_achievements ─────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM user_achievements")
            rows = cursor.fetchall()
            print(f"  user_achievements: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM user_achievements"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO user_achievements (id, user_id, achievement_id, earned_at, is_new)
                        VALUES (:id, :uid, :aid, :earned, :is_new)
                    """), {
                        "id": row["id"], "uid": row["user_id"], "aid": row["achievement_id"],
                        "earned": parse_dt(row["earned_at"]), "is_new": safe_bool(row, "is_new", True),
                    })
                await pg.execute(text("SELECT setval('user_achievements_id_seq', (SELECT MAX(id) FROM user_achievements))"))
            print(f"  ✅ user_achievements taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ user_achievements HATA: {e}")
            _failed += 1

        # ── barcode_products ──────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM barcode_products")
            rows = cursor.fetchall()
            print(f"  barcode_products: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM barcode_products"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO barcode_products (id, barcode, name, brand, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, serving_size_g, image_url, source, created_at, updated_at)
                        VALUES (:id, :barcode, :name, :brand, :cal, :prot, :carbs, :fat, :serving, :img, :source, :created, :updated)
                    """), {
                        "id": row["id"], "barcode": row["barcode"], "name": row["name"],
                        "brand": safe_get(row, "brand"), "cal": row["calories_per_100g"],
                        "prot": row["protein_per_100g"], "carbs": row["carbs_per_100g"], "fat": row["fat_per_100g"],
                        "serving": safe_get(row, "serving_size_g"), "img": safe_get(row, "image_url"),
                        "source": safe_get(row, "source", "openfoodfacts"),
                        "created": parse_dt(safe_get(row, "created_at")), "updated": parse_dt(safe_get(row, "updated_at")),
                    })
                await pg.execute(text("SELECT setval('barcode_products_id_seq', (SELECT MAX(id) FROM barcode_products))"))
            print(f"  ✅ barcode_products taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ barcode_products HATA: {e}")
            _failed += 1

        # ── ai_chat_sessions (String PK) ──────────────────────────────────
        try:
            cursor.execute("SELECT * FROM ai_chat_sessions")
            rows = cursor.fetchall()
            print(f"  ai_chat_sessions: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM ai_generated_foods"))
                await pg.execute(text("DELETE FROM ai_chat_messages"))
                await pg.execute(text("DELETE FROM ai_chat_sessions"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO ai_chat_sessions (id, user_id, created_at, last_activity, message_count)
                        VALUES (:id, :uid, :created, :last, :cnt)
                    """), {
                        "id": row["id"], "uid": row["user_id"],
                        "created": parse_dt(row["created_at"]), "last": parse_dt(row["last_activity"]),
                        "cnt": safe_get(row, "message_count", 0),
                    })
            print(f"  ✅ ai_chat_sessions taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ ai_chat_sessions HATA: {e}")
            _failed += 1

        # ── ai_chat_messages (String PK) ──────────────────────────────────
        try:
            cursor.execute("SELECT * FROM ai_chat_messages")
            rows = cursor.fetchall()
            print(f"  ai_chat_messages: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM ai_chat_messages"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO ai_chat_messages (id, session_id, message_type, content, nutrition_data, timestamp)
                        VALUES (:id, :sid, :mtype, :content, :nutrition, :ts)
                    """), {
                        "id": row["id"], "sid": row["session_id"],
                        "mtype": safe_get(row, "message_type", safe_get(row, "role", "user")),
                        "content": row["content"], "nutrition": safe_get(row, "nutrition_data"),
                        "ts": parse_dt(safe_get(row, "timestamp", safe_get(row, "created_at"))),
                    })
            print(f"  ✅ ai_chat_messages taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ ai_chat_messages HATA: {e}")
            _failed += 1

        # ── ai_generated_foods ────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM ai_generated_foods")
            rows = cursor.fetchall()
            print(f"  ai_generated_foods: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM ai_generated_foods"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO ai_generated_foods (id, session_id, message_id, food_name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, confidence, created_at)
                        VALUES (:id, :sid, :mid, :fname, :cal, :prot, :carbs, :fat, :conf, :created)
                    """), {
                        "id": row["id"], "sid": row["session_id"], "mid": row["message_id"],
                        "fname": row["food_name"], "cal": row["calories_per_100g"],
                        "prot": row["protein_per_100g"], "carbs": row["carbs_per_100g"], "fat": row["fat_per_100g"],
                        "conf": safe_get(row, "confidence", "medium"), "created": parse_dt(safe_get(row, "created_at")),
                    })
                await pg.execute(text("SELECT setval('ai_generated_foods_id_seq', (SELECT MAX(id) FROM ai_generated_foods))"))
            print(f"  ✅ ai_generated_foods taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ ai_generated_foods HATA: {e}")
            _failed += 1

        # ── scrape_metadata ───────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM scrape_metadata")
            rows = cursor.fetchall()
            print(f"  scrape_metadata: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM scrape_metadata"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO scrape_metadata (id, last_scrape_at, food_count, status, error_message)
                        VALUES (:id, :last, :cnt, :status, :err)
                    """), {
                        "id": row["id"], "last": parse_dt(row["last_scrape_at"]),
                        "cnt": row["food_count"], "status": row["status"],
                        "err": safe_get(row, "error_message"),
                    })
                await pg.execute(text("SELECT setval('scrape_metadata_id_seq', (SELECT MAX(id) FROM scrape_metadata))"))
            print(f"  ✅ scrape_metadata taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ scrape_metadata HATA: {e}")
            _failed += 1

        # ── ai_coach_recommendations ──────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM ai_coach_recommendations")
            rows = cursor.fetchall()
            print(f"  ai_coach_recommendations: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM ai_coach_recommendations"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO ai_coach_recommendations (id, user_id, recommendation_type, workout_plan, calorie_balance, calorie_percentage, intensity_level, duration_minutes, motivation_message, user_feedback, feedback_reason, status, created_at, accepted_at, completed_at)
                        VALUES (:id, :uid, :rtype, :wplan, :cbal, :cpct, :ilevel, :dur, :msg, :ufb, :fbr, :status, :created, :accepted, :completed)
                    """), {
                        "id": row["id"], "uid": row["user_id"], "rtype": row["recommendation_type"],
                        "wplan": safe_json(row, "workout_plan"), "cbal": safe_get(row, "calorie_balance", 0.0),
                        "cpct": safe_get(row, "calorie_percentage", 0.0), "ilevel": safe_get(row, "intensity_level", "moderate"),
                        "dur": safe_get(row, "duration_minutes", 30), "msg": safe_get(row, "motivation_message", ""),
                        "ufb": safe_get(row, "user_feedback"), "fbr": safe_get(row, "feedback_reason"),
                        "status": safe_get(row, "status", "pending"), "created": parse_dt(safe_get(row, "created_at")),
                        "accepted": parse_dt(safe_get(row, "accepted_at")), "completed": parse_dt(safe_get(row, "completed_at")),
                    })
                await pg.execute(text("SELECT setval('ai_coach_recommendations_id_seq', (SELECT MAX(id) FROM ai_coach_recommendations))"))
            print(f"  ✅ ai_coach_recommendations taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ ai_coach_recommendations HATA: {e}")
            _failed += 1

        # ── ai_coach_progress ─────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM ai_coach_progress")
            rows = cursor.fetchall()
            print(f"  ai_coach_progress: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM ai_coach_progress"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO ai_coach_progress (id, user_id, week_start_date, week_end_date, workouts_completed, workouts_recommended, completion_rate, avg_workout_duration, intensity_distribution, progress_score, adaptation_needed, adaptation_reason, goals_achieved, created_at)
                        VALUES (:id, :uid, :wstart, :wend, :wcomp, :wrec, :crate, :avgdur, :idist, :pscore, :adapt, :areason, :goals, :created)
                    """), {
                        "id": row["id"], "uid": row["user_id"],
                        "wstart": parse_dt(row["week_start_date"]), "wend": parse_dt(row["week_end_date"]),
                        "wcomp": safe_get(row, "workouts_completed", 0), "wrec": safe_get(row, "workouts_recommended", 0),
                        "crate": safe_get(row, "completion_rate", 0.0), "avgdur": safe_get(row, "avg_workout_duration", 0.0),
                        "idist": safe_json(row, "intensity_distribution", {}), "pscore": safe_get(row, "progress_score", 0.0),
                        "adapt": safe_bool(row, "adaptation_needed"), "areason": safe_get(row, "adaptation_reason"),
                        "goals": safe_json(row, "goals_achieved", {}), "created": parse_dt(safe_get(row, "created_at")),
                    })
                await pg.execute(text("SELECT setval('ai_coach_progress_id_seq', (SELECT MAX(id) FROM ai_coach_progress))"))
            print(f"  ✅ ai_coach_progress taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ ai_coach_progress HATA: {e}")
            _failed += 1

        # ── ai_coach_preferences ──────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM ai_coach_preferences")
            rows = cursor.fetchall()
            print(f"  ai_coach_preferences: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM ai_coach_preferences"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO ai_coach_preferences (id, user_id, preferred_workout_types, preferred_duration_min, preferred_duration_max, preferred_intensity, avoided_exercises, health_conditions, learned_patterns, feedback_history, motivation_style, safety_level, updated_at)
                        VALUES (:id, :uid, :pwt, :pdmin, :pdmax, :pi, :ae, :hc, :lp, :fh, :ms, :sl, :updated)
                    """), {
                        "id": row["id"], "uid": row["user_id"],
                        "pwt": safe_json(row, "preferred_workout_types", []),
                        "pdmin": safe_get(row, "preferred_duration_min", 30), "pdmax": safe_get(row, "preferred_duration_max", 60),
                        "pi": safe_json(row, "preferred_intensity", {}), "ae": safe_json(row, "avoided_exercises", []),
                        "hc": safe_json(row, "health_conditions", []), "lp": safe_json(row, "learned_patterns", {}),
                        "fh": safe_json(row, "feedback_history", {}), "ms": safe_get(row, "motivation_style", "balanced"),
                        "sl": safe_get(row, "safety_level", "standard"), "updated": parse_dt(safe_get(row, "updated_at")),
                    })
                await pg.execute(text("SELECT setval('ai_coach_preferences_id_seq', (SELECT MAX(id) FROM ai_coach_preferences))"))
            print(f"  ✅ ai_coach_preferences taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ ai_coach_preferences HATA: {e}")
            _failed += 1

        # ── weight_validations ────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM weight_validations")
            rows = cursor.fetchall()
            print(f"  weight_validations: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM weight_validations"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO weight_validations (id, user_id, weight_kg, previous_weight_kg, change_kg, is_valid, validation_reason, validated_at)
                        VALUES (:id, :uid, :w, :pw, :chg, :valid, :reason, :validated)
                    """), {
                        "id": row["id"], "uid": row["user_id"], "w": row["weight_kg"],
                        "pw": safe_get(row, "previous_weight_kg"), "chg": safe_get(row, "change_kg", 0.0),
                        "valid": safe_bool(row, "is_valid", True), "reason": safe_get(row, "validation_reason"),
                        "validated": parse_dt(safe_get(row, "validated_at")),
                    })
                await pg.execute(text("SELECT setval('weight_validations_id_seq', (SELECT MAX(id) FROM weight_validations))"))
            print(f"  ✅ weight_validations taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ weight_validations HATA: {e}")
            _failed += 1

        # ── sport_profiles ────────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM sport_profiles")
            rows = cursor.fetchall()
            print(f"  sport_profiles: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM sport_profiles"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO sport_profiles (id, user_id, is_athlete, sport_type, training_frequency, training_intensity, rest_day_calories_adjustment, training_day_calories_adjustment, preferred_macro_split, created_at, updated_at)
                        VALUES (:id, :uid, :ath, :stype, :freq, :intensity, :rest_adj, :train_adj, :macros, :created, :updated)
                    """), {
                        "id": row["id"], "uid": row["user_id"], "ath": safe_bool(row, "is_athlete"),
                        "stype": safe_get(row, "sport_type"), "freq": safe_get(row, "training_frequency", 3),
                        "intensity": safe_get(row, "training_intensity", "moderate"),
                        "rest_adj": safe_get(row, "rest_day_calories_adjustment", 1.05),
                        "train_adj": safe_get(row, "training_day_calories_adjustment", 1.15),
                        "macros": safe_json(row, "preferred_macro_split", {}),
                        "created": parse_dt(safe_get(row, "created_at")), "updated": parse_dt(safe_get(row, "updated_at")),
                    })
                await pg.execute(text("SELECT setval('sport_profiles_id_seq', (SELECT MAX(id) FROM sport_profiles))"))
            print(f"  ✅ sport_profiles taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ sport_profiles HATA: {e}")
            _failed += 1

        # ── trend_analyses ────────────────────────────────────────────────
        try:
            cursor.execute("SELECT * FROM trend_analyses")
            rows = cursor.fetchall()
            print(f"  trend_analyses: {len(rows)} kayıt")
            if rows:
                await pg.execute(text("DELETE FROM trend_analyses"))
                for row in rows:
                    await pg.execute(text("""
                        INSERT INTO trend_analyses (id, user_id, analysis_type, period_start, period_end, data_json, created_at)
                        VALUES (:id, :uid, :atype, :pstart, :pend, :data, :created)
                    """), {
                        "id": row["id"], "uid": row["user_id"], "atype": row["analysis_type"],
                        "pstart": parse_dt(safe_get(row, "period_start")), "pend": parse_dt(safe_get(row, "period_end")),
                        "data": safe_json(row, "data_json", {}), "created": parse_dt(safe_get(row, "created_at")),
                    })
                await pg.execute(text("SELECT setval('trend_analyses_id_seq', (SELECT MAX(id) FROM trend_analyses))"))
            print(f"  ✅ trend_analyses taşındı")
            _success += 1
        except Exception as e:
            print(f"  ❌ trend_analyses HATA: {e}")
            _failed += 1

    conn.close()
    print(f"\n{'='*50}")
    print(f"🎉 Migration tamamlandı!")
    print(f"   ✅ Başarılı: {_success} tablo")
    if _failed > 0:
        print(f"   ❌ Başarısız: {_failed} tablo (yukarıdaki hata mesajlarını kontrol edin)")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(migrate())
