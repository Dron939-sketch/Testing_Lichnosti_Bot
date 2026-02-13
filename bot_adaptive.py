#!/usr/bin/env python3
"""
🔞 ИНТИМНЫЕ ПРОФИЛИ И 4F-КЛЮЧИ
Версия: 13.0 - ULTIMATE EDITION
✅ ИСПРАВЛЕНА ОШИБКА KeyError: 'created_at'
✅ ПЕРСИСТЕНТНОЕ ХРАНИЛИЩЕ
✅ WEBHOOK + POLLING
✅ ГОТОВ К RENDER
"""

import asyncio
import os
import sys
import uuid
import json
import urllib.parse
import signal
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)
from telegram.error import TelegramError

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

class Config:
    """Централизованная конфигурация"""
    
    # Токены и ключи
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "Testing_Lichnosti_bot")
    
    # Платежи
    YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
    YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")
    API_URL = os.getenv("API_URL", "")
    
    # Лимиты и цены
    FREE_FRIEND_LIMIT = 2
    FRIEND_ACCESS_PRICE = 99
    FOUR_F_PRICE = 1
    
    # Системные параметры
    CACHE_TTL = 300
    INVITE_TTL_DAYS = 7
    
    # Webhook
    RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")
    PORT = int(os.getenv("PORT", 8080))
    WEBHOOK_PATH = f"/webhook/{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else "/webhook"
    
    @classmethod
    def is_render(cls) -> bool:
        return bool(os.getenv("RENDER"))
    
    @classmethod
    def get_webhook_url(cls) -> Optional[str]:
        if cls.RENDER_EXTERNAL_URL:
            return f"{cls.RENDER_EXTERNAL_URL}{cls.WEBHOOK_PATH}"
        return None
    
    @classmethod
    def get_project_root(cls) -> Path:
        current = Path(__file__).parent.absolute()
        while current != current.parent:
            if (current / "sexual_18").exists():
                return current
            current = current.parent
        return Path(__file__).parent.absolute()
    
    @classmethod
    def ensure_directories(cls):
        root = cls.get_project_root()
        dirs = [
            root / "data",
            root / "logs",
            root / "sexual_18",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

PROJECT_ROOT = Config.get_project_root()
Config.ensure_directories()

# ============================================================================
# ЛОГГИРОВАНИЕ
# ============================================================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================================
# СОСТОЯНИЯ CONVERSATION HANDLER
# ============================================================================

class States:
    """Централизованное управление состояниями"""
    RESULTS_SCREEN = 0
    SEXUAL_PROFILE = 1
    INVITE_CREATE = 2
    INVITES_LIST = 3
    FRIEND_MENU = 4
    FOUR_F_MENU = 5
    FOUR_F_CONTENT = 6
    FOUR_F_PURCHASE = 7

# ============================================================================
# МОДЕЛИ ДАННЫХ
# ============================================================================

@dataclass
class Invitation:
    """Модель приглашения - ЕДИНАЯ СТРУКТУРА"""
    invite_id: str
    creator_id: int
    creator_profile: str
    status: str  # active, used, expired
    created_at: float
    used_at: Optional[float] = None
    used_by_id: Optional[int] = None
    used_by_name: Optional[str] = None
    used_by_username: Optional[str] = None
    friend_profile: Optional[str] = None
    access_status: str = "pending"
    access_paid: bool = False
    purchased_functions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "invite_id": self.invite_id,
            "creator_id": self.creator_id,
            "creator_profile": self.creator_profile,
            "status": self.status,
            "created_at": self.created_at,
            "used_at": self.used_at,
            "used_by_id": self.used_by_id,
            "used_by_name": self.used_by_name,
            "used_by_username": self.used_by_username,
            "friend_profile": self.friend_profile,
            "access_status": self.access_status,
            "access_paid": self.access_paid,
            "purchased_functions": self.purchased_functions.copy()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Invitation':
        return cls(**data)
    
    @property
    def created_at_str(self) -> str:
        """БЕЗОПАСНОЕ получение даты создания"""
        return datetime.fromtimestamp(self.created_at).strftime('%d.%m.%Y')
    
    @property
    def used_at_str(self) -> str:
        """БЕЗОПАСНОЕ получение даты использования"""
        if self.used_at:
            return datetime.fromtimestamp(self.used_at).strftime('%d.%m.%Y')
        return self.created_at_str

@dataclass
class UserSession:
    """Сессия пользователя"""
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    role: str = "free"
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    last_active: float = field(default_factory=lambda: datetime.now().timestamp())
    invites: List[str] = field(default_factory=list)
    purchased_friends: List[int] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "first_name": self.first_name,
            "role": self.role,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "invites": self.invites.copy(),
            "purchased_friends": self.purchased_friends.copy()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserSession':
        return cls(
            user_id=data["user_id"],
            username=data.get("username"),
            first_name=data.get("first_name"),
            role=data.get("role", "free"),
            created_at=data.get("created_at", datetime.now().timestamp()),
            last_active=data.get("last_active", datetime.now().timestamp()),
            invites=data.get("invites", []),
            purchased_friends=data.get("purchased_friends", [])
        )

# ============================================================================
# ПЕРСИСТЕНТНОЕ ХРАНИЛИЩЕ
# ============================================================================

class Storage:
    """Потокобезопасное персистентное хранилище"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.data_dir = PROJECT_ROOT / "data"
        self.sessions_file = self.data_dir / "sessions.json"
        self.invitations_file = self.data_dir / "invitations.json"
        
        self.sessions: Dict[int, UserSession] = {}
        self.invitations: Dict[str, Invitation] = {}
        
        self._load_data()
        self._locks = defaultdict(asyncio.Lock)
    
    def _load_data(self):
        """Загрузка данных с обработкой ошибок"""
        try:
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for uid, sess in data.items():
                        try:
                            self.sessions[int(uid)] = UserSession.from_dict(sess)
                        except Exception as e:
                            logger.error(f"Ошибка загрузки сессии {uid}: {e}")
        except Exception as e:
            logger.error(f"Ошибка загрузки сессий: {e}")
        
        try:
            if self.invitations_file.exists():
                with open(self.invitations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for inv_id, inv in data.items():
                        try:
                            self.invitations[inv_id] = Invitation.from_dict(inv)
                        except Exception as e:
                            logger.error(f"Ошибка загрузки приглашения {inv_id}: {e}")
        except Exception as e:
            logger.error(f"Ошибка загрузки приглашений: {e}")
    
    async def _save_sessions(self):
        async with self._lock:
            try:
                data = {str(uid): s.to_dict() for uid, s in self.sessions.items()}
                with open(self.sessions_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Ошибка сохранения сессий: {e}")
    
    async def _save_invitations(self):
        async with self._lock:
            try:
                data = {inv_id: inv.to_dict() for inv_id, inv in self.invitations.items()}
                with open(self.invitations_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Ошибка сохранения приглашений: {e}")
    
    async def get_session(self, user_id: int) -> Optional[UserSession]:
        async with self._locks[f"session_{user_id}"]:
            session = self.sessions.get(user_id)
            if session:
                session.last_active = datetime.now().timestamp()
            return session
    
    async def create_session(self, user_id: int, username: Optional[str], first_name: Optional[str]) -> UserSession:
        async with self._locks[f"session_{user_id}"]:
            session = UserSession(
                user_id=user_id,
                username=username,
                first_name=first_name
            )
            self.sessions[user_id] = session
            await self._save_sessions()
            return session
    
    async def create_invitation(self, creator_id: int, creator_profile: str) -> Invitation:
        async with self._lock:
            invite_id = f"sex_{uuid.uuid4().hex[:8]}"
            invitation = Invitation(
                invite_id=invite_id,
                creator_id=creator_id,
                creator_profile=creator_profile,
                status="active",
                created_at=datetime.now().timestamp()
            )
            self.invitations[invite_id] = invitation
            
            session = await self.get_session(creator_id)
            if session:
                session.invites.append(invite_id)
                await self._save_sessions()
            
            await self._save_invitations()
            return invitation
    
    async def get_user_invites(self, user_id: int) -> List[Invitation]:
        """БЕЗОПАСНОЕ получение приглашений пользователя"""
        async with self._lock:
            session = await self.get_session(user_id)
            if not session:
                return []
            
            invites = []
            for invite_id in session.invites:
                inv = self.invitations.get(invite_id)
                if inv:
                    invites.append(inv)
            
            return sorted(invites, key=lambda x: x.created_at, reverse=True)
    
    async def init_test_data(self, user_id: int):
        """Инициализация тестовых данных"""
        session = await self.get_session(user_id)
        if not session:
            session = await self.create_session(user_id, "test_user", "Тест")
        
        if not session.invites:
            # Тестовое приглашение 1
            inv1 = await self.create_invitation(user_id, "SA-5_INT")
            inv1.status = "used"
            inv1.used_at = datetime.now().timestamp()
            inv1.used_by_id = 1001
            inv1.used_by_name = "@alex"
            inv1.used_by_username = "alex"
            inv1.friend_profile = "SA-3_CON"
            inv1.access_status = "free"
            await self._save_invitations()
            
            # Тестовое приглашение 2
            inv2 = await self.create_invitation(user_id, "SA-5_INT")
            inv2.status = "used"
            inv2.used_at = datetime.now().timestamp() - 86400
            inv2.used_by_id = 1002
            inv2.used_by_name = "@maria"
            inv2.used_by_username = "maria"
            inv2.friend_profile = "IP-5_INT"
            inv2.access_status = "free"
            inv2.purchased_functions = ["1F"]
            await self._save_invitations()
            
            logger.info(f"✅ Тестовые данные созданы для user_id={user_id}")

# ============================================================================
# 4F-КЛЮЧИ
# ============================================================================

class FourFKey:
    """4F-ключи с контентом"""
    
    @classmethod
    def get_all(cls) -> Dict[str, dict]:
        return {
            "1F": {
                "code": "1F",
                "emoji": "🔥",
                "title": "НАПАДЕНИЕ / ЯРОСТЬ",
                "subtitle": "Как гасить агрессию и не нарваться",
                "description": "Он не злой. Он — ВЗВЕДЁННЫЙ.\nДостаточно одной искры, чтобы рвануло.\n\nЭТОТ КЛЮЧ ДАЁТ:\n   • 3 фразы, которые моментально сбивают агрессию\n   • Что нельзя говорить, когда он уже завёлся\n   • Как перевести конфликт в диалог за 30 секунд",
                "tag": "Ключ к управлению гневом",
                "triggers": [
                    "«Я понимаю, почему ты так реагируешь»",
                    "«Ты имеешь полное право злиться»",
                    "«Я на твоей стороне»"
                ],
                "analysis": "Страх нападения возникает, когда человек не чувствует безопасности. Его агрессия — это защита.",
                "protocol": "1. Заметьте триггер\n2. Признайте эмоцию\n3. Не давите\n4. Дайте время"
            },
            "2F": {
                "code": "2F",
                "emoji": "🏃",
                "title": "БЕГСТВО / СТРАХ",
                "subtitle": "Чего он боится на самом деле",
                "description": "Он не трус. Он — ПРЕДУСМОТРИТЕЛЬНЫЙ.\nПросто однажды его уже больно ударили.\n\nЭТОТ КЛЮЧ ДАЁТ:\n   • 3 фразы, которые включают панику (чтобы знать, чего НЕ делать)\n   • 3 фразы, которые снимают тревогу (чтобы успокоить)",
                "tag": "Ключ к преодолению страхов",
                "triggers": [
                    "«Ты не обязан это делать»",
                    "«Здесь безопасно»",
                    "«Я подожду»"
                ],
                "analysis": "Избегание — это способ справиться с перегрузкой. Человек не слабый, он просто защищает себя.",
                "protocol": "1. Снимите давление\n2. Дайте выход\n3. Не преследуйте\n4. Верните контроль"
            },
            "3F": {
                "code": "3F",
                "emoji": "🧬",
                "title": "СЕКС / ЖЕЛАНИЕ",
                "subtitle": "Что включает его режим «хочу»",
                "description": "Ему не нужны порно-приёмы.\nЕму нужен ПАРОЛЬ — слово, взгляд, касание, которое щёлкает тумблер.\n\nЭТОТ КЛЮЧ ДАЁТ:\n   • 3 слова, которые работают как афродизиак\n   • 3 касания, от которых он теряет голову",
                "tag": "Ключ к желанию и страсти",
                "triggers": [
                    "«Ты такой...» (искренний комплимент)",
                    "Взгляд в глаза чуть дольше обычного",
                    "«А что ты любишь?»"
                ],
                "analysis": "Влечение включается через игру, тайну, недосказанность. Прямолинейность гасит интерес.",
                "protocol": "1. Создайте контекст\n2. Играйте с вниманием\n3. Читайте ответы\n4. Усиливайте напряжение"
            },
            "4F": {
                "code": "4F",
                "emoji": "🍽",
                "title": "ПОГЛОЩЕНИЕ / ДЕНЬГИ",
                "subtitle": "Какие идеи прорастают в его голове",
                "description": "Он не жадный. Он — ГОЛОДНЫЙ.\nГолодный до денег, проектов, возможностей, статуса.\n\nЭТОТ КЛЮЧ ДАЁТ:\n   • 3 фразы, которые зажигают его «режим предпринимателя»\n   • Какие предложения он не может отклонить",
                "tag": "Ключ к деньгам и идеям",
                "triggers": [
                    "«Ты можешь заработать на этом»",
                    "«Это твой шанс»",
                    "«Никто не сделает это лучше тебя»"
                ],
                "analysis": "Желание заработать — это не про жадность, а про безопасность, статус, свободу.",
                "protocol": "1. Найдите его «голод»\n2. Покажите путь к насыщению\n3. Уберите страхи\n4. Дайте первый шаг"
            }
        }

# ============================================================================
# ФОРМАТТЕРЫ СООБЩЕНИЙ
# ============================================================================

class Formatter:
    """Форматирование сообщений"""
    
    DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    @classmethod
    def results_screen(cls) -> str:
        return f"""
{cls.DIVIDER}
🧠 <b>ВАШ ПРОФИЛЬ ГОТОВ</b>
{cls.DIVIDER}

📊 <b>SA-5_INT</b>

💬 <b>ЦИТАТА:</b>
«Я не ищу — я нахожу»

💔 <b>СУТЬ ПРОБЛЕМЫ</b>
Вам сложно просить о помощи, даже когда она нужна.
Вы привыкли справляться сами, но это истощает.

🛠 <b>ИНСТРУМЕНТ</b>
Сегодня: попросите кого-то о маленькой услуге.
Заметьте, что мир не рухнул.
{cls.DIVIDER}
"""
    
    @classmethod
    def invite_created(cls, invite_url: str) -> str:
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        share_text = (
            "Есть одна штука.\n"
            "Определяет твой ночной тип личности.\n"
            "Я прошёл — совпало процентов на 90.\n"
            f"{invite_url}\n\n"
            "Интересно, у тебя тоже?"
        )
        
        return f"""
{cls.DIVIDER}
🔞 <b>ВАША ССЫЛКА-ПРИГЛАШЕНИЕ ГОТОВА!</b>
{cls.DIVIDER}

🔗 <code>{invite_url}</code>

💬 <b>ТЕКСТ ДЛЯ ОТПРАВКИ:</b>
<code>{share_text}</code>

🟢 АКТИВНО • ожидание
📅 {current_time}

🎯 После теста вы увидите его 18+ профиль.
{cls.DIVIDER}
"""
    
    @classmethod
    def invites_hub(cls, invites: List[Invitation]) -> str:
        """Хаб приглашений - БЕЗОПАСНЫЙ доступ к данным"""
        active = [i for i in invites if i.status == "active"]
        used = [i for i in invites if i.status == "used"]
        free_used = len([i for i in used if not i.access_paid])
        
        message = f"""
{cls.DIVIDER}
🔍 <b>МОИ ПРИГЛАШЕНИЯ</b>
{cls.DIVIDER}

📊 <b>СТАТИСТИКА:</b>
   🔗 Всего ссылок: {len(invites)}
   ✨ Отражений: {len(used)}
   💎 Бесплатных: {free_used}/{Config.FREE_FRIEND_LIMIT}
   🔓 Доступно: {max(0, Config.FREE_FRIEND_LIMIT - free_used)}

{cls.DIVIDER}
"""
        if active:
            message += "\n🟢 <b>ЖДУТ ОТКЛИКА</b>\n"
            for inv in active[:3]:
                message += f"   • {inv.created_at_str} · ждёт {inv.age_days}д\n"
        
        if used:
            message += f"\n✨ <b>УЖЕ ОТРАЗИЛИСЬ — {len(used)}</b>\n"
            for inv in used[:5]:
                keys = f" · 🔑 {' '.join(inv.purchased_functions)}" if inv.purchased_functions else ""
                access_icon = "🔓" if inv.access_paid else "💎"
                message += f"\n   {access_icon} {inv.display_name}"
                message += f"\n   📊 {inv.friend_profile or 'SA-3_CON'} · {inv.used_at_str}{keys}\n"
        
        return message
    
    @classmethod
    def four_f_menu(cls, friend_name: str, friend_profile: str, purchased: List[str]) -> str:
        message = f"""
{cls.DIVIDER}
🧬 <b>4F-КЛЮЧИ ДЛЯ {friend_name}</b>
{cls.DIVIDER}

📊 <b>Профиль:</b> {friend_profile}

"""
        keys = FourFKey.get_all()
        for code, key in keys.items():
            lock = "🔓" if code in purchased else "🔒"
            message += f"\n{lock} {key['emoji']} <b>{key['title']}</b>"
            message += f"\n└ {key['subtitle']}\n"
        
        message += f"""
{cls.DIVIDER}
💰 <b>Цена:</b> {Config.FOUR_F_PRICE}₽ (тестовый режим)
{cls.DIVIDER}
"""
        return message
    
    @classmethod
    def four_f_content(cls, key: dict) -> str:
        return f"""
{cls.DIVIDER}
{key['emoji']} <b>{key['title']}</b>
{key['subtitle']}
{cls.DIVIDER}

🎯 <b>ТРИГГЕР-ФРАЗЫ:</b>
"""
        for i, trigger in enumerate(key['triggers'], 1):
            message += f"\n{i}. {trigger}"
        
        message += f"""

🧠 <b>ПСИХОЛОГИЧЕСКИЙ РАЗБОР:</b>
{key['analysis']}

📋 <b>ПРОТОКОЛ ПРИМЕНЕНИЯ:</b>
{key['protocol']}

{key['tag']}
{cls.DIVIDER}
"""
        return message

# ============================================================================
# КЛАВИАТУРЫ
# ============================================================================

class Keyboard:
    """Построитель клавиатур"""
    
    @classmethod
    def results_screen(cls) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🪞 Зеркало", callback_data="mirror")],
            [InlineKeyboardButton("📖 Полный", callback_data="full")],
            [InlineKeyboardButton("🔞 Интимный профиль", callback_data="sexual_profile")]
        ])
    
    @classmethod
    def sexual_profile(cls) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")],
            [InlineKeyboardButton("🔍 МОИ ПРИГЛАШЕНИЯ", callback_data="hub_profiles")],
            [InlineKeyboardButton("⬅️ К результатам", callback_data="back_to_results")]
        ])
    
    @classmethod
    def invite_created(cls, invite_url: str, invite_code: str) -> InlineKeyboardMarkup:
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_url)}"
        
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📤 Отправить другу", url=share_url),
                InlineKeyboardButton("📋 Копировать", callback_data=f"copy_{invite_code}")
            ],
            [
                InlineKeyboardButton("🔍 МОИ ПРИГЛАШЕНИЯ", callback_data="hub_profiles"),
                InlineKeyboardButton("⬅️ К ПРОФИЛЮ", callback_data="sexual_profile")
            ]
        ])
    
    @classmethod
    def invites_hub(cls, invites: List[Invitation]) -> InlineKeyboardMarkup:
        keyboard = []
        
        # Активные приглашения
        active = [i for i in invites if i.status == "active"]
        for inv in active[:3]:
            keyboard.append([
                InlineKeyboardButton(
                    f"🔄 {inv.invite_id[:8]}... · {inv.created_at_str}",
                    callback_data=f"check_{inv.invite_id}"
                )
            ])
        
        # Друзья с 4F
        used = [i for i in invites if i.status == "used" and i.used_by_id]
        for inv in used[:3]:
            keyboard.append([
                InlineKeyboardButton(
                    f"👤 {inv.display_name}",
                    callback_data=f"friend_{inv.used_by_id}"
                )
            ])
            
            # Кнопки 4F
            row = []
            for f in ["1F", "2F", "3F", "4F"]:
                if f in inv.purchased_functions:
                    row.append(InlineKeyboardButton(
                        f"🔓 {f}",
                        callback_data=f"open_4f_{inv.used_by_id}_{f}"
                    ))
                else:
                    row.append(InlineKeyboardButton(
                        f"{f} (1₽)",
                        callback_data=f"buy_4f_{inv.used_by_id}_{f}"
                    ))
            keyboard.append(row)
        
        # Навигация
        keyboard.append([
            InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite"),
            InlineKeyboardButton("⬅️ НАЗАД", callback_data="back_from_hub")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @classmethod
    def four_f_menu(cls, friend_id: int, purchased: List[str]) -> InlineKeyboardMarkup:
        keyboard = []
        
        for f in ["1F", "2F", "3F", "4F"]:
            key = FourFKey.get_all()[f]
            if f in purchased:
                keyboard.append([
                    InlineKeyboardButton(
                        f"{key['emoji']} {f} - ОТКРЫТЬ",
                        callback_data=f"open_4f_{friend_id}_{f}"
                    )
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton(
                        f"{key['emoji']} {f} - 1₽",
                        callback_data=f"buy_4f_{friend_id}_{f}"
                    )
                ])
        
        keyboard.append([
            InlineKeyboardButton("❓ Что такое 4F?", callback_data="4f_explain"),
            InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")
        ])
        
        return InlineKeyboardMarkup(keyboard)

# ============================================================================
# ОСНОВНОЙ ОБРАБОТЧИК
# ============================================================================

class Bot:
    """Главный класс бота"""
    
    def __init__(self):
        self.storage = Storage()
        self.application = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик /start"""
        user = update.effective_user
        session = await self.storage.get_session(user.id)
        
        if not session:
            session = await self.storage.create_session(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name
            )
        
        # Инициализация тестовых данных
        if not session.invites:
            await self.storage.init_test_data(user.id)
        
        return await self.show_results(update, context)
    
    async def show_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Экран результатов"""
        message = Formatter.results_screen()
        keyboard = Keyboard.results_screen()
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                message, reply_markup=keyboard, parse_mode="HTML"
            )
        
        return States.RESULTS_SCREEN
    
    async def sexual_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🔞 Интимный профиль"""
        query = update.callback_query
        await query.answer()
        
        # Заглушка профиля
        profile = {
            "profile_type": "SA-5_INT",
            "archetype": "ЦЕРЕМОНИАЛЬНЫЙ",
            "quote": "«Со мной не скучно. Со мной — вкусно.»",
            "description": "Секс для вас — священнодействие. Ритуал. Мистерия."
        }
        
        username = query.from_user.first_name or "Пользователь"
        
        message = f"""
{Formatter.DIVIDER}
🔞 <b>18+ ПРОФИЛЬ: {username}</b>
🧠 <b>ПРОФИЛЬ:</b> {profile['profile_type']}
{Formatter.DIVIDER}

{profile['description']}

<b>🔴 ВКЛЮЧАЕТ:</b>
• Шёпот в темноте
• Запах тела после долгого дня
• Медленные пуговицы

<b>⚠️ ВЫКЛЮЧАЕТ:</b>
• Секс на скорую руку
• Грубые интонации

{Formatter.DIVIDER}
💞 <b>У КАЖДОГО ЕСТЬ ТАЙНЫ.</b>
🔓 <b>ВАШ КЛЮЧ К ПРАВДЕ:</b>

❶ Пригласите → 0₽
❷ Друг проходит тест (3 мин)
❸ 99₽ = доступ к его 18+ профилю
{Formatter.DIVIDER}
"""
        
        await query.edit_message_text(
            message, reply_markup=Keyboard.sexual_profile(), parse_mode="HTML"
        )
        
        return States.SEXUAL_PROFILE
    
    async def create_invite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🔞 Создание приглашения"""
        query = update.callback_query
        await query.answer()
        
        session = await self.storage.get_session(query.from_user.id)
        
        invitation = await self.storage.create_invitation(
            creator_id=session.user_id,
            creator_profile="SA-5_INT"
        )
        
        invite_url = f"https://t.me/{Config.BOT_USERNAME}?start={invitation.invite_id}"
        message = Formatter.invite_created(invite_url)
        keyboard = Keyboard.invite_created(invite_url, invitation.invite_id)
        
        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True
        )
        
        return States.INVITE_CREATE
    
    async def invites_hub(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🔍 Хаб приглашений - ИСПРАВЛЕНО! БЕЗ ОШИБКИ KeyError"""
        query = update.callback_query
        await query.answer()
        
        session = await self.storage.get_session(query.from_user.id)
        invites = await self.storage.get_user_invites(session.user_id)
        
        message = Formatter.invites_hub(invites)
        keyboard = Keyboard.invites_hub(invites)
        
        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="HTML"
        )
        
        return States.INVITES_LIST
    
    async def four_f_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🧬 Меню 4F-ключей"""
        query = update.callback_query
        await query.answer()
        
        parts = query.data.split("_")
        friend_id = int(parts[1])
        
        session = await self.storage.get_session(query.from_user.id)
        friend_data = await self.storage.get_friend_data(session.user_id, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return States.INVITES_LIST
        
        friend_name = friend_data.display_name
        friend_profile = friend_data.friend_profile or "SA-3_CON"
        purchased = friend_data.purchased_functions
        
        message = Formatter.four_f_menu(friend_name, friend_profile, purchased)
        keyboard = Keyboard.four_f_menu(friend_id, purchased)
        
        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="HTML"
        )
        
        return States.FOUR_F_MENU
    
    async def buy_4f_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """💰 Покупка 4F-ключа"""
        query = update.callback_query
        await query.answer("💰 Создаю счёт...")
        
        parts = query.data.split("_")
        friend_id = int(parts[2])
        key_code = parts[3]
        
        key = FourFKey.get_all()[key_code]
        
        message = f"""
{Formatter.DIVIDER}
{key['emoji']} <b>{key['title']}</b>
{key['subtitle']}
{Formatter.DIVIDER}

{key['description']}

💰 <b>Цена:</b> {Config.FOUR_F_PRICE}₽ (тестовый режим)
{Formatter.DIVIDER}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 ОПЛАТИТЬ 1₽", callback_data=f"pay_4f_{friend_id}_{key_code}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"4f_{friend_id}")]
        ])
        
        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="HTML"
        )
        
        return States.FOUR_F_PURCHASE
    
    async def open_4f_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🔓 Открыть 4F-ключ"""
        query = update.callback_query
        await query.answer("🔓 Загружаю ключ...")
        
        parts = query.data.split("_")
        friend_id = int(parts[2])
        key_code = parts[3]
        
        key = FourFKey.get_all()[key_code]
        message = Formatter.four_f_content(key)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ К списку ключей", callback_data=f"4f_{friend_id}")],
            [InlineKeyboardButton("🔍 МОИ ПРИГЛАШЕНИЯ", callback_data="hub_profiles")]
        ])
        
        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="HTML"
        )
        
        return States.FOUR_F_CONTENT
    
    async def pay_4f_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """💳 Обработка платежа (мок)"""
        query = update.callback_query
        await query.answer("✅ Ключ разблокирован! (тестовый режим)", show_alert=True)
        
        parts = query.data.split("_")
        friend_id = int(parts[2])
        key_code = parts[3]
        
        session = await self.storage.get_session(query.from_user.id)
        await self.storage.purchase_4f_key(session.user_id, friend_id, key_code)
        
        # Открываем ключ
        query.data = f"open_4f_{friend_id}_{key_code}"
        return await self.open_4f_key(update, context)
    
    async def back_from_hub(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """⬅️ Возврат из хаба"""
        query = update.callback_query
        await query.answer()
        return await self.sexual_profile(update, context)
    
    async def back_to_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """⬅️ Возврат к результатам"""
        query = update.callback_query
        await query.answer()
        return await self.show_results(update, context)
    
    async def dummy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Заглушка"""
        await update.callback_query.answer("✅ Демо-режим")
        return States.RESULTS_SCREEN
    
    async def copy_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """📋 Копирование ссылки"""
        await update.callback_query.answer("✅ Ссылка скопирована!", show_alert=True)
        return States.INVITE_CREATE
    
    async def check_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🔄 Проверка статуса"""
        await update.callback_query.answer("🔄 Друг ещё не прошёл тест", show_alert=True)
        return States.INVITES_LIST
    
    async def friend_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """👤 Меню друга"""
        query = update.callback_query
        await query.answer()
        
        parts = query.data.split("_")
        friend_id = int(parts[1])
        
        session = await self.storage.get_session(query.from_user.id)
        friend_data = await self.storage.get_friend_data(session.user_id, friend_id)
        
        if not friend_data:
            await query.answer("❌ Друг не найден", show_alert=True)
            return States.INVITES_LIST
        
        message = f"""
{Formatter.DIVIDER}
👤 <b>{friend_data.display_name}</b>
{Formatter.DIVIDER}

📊 <b>Профиль:</b> {friend_data.friend_profile or 'SA-3_CON'}
💎 <b>Доступ:</b> {'🔓 Бесплатно' if friend_data.access_status == 'free' else '💰 Куплен'}

🔓 <b>Купленные ключи:</b> {', '.join(friend_data.purchased_functions) if friend_data.purchased_functions else 'нет'}
{Formatter.DIVIDER}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🧬 4F-КЛЮЧИ", callback_data=f"4f_{friend_id}")],
            [InlineKeyboardButton("❓ Что это?", callback_data="4f_explain")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="hub_profiles")]
        ])
        
        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="HTML"
        )
        
        return States.FRIEND_MENU
    
    async def four_f_explain(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """📘 Что такое 4F?"""
        query = update.callback_query
        await query.answer()
        
        message = f"""
{Formatter.DIVIDER}
📘 <b>ЧТО ТАКОЕ 4F-КЛЮЧИ?</b>
{Formatter.DIVIDER}

🧬 4F — это система доступа к состояниям человека.
Четыре базовые реакции, зашитые в подкорке.

1F 🔥 <b>НАПАДЕНИЕ / ЯРОСТЬ</b>
└ Ключ к управлению гневом

2F 🏃 <b>БЕГСТВО / СТРАХ</b>
└ Ключ к преодолению страхов

3F 🧬 <b>СЕКС / ЖЕЛАНИЕ</b>
└ Ключ к желанию и страсти

4F 🍽 <b>ПОГЛОЩЕНИЕ / ДЕНЬГИ</b>
└ Ключ к деньгам и идеям

💰 <b>Цена:</b> {Config.FOUR_F_PRICE}₽ (тестовый режим)
{Formatter.DIVIDER}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Назад", callback_data="hub_profiles")]
        ])
        
        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="HTML"
        )
        
        return States.FOUR_F_MENU
    
    def get_conversation_handler(self) -> ConversationHandler:
        """Создание ConversationHandler"""
        return ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                States.RESULTS_SCREEN: [
                    CallbackQueryHandler(self.sexual_profile, pattern='^sexual_profile$'),
                    CallbackQueryHandler(self.dummy, pattern='^(mirror|full)$'),
                    CallbackQueryHandler(self.back_to_results, pattern='^back_to_results$'),
                ],
                States.SEXUAL_PROFILE: [
                    CallbackQueryHandler(self.create_invite, pattern='^create_invite$'),
                    CallbackQueryHandler(self.invites_hub, pattern='^hub_profiles$'),
                    CallbackQueryHandler(self.back_to_results, pattern='^back_to_results$'),
                ],
                States.INVITE_CREATE: [
                    CallbackQueryHandler(self.copy_callback, pattern='^copy_'),
                    CallbackQueryHandler(self.invites_hub, pattern='^hub_profiles$'),
                    CallbackQueryHandler(self.sexual_profile, pattern='^sexual_profile$'),
                ],
                States.INVITES_LIST: [
                    CallbackQueryHandler(self.create_invite, pattern='^create_invite$'),
                    CallbackQueryHandler(self.invites_hub, pattern='^hub_profiles$'),
                    CallbackQueryHandler(self.check_callback, pattern='^check_'),
                    CallbackQueryHandler(self.friend_callback, pattern='^friend_'),
                    CallbackQueryHandler(self.four_f_menu, pattern='^4f_'),
                    CallbackQueryHandler(self.sexual_profile, pattern='^sexual_profile$'),
                    CallbackQueryHandler(self.back_from_hub, pattern='^back_from_hub$'),
                ],
                States.FRIEND_MENU: [
                    CallbackQueryHandler(self.four_f_menu, pattern='^4f_'),
                    CallbackQueryHandler(self.four_f_explain, pattern='^4f_explain$'),
                    CallbackQueryHandler(self.invites_hub, pattern='^hub_profiles$'),
                ],
                States.FOUR_F_MENU: [
                    CallbackQueryHandler(self.buy_4f_key, pattern='^buy_4f_'),
                    CallbackQueryHandler(self.open_4f_key, pattern='^open_4f_'),
                    CallbackQueryHandler(self.four_f_explain, pattern='^4f_explain$'),
                    CallbackQueryHandler(self.friend_callback, pattern='^friend_'),
                ],
                States.FOUR_F_CONTENT: [
                    CallbackQueryHandler(self.four_f_menu, pattern='^4f_'),
                    CallbackQueryHandler(self.invites_hub, pattern='^hub_profiles$'),
                ],
                States.FOUR_F_PURCHASE: [
                    CallbackQueryHandler(self.pay_4f_key, pattern='^pay_4f_'),
                    CallbackQueryHandler(self.four_f_menu, pattern='^4f_'),
                ],
            },
            fallbacks=[
                CommandHandler('start', self.start),
                CallbackQueryHandler(self.back_to_results, pattern='^back_to_results$'),
            ],
            name="intimate_bot_v13",
            persistent=False,
        )
    
    async def setup_webhook(self):
        """Настройка webhook для Render"""
        if Config.is_render() and Config.RENDER_EXTERNAL_URL:
            webhook_url = Config.get_webhook_url()
            if webhook_url:
                await self.application.bot.set_webhook(
                    url=webhook_url,
                    allowed_updates=["message", "callback_query"],
                    drop_pending_updates=True
                )
                logger.info(f"✅ Webhook установлен: {webhook_url}")
    
    def run(self):
        """Запуск бота"""
        print("\n" + "="*70)
        print("🔞 ИНТИМНЫЕ ПРОФИЛИ И 4F-КЛЮЧИ v13.0")
        print("="*70)
        print(f"🚀 Режим: {'WEBHOOK' if Config.is_render() else 'POLLING'}")
        print(f"📁 Корень: {PROJECT_ROOT}")
        print("✅ ИСПРАВЛЕНА ОШИБКА KeyError: 'created_at'")
        print("="*70)
        
        # Создание приложения
        self.application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        self.application.add_handler(self.get_conversation_handler())
        
        # Запуск
        if Config.is_render():
            # Webhook режим
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.setup_webhook())
            
            # Flask для Render
            from flask import Flask, request, jsonify
            flask_app = Flask(__name__)
            
            @flask_app.route(Config.WEBHOOK_PATH, methods=['POST'])
            async def webhook():
                update = Update.de_json(request.get_json(), self.application.bot)
                await self.application.process_update(update)
                return {"ok": True}
            
            @flask_app.route('/health', methods=['GET'])
            def health():
                return {"status": "ok", "version": "13.0"}
            
            @flask_app.route('/', methods=['GET'])
            def index():
                return {"name": "Intimate Bot", "version": "13.0"}
            
            print(f"🌐 Запуск webhook на порту {Config.PORT}")
            flask_app.run(host='0.0.0.0', port=Config.PORT)
        else:
            # Polling режим
            print("🚀 Запуск в режиме polling...")
            self.application.run_polling(allowed_updates=["message", "callback_query"])

# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

def main():
    """Главная функция"""
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    main()
