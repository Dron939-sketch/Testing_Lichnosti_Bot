"""
Обработчики для экрана результатов
"""

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# ИСПРАВЛЕНО: Импортируем константу из constants.py вместо config.py
from constants import RESULTS
from config import GIFT_PDF_LINK, BOT_LINK, SHARE_TEXT, GIFT_SCREEN_TEXT, logger
from questions import STANDARD_SUFFIXES, SUFFIX_TO_DILTS, CONFLICT_PHRASES
from utils.calculations import calculate_profile_final
from utils.profile_utils import get_profile_fallback, get_discrepancy_note
from utils.text_utils import get_card_description_from_profile, format_profile_title

# Импорт из 18+ модуля для ссылок
from sexual_18_plus import get_disk_link_by_profile

# Импорт вариативных блоков
from profile_variants import PROFILE_VARIANTS

# Импорт загрузчика и профилей
from loader import loader

class ProfileNotFoundError(Exception):
    """Исключение для случая, когда профиль не найден"""
    pass

# ============================================================================
# ФУНКЦИИ ДЛЯ ПОНЯТНОГО ОПИСАНИЯ
# ============================================================================

def get_strategy_full_name(strategy: str) -> str:
    """Возвращает полное название стратегии"""
    names = {
        "СБ": "⚔️ РЕАКЦИЯ НА УГРОЗУ",
        "ТФ": "💰 РЕАКЦИЯ НА РЕСУРС",
        "УБ": "❓ РЕАКЦИЯ НА НЕПОНЯТНОЕ",
        "ЧВ": "👥 РЕАКЦИЯ НА ДРУГИХ"
    }
    return names.get(strategy, strategy)

def get_evolutionary_context(strategy: str, level: float) -> str:
    """
    Возвращает эволюционный контекст — почему эта стратегия закрепилась
    """
    contexts = {
        "СБ": {
            "high": "Когда-то вы поняли: если не обозначить свои границы сразу — вас начнут использовать. Мир воспринимался как место, где сильные побеждают слабых, и вы выбрали быть сильным.",
            "medium": "Вы обнаружили, что иногда лучше проявить жёсткость, чем уступить. Это срабатывало достаточно часто, чтобы стать привычкой.",
            "low": "В детстве вы усвоили: если проявлять агрессию — станет только хуже. Безопаснее быть незаметным или уступить."
        },
        "ТФ": {
            "high": "Вы рано поняли: результаты приходят к тем, кто умеет организовывать и накапливать. Одиночка всегда проигрывает тому, у кого есть система.",
            "medium": "Труд всегда приносил вам результаты. Вы привыкли добиваться своего через усилия и обмен.",
            "low": "Когда-то вы поняли, что просить легче, чем добывать самому. Это работало — и закрепилось."
        },
        "УБ": {
            "high": "Мир всегда казался вам сложным и неочевидным. Вы научились искать скрытые связи, чтобы хоть как-то его упорядочить.",
            "medium": "Вы обнаружили, что понимание устройства вещей даёт преимущество. Знания стали вашим инструментом.",
            "low": "Сложные объяснения только запутывали вас. Вы привыкли доверять простым решениям и интуиции."
        },
        "ЧВ": {
            "high": "Вы рано поняли: одиночка не выживает. Только в связях с другими можно быть сильным и защищённым.",
            "medium": "Люди всегда были для вас источником возможностей. Вы научились находить общий язык и использовать знакомства.",
            "low": "Отношения приносили боль. Вы привыкли полагаться только на себя и держать дистанцию."
        }
    }
    
    if level >= 4.5:
        return contexts[strategy]["high"]
    elif level >= 3.0:
        return contexts[strategy]["medium"]
    else:
        return contexts[strategy]["low"]

def get_price_description(strategy: str, level: float) -> str:
    """
    Возвращает описание цены — что теряется при такой стратегии
    """
    prices = {
        "СБ": {
            "high": "Цена этого дара — вы редко позволяете себе расслабиться. Даже в безопасности вы сохраняете бдительность, словно готовясь к атаке. Спокойствие кажется подозрительным.",
            "medium": "Вы умеете постоять за себя, но иногда первая реакция — жёстче, чем ситуация требует. Люди могут считать вас излишне прямолинейным.",
            "low": "Ваша мягкость делает вас удобным для других, но свои интересы часто остаются на втором плане."
        },
        "ТФ": {
            "high": "Цена вашей организованности — вы редко позволяете себе просто плыть по течению. Даже в отпуске ищете, что можно улучшить, оптимизировать, запустить.",
            "medium": "Вы умеете работать, но иногда труд становится способом избежать других сфер жизни — отношений, отдыха, развития.",
            "low": "Привычка просить и искать лёгкие пути лишает вас самостоятельности. Вы зависите от щедрости других."
        },
        "УБ": {
            "high": "Цена вашего глубокого понимания — вы редко довольствуетесь простыми ответами. Даже там, где всё очевидно, вы ищете скрытые смыслы, усложняя себе жизнь.",
            "medium": "Ваш скептицизм защищает от ошибок, но иногда мешает довериться хорошему просто так, без гарантий.",
            "low": "Нежелание вникать в сложное делает вас уязвимым для манипуляций. Вы берёте готовые ответы, не проверяя их."
        },
        "ЧВ": {
            "high": "Цена ваших связей — искренняя близость иногда подменяется взаимовыгодным партнёрством. Трудно понять, кто с вами по расчёту, а кто по любви.",
            "medium": "Вы умеете нравиться, но за этим умением иногда теряется настоящая глубина. Вас знают многие, но знает ли кто-то по-настоящему?",
            "low": "Ваша закрытость защищает от разочарований, но оставляет в изоляции. Вам трудно просить о помощи, даже когда она нужна."
        }
    }
    
    if level >= 4.5:
        return prices[strategy]["high"]
    elif level >= 3.0:
        return prices[strategy]["medium"]
    else:
        return prices[strategy]["low"]

def get_blind_spot(strategy: str, level: float, all_levels: dict) -> str:
    """
    Возвращает описание слепого пятна — чего не видит человек
    """
    # Находим самую слабую стратегию
    weakest = min(all_levels.items(), key=lambda x: x[1])[0]
    
    blind_spots = {
        "СБ": "Ваша сила иногда мешает видеть другие способы взаимодействия — дипломатию, гибкость, умение ждать. Не всё решается напором.",
        "ТФ": "Ваша погружённость в процесс иногда закрывает общую картину. Вы можете так увлечься работой, что не заметите, куда движетесь.",
        "УБ": "Ваш анализ иногда парализует действие. Можно так долго искать истину, что пропустить момент, когда нужно просто делать.",
        "ЧВ": "Ваша ориентация на людей иногда делает вас зависимым от их мнения. Вы можете потерять себя в ожиданиях других."
    }
    
    return f"Ваше слепое пятно — {blind_spots[weakest]}"

def get_detailed_strategy_description(strategy: str, level: float, all_levels: dict) -> str:
    """
    Собирает полное описание стратегии: контекст + цена + слепое пятно
    """
    context = get_evolutionary_context(strategy, level)
    price = get_price_description(strategy, level)
    
    # Для доминирующей стратегии добавляем слепое пятно
    sorted_items = sorted(all_levels.items(), key=lambda x: x[1], reverse=True)
    if strategy == sorted_items[0][0]:  # если это доминанта
        blind = get_blind_spot(strategy, level, all_levels)
        return f"{context} {price} {blind}"
    else:
        return f"{context} {price}"

def get_quadrant_description(x: float, y: float, all_levels: dict) -> str:
    """
    Возвращает описание положения в системе координат
    """
    # Определяем доминирующие стратегии
    sorted_strategies = sorted(all_levels.items(), key=lambda x: x[1], reverse=True)
    main = sorted_strategies[0][0]
    second = sorted_strategies[1][0]
    
    # 🔥 ИСПРАВЛЕНО: определяем квадрант ТОЛЬКО если не в центре
    if x > 0 and y > 0:
        quadrant = "📚 МЫСЛИТЕЛЬНОМ"
        desc = "вы ищете закономерности, анализируете, строите теории. Мир для вас — это текст, который нужно расшифровать."
        strength = "видите то, что скрыто от других"
        weakness = "можете застрять в анализе, так и не начав действовать"
    elif x < 0 and y > 0:
        quadrant = "🔧 ТРУДОВОМ"
        desc = "вы создаёте порядок, накапливаете, организуете. Мир для вас — это материал, который нужно обработать."
        strength = "надёжны и практичны"
        weakness = "можете увязнуть в рутине, боясь нового"
    elif x < 0 and y < 0:
        quadrant = "⚔️ СИЛОВОМ"
        desc = "вы действуете, защищаете, контролируете. Мир для вас — это поле, где нужно отстаивать своё место."
        strength = "решительны и прямолинейны"
        weakness = "можете быть излишне агрессивны, не доверяя другим"
    elif x > 0 and y < 0:
        quadrant = "🤝 СОЦИАЛЬНОМ"
        desc = "вы общаетесь, влияете, строите связи. Мир для вас — это сеть, где важно быть на связи."
        strength = "гибки и общительны"
        weakness = "можете зависеть от чужого мнения, теряя себя"
    else:
        # 🔥 СЛУЧАЙ ЦЕНТРА (0,0)
        return (f"<b>Вы находитесь в ЦЕНТРЕ системы координат</b> — точке равновесия.\n\n"
                f"Это значит, что у вас нет ярко выраженного перекоса ни в одну из сторон. "
                f"Ваши стратегии сбалансированы, вы можете быть гибким и адаптироваться к разным ситуациям.\n\n"
                f"• Ваша ведущая стратегия — {main}\n"
                f"• Вторая по значимости — {second}\n\n"
                f"Такое положение даёт вам уникальную способность — выбирать способ реакции в зависимости от контекста, "
                f"не будучи заложником одной доминирующей стратегии.")
    
    # Определяем расстояние от центра
    distance = (x**2 + y**2)**0.5
    
    if distance < 1.0:
        position_desc = f"Вы близки к центру, с небольшим уклоном в {quadrant} квадрант."
    elif abs(x) > abs(y):
        direction = "выше" if x > 0 else "ниже"
        position_desc = f"Ось ограничений у вас развита {direction} среднего (отклонение {abs(x):.1f})."
    else:
        direction = "выше" if y > 0 else "ниже"
        position_desc = f"Ось воображения у вас развита {direction} среднего (отклонение {abs(y):.1f})."
    
    return (f"<b>Вы находитесь в {quadrant} квадранте</b> — {desc}\n"
            f"• Ваша сила: {strength}\n"
            f"• Зона роста: {weakness}\n"
            f"• {position_desc}\n"
            f"• Ведущая стратегия — {main}, вторая по значимости — {second}.")

def get_profile_summary(profile_data: dict, strategy_levels: dict) -> str:
    """Возвращает краткое описание профиля (2-3 предложения)"""
    
    type_code = profile_data.get('type_code', 'IP')
    
    # Маппинг кодов на названия
    type_names = {
        "SP": "Силовик-Беспредельщик",
        "IP": "Трудяга-Фермер",
        "IA": "Умный-Бедный",
        "SA": "Человек Возможностей"
    }
    
    # Маппинг типа профиля на доминирующую стратегию
    type_to_strategy = {
        "SP": "СБ",
        "IP": "ТФ",
        "IA": "УБ",
        "SA": "ЧВ"
    }
    
    # Определяем ведущую стратегию из типа профиля
    dominant_strategy = type_to_strategy.get(type_code, "ЧВ")
    dom_level = strategy_levels.get(dominant_strategy, 3.0)
    
    # Краткие описания по типам
    summaries = {
        "SP": "Вы строите свою жизнь через действие и готовность защищаться. Для вас важна возможность постоять за себя и своих близких.",
        "IP": "Ваша опора — труд и порядок. Вы надёжны, практичны, цените стабильность и результат, который можно пощупать руками.",
        "IA": "Ваш мир — это мысли и смыслы. Вы ищете понимание там, где другие видят хаос, и способны видеть глубже поверхности.",
        "SA": "Вы живёте в мире людей и связей. Вы общительны, гибки, умеете находить общий язык и влиять на других."
    }
    
    base = summaries.get(type_code, "У вас уникальное сочетание стратегий.")
    
    # Добавляем контекст из эволюционной психологии
    context = get_evolutionary_context(dominant_strategy, dom_level)
    
    return f"{base} {context}"

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
    """ЭКРАН РЕЗУЛЬТАТОВ с 18+ кнопкой и сохранением приглашений"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    logger.info(f"📊 show_results_screen ВЫЗВАН для пользователя {user_id}")
    
    # ===== 👇 ВОССТАНАВЛИВАЕМ has_shared ИЗ БЕКАПА 18+ МОДУЛЯ =====
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
        
        # Удаляем бекап после восстановления
        context.user_data.pop("sexual_module_backup", None)
        logger.info("🧹 Удален sexual_module_backup после восстановления")
    # ===== 👆 КОНЕЦ БЛОКА =====
    
    # ===== 👇 НОВЫЙ БЛОК: ПРОВЕРКА current_invite и БД =====
    logger.info(f"🔍 ПРОВЕРКА current_invite В НАЧАЛЕ: {context.user_data.get('current_invite')}")
    
    # Сначала проверяем в памяти
    current_invite = context.user_data.get("current_invite")
    
    # Если нет в памяти - проверяем в БД
    if not current_invite:
        try:
            import requests
            from config import API_URL
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
    # ===== 👆 КОНЕЦ НОВОГО БЛОКА =====
    
    has_shared = context.user_data.get("has_shared", False) or force_shared_view
    profile_data = context.user_data.get("profile_data")
    
    if not profile_data:
        profile_data = calculate_profile_final(context.user_data)
        context.user_data["profile_data"] = profile_data
    
    # ===== 👇 НОВЫЙ БЛОК: ПОЛУЧАЕМ УРОВНИ ВСЕХ СТРАТЕГИЙ =====
    # Из stage2
    strategy_levels = context.user_data.get("strategy_levels", {})
    
    # Из stage3
    behavioral_levels = context.user_data.get("behavioral_levels", {})
    
    # Из stage4
    dilts_counts = context.user_data.get("dilts_counts", {})
    dominant_dilts = context.user_data.get("dominant_dilts", "ENVIRONMENT")
    
    # Вычисляем средние для каждой стратегии
    final_strategy_levels = {}
    
    # СБ: из stage2 + stage3
    sb_values = strategy_levels.get("СБ", []) + behavioral_levels.get("СБ", [])
    final_strategy_levels["СБ"] = round(sum(sb_values) / len(sb_values), 1) if sb_values else 3.0
    
    # ТФ: из stage2 + stage3
    tf_values = strategy_levels.get("ТФ", []) + behavioral_levels.get("ТФ", [])
    final_strategy_levels["ТФ"] = round(sum(tf_values) / len(tf_values), 1) if tf_values else 3.0
    
    # УБ: из stage2 + stage3
    ub_values = strategy_levels.get("УБ", []) + behavioral_levels.get("УБ", [])
    final_strategy_levels["УБ"] = round(sum(ub_values) / len(ub_values), 1) if ub_values else 3.0
    
    # ЧВ: из stage2 + stage3
    chv_values = strategy_levels.get("ЧВ", []) + behavioral_levels.get("ЧВ", [])
    final_strategy_levels["ЧВ"] = round(sum(chv_values) / len(chv_values), 1) if chv_values else 3.0
    
    logger.info(f"📊 ИТОГОВЫЕ УРОВНИ СТРАТЕГИЙ: {final_strategy_levels}")
    # ===== 👆 КОНЕЦ НОВОГО БЛОКА =====
    
    # ===== 👇 НОВЫЙ БЛОК: ОБРАБОТКА ПРИГЛАШЕНИЯ =====
    if current_invite:
        logger.info(f"🔍 Найдено активное приглашение: {current_invite}")
        
        friend_data = {
            "target_id": user_id,
            "target_name": update.effective_user.username or update.effective_user.first_name,
            "target_profile": profile_data.get('display_name', 'unknown')
        }
        
        try:
            # Импортируем здесь, чтобы избежать циклических импортов
            from sexual_19_7 import update_invite_in_api, get_disk_link_by_profile
            
            success = update_invite_in_api(current_invite["invite_id"], friend_data)
            
            if success:
                logger.info(f"✅ Приглашение {current_invite['invite_id']} обновлено")
                
                # Очищаем сессию в БД
                try:
                    import requests
                    from config import API_URL
                    requests.post(
                        f"{API_URL}/api/user-session/clear/{user_id}",
                        timeout=5
                    )
                    logger.info(f"🧹 Сессия в БД очищена для user_id={user_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка очистки сессии: {e}")
                
                # Очищаем из памяти
                context.user_data.pop("current_invite", None)
                
                # Отправляем уведомление создателю
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
    # ===== 👆 КОНЕЦ НОВОГО БЛОКА =====
    
    try:
        profile = get_profile_fallback(profile_data)
    except ProfileNotFoundError as e:
        error_text = (
            f"🧠 <b>К сожалению, возникла техническая ошибка</b>\n\n"
            f"Как ваш виртуальный психолог, я не смог обработать все данные.\n\n"
            f"Попробуйте пройти тест заново, чтобы я мог помочь вам лучше:\n"
            f"/start\n\n"
            f"<i>Приношу извинения за неудобства.</i>"
        )
        await query.edit_message_text(error_text, parse_mode="HTML")
        return ConversationHandler.END
    
    profile_card = get_card_description_from_profile(profile, profile_data)
    context.user_data["profile_card"] = profile_card
    
    # 🔥 ДОБАВЛЯЕМ ВАРИАТИВНЫЕ БЛОКИ
    profile_code = f"{profile_data.get('type_code', '')}_{profile_data.get('level', '')}_{profile_data.get('dilts_code', '')}"
    add_profile_variants(profile_card, profile_code, final_strategy_levels)
    
    actual_profile_key = None
    try:
        if hasattr(profile, 'key'):
            actual_profile_key = profile.key.lower()
            logger.info(f"🔍 Найден ключ профиля: {actual_profile_key}")
            context.user_data["actual_profile_key"] = actual_profile_key
        elif hasattr(profile, 'profile_name'):
            actual_profile_key = profile.profile_name.lower()
            context.user_data["actual_profile_key"] = actual_profile_key
        else:
            actual_profile_key = f"{profile_card.get('type_code', 'sa')}_{profile_card.get('level', 1)}_{profile_card.get('dilts_code', 'def')}".lower()
            context.user_data["actual_profile_key"] = actual_profile_key
        
        parts = actual_profile_key.split('_')
        if len(parts) >= 3:
            profile_data['type_code'] = parts[0].upper()
            profile_data['level'] = int(parts[1])
            profile_data['dilts_code'] = parts[2].lower()
            profile_data['display_name'] = actual_profile_key.upper()
            context.user_data["profile_data"] = profile_data
            logger.info(f"✅ Обновлен profile_data реальным профилем: {profile_data['display_name']}")
            
    except Exception as e:
        logger.error(f"⚠️ Ошибка определения реального профиля: {e}")
    
    # ПРИМЕЧАНИЕ О КОНФЛИКТЕ
    discrepancy_note = ""
    if actual_profile_key:
        discrepancy_note = get_discrepancy_note(profile_data, actual_profile_key)
        logger.info(f"📝 Примечание о конфликте: {'✅ Есть' if discrepancy_note else '❌ Нет'}")
    
    # ===== ФОРМИРУЕМ ПЕРВОЕ СООБЩЕНИЕ =====
    message_1 = (
        f"🧠 <b>ВАШ ПРОФИЛЬ</b>\n\n"
        f"<i>Как ваш виртуальный психолог, я проанализировал ваши ответы.</i>\n\n"
    )
    
    # Краткое описание
    profile_summary = get_profile_summary(profile_data, final_strategy_levels)
    message_1 += f"{profile_summary}\n\n"
    
    # ===== НОВЫЙ БЛОК СТРАТЕГИЙ С ЭВОЛЮЦИОННЫМ КОНТЕКСТОМ =====
    message_1 += f"📊 <b>ВАШ УНИКАЛЬНЫЙ КОКТЕЙЛЬ РЕАКЦИЙ</b>\n\n"
    message_1 += f"У вас есть 4 базовых способа реагировать на мир. Каждый когда-то помог вам выжить — и теперь стал частью вашего характера:\n\n"
    
    # Сортируем стратегии по убыванию
    sorted_strategies = sorted(final_strategy_levels.items(), key=lambda x: x[1], reverse=True)
    
    for strategy, level in sorted_strategies:
        full_name = get_strategy_full_name(strategy)
        description = get_detailed_strategy_description(strategy, level, final_strategy_levels)
        message_1 += f"<b>{full_name} — {level}/6</b>\n"
        message_1 += f"{description}\n\n"
    
    # ===== БЛОК КООРДИНАТ =====
    # Рассчитываем координаты
    x = final_strategy_levels.get("УБ", 3) - final_strategy_levels.get("ТФ", 3)
    y = final_strategy_levels.get("УБ", 3) - final_strategy_levels.get("ЧВ", 3)
    
    x = max(-6, min(6, x * 1.2))
    y = max(-6, min(6, y * 1.2))
    
    message_1 += f"\n📍 <b>ГДЕ ВЫ СЕЙЧАС</b>\n\n"
    message_1 += f"Представьте карту с двумя осями:\n"
    message_1 += f"• 🧠 <b>Воображение</b> — способность придумывать, видеть варианты\n"
    message_1 += f"• ⛓️ <b>Ограничения</b> — внутренние правила, страхи, мораль\n\n"
    message_1 += f"<b>Ваши координаты:</b>\n"
    message_1 += f"• Воображение: {y:+.1f} (от -6 до +6)\n"
    message_1 += f"• Ограничения: {x:+.1f} (от -6 до +6)\n\n"
    
    # Описание квадранта
    message_1 += get_quadrant_description(x, y, final_strategy_levels)
    message_1 += "\n\n"
    
    # БЛОК ТОЧКИ НАПРЯЖЕНИЯ
    dilts_names = {
        "ENVIRONMENT": "🌍 <b>Окружение</b> — проблема во внешних условиях, месте, людях",
        "BEHAVIOR": "👣 <b>Поведение</b> — проблема в действиях, в том, что вы делаете",
        "CAPABILITIES": "🛠️ <b>Способности</b> — не хватает навыков, умений, компетенций",
        "VALUES": "💎 <b>Ценности</b> — конфликт мотивов, непонимание, чего вы на самом деле хотите",
        "IDENTITY": "🧬 <b>Идентичность</b> — вы не знаете, кто вы, потеряли себя"
    }
    
    message_1 += f"\n🎯 <b>ТОЧКА НАПРЯЖЕНИЯ</b>\n"
    message_1 += f"{dilts_names.get(dominant_dilts, '🌍 Окружение')}\n\n"
    
    # ЗАГОЛОВОК ПРОФИЛЯ
    profile_header = profile_data.get('display_name', f"{profile_data['type_code']}_{profile_data['level']}_{profile_data['dilts_code']}")
    raw_title = profile_card.get('title', f"Профиль {profile_data['level']}")
    formatted_title = format_profile_title(raw_title, profile_header)
    message_1 += f"<b>{formatted_title}</b>\n\n"
    
    # ОСТАЛЬНОЕ ОПИСАНИЕ ИЗ ПРОФИЛЯ
    archetype = profile_card.get('archetype', '')
    if archetype:
        message_1 += f"<i>{archetype}</i>\n\n"
    
    quote = profile_card.get('quote', '')
    if quote:
        message_1 += f"<b>💬 ЦИТАТА:</b>\n{quote}\n\n"
    
    trigger = profile_card.get('trigger', '')
    if trigger:
        message_1 += f"<b>🔍 ЭТО ВЫ, ЕСЛИ...</b>\n\n{trigger}\n\n"
    
    pain = profile_card.get('pain', '')
    if pain:
        message_1 += f"<b>💔 СУТЬ ПРОБЛЕМЫ</b>\n\n{pain.strip()}\n\n"

    if message_1.strip():
        # Проверяем длину сообщения (лимит Telegram 4096 символов)
        if len(message_1.strip()) > 4000:
            # Разбиваем на части
            parts = [message_1[i:i+4000] for i in range(0, len(message_1), 4000)]
            
            # Редактируем первое сообщение
            await query.edit_message_text(parts[0], parse_mode="HTML")
            
            # Отправляем остальные как новые сообщения
            for part in parts[1:]:
                await query.message.reply_text(part, parse_mode="HTML")
                await asyncio.sleep(0.5)
        else:
            await query.edit_message_text(message_1.strip(), parse_mode="HTML")
            await asyncio.sleep(0.5)
    
    # ===== ВТОРОЕ СООБЩЕНИЕ С ИНСТРУМЕНТАМИ =====
    message_2 = ""
    
    tool = profile_card.get('immediate_tool', '')
    if tool:
        message_2 += f"<b>🛠 ПРАКТИЧЕСКИЙ ИНСТРУМЕНТ</b>\n\n"
        message_2 += f"{tool.strip()}\n\n"
    
    cta = profile_card.get('cta', '')
    if cta:
        message_2 += f"<b>🚀 СЛЕДУЮЩИЕ ШАГИ</b>\n\n"
        message_2 += f"{cta.strip()}\n\n"
    
    message_2 += (
        f"🧠 <b>ЧТО ДАЛЬШЕ В НАШЕМ ПУТЕШЕСТВИИ?</b>\n\n"
        f"<i>Это только начало вашего пути к самопознанию.</i>\n\n"
    )
    
    # ПРИМЕЧАНИЕ В КОНЦЕ
    if discrepancy_note:
        message_2 += f"\n{discrepancy_note}\n"
    
    # КНОПКА 18+ ПРОФИЛЯ
    sexual_button = [InlineKeyboardButton("🔞 Мой интимный профиль", callback_data="show_my_sexual_profile")]
    
    # Проверяем флаг возврата из 18+
    coming_from_sexual = context.user_data.get("coming_from_sexual", False)
    logger.info(f"🚩 coming_from_sexual = {coming_from_sexual}")
    
    # ЛОГИКА КНОПОК
    if not has_shared and not coming_from_sexual:
        # Случай 1: первый вход после теста (нет репоста, не из 18+)
        keyboard = [
            [InlineKeyboardButton("🪞 Поделиться зеркалом", callback_data="get_gift")],
            [InlineKeyboardButton("📖 Полное описание профиля", callback_data="show_package")],
            sexual_button
        ]
        logger.info(f"🔘 Клавиатура: без подарка (has_shared={has_shared}, coming={coming_from_sexual})")
    else:
        # Случай 2: ВСЕ ОСТАЛЬНЫЕ СИТУАЦИИ!
        keyboard = [
            [InlineKeyboardButton("🎁 Получить сказку «Мастер Меча»", url=GIFT_PDF_LINK)],
            [InlineKeyboardButton("📖 Полное описание профиля", callback_data="show_package")],
            sexual_button
        ]
        logger.info(f"🔘 Клавиатура: СРАЗУ ССЫЛКА НА ПОДАРОК! (has_shared={has_shared}, coming={coming_from_sexual})")
        
        if coming_from_sexual:
            context.user_data.pop("coming_from_sexual", None)
            logger.info("🚩 Сброшен флаг coming_from_sexual")
    
    # ОТПРАВКА ВТОРОГО СООБЩЕНИЯ
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    logger.debug(f"📤 Отправка message_2 ({len(message_2)} символов) с {len(keyboard)} рядами кнопок")
    await query.message.reply_text(message_2.strip(), reply_markup=reply_markup, parse_mode="HTML")
    
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
    
    from sexual_18_plus import get_user_invites
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
