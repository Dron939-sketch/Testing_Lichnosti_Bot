"""
Обработчики для экрана результатов
ВЕРСИЯ С ПЕРСОНАЛИЗАЦИЕЙ:
✅ Удалены все лишние блоки
✅ Добавлена AI-генерация персонализированных профилей
✅ Исправлены импорты
✅ Сохранение ответов для AI
"""

import logging
import asyncio
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# Импорты констант
from constants import RESULTS
from config import GIFT_PDF_LINK, BOT_LINK, SHARE_TEXT, GIFT_SCREEN_TEXT, logger, API_URL

# Импорты утилит
from questions import STANDARD_SUFFIXES, SUFFIX_TO_DILTS, CONFLICT_PHRASES
from utils.calculations import calculate_profile_final
from utils.profile_utils import get_profile_fallback, get_discrepancy_note
from utils.text_utils import get_card_description_from_profile, format_profile_title

# ✅ Импорт из 19_7
from sexual_19_7 import get_disk_link_by_profile, update_invite_in_api, get_user_invites

# Импорт вариативных блоков
from profile_variants import PROFILE_VARIANTS

# Импорт загрузчика
from loader import loader

# Импорт AI-генератора
from ai_personalized import PersonalizedProfileGenerator

# Создаем глобальный экземпляр генератора
ai_generator = PersonalizedProfileGenerator()

class ProfileNotFoundError(Exception):
    """Исключение для случая, когда профиль не найден"""
    pass

# ============================================================================
# ФУНКЦИИ ДЛЯ ВАРИАТИВНЫХ БЛОКОВ
# ============================================================================

def add_profile_variants(profile_card: dict, profile_code: str, strategy_levels: dict):
    """Добавляет вариативные блоки в описание профиля"""
    
    if profile_code not in PROFILE_VARIANTS:
        return
    
    variants = PROFILE_VARIANTS[profile_code]
    
    # Добавляем варианты в зависимости от уровней стратегий
    if strategy_levels.get("ТФ", 0) > 4.0 and "high_tf" in variants:
        profile_card["trigger"] += f"\n\n{variants['high_tf']['trigger']}"
        profile_card["pain"] += f"\n\n{variants['high_tf']['pain']}"
    
    if strategy_levels.get("ЧВ", 0) > 4.0 and "high_chv" in variants:
        profile_card["trigger"] += f"\n\n{variants['high_chv']['trigger']}"
        profile_card["pain"] += f"\n\n{variants['high_chv']['pain']}"
    
    if strategy_levels.get("УБ", 0) > 4.0 and "high_ub" in variants:
        profile_card["trigger"] += f"\n\n{variants['high_ub']['trigger']}"
        profile_card["pain"] += f"\n\n{variants['high_ub']['pain']}"
    
    if strategy_levels.get("СБ", 0) < 3.0 and "low_sb" in variants:
        profile_card["trigger"] += f"\n\n{variants['low_sb']['trigger']}"
        profile_card["pain"] += f"\n\n{variants['low_sb']['pain']}"

async def show_results_screen(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    force_shared_view: bool = False
):
    """ЭКРАН РЕЗУЛЬТАТОВ с AI-персонализацией"""
    query = update.callback_query
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Пользователь"
    
    logger.info(f"📊 show_results_screen ВЫЗВАН для пользователя {user_id}")
    
    # ===== ВОССТАНАВЛИВАЕМ has_shared ИЗ БЕКАПА 18+ МОДУЛЯ =====
    sexual_backup = context.user_data.get("sexual_module_backup")
    if sexual_backup:
        if "has_shared" in sexual_backup:
            context.user_data["has_shared"] = sexual_backup["has_shared"]
            logger.info(f"🔄 Восстановлен has_shared={sexual_backup['has_shared']} из sexual_module_backup")
        
        # Восстанавливаем другие важные данные
        for key in ["profile_data", "profile", "scores", "stage1_current", 
                    "stage2_level_scores_dict", "stage3_level_scores", "stage4_dilts_answers",
                    "actual_profile_key", "profile_card"]:
            if key in sexual_backup:
                context.user_data[key] = sexual_backup[key]
        
        # Удаляем бекап
        context.user_data.pop("sexual_module_backup", None)
        logger.info("🧹 Удален sexual_module_backup")
    
    # ===== ПРОВЕРКА current_invite =====
    logger.info(f"🔍 ПРОВЕРКА current_invite: {context.user_data.get('current_invite')}")
    
    current_invite = context.user_data.get("current_invite")
    
    if not current_invite:
        try:
            session_response = requests.get(
                f"{API_URL}/api/user-session/get/{user_id}",
                timeout=5
            )
            if session_response.status_code == 200:
                session_data = session_response.json()
                if session_data.get('invite_data'):
                    current_invite = session_data['invite_data']
                    context.user_data["current_invite"] = current_invite
                    logger.info(f"🔄 Нашли сессию в БД для user_id={user_id}: {current_invite}")
        except Exception as e:
            logger.error(f"❌ Ошибка проверки сессии в БД: {e}")
    
    has_shared = context.user_data.get("has_shared", False) or force_shared_view
    profile_data = context.user_data.get("profile_data")
    
    if not profile_data:
        profile_data = calculate_profile_final(context.user_data)
        context.user_data["profile_data"] = profile_data
    
    # ===== ПОЛУЧАЕМ УРОВНИ СТРАТЕГИЙ =====
    strategy_levels = context.user_data.get("strategy_levels", {})
    behavioral_levels = context.user_data.get("behavioral_levels", {})
    dilts_counts = context.user_data.get("dilts_counts", {})
    dominant_dilts = context.user_data.get("dominant_dilts", "ENVIRONMENT")
    
    # Вычисляем средние для каждой стратегии
    final_strategy_levels = {}
    
    sb_values = strategy_levels.get("СБ", []) + behavioral_levels.get("СБ", [])
    final_strategy_levels["СБ"] = round(sum(sb_values) / len(sb_values), 1) if sb_values else 3.0
    
    tf_values = strategy_levels.get("ТФ", []) + behavioral_levels.get("ТФ", [])
    final_strategy_levels["ТФ"] = round(sum(tf_values) / len(tf_values), 1) if tf_values else 3.0
    
    ub_values = strategy_levels.get("УБ", []) + behavioral_levels.get("УБ", [])
    final_strategy_levels["УБ"] = round(sum(ub_values) / len(ub_values), 1) if ub_values else 3.0
    
    chv_values = strategy_levels.get("ЧВ", []) + behavioral_levels.get("ЧВ", [])
    final_strategy_levels["ЧВ"] = round(sum(chv_values) / len(chv_values), 1) if chv_values else 3.0
    
    logger.info(f"📊 ИТОГОВЫЕ УРОВНИ СТРАТЕГИЙ: {final_strategy_levels}")
    
    # ===== ОБРАБОТКА ПРИГЛАШЕНИЯ =====
    if current_invite:
        logger.info(f"🔍 Найдено активное приглашение: {current_invite}")
        
        friend_data = {
            "target_id": user_id,
            "target_name": update.effective_user.username or update.effective_user.first_name,
            "target_profile": profile_data.get('display_name', 'unknown')
        }
        
        try:
            success = update_invite_in_api(current_invite["invite_id"], friend_data)
            
            if success:
                logger.info(f"✅ Приглашение {current_invite['invite_id']} обновлено")
                
                try:
                    requests.post(
                        f"{API_URL}/api/user-session/clear/{user_id}",
                        timeout=5
                    )
                    logger.info(f"🧹 Сессия в БД очищена для user_id={user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка очистки сессии: {e}")
                
                context.user_data.pop("current_invite", None)
                
                buyer_id = current_invite.get("buyer_id")
                if buyer_id:
                    try:
                        username = update.effective_user.username or update.effective_user.first_name
                        profile_name = profile_data.get('display_name', 'неизвестно')
                        profile_link = get_disk_link_by_profile(profile_name)
                        
                        message_text = (
                            f"👤 <b>🪞 НОВОЕ ОТРАЖЕНИЕ!</b>\n\n"
                            f"✨ @{username} посмотрелся в зеркало!\n"
                            f"📊 <b>Профиль:</b> <code>{profile_name}</code>\n"
                            f"📁 <b>Материалы профиля:</b>\n"
                            f"{profile_link}"
                        )
                        
                        keyboard = [[
                            InlineKeyboardButton("👥 МОИ ОТРАЖЕНИЯ", callback_data="my_invites")
                        ]]
                        
                        await context.bot.send_message(
                            chat_id=buyer_id,
                            text=message_text,
                            parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                        logger.info(f"✅ Уведомление отправлено {buyer_id}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка отправки уведомления: {e}")
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении приглашения: {e}")
    
    # ===== ПОЛУЧАЕМ ОТВЕТЫ ПОЛЬЗОВАТЕЛЯ ДЛЯ AI =====
    user_answers = context.user_data.get('all_answers', [])
    profile_type = profile_data.get('display_name')  # например "IA_3_con"
    
    # ===== ГЕНЕРИРУЕМ ПЕРСОНАЛИЗИРОВАННЫЙ ПРОФИЛЬ =====
    personalized_profile = None
    try:
        if user_answers and profile_type:
            logger.info(f"🤖 Генерация персонализированного профиля для {profile_type}")
            personalized_profile = ai_generator.generate_personalized_profile(
                profile_type=profile_type,
                user_answers=user_answers,
                user_name=user_name
            )
    except Exception as e:
        logger.error(f"❌ Ошибка AI генерации: {e}")
        personalized_profile = None
    
    # ===== ЕСЛИ AI НЕ СРАБОТАЛ - ЗАГРУЖАЕМ ОБЫЧНЫЙ ПРОФИЛЬ =====
    if not personalized_profile:
        try:
            profile = get_profile_fallback(profile_data)
            profile_card = get_card_description_from_profile(profile, profile_data)
            context.user_data["profile_card"] = profile_card
            
            # Добавляем вариативные блоки
            profile_code = f"{profile_data.get('type_code', '')}_{profile_data.get('level', '')}_{profile_data.get('dilts_code', '')}"
            add_profile_variants(profile_card, profile_code, final_strategy_levels)
            
            # Формируем сообщение из профиля
            message = ""
            
            # Заголовок
            profile_header = profile_data.get('display_name', f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}")
            raw_title = profile_card.get('title', f"Профиль {profile_data['level']}")
            formatted_title = format_profile_title(raw_title, profile_header)
            message += f"<b>{formatted_title}</b>\n\n"
            
            # Архетип
            archetype = profile_card.get('archetype', '')
            if archetype:
                message += f"<i>{archetype}</i>\n\n"
            
            # Цитата
            quote = profile_card.get('quote', '')
            if quote:
                message += f"<b>💬 ЦИТАТА:</b>\n{quote}\n\n"
            
            # Триггер
            trigger = profile_card.get('trigger', '')
            if trigger:
                if trigger.startswith('🔍 ЭТО ТЫ, ЕСЛИ...'):
                    trigger = trigger.replace('🔍 ЭТО ТЫ, ЕСЛИ...\n\n', '').replace('🔍 ЭТО ТЫ, ЕСЛИ...', '')
                message += f"<b>🔍 ЭТО ВЫ, ЕСЛИ...</b>\n\n{trigger}\n\n"
            
            # Боль
            pain = profile_card.get('pain', '')
            if pain:
                pain_lines = pain.strip().split('\n')
                if pain_lines and any(h in pain_lines[0] for h in ['СУТЬ ПРОБЛЕМЫ:', 'СУТЬ ПРОБЛЕМЫ']):
                    pain = '\n'.join(pain_lines[1:]) if len(pain_lines) > 1 else ""
                if pain.strip():
                    message += f"<b>💔 СУТЬ ПРОБЛЕМЫ</b>\n\n{pain.strip()}\n\n"
            
            # Инструмент
            tool = profile_card.get('immediate_tool', '')
            if tool:
                message += f"<b>🛠 ПРАКТИЧЕСКИЙ ИНСТРУМЕНТ</b>\n\n{tool.strip()}\n\n"
            
            # Следующие шаги
            cta = profile_card.get('cta', '')
            if cta:
                message += f"<b>🚀 СЛЕДУЮЩИЕ ШАГИ</b>\n\n{cta.strip()}\n\n"
            
        except ProfileNotFoundError as e:
            error_text = (
                f"🧠 <b>К сожалению, возникла техническая ошибка</b>\n\n"
                f"Как ваш виртуальный психолог, я не смог обработать все данные.\n\n"
                f"Попробуйте пройти тест заново:\n"
                f"/start\n\n"
                f"<i>Приношу извинения за неудобства.</i>"
            )
            await query.edit_message_text(error_text, parse_mode="HTML")
            return ConversationHandler.END
    else:
        # Используем сгенерированный AI профиль
        message = personalized_profile
    
    # ===== СОХРАНЯЕМ ДЛЯ AI =====
    if "all_answers" not in context.user_data:
        context.user_data["all_answers"] = []
    
    context.user_data["all_answers"].append({
        'stage': 'results',
        'profile_code': profile_data.get('display_name'),
        'has_shared': has_shared,
        'used_ai': bool(personalized_profile),
        'timestamp': time.time()
    })
    
    # ===== ОТПРАВКА СООБЩЕНИЯ =====
    if message.strip():
        if len(message.strip()) > 4000:
            parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
            await query.edit_message_text(parts[0], parse_mode="HTML")
            for part in parts[1:]:
                await query.message.reply_text(part, parse_mode="HTML")
                await asyncio.sleep(0.5)
        else:
            await query.edit_message_text(message.strip(), parse_mode="HTML")
            await asyncio.sleep(0.5)
    
    # ===== ПРИМЕЧАНИЕ О КОНФЛИКТЕ =====
    message_2 = ""
    if hasattr(profile_data, 'actual_profile_key'):
        discrepancy_note = get_discrepancy_note(profile_data, profile_data.get('actual_profile_key'))
        if discrepancy_note:
            message_2 += f"\n{discrepancy_note}\n"
    
    # ===== КНОПКИ =====
    sexual_button = [InlineKeyboardButton("🔞 Мой интимный профиль", callback_data="show_my_sexual_profile")]
    
    coming_from_sexual = context.user_data.get("coming_from_sexual", False)
    logger.info(f"🚩 coming_from_sexual = {coming_from_sexual}")
    
    if not has_shared and not coming_from_sexual:
        keyboard = [
            [InlineKeyboardButton("🪞 Поделиться зеркалом", callback_data="get_gift")],
            [InlineKeyboardButton("📖 Полное описание профиля", callback_data="show_package")],
            sexual_button
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎁 Получить сказку «Мастер Меча»", url=GIFT_PDF_LINK)],
            [InlineKeyboardButton("📖 Полное описание профиля", callback_data="show_package")],
            sexual_button
        ]
        if coming_from_sexual:
            context.user_data.pop("coming_from_sexual", None)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if message_2:
        await query.message.reply_text(message_2.strip(), reply_markup=reply_markup, parse_mode="HTML")
    else:
        await query.message.reply_text("🧠 Что дальше?", reply_markup=reply_markup, parse_mode="HTML")
    
    logger.info(f"✅ Результаты показаны пользователю {user_id}")
    return RESULTS

async def back_to_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результатам"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"⬅️ back_to_results ВЫЗВАН для пользователя {user_id}")
    
    if "temp_has_shared" in context.user_data:
        context.user_data["has_shared"] = context.user_data.pop("temp_has_shared")
        logger.info(f"🔄 Восстановлен has_shared = {context.user_data['has_shared']}")
    
    await query.answer("🔄 Возвращаюсь к результатам...")
    await show_results_screen(update, context, force_shared_view=True)
    
    logger.info(f"🔄 User {user_id}: back_to_results → RESULTS = {RESULTS}")
    return RESULTS

async def back_to_results_after_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к результатам после подарка"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"⬅️ back_to_results_after_gift ВЫЗВАН для пользователя {user_id}")
    
    await query.answer("🔄 Возвращаюсь к результатам...")
    await show_results_screen(update, context, force_shared_view=True)
    
    logger.info(f"🎁 User {user_id}: back_to_results_after_gift → RESULTS = {RESULTS}")
    return RESULTS

async def skip_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропуск шаринга"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"⏩ skip_share ВЫЗВАН для пользователя {user_id}")
    
    await query.answer("⏩ Продолжаем без репоста")
    await show_results_screen(update, context, force_shared_view=True)
    
    logger.info(f"🔄 User {user_id}: skip_share → RESULTS = {RESULTS}")
    return RESULTS

async def confirm_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение шаринга"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"✅ confirm_share ВЫЗВАН для пользователя {user_id}")
    
    await query.answer("✅ Спасибо за репост! Ваш бонус готов!")
    context.user_data["has_shared"] = True
    
    logger.info(f"✅ User {user_id}: confirm_share → open_gift_screen")
    from handlers.gifts import open_gift_screen
    return await open_gift_screen(update, context)

async def restart_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапуск теста"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"🔄 restart_test ВЫЗВАН для пользователя {user_id}")
    
    await query.answer("🔄 Перезапускаю тест...")
    
    context.user_data.clear()
    
    context.user_data["scores"] = {"EXTERNAL": 0, "INTERNAL": 0, "SYMBOLIC": 0, "MATERIAL": 0}
    context.user_data["stage1_current"] = 0
    context.user_data["stage2_level_scores_dict"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0}
    context.user_data["stage3_level_scores"] = []
    context.user_data["stage4_dilts_answers"] = []
    context.user_data["processing"] = False
    context.user_data["has_shared"] = False
    
    context.user_data["sexual_invites"] = get_user_invites(user_id)
    
    logger.info(f"User {user_id} перезапустил тест")
    
    from handlers.stage1 import show_stage_1_intro
    return await show_stage_1_intro(update, context)

__all__ = [
    'show_results_screen',
    'back_to_results',
    'back_to_results_after_gift',
    'skip_share',
    'confirm_share',
    'restart_test'
]
