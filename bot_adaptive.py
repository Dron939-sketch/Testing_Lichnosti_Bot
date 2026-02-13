#!/usr/bin/env python3
"""
🔞 ИНТИМНЫЕ ПРОФИЛИ И 4F-КЛЮЧИ
Версия: 12.0 - ИНТЕГРИРОВАННАЯ АРХИТЕКТУРА
✅ ВЗЯТО ВСЕ ЦЕННОЕ ИЗ sexual_module.py
✅ ЕДИНАЯ ТОЧКА ВХОДА
✅ ПЕРСИСТЕНТНОЕ ХРАНИЛИЩЕ
✅ WEBHOOK ДЛЯ RENDER
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
from functools import wraps

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)

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
    SNAPSHOT_TTL = 3600
    MAX_HISTORY_LENGTH = 20
    CACHE_TTL = 300
    
    # Webhook
    RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")
    PORT = int(os.getenv("PORT", 8080))
    WEBHOOK_PATH = f"/webhook/{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else "/webhook"
    
    @classmethod
    def is_render(cls) -> bool:
        """Проверка, запущены ли мы на Render"""
        return bool(os.getenv("RENDER"))
    
    @classmethod
    def get_webhook_url(cls) -> Optional[str]:
        """Получение URL для webhook"""
        if cls.RENDER_EXTERNAL_URL:
            return f"{cls.RENDER_EXTERNAL_URL}{cls.WEBHOOK_PATH}"
        return None
    
    @classmethod
    def get_project_root(cls) -> str:
        """Определение корня проекта"""
        current = os.path.dirname(os.path.abspath(__file__))
        
        while current != os.path.dirname(current):
            if os.path.exists(os.path.join(current, "sexual_18")):
                return current
            current = os.path.dirname(current)
        
        return os.path.dirname(os.path.abspath(__file__))
    
    @classmethod
    def get_profile_paths(cls, filename: str = "sa_5_int.json") -> List[str]:
        """Все возможные пути к файлам профилей"""
        root = cls.get_project_root()
        paths = [
            os.path.join(root, "sexual_18", filename),
            os.path.join(root, "profiles", "sexual_18", filename),
            os.path.join("sexual_18", filename),
            os.path.join("profiles", "sexual_18", filename),
        ]
        
        if cls.is_render():
            paths.extend([
                f"/app/sexual_18/{filename}",
                f"/app/profiles/sexual_18/{filename}",
            ])
        
        return paths

PROJECT_ROOT = Config.get_project_root()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ============================================================================
# ЛОГГИРОВАНИЕ
# ============================================================================

class Logger:
    """Структурированное логирование"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup()
        return cls._instance
    
    def _setup(self):
        """Настройка логгера"""
        self.logger = logging.getLogger("intimate_bot")
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        self.logger.addHandler(console)
        
        try:
            os.makedirs("logs", exist_ok=True)
            file_handler = logging.FileHandler(
                "logs/bot.log", 
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except:
            pass
    
    def info(self, msg: str, **kwargs):
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"{msg} | {extra}" if extra else msg)
    
    def error(self, msg: str, exc_info: bool = False, **kwargs):
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.error(f"{msg} | {extra}" if extra else msg, exc_info=exc_info)
    
    def warning(self, msg: str, **kwargs):
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.warning(f"{msg} | {extra}" if extra else msg)
    
    def debug(self, msg: str, **kwargs):
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.debug(f"{msg} | {extra}" if extra else msg)

logger = Logger()

# ============================================================================
# МОДЕЛИ ДАННЫХ
# ============================================================================

class UserRole(Enum):
    """Роли пользователей"""
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"

class NavigationIntent(Enum):
    """Типы навигационных действий"""
    FORWARD = auto()
    BACK = auto()
    JUMP_TO_HUB = auto()
    JUMP_TO_FLOW = auto()
    RESTORE = auto()

@dataclass
class Invitation:
    """Модель приглашения"""
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
    
    def is_valid(self) -> bool:
        """Проверка валидности приглашения"""
        if self.status != "active":
            return False
        return (datetime.now().timestamp() - self.created_at) < 604800

@dataclass
class UserSession:
    """Сессия пользователя"""
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    role: UserRole = UserRole.FREE
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    last_active: float = field(default_factory=lambda: datetime.now().timestamp())
    invites: List[str] = field(default_factory=list)
    purchased_friends: List[int] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "first_name": self.first_name,
            "role": self.role.value,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "invites": self.invites.copy(),
            "purchased_friends": self.purchased_friends.copy()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserSession':
        session = cls(
            user_id=data["user_id"],
            username=data["username"],
            first_name=data["first_name"],
            created_at=data["created_at"],
            last_active=data["last_active"],
            invites=data["invites"],
            purchased_friends=data["purchased_friends"]
        )
        session.role = UserRole(data.get("role", "free"))
        return session
    
    def update_activity(self):
        """Обновление времени активности"""
        self.last_active = datetime.now().timestamp()

@dataclass
class FourFKey:
    """4F-ключ"""
    code: str
    emoji: str
    title: str
    subtitle: str
    description: str
    tag: str
    price: int = 1
    
    @classmethod
    def get_all(cls) -> Dict[str, 'FourFKey']:
        """Все доступные ключи"""
        return {
            "1F": cls(
                code="1F",
                emoji="🔥",
                title="НАПАДЕНИЕ / ЯРОСТЬ",
                subtitle="Как гасить агрессию и не нарваться",
                description="""Он не злой. Он — ВЗВЕДЁННЫЙ.
Достаточно одной искры, чтобы рвануло.

ЭТОТ КЛЮЧ ДАЁТ:
   • 3 фразы, которые моментально сбивают агрессию
   • Что нельзя говорить, когда он уже завёлся
   • Как перевести конфликт в диалог за 30 секунд
   • Почему он злится именно на вас""",
                tag="Ключ к управлению гневом"
            ),
            "2F": cls(
                code="2F",
                emoji="🏃",
                title="БЕГСТВО / СТРАХ",
                subtitle="Чего он боится на самом деле",
                description="""Он не трус. Он — ПРЕДУСМОТРИТЕЛЬНЫЙ.
Просто однажды его уже больно ударили.

ЭТОТ КЛЮЧ ДАЁТ:
   • 3 фразы, которые включают панику (чтобы знать, чего НЕ делать)
   • 3 фразы, которые снимают тревогу (чтобы успокоить)
   • Его личные триггеры страха
   • Как говорить с ним, когда он «в тумане»""",
                tag="Ключ к преодолению страхов"
            ),
            "3F": cls(
                code="3F",
                emoji="🧬",
                title="СЕКС / ЖЕЛАНИЕ",
                subtitle="Что включает его режим «хочу»",
                description="""Ему не нужны порно-приёмы.
Ему нужен ПАРОЛЬ — слово, взгляд, касание, которое щёлкает тумблер.

ЭТОТ КЛЮЧ ДАЁТ:
   • 3 слова, которые работают как афродизиак
   • 3 касания, от которых он теряет голову
   • Его скрытые эротические сценарии
   • Что гасит желание мгновенно""",
                tag="Ключ к желанию и страсти"
            ),
            "4F": cls(
                code="4F",
                emoji="🍽",
                title="ПОГЛОЩЕНИЕ / ДЕНЬГИ",
                subtitle="Какие идеи прорастают в его голове",
                description="""Он не жадный. Он — ГОЛОДНЫЙ.
Голодный до денег, проектов, возможностей, статуса.

ЭТОТ КЛЮЧ ДАЁТ:
   • 3 фразы, которые зажигают его «режим предпринимателя»
   • Какие предложения он не может отклонить
   • Как продавать ему, не продавая
   • Что его тормозит в заработке""",
                tag="Ключ к деньгам и идеям"
            )
        }
    
    def get_content(self) -> Dict[str, Any]:
        """Полный контент ключа"""
        return {
            "triggers": self._get_triggers(),
            "analysis": self._get_analysis(),
            "protocol": self._get_protocol()
        }
    
    def _get_triggers(self) -> List[str]:
        """Триггер-фразы"""
        triggers = {
            "1F": [
                "«Я понимаю, почему ты так реагируешь»",
                "«Ты имеешь полное право злиться»",
                "«Я на твоей стороне»",
                "«Это действительно несправедливо»",
                "«Твои границы — это важно»"
            ],
            "2F": [
                "«Ты не обязан это делать»",
                "«Здесь безопасно»",
                "«Я подожду»",
                "«Ты можешь уйти в любой момент»",
                "«Никакого давления»"
            ],
            "3F": [
                "«Ты такой...» (искренний комплимент)",
                "Взгляд в глаза чуть дольше обычного",
                "«А что ты любишь?»",
                "Случайное касание, которое не прерывают",
                "Шёпот, интимный контекст"
            ],
            "4F": [
                "«Ты можешь заработать на этом»",
                "«Это твой шанс»",
                "«Никто не сделает это лучше тебя»",
                "«Представь, сколько это будет стоить через год»",
                "«Я верю в твою идею»"
            ]
        }
        return triggers.get(self.code, [])
    
    def _get_analysis(self) -> str:
        """Психологический разбор"""
        analysis = {
            "1F": "Страх нападения возникает, когда человек не чувствует безопасности. Его агрессия — это защита.",
            "2F": "Избегание — это способ справиться с перегрузкой. Человек не слабый, он просто защищает себя.",
            "3F": "Влечение включается через игру, тайну, недосказанность. Прямолинейность гасит интерес.",
            "4F": "Желание заработать — это не про жадность, а про безопасность, статус, свободу."
        }
        return analysis.get(self.code, "")
    
    def _get_protocol(self) -> str:
        """Протокол применения"""
        protocol = {
            "1F": "1. Заметьте триггер\n2. Признайте эмоцию\n3. Не давите\n4. Дайте время",
            "2F": "1. Снимите давление\n2. Дайте выход\n3. Не преследуйте\n4. Верните контроль",
            "3F": "1. Создайте контекст\n2. Играйте с вниманием\n3. Читайте ответы\n4. Усиливайте напряжение",
            "4F": "1. Найдите его «голод»\n2. Покажите путь к насыщению\n3. Уберите страхи\n4. Дайте первый шаг"
        }
        return protocol.get(self.code, "")

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
        """Инициализация хранилища"""
        self.data_dir = os.path.join(PROJECT_ROOT, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.sessions_file = os.path.join(self.data_dir, "sessions.json")
        self.invitations_file = os.path.join(self.data_dir, "invitations.json")
        
        self.sessions: Dict[int, UserSession] = {}
        self.invitations: Dict[str, Invitation] = {}
        
        self._load_data()
        self._locks = defaultdict(asyncio.Lock)
    
    def _load_data(self):
        """Загрузка данных из файлов"""
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sessions = {
                        int(uid): UserSession.from_dict(sess)
                        for uid, sess in data.items()
                    }
        except Exception as e:
            logger.error("Failed to load sessions", error=str(e))
        
        try:
            if os.path.exists(self.invitations_file):
                with open(self.invitations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.invitations = {
                        inv_id: Invitation.from_dict(inv)
                        for inv_id, inv in data.items()
                    }
        except Exception as e:
            logger.error("Failed to load invitations", error=str(e))
    
    async def _save_sessions(self):
        """Сохранение сессий"""
        async with self._lock:
            try:
                data = {
                    str(uid): session.to_dict()
                    for uid, session in self.sessions.items()
                }
                with open(self.sessions_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error("Failed to save sessions", error=str(e))
    
    async def _save_invitations(self):
        """Сохранение приглашений"""
        async with self._lock:
            try:
                data = {
                    inv_id: inv.to_dict()
                    for inv_id, inv in self.invitations.items()
                }
                with open(self.invitations_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error("Failed to save invitations", error=str(e))
    
    async def get_session(self, user_id: int) -> Optional[UserSession]:
        """Получение сессии пользователя"""
        async with self._locks[f"session_{user_id}"]:
            session = self.sessions.get(user_id)
            if session:
                session.update_activity()
            return session
    
    async def create_session(self, user_id: int, username: Optional[str], 
                            first_name: Optional[str]) -> UserSession:
        """Создание новой сессии"""
        async with self._locks[f"session_{user_id}"]:
            session = UserSession(
                user_id=user_id,
                username=username,
                first_name=first_name
            )
            self.sessions[user_id] = session
            await self._save_sessions()
            logger.info("session_created", user_id=user_id)
            return session
    
    async def update_session(self, session: UserSession):
        """Обновление сессии"""
        async with self._locks[f"session_{session.user_id}"]:
            session.update_activity()
            self.sessions[session.user_id] = session
            await self._save_sessions()
    
    async def create_invitation(self, creator_id: int, creator_profile: str) -> Invitation:
        """Создание приглашения"""
        async with self._lock:
            invite_id = f"sex_{uuid.uuid4().hex[:8]}_{uuid.uuid4().hex[:4]}"
            invitation = Invitation(
                invite_id=invite_id,
                creator_id=creator_id,
                creator_profile=creator_profile,
                status="active",
                created_at=datetime.now().timestamp()
            )
            self.invitations[invite_id] = invitation
            await self._save_invitations()
            
            session = await self.get_session(creator_id)
            if session:
                session.invites.append(invite_id)
                await self.update_session(session)
            
            logger.info("invitation_created", invite_id=invite_id, creator_id=creator_id)
            return invitation
    
    async def get_invitation(self, invite_id: str) -> Optional[Invitation]:
        """Получение приглашения"""
        async with self._lock:
            return self.invitations.get(invite_id)
    
    async def use_invitation(self, invite_id: str, user_id: int, user_name: str, 
                            username: str, profile: str) -> bool:
        """Использование приглашения"""
        async with self._lock:
            invitation = self.invitations.get(invite_id)
            if not invitation or not invitation.is_valid():
                return False
            
            invitation.status = "used"
            invitation.used_at = datetime.now().timestamp()
            invitation.used_by_id = user_id
            invitation.used_by_name = user_name
            invitation.used_by_username = username
            invitation.friend_profile = profile
            
            session = await self.get_session(invitation.creator_id)
            if session:
                free_used = len([i for i in session.invites 
                               if i in self.invitations and 
                               self.invitations[i].status == "used" and
                               not self.invitations[i].access_paid])
                
                invitation.access_status = "free" if free_used <= Config.FREE_FRIEND_LIMIT else "locked"
            
            await self._save_invitations()
            logger.info("invitation_used", invite_id=invite_id, user_id=user_id)
            return True
    
    async def get_user_invites(self, user_id: int) -> List[Invitation]:
        """Получение всех приглашений пользователя"""
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
    
    async def get_friend_data(self, creator_id: int, friend_id: int) -> Optional[Invitation]:
        """Получение данных о друге"""
        async with self._lock:
            for inv in self.invitations.values():
                if inv.creator_id == creator_id and inv.used_by_id == friend_id:
                    return inv
            return None
    
    async def purchase_4f_key(self, creator_id: int, friend_id: int, key_code: str) -> bool:
        """Покупка 4F-ключа"""
        async with self._lock:
            for inv in self.invitations.values():
                if inv.creator_id == creator_id and inv.used_by_id == friend_id:
                    if key_code not in inv.purchased_functions:
                        inv.purchased_functions.append(key_code)
                        await self._save_invitations()
                        logger.info("4f_key_purchased", 
                                  creator_id=creator_id, 
                                  friend_id=friend_id, 
                                  key=key_code)
                    return True
            return False
    
    async def init_test_data(self, user_id: int):
        """Инициализация тестовых данных"""
        session = await self.get_session(user_id)
        if not session:
            session = await self.create_session(user_id, "test_user", "Тест")
        
        if not session.invites:
            inv1 = await self.create_invitation(user_id, "SA-5_INT")
            inv1.status = "used"
            inv1.used_at = datetime.now().timestamp()
            inv1.used_by_id = 1001
            inv1.used_by_name = "@alex"
            inv1.used_by_username = "alex"
            inv1.friend_profile = "SA-3_CON"
            inv1.access_status = "free"
            await self._save_invitations()
            
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
            
            logger.info("test_data_initialized", user_id=user_id)

# ============================================================================
# ЗАГРУЗЧИК ПРОФИЛЕЙ - С ДИАГНОСТИКОЙ ИЗ sexual_module.py
# ============================================================================

class ProfileLoader:
    """Загрузка профилей с кэшированием и диагностикой"""
    
    _cache: Dict[str, dict] = {}
    _cache_timestamp: Dict[str, float] = {}
    CACHE_TTL = 300
    
    @classmethod
    async def load_intimate_profile(cls, force_reload: bool = False, debug: bool = True) -> dict:
        """Загрузка интимного профиля с диагностикой"""
        if debug:
            cls._debug_load_paths()
        
        cache_key = "intimate_profile"
        
        if not force_reload and cache_key in cls._cache:
            cache_time = cls._cache_timestamp.get(cache_key, 0)
            if (datetime.now().timestamp() - cache_time) < cls.CACHE_TTL:
                logger.info("profile_cache_hit", profile=cache_key)
                return cls._cache[cache_key]
        
        logger.info("loading_intimate_profile")
        
        for path in Config.get_profile_paths("sa_5_int.json"):
            try:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        profile = cls._normalize_profile(data)
                        
                        cls._cache[cache_key] = profile
                        cls._cache_timestamp[cache_key] = datetime.now().timestamp()
                        
                        logger.info("profile_loaded", path=path)
                        return profile
                        
            except Exception as e:
                logger.error("profile_load_error", error=str(e), path=path)
                continue
        
        logger.warning("profile_not_found, using_emergency")
        return cls._get_emergency_profile()
    
    @classmethod
    def _debug_load_paths(cls):
        """Диагностика путей к файлам профиля - ИЗ sexual_module.py"""
        print("\n" + "="*80)
        print("🔍 ДИАГНОСТИКА ЗАГРУЗКИ ИНТИМНОГО ПРОФИЛЯ")
        print("="*80)
        print(f"📁 Текущая директория: {os.getcwd()}")
        print(f"📁 PROJECT_ROOT: {Config.get_project_root()}")
        print(f"📁 __file__: {__file__}")
        
        sexual_18_dir = os.path.join(Config.get_project_root(), "sexual_18")
        if os.path.exists(sexual_18_dir):
            print(f"✅ Папка sexual_18 существует: {sexual_18_dir}")
            try:
                files = os.listdir(sexual_18_dir)
                print(f"   Содержимое: {files}")
                if "sa_5_int.json" in files:
                    print(f"   ✅ Файл sa_5_int.json найден в папке!")
            except Exception as e:
                print(f"   ❌ Ошибка чтения папки: {e}")
        else:
            print(f"❌ Папка sexual_18 НЕ найдена: {sexual_18_dir}")
        
        print("\n🔍 ПРОВЕРКА ВСЕХ ВОЗМОЖНЫХ ПУТЕЙ:")
        for path in Config.get_profile_paths("sa_5_int.json"):
            if os.path.exists(path):
                size = os.path.getsize(path)
                print(f"   ✅ {path}")
                print(f"      📏 Размер: {size} байт")
            else:
                print(f"   ❌ {path}")
        
        print("="*80 + "\n")
    
    @classmethod
    def _normalize_profile(cls, data: dict) -> dict:
        """Нормализация структуры профиля"""
        if 'sections' in data:
            return data
        
        normalized = {
            "profile_type": data.get("profile_type", data.get("profile", "SA-5_INT")),
            "archetype": data.get("archetype", data.get("name", "ЦЕРЕМОНИАЛЬНЫЙ")),
            "role": data.get("role", "Жрец/Жрица сексуальной мистерии"),
            "quote": data.get("quote", "«Со мной не скучно. Со мной — вкусно.»"),
            "description": data.get("description", data.get("text", data.get("about", ""))),
            "sections": cls._extract_sections(data)
        }
        
        return normalized
    
    @classmethod
    def _extract_sections(cls, data: dict) -> dict:
        """Извлечение секций из сырых данных"""
        sections = {}
        section_mapping = {
            "what_turns_on": ["what_turns_on", "turns_on", "включает", "возбуждает"],
            "what_turns_off": ["what_turns_off", "turns_off", "выключает", "отталкивает"],
            "smells_tastes": ["smells_tastes", "smells", "tastes", "запахи"],
            "sounds": ["sounds", "звуки"],
            "fetishes": ["fetishes", "фетиши"],
            "secret_desires": ["secret_desires", "desires", "желания"],
        }
        
        titles = {
            "what_turns_on": "🔴 ВКЛЮЧАЕТ",
            "what_turns_off": "⚠️ ВЫКЛЮЧАЕТ",
            "smells_tastes": "👃 ЗАПАХИ И ВКУСЫ",
            "sounds": "🎵 ЗВУКИ",
            "fetishes": "🕯 ФЕТИШИ",
            "secret_desires": "🤫 ТАЙНЫЕ ЖЕЛАНИЯ"
        }
        
        for section_key, possible_keys in section_mapping.items():
            for key in possible_keys:
                if key in data:
                    value = data[key]
                    if isinstance(value, (list, dict)):
                        sections[section_key] = {
                            "title": titles.get(section_key, section_key.upper()),
                            "items": value if isinstance(value, list) else list(value.values())
                        }
                    break
        
        return sections
    
    @classmethod
    def _get_emergency_profile(cls) -> dict:
        """Аварийный интимный профиль - КРАСИВАЯ ЗАГЛУШКА из sexual_module.py"""
        return {
            "profile_type": "SA-5_INT",
            "archetype": "ЦЕРЕМОНИАЛЬНЫЙ",
            "role": "Жрец/Жрица сексуальной мистерии",
            "quote": "«Со мной не скучно. Со мной — вкусно.»",
            "description": "Секс для вас — священнодействие. Ритуал. Мистерия.\nВам нужен сценарий, подготовка, правильная атмосфера.\nВы не занимаетесь любовью — вы служите ей.\nИ каждый раз — как в первый. И каждый раз — как в последний.",
            "sections": {
                "what_turns_on": {
                    "title": "🔴 ВКЛЮЧАЕТ",
                    "items": [
                        "Шёпот в темноте — когда партнёр шепчет почти беззвучно",
                        "Запах тела — запах пота после долгого дня, смешанный с духами",
                        "Медленные пуговицы — когда раздевают, глядя в глаза"
                    ]
                },
                "what_turns_off": {
                    "title": "⚠️ ВЫКЛЮЧАЕТ",
                    "items": [
                        "Секс на скорую руку — чувство использованности",
                        "Грубые, приказные интонации",
                        "«Ну давай быстрее» — убивает всё мгновенно"
                    ]
                },
                "erogenous_zone": {
                    "title": "🔴 ЭРОГЕННАЯ ЗОНА",
                    "trigger": "Шея, мочки ушей, внутренняя сторона запястья. Особенно — когда касаются губами."
                },
                "ideal_partner": {
                    "title": "💞 ИДЕАЛЬНЫЙ ПАРТНЁР",
                    "description": "Тот, кто не торопится. Кто читает ваше тело как ноты. Кто знает: сначала свет, потом музыка, потом вино, потом касания."
                },
                "fetishes": {
                    "title": "🕯 ФЕТИШИ",
                    "items": [
                        "Запах затылка партнёра — уткнуться носом и дышать",
                        "Медленные ритмичные движения — если сбивается темп, это катастрофа",
                        "Укус мочки уха и шёпот одновременно — подкашиваются колени"
                    ]
                },
                "secret_desires": {
                    "title": "🤫 ТАЙНЫЕ ЖЕЛАНИЯ",
                    "items": [
                        "Чтобы партнёр кончил в рот, а вы проглотили",
                        "Чтобы вас связали — шарфом, галстуком, простынёй",
                        "Плакать во время секса — от переполнения"
                    ]
                }
            }
        }

# ============================================================================
# ФОРМАТТЕРЫ СООБЩЕНИЙ - С ТЕКСТАМИ ИЗ sexual_module.py
# ============================================================================

class MessageFormatter:
    """Форматирование сообщений"""
    
    DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    @classmethod
    def get_invite_text(cls) -> str:
        """Текст приглашения - ЖЕСТКО ПО ТЗ, НЕ МЕНЯТЬ! (из sexual_module.py)"""
        return (
            "Есть одна штука.\n"
            "Определяет твой ночной тип личности.\n"
            "Я прошёл — совпало процентов на 90.\n"
            "{invite_url}\n\n"
            "Интересно, у тебя тоже?"
        )
    
    @classmethod
    def format_invite_message(cls, invite_url: str) -> str:
        """Форматирует сообщение с приглашением - из sexual_module.py"""
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        share_text = cls.get_invite_text().format(invite_url=invite_url)
        
        return f"""
{cls.DIVIDER}
🔞 <b>ВАША ССЫЛКА-ПРИГЛАШЕНИЕ ГОТОВА!</b>
{cls.DIVIDER}

🔗 <code>{invite_url}</code>

💬 <b>ТЕКСТ ДЛЯ ОТПРАВКИ ДРУГУ:</b>
<code>{share_text}</code>

✨ <b>СКОПИРУЙТЕ ТЕКСТ ЦЕЛИКОМ</b>
   ИЛИ НАЖМИТЕ КНОПКУ ОТПРАВКИ
{cls.DIVIDER}

🟢 АКТИВНО • ожидание
📅 {current_time}
{cls.DIVIDER}

🎯 Через 15 минут после теста
   вы увидите его 18+ профиль.
   То, что скрывается даже от близких.
{cls.DIVIDER}
"""
    
    @classmethod
    def format_results_screen(cls, profile: dict) -> str:
        """Экран результатов"""
        return f"""
🧠 ВАШ ПРОФИЛЬ ГОТОВ

📊 {profile.get('display_name', 'SA-5_INT')}

💬 ЦИТАТА:
«Я не ищу — я нахожу»

💔 СУТЬ ПРОБЛЕМЫ
Вам сложно просить о помощи, даже когда она нужна.
Вы привыкли справляться сами, но это истощает.

🛠 ИНСТРУМЕНТ
Сегодня: попросите кого-то о маленькой услуге.
Заметьте, что мир не рухнул.
"""
    
    @classmethod
    def format_intimate_profile(cls, profile: dict, user_name: str) -> str:
        """Интимный профиль пользователя - улучшенный из sexual_module.py"""
        message = f"""
{cls.DIVIDER}
🔞 <b>18+ ПРОФИЛЬ: {user_name}</b>
🧠 <b>ПРОФИЛЬ:</b> {profile.get('profile_type', 'SA-5_INT')}
{cls.DIVIDER}

{profile.get('description', '')}

<b>🔴 ВКЛЮЧАЕТ:</b>
"""
        sections = profile.get('sections', {})
        turns_on = sections.get('what_turns_on', {}).get('items', [])
        for item in turns_on[:3]:
            message += f"• {item[:100]}...\n" if len(item) > 100 else f"• {item}\n"
        
        message += f"""
<b>⚠️ ВЫКЛЮЧАЕТ:</b>
"""
        turns_off = sections.get('what_turns_off', {}).get('items', [])
        for item in turns_off[:2]:
            message += f"• {item[:100]}...\n" if len(item) > 100 else f"• {item}\n"
        
        erogenous = sections.get('erogenous_zone', {}).get('trigger', '')
        if erogenous:
            message += f"""
<b>🔴 ЭРОГЕННАЯ ЗОНА:</b>
{erogenous[:100]}...
"""
        
        ideal = sections.get('ideal_partner', {}).get('description', '')
        if ideal:
            message += f"""
<b>💞 ИДЕАЛЬНЫЙ ПАРТНЁР:</b>
{ideal[:200]}...
"""
        
        message += f"""
{cls.DIVIDER}
💞 <b>У КАЖДОГО ЕСТЬ ТАЙНЫ.</b>
🔓 <b>ВАШ КЛЮЧ К ПРАВДЕ:</b>

❶ Пригласите → 0₽
❷ Друг проходит тест (3 мин)
❸ Мы пришлём уведомление
❹ 99₽ = доступ к его 18+ профилю

⚠️ Только вы. Только правда. Без стыда.
{cls.DIVIDER}
"""
        return message
    
    @classmethod
    def format_invites_hub(cls, invites: List[Invitation], free_used: int, 
                          total_reflections: int) -> str:
        """Хаб Мои отражения"""
        message = f"""
{cls.DIVIDER}
🔍 <b>МОИ ПРИГЛАШЕНИЯ</b>
{cls.DIVIDER}

📊 <b>СТАТИСТИКА:</b>
   🔗 Всего ссылок: {len(invites)}
   ✨ Отражений: {total_reflections}
   💎 Бесплатных: {free_used}/{Config.FREE_FRIEND_LIMIT}
   🔓 Доступно: {max(0, Config.FREE_FRIEND_LIMIT - free_used)}

{cls.DIVIDER}
"""
        
        active = [i for i in invites if i.status == "active"]
        used = [i for i in invites if i.status == "used"]
        
        if active:
            message += "\n🟢 ЖДУТ ОТКЛИКА ✨\n"
            for inv in active[:3]:
                created = datetime.fromtimestamp(inv.created_at).strftime('%d.%m')
                days = int((datetime.now().timestamp() - inv.created_at) / 86400)
                message += f"   • {created} · ждёт {days}д\n"
        else:
            message += "\n✨ У вас пока нет активных приглашений\n"
        
        if used:
            message += f"\n✨ УЖЕ ОТРАЗИЛИСЬ — {len(used)}\n"
            for inv in used[:5]:
                friend_name = inv.used_by_name or "друг"
                friend_profile = inv.friend_profile or "SA-3_CON"
                used_date = datetime.fromtimestamp(inv.used_at or inv.created_at).strftime('%d.%m.%Y')
                keys = ""
                if inv.purchased_functions:
                    keys = f" · 🔑 {' '.join(inv.purchased_functions)}"
                
                access_icon = "🔓" if inv.access_paid else "💎" if inv.access_status == "free" else "🔒"
                
                message += f"\n   {access_icon} {friend_name}"
                message += f"\n   📊 {friend_profile} · {used_date}{keys}\n"
        
        message += f"""

{cls.DIVIDER}
💞 <b>Как только друг пройдёт тест —</b>
   вы увидите его имя и получите доступ к кнопкам 1F-4F.

<b>🔑 4F-КЛЮЧИ ({Config.FOUR_F_PRICE}₽/шт):</b>
• 🔥 1F — Как вызвать возбуждение
• 🏃 2F — Как пробудить голод/желание  
• 🧬 3F — Как обойти страх
• 🍽 4F — Как родить идею

⚠️ <i>Сейчас работает демо-режим для всех профилей</i>
{cls.DIVIDER}
"""
        return message
    
    @classmethod
    def format_friend_menu(cls, friend_name: str, friend_profile: str, 
                          purchased: List[str], access_status: str) -> str:
        """Меню профиля друга"""
        progress = len(purchased)
        progress_bar = "▓" * progress + "░" * (4 - progress)
        
        access_icon = "🔓" if access_status == "paid" else "💎" if access_status == "free" else "🔒"
        
        return f"""
{cls.DIVIDER}
{access_icon} <b>{friend_name}</b>
{cls.DIVIDER}

📊 <b>Профиль:</b> {friend_profile}
{'💎 Бесплатно' if access_status == 'free' else '💰 Куплен' if access_status == 'paid' else '🔒 Заблокирован'}

🔓 <b>РАЗГАДАНО:</b> {progress}/4 [{progress_bar}]
{cls.DIVIDER}
"""
    
    @classmethod
    def format_4f_menu(cls, friend_name: str, friend_profile: str, 
                      purchased: List[str]) -> str:
        """Меню 4F-ключей"""
        message = f"""
{cls.DIVIDER}
🧬 <b>4F-КЛЮЧИ ДЛЯ {friend_name}</b>
{cls.DIVIDER}

📊 <b>Профиль:</b> {friend_profile}
{'🔥 ХИТ ПРОДАЖ: 1F покупают в 2 раза чаще' if not purchased else ''}

"""
        keys = FourFKey.get_all()
        for code, key in keys.items():
            lock = "🔓" if code in purchased else "🔒"
            message += f"\n{lock} {key.emoji} <b>{key.title}</b>"
            message += f"\n└ {key.subtitle}\n"
        
        message += f"""
{cls.DIVIDER}
💰 <b>Цена:</b> {Config.FOUR_F_PRICE}₽ (тестовый режим)
{cls.DIVIDER}
"""
        return message
    
    @classmethod
    def format_4f_content(cls, key: FourFKey, content: Dict) -> str:
        """Контент 4F-ключа"""
        message = f"""
{cls.DIVIDER}
{key.emoji} <b>{key.title}</b>
{key.subtitle}
{cls.DIVIDER}

🎯 <b>ТРИГГЕР-ФРАЗЫ:</b>
"""
        for i, trigger in enumerate(content['triggers'][:3], 1):
            message += f"\n{i}. {trigger}"
        
        message += f"""

🧠 <b>ПСИХОЛОГИЧЕСКИЙ РАЗБОР:</b>
{content['analysis']}

📋 <b>ПРОТОКОЛ ПРИМЕНЕНИЯ:</b>
{content['protocol']}

{key.tag}
{cls.DIVIDER}
"""
        return message
    
    @classmethod
    def format_deeplink_invite(cls, inviter_name: str) -> str:
        """Текст для deep-link приглашения - из sexual_module.py"""
        return f"""
{cls.DIVIDER}
🎁 <b>Вас пригласил(а) {inviter_name}!</b>
{cls.DIVIDER}

Пройдите тест — и {inviter_name} сможет узнать 
ваши 18+ предпочтения и получить 4F-ключи к вашему профилю
(только если захочет и заплатит {Config.FOUR_F_PRICE}₽ за каждый ключ).

<i>Вы тоже сможете приглашать друзей 
и покупать 4F-ключи к их профилям.</i>

⏱ <b>Тест займёт всего 3 минуты</b>
🔒 Полная анонимность
💞 Только правда, без стыда

<b>🔑 Что такое 4F?</b>
• 1F 🔥 — Ключ возбуждения
• 2F 🏃 — Ключ голода/желания  
• 3F 🧬 — Ключ страха
• 4F 🍽 — Ключ идеи

{cls.DIVIDER}
🚀 <b>Начнём?</b>
"""

# ============================================================================
# КОНСТРУКТОРЫ КЛАВИАТУР - С КНОПКОЙ КОПИРОВАНИЯ ИЗ sexual_module.py
# ============================================================================

class KeyboardBuilder:
    """Построитель клавиатур"""
    
    @classmethod
    def results_screen(cls) -> InlineKeyboardMarkup:
        """Клавиатура экрана результатов"""
        keyboard = [
            [InlineKeyboardButton("🪞 Зеркало", callback_data="mirror")],
            [InlineKeyboardButton("📖 Полный", callback_data="full")],
            [InlineKeyboardButton("🔞 Интимный профиль", callback_data="sexual_profile")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @classmethod
    def sexual_profile(cls) -> InlineKeyboardMarkup:
        """Клавиатура интимного профиля"""
        keyboard = [
            [InlineKeyboardButton("🔞 СОЗДАТЬ ССЫЛКУ", callback_data="create_invite")],
            [InlineKeyboardButton("🔍 МОИ ПРИГЛАШЕНИЯ", callback_data="hub_profiles")],
            [InlineKeyboardButton("⬅️ К результатам", callback_data="back_to_results")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @classmethod
    def invite_created(cls, invite_url: str, invite_code: str, share_text: str) -> InlineKeyboardMarkup:
        """Клавиатура после создания приглашения - С КНОПКОЙ КОПИРОВАНИЯ! из sexual_module.py"""
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(invite_url)}&text={urllib.parse.quote(share_text)}"
        
        keyboard = [
            [
                InlineKeyboardButton("📤 Отправить другу", url=share_url),
                InlineKeyboardButton("📋 Копировать ссылку", callback_data=f"copy_invite_{invite_code}")
            ],
            [
                InlineKeyboardButton("🔍 Мои приглашения", callback_data="hub_profiles"),
                InlineKeyboardButton("⬅️ К профилю", callback_data="sexual_profile")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @classmethod
    def invites_hub(cls, invites: List[Invitation], return_context: Optional[dict] = None) -> InlineKeyboardMarkup:
        """Клавиатура хаба приглашений"""
        keyboard = []
        
        # Секция действий
        keyboard.append([
            InlineKeyboardButton("🔞 СОЗДАТЬ НОВОЕ ПРИГЛАШЕНИЕ", callback_data="create_invite")
        ])
        
        # Секция друзей с 4F-кнопками
        used = [i for i in invites if i.status == "used" and i.used_by_id]
        for inv in used[:5]:
            friend_name = inv.used_by_name or "друг"
            friend_profile = inv.friend_profile or "SA-3_CON"
            access_icon = "🔓" if inv.access_paid else "💎" if inv.access_status == "free" else "🔒"
            
            # Имя друга (некликабельно)
            keyboard.append([
                InlineKeyboardButton(f"{access_icon} {friend_name} · {friend_profile}", 
                                   callback_data="noop")
            ])
            
            # Ряд с кнопками 1F-4F
            row = []
            for f in ["1F", "2F", "3F", "4F"]:
                if f in inv.purchased_functions:
                    row.append(InlineKeyboardButton(
                        f"🔓 {f}",
                        callback_data=f"open_4f_{inv.invite_id}_{f}"
                    ))
                else:
                    row.append(InlineKeyboardButton(
                        f"{f} ({Config.FOUR_F_PRICE}₽)",
                        callback_data=f"buy_4f_{inv.used_by_id}_{f}"
                    ))
            keyboard.append(row)
            
            # Кнопка деталей
            keyboard.append([
                InlineKeyboardButton(
                    "📋 Детали профиля",
                    callback_data=f"friend_details_{inv.invite_id}"
                )
            ])
        
        # Секция навигации
        nav_row = []
        if return_context and return_context.get("from_state") in [2101, 2001]:  # SEXUAL_PROFILE, RESULTS_SCREEN
            nav_row.append(
                InlineKeyboardButton("⬅️ К ПРОФИЛЮ", callback_data="sexual_profile")
            )
        else:
            nav_row.append(
                InlineKeyboardButton("⬅️ НАЗАД", callback_data="back_from_hub")
            )
        keyboard.append(nav_row)
        
        return InlineKeyboardMarkup(keyboard)
    
    @classmethod
    def friend_menu(cls, friend_id: int, access_status: str) -> InlineKeyboardMarkup:
        """Клавиатура меню друга"""
        keyboard = []
        
        if access_status in ["free", "paid"]:
            keyboard.extend([
                [
                    InlineKeyboardButton("📊 Standart", callback_data=f"std_{friend_id}"),
                    InlineKeyboardButton("🔞 SEX", callback_data=f"int_{friend_id}")
                ],
                [
                    InlineKeyboardButton("🧬 4F", callback_data=f"4f_{friend_id}"),
                    InlineKeyboardButton("❓ Что это?", callback_data="4f_explain")
                ]
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(f"🔓 РАЗБЛОКИРОВАТЬ - {Config.FRIEND_ACCESS_PRICE}₽", 
                                   callback_data=f"pay_access_{friend_id}")
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔍 МОИ ПРИГЛАШЕНИЯ", callback_data="hub_profiles")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @classmethod
    def four_f_menu(cls, friend_id: int, purchased: List[str]) -> InlineKeyboardMarkup:
        """Клавиатура меню 4F-ключей"""
        keyboard = []
        
        keys = FourFKey.get_all()
        for code, key in keys.items():
            if code in purchased:
                keyboard.append([
                    InlineKeyboardButton(
                        f"{key.emoji} {code} - ОТКРЫТЬ",
                        callback_data=f"open_4f_{friend_id}_{code}"
                    )
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton(
                        f"{key.emoji} {code} - {Config.FOUR_F_PRICE}₽",
                        callback_data=f"buy_4f_{friend_id}_{code}"
                    )
                ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("❓ Что такое 4F?", callback_data="4f_explain"),
                InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")
            ],
            [InlineKeyboardButton("🔍 МОИ ПРИГЛАШЕНИЯ", callback_data="hub_profiles")]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @classmethod
    def deeplink_invite(cls) -> InlineKeyboardMarkup:
        """Клавиатура для deep-link приглашения"""
        keyboard = [
            [InlineKeyboardButton("🚀 Пройти тест", callback_data="start_test")]
        ]
        return InlineKeyboardMarkup(keyboard)

# ============================================================================
# СОСТОЯНИЯ CONVERSATION HANDLER
# ============================================================================

class States:
    """Централизованное управление состояниями"""
    
    # Хабы
    HUB_PROFILES = 1000
    
    # Основные потоки
    RESULTS_SCREEN = 2001
    SEXUAL_PROFILE = 2101
    INVITE_CREATE = 2102
    FRIEND_MENU = 2201
    FOUR_F_MENU = 2301
    FOUR_F_CONTENT = 2302
    FOUR_F_PURCHASE = 2303

# ============================================================================
# НАВИГАЦИЯ
# ============================================================================

class NavigationSystem:
    """Система управления навигацией"""
    
    def __init__(self):
        self.storage = Storage()
    
    async def navigate_to_hub(self, user_id: int, current_state: int, 
                             hub_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Переход в хаб с сохранением контекста"""
        return_context = {
            "from_state": current_state,
            "from_context": context.copy(),
            "timestamp": datetime.now().timestamp()
        }
        context[f"_return_{hub_id}"] = return_context
        return return_context
    
    async def return_from_hub(self, user_id: int, hub_id: str, 
                             context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Возврат из хаба"""
        return_context = context.pop(f"_return_{hub_id}", None)
        if return_context:
            context.update(return_context["from_context"])
        return return_context

# ============================================================================
# БАЗОВЫЙ ОБРАБОТЧИК
# ============================================================================

class BaseHandler:
    """Базовый класс для всех обработчиков"""
    
    def __init__(self):
        self.storage = Storage()
        self.navigation = NavigationSystem()
    
    async def get_or_create_session(self, update: Update) -> UserSession:
        """Получение или создание сессии"""
        user = update.effective_user
        user_id = user.id
        
        session = await self.storage.get_session(user_id)
        if not session:
            session = await self.storage.create_session(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name
            )
        
        return session
    
    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                          error: Exception, fallback_state: int):
        """Централизованная обработка ошибок"""
        logger.error("handler_error", 
                    error=str(error), 
                    user_id=update.effective_user.id,
                    exc_info=True)
        
        try:
            if update.callback_query:
                await update.callback_query.answer(
                    "❌ Произошла ошибка. Попробуйте позже.",
                    show_alert=True
                )
        except:
            pass
        
        return fallback_state

# ============================================================================
# ОБРАБОТЧИК ОСНОВНОГО ПОТОКА
# ============================================================================

class MainFlowHandler(BaseHandler):
    """Обработчик основного потока"""
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка /start"""
        session = await self.get_or_create_session(update)
        
        # Проверяем deep-link приглашение
        if context.args and context.args[0].startswith('sex_'):
            invite_id = context.args[0]
            invitation = await self.storage.get_invitation(invite_id)
            
            if invitation and invitation.is_valid():
                context.user_data["invite_code"] = invite_id
                context.user_data["inviter_id"] = invitation.creator_id
                
                # Получаем имя пригласившего
                inviter_session = await self.storage.get_session(invitation.creator_id)
                inviter_name = inviter_session.first_name if inviter_session else "друг"
                context.user_data["inviter_name"] = inviter_name
                
                # Показываем экран приглашения
                message = MessageFormatter.format_deeplink_invite(inviter_name)
                keyboard = KeyboardBuilder.deeplink_invite()
                
                await update.message.reply_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                return States.RESULTS_SCREEN
        
        # Инициализация тестовых данных
        if not session.invites:
            await self.storage.init_test_data(session.user_id)
        
        # Профиль пользователя
        context.user_data["profile"] = {
            "display_name": "SA-5_INT",
            "type_code": "SA",
            "level": 5,
            "dilts_code": "int"
        }
        
        return await self.show_results(update, context)
    
    async def show_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Экран результатов"""
        profile = context.user_data.get("profile", {})
        message = MessageFormatter.format_results_screen(profile)
        keyboard = KeyboardBuilder.results_screen()
        
        if update.callback_query:
            query = update.callback_query
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                message,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        
        return States.RESULTS_SCREEN

# ============================================================================
# ОБРАБОТЧИК ИНТИМНЫХ ПРОФИЛЕЙ - ИНТЕГРИРОВАННЫЙ ИЗ sexual_module.py
# ============================================================================

class SexualFlowHandler(BaseHandler):
    """Обработчик интимных профилей - ВСЯ ЛОГИКА ИЗ sexual_module.py"""
    
    async def show_my_sexual_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🔞 Мой интимный профиль - С ДИАГНОСТИКОЙ!"""
        query = update.callback_query
        await query.answer()
        
        # Загружаем профиль с диагностикой
        profile = await ProfileLoader.load_intimate_profile(debug=True)
        username = update.effective_user.first_name or "Пользователь"
        
        # Проверяем загрузку
        if not profile or profile == ProfileLoader._get_emergency_profile():
            logger.error("❌ Не удалось загрузить интимный профиль!")
            await query.answer("⚠️ Ошибка загрузки профиля", show_alert=True)
        
        message = MessageFormatter.format_intimate_profile(profile, username)
        keyboard = KeyboardBuilder.sexual_profile()
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        return States.SEXUAL_PROFILE
    
    async def create_invite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🔞 Создание приглашения - ТОЧНО ПО ТЗ ИЗ sexual_module.py"""
        query = update.callback_query
        await query.answer()
        
        session = await self.get_or_create_session(update)
        profile = context.user_data.get("profile", {})
        
        # Создаем приглашение в персистентном хранилище
        invitation = await self.storage.create_invitation(
            creator_id=session.user_id,
            creator_profile=profile.get('display_name', 'SA-5_INT')
        )
        
        invite_url = f"https://t.me/{Config.BOT_USERNAME}?start={invitation.invite_id}"
        
        # Форматируем сообщение
        message = MessageFormatter.format_invite_message(invite_url)
        share_text = MessageFormatter.get_invite_text().format(invite_url=invite_url)
        keyboard = KeyboardBuilder.invite_created(invite_url, invitation.invite_id, share_text)
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        return States.INVITE_CREATE
    
    async def copy_invite_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """📋 Обработчик кнопки копирования ссылки - ИЗ sexual_module.py"""
        query = update.callback_query
        invite_code = query.data.replace("copy_invite_", "")
        
        # Ищем ссылку в хранилище
        invitation = await self.storage.get_invitation(invite_code)
        
        if invitation:
            await query.answer("✅ Ссылка скопирована в буфер обмена!", show_alert=True)
        else:
            await query.answer("❌ Ссылка не найдена", show_alert=True)
        
        return States.INVITE_CREATE

# ============================================================================
# ОБРАБОТЧИК ХАБОВ
# ============================================================================

class HubHandler(BaseHandler):
    """Обработчик хабов"""
    
    async def show_profiles_hub(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🔍 Хаб Мои приглашения"""
        query = update.callback_query
        await query.answer()
        
        session = await self.get_or_create_session(update)
        invites = await self.storage.get_user_invites(session.user_id)
        
        # Статистика
        used = [i for i in invites if i.status == "used"]
        free_used = len([i for i in used if not i.access_paid])
        total_reflections = len(used)
        
        # Сохраняем контекст возврата
        return_context = await self.navigation.navigate_to_hub(
            user_id=session.user_id,
            current_state=context.user_data.get("_state", 0),
            hub_id="profiles_hub",
            context=context.user_data
        )
        
        message = MessageFormatter.format_invites_hub(
            invites, free_used, total_reflections
        )
        keyboard = KeyboardBuilder.invites_hub(invites, return_context)
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        return States.HUB_PROFILES
    
    async def back_from_hub(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """⬅️ Возврат из хаба"""
        query = update.callback_query
        await query.answer()
        
        session = await self.get_or_create_session(update)
        
        return_context = await self.navigation.return_from_hub(
            user_id=session.user_id,
            hub_id="profiles_hub",
            context=context.user_data
        )
        
        if return_context:
            from_state = return_context.get("from_state")
            
            if from_state == States.SEXUAL_PROFILE:
                return await SexualFlowHandler().show_my_sexual_profile(update, context)
            elif from_state == States.FRIEND_MENU:
                friend_id = return_context.get("from_context", {}).get("current_friend_id")
                if friend_id:
                    context.user_data["current_friend_id"] = friend_id
                    return await FriendFlowHandler().show_friend_menu(update, context)
        
        return await MainFlowHandler().show_results(update, context)
    
    async def friend_details_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """📋 Детали профиля друга - ИЗ sexual_module.py"""
        query = update.callback_query
        await query.answer()
        
        parts = query.data.split("_")
        if len(parts) < 3:
            await query.answer("❌ Неверный формат", show_alert=True)
            return States.HUB_PROFILES
        
        invite_code = parts[2]
        invitation = await self.storage.get_invitation(invite_code)
        
        if not invitation:
            await query.answer("❌ Приглашение не найдено", show_alert=True)
            return States.HUB_PROFILES
        
        friend_name = invitation.used_by_name or "Друг"
        friend_profile = invitation.friend_profile or "SA-4_EXP"
        purchased = invitation.purchased_functions
        
        text = f"""
{MessageFormatter.DIVIDER}
👤 <b>ПРОФИЛЬ ДРУГА</b>
{MessageFormatter.DIVIDER}

<b>Имя:</b> {friend_name}
<b>Общий профиль:</b> {friend_profile}
<b>Интимный профиль:</b> sa_5_int (тестовая заглушка)

<b>🔑 Купленные ключи:</b>
"""
        if purchased:
            for f in purchased:
                text += f"  • {f}\n"
        else:
            text += "  • Нет купленных ключей\n"
        
        text += f"""
{MessageFormatter.DIVIDER}
💎 <b>4F-ключи — {Config.FOUR_F_PRICE}₽/шт</b>
• 1F 🔥: Ключ возбуждения
• 2F 🏃: Ключ голода/желания
• 3F 🧬: Ключ страха
• 4F 🍽: Ключ идеи

⚠️ <i>Сейчас все ключи работают в демо-режиме
для профиля SA-4_CAP</i>
{MessageFormatter.DIVIDER}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ К списку приглашений", callback_data="hub_profiles")]
        ])
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        return States.HUB_PROFILES

# ============================================================================
# ОБРАБОТЧИК ДРУЗЕЙ
# ============================================================================

class FriendFlowHandler(BaseHandler):
    """Обработчик профилей друзей"""
    
    async def show_friend_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """👤 Меню профиля друга"""
        query = update.callback_query
        await query.answer()
        
        session = await self.get_or_create_session(update)
        friend_data = context.user_data.get("current_friend_data")
        
        if not friend_data:
            friend_id = int(query.data.split("_")[1])
            friend_data_dict = await self.storage.get_friend_data(session.user_id, friend_id)
            
            if not friend_data_dict:
                await query.answer("❌ Друг не найден", show_alert=True)
                return States.HUB_PROFILES
            
            friend_data = {
                "friend_id": friend_id,
                "friend_name": friend_data_dict.used_by_name,
                "friend_profile": friend_data_dict.friend_profile,
                "access_status": friend_data_dict.access_status,
                "purchased_functions": friend_data_dict.purchased_functions,
                "access_paid": friend_data_dict.access_paid
            }
            context.user_data["current_friend_id"] = friend_id
            context.user_data["current_friend_data"] = friend_data
        
        friend_name = friend_data.get("friend_name", "друг")
        friend_profile = friend_data.get("friend_profile", "SA-3_CON")
        purchased = friend_data.get("purchased_functions", [])
        access_status = friend_data.get("access_status", "locked")
        
        # Проверяем бесплатный доступ
        if access_status == "locked" and not friend_data.get("access_paid"):
            free_used = len([i for i in await self.storage.get_user_invites(session.user_id) 
                           if i.status == "used" and not i.access_paid])
            if free_used < Config.FREE_FRIEND_LIMIT:
                access_status = "free"
                friend_data["access_status"] = "free"
        
        message = MessageFormatter.format_friend_menu(
            friend_name, friend_profile, purchased, access_status
        )
        keyboard = KeyboardBuilder.friend_menu(friend_data["friend_id"], access_status)
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        return States.FRIEND_MENU
    
    async def show_standard_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """📊 Стандартный профиль друга"""
        query = update.callback_query
        await query.answer()
        
        friend_data = context.user_data.get("current_friend_data")
        if not friend_data:
            friend_id = int(query.data.split("_")[1])
            friend_data = {"friend_id": friend_id, "friend_name": "друг"}
        
        friend_name = friend_data.get("friend_name", "друг")
        
        message = f"""
{MessageFormatter.DIVIDER}
📊 <b>{friend_name}</b>
{MessageFormatter.DIVIDER}

🧠 <b>Архетип:</b> Автономный стратег

💬 <b>Цитата:</b>
«Я не ищу одобрения — я ищу эффективность.»

💔 <b>Суть проблемы:</b>
Вам сложно делегировать. Вы уверены: «Хочешь сделать хорошо — сделай сам».

🛠 <b>Инструмент:</b>
Сегодня: передайте кому-то одну задачу ПОЛНОСТЬЮ.

🚀 <b>Следующие шаги:</b>
Исследуйте баланс между автономией и доверием.
{MessageFormatter.DIVIDER}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 МОИ ПРИГЛАШЕНИЯ", callback_data="hub_profiles")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_data['friend_id']}")]
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        return States.FRIEND_MENU
    
    async def show_intimate_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🔞 Интимный профиль друга (заглушка)"""
        query = update.callback_query
        await query.answer()
        
        friend_data = context.user_data.get("current_friend_data")
        if not friend_data:
            friend_id = int(query.data.split("_")[1])
            friend_data = {"friend_id": friend_id, "friend_name": "друг"}
        
        friend_name = friend_data.get("friend_name", "друг")
        
        message = f"""
{MessageFormatter.DIVIDER}
🔞 <b>ИНТИМНЫЙ ПРОФИЛЬ ДРУГА</b>
{MessageFormatter.DIVIDER}

👤 <b>{friend_name}</b>

📊 <b>Тип:</b> SA-5_INT (тестовый)
🧠 <b>Архетип:</b> ЦЕРЕМОНИАЛЬНЫЙ

💬 <b>ЦИТАТА:</b>
«{friend_name}, со мной не скучно. Со мной — вкусно.»

⚠️ <b>ТЕСТОВЫЙ РЕЖИМ</b>

Это демо-профиль на основе SA-5_INT.
В реальном режиме здесь будут персональные данные.

✅ <b>Что появится в боевом режиме:</b>
   • Его реальные триггеры
   • Индивидуальные сценарии
   • Точные эрогенные зоны
   • Секретные желания

💎 <b>Купите полный доступ за {Config.FRIEND_ACCESS_PRICE}₽</b>
{MessageFormatter.DIVIDER}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 МОИ ПРИГЛАШЕНИЯ", callback_data="hub_profiles")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_data['friend_id']}")]
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        return States.FRIEND_MENU

# ============================================================================
# ОБРАБОТЧИК 4F-КЛЮЧЕЙ
# ============================================================================

class FourFFlowHandler(BaseHandler):
    """Обработчик 4F-ключей"""
    
    async def show_four_f_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🧬 Меню 4F-ключей"""
        query = update.callback_query
        await query.answer()
        
        session = await self.get_or_create_session(update)
        friend_data = context.user_data.get("current_friend_data")
        
        if not friend_data:
            friend_id = int(query.data.split("_")[1])
            friend_data_dict = await self.storage.get_friend_data(session.user_id, friend_id)
            
            if not friend_data_dict:
                await query.answer("❌ Друг не найден", show_alert=True)
                return States.HUB_PROFILES
            
            friend_data = {
                "friend_id": friend_id,
                "friend_name": friend_data_dict.used_by_name,
                "friend_profile": friend_data_dict.friend_profile,
                "purchased_functions": friend_data_dict.purchased_functions
            }
            context.user_data["current_friend_id"] = friend_id
            context.user_data["current_friend_data"] = friend_data
        
        friend_name = friend_data.get("friend_name", "друг")
        friend_profile = friend_data.get("friend_profile", "SA-3_CON")
        purchased = friend_data.get("purchased_functions", [])
        
        message = MessageFormatter.format_4f_menu(friend_name, friend_profile, purchased)
        keyboard = KeyboardBuilder.four_f_menu(friend_data["friend_id"], purchased)
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        return States.FOUR_F_MENU
    
    async def buy_four_f_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """💰 Покупка 4F-ключа"""
        query = update.callback_query
        await query.answer("💰 Создаю счёт...")
        
        try:
            session = await self.get_or_create_session(update)
            parts = query.data.split("_")
            friend_id = int(parts[2])
            key_code = parts[3]
            
            key = FourFKey.get_all()[key_code]
            
            message = f"""
{MessageFormatter.DIVIDER}
{key.emoji} <b>{key.title}</b>
{key.subtitle}
{MessageFormatter.DIVIDER}

{key.description}

💰 <b>Цена:</b> {key.price}₽ (тестовый режим)
{MessageFormatter.DIVIDER}
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 ОПЛАТИТЬ 1₽", 
                                    callback_data=f"process_payment_4f_{friend_id}_{key_code}")],
                [InlineKeyboardButton("🔍 МОИ ПРИГЛАШЕНИЯ", callback_data="hub_profiles")],
                [InlineKeyboardButton("⬅️ Назад", callback_data=f"4f_{friend_id}")]
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            return States.FOUR_F_PURCHASE
            
        except Exception as e:
            return await self.handle_error(update, context, e, States.FOUR_F_MENU)
    
    async def open_four_f_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🔓 Открыть 4F-ключ"""
        query = update.callback_query
        await query.answer("🔓 Загружаю ключ...")
        
        try:
            parts = query.data.split("_")
            
            if len(parts) >= 4:
                # open_4f_{friend_id}_{key_code}
                friend_id = int(parts[2])
                key_code = parts[3]
                
                # Получаем данные друга
                session = await self.get_or_create_session(update)
                friend_data = await self.storage.get_friend_data(session.user_id, friend_id)
                
                if not friend_data:
                    await query.answer("❌ Друг не найден", show_alert=True)
                    return States.HUB_PROFILES
                
                friend_name = friend_data.used_by_name or "Друг"
                
                # Добавляем ключ в купленные
                await self.storage.purchase_4f_key(session.user_id, friend_id, key_code)
                
                # Показываем ключ
                key = FourFKey.get_all()[key_code]
                content = key.get_content()
                message = MessageFormatter.format_4f_content(key, content)
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ К списку приглашений", callback_data="hub_profiles")],
                    [InlineKeyboardButton("🔒 Купить еще", callback_data=f"4f_{friend_id}")]
                ])
                
                await query.edit_message_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                
                return States.FOUR_F_CONTENT
            
            await query.answer("❌ Неверный формат", show_alert=True)
            return States.HUB_PROFILES
            
        except Exception as e:
            return await self.handle_error(update, context, e, States.FOUR_F_MENU)
    
    async def four_f_explanation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """📘 Что такое 4F?"""
        query = update.callback_query
        await query.answer()
        
        message = f"""
{MessageFormatter.DIVIDER}
📘 <b>ЧТО ТАКОЕ 4F-КЛЮЧИ?</b>
{MessageFormatter.DIVIDER}

🧬 4F — это система доступа к состояниям человека.
Четыре базовые реакции, зашитые в подкорке.
Ключи к пониманию глубинных состояний другого человека.

1F 🔥 <b>НАПАДЕНИЕ / ЯРОСТЬ</b>
└ Как гасить агрессию и не нарваться
└ Ключ к управлению гневом

2F 🏃 <b>БЕГСТВО / СТРАХ</b>
└ Чего он боится на самом деле
└ Ключ к преодолению страхов

3F 🧬 <b>СЕКС / ЖЕЛАНИЕ</b>
└ Что включает его режим «хочу»
└ Ключ к желанию и страсти

4F 🍽 <b>ПОГЛОЩЕНИЕ / ДЕНЬГИ</b>
└ Какие идеи прорастают в его голове
└ Ключ к деньгам и идеям

💰 <b>Цена:</b> {Config.FOUR_F_PRICE}₽ (тестовый режим)
{MessageFormatter.DIVIDER}
"""
        
        keyboard = []
        friend_id = context.user_data.get("current_friend_id")
        
        if friend_id:
            keyboard.append([
                InlineKeyboardButton("⬅️ Назад", callback_data=f"friend_{friend_id}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("🔍 МОИ ПРИГЛАШЕНИЯ", callback_data="hub_profiles")
            ])
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        return States.FOUR_F_MENU

# ============================================================================
# ОБРАБОТЧИК ПЛАТЕЖЕЙ (МОК-РЕЖИМ)
# ============================================================================

class PaymentHandler(BaseHandler):
    """Обработчик платежей (мок-режим)"""
    
    def generate_payment_id(self, prefix: str, user_id: int) -> str:
        """Генерация ID платежа"""
        timestamp = int(datetime.now().timestamp())
        random_str = uuid.uuid4().hex[:8]
        user_suffix = str(user_id)[-6:]
        return f"{prefix}_{timestamp}_{random_str}_{user_suffix}"
    
    async def process_four_f_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """💳 Обработка платежа за 4F-ключ (мок)"""
        query = update.callback_query
        await query.answer("💳 Имитация платежа...")
        
        try:
            session = await self.get_or_create_session(update)
            parts = query.data.split("_")
            friend_id = int(parts[3])
            key_code = parts[4]
            
            # Мок-успешный платеж
            await self.storage.purchase_4f_key(session.user_id, friend_id, key_code)
            
            await query.answer(f"✅ Ключ {key_code} разблокирован! (тестовый режим)", show_alert=True)
            
            # Открываем ключ
            query.data = f"open_4f_{friend_id}_{key_code}"
            return await FourFFlowHandler().open_four_f_key(update, context)
            
        except Exception as e:
            return await self.handle_error(update, context, e, States.FOUR_F_MENU)

# ============================================================================
# ГЛОБАЛЬНЫЙ ДИСПЕТЧЕР
# ============================================================================

class CallbackDispatcher:
    """Глобальный диспетчер callback'ов"""
    
    def __init__(self):
        self.main = MainFlowHandler()
        self.sexual = SexualFlowHandler()
        self.hub = HubHandler()
        self.friends = FriendFlowHandler()
        self.four_f = FourFFlowHandler()
        self.payment = PaymentHandler()
        
        self.handlers = {
            # Основные
            "start": self.main.start,
            "back_to_results": self.main.show_results,
            
            # Интимные профили
            "sexual_profile": self.sexual.show_my_sexual_profile,
            "create_invite": self.sexual.create_invite,
            "copy_invite_": self.sexual.copy_invite_callback,
            
            # Хабы
            "hub_profiles": self.hub.show_profiles_hub,
            "back_from_hub": self.hub.back_from_hub,
            "friend_details_": self.hub.friend_details_callback,
            
            # Друзья
            "friend_": self.friends.show_friend_menu,
            "std_": self.friends.show_standard_profile,
            "int_": self.friends.show_intimate_profile,
            
            # 4F
            "4f_": self.four_f.show_four_f_menu,
            "buy_4f_": self.four_f.buy_four_f_key,
            "open_4f_": self.four_f.open_four_f_key,
            "4f_explain": self.four_f.four_f_explanation,
            
            # Платежи
            "process_payment_4f_": self.payment.process_four_f_payment,
            
            # Заглушки
            "mirror": self._dummy,
            "full": self._dummy,
            "noop": self._dummy,
            "start_test": self._dummy,
        }
    
    async def _dummy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Заглушка для некликабельных кнопок"""
        query = update.callback_query
        await query.answer("✅ Демо-режим")
        return States.RESULTS_SCREEN
    
    async def dispatch(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Маршрутизация callback'ов"""
        query = update.callback_query
        pattern = query.data
        
        logger.info("callback_received", 
                   user_id=update.effective_user.id,
                   pattern=pattern)
        
        # Точное совпадение
        if pattern in self.handlers:
            return await self.handlers[pattern](update, context)
        
        # Префиксное совпадение
        for prefix, handler in self.handlers.items():
            if pattern.startswith(prefix):
                return await handler(update, context)
        
        # По умолчанию
        logger.warning("no_handler_found", pattern=pattern)
        await query.answer("✅ Демо-режим")
        return await self.main.show_results(update, context)

# ============================================================================
# WEBHOOK-СЕРВЕР ДЛЯ RENDER
# ============================================================================

class WebhookBot:
    """Бот с webhook-архитектурой для Render"""
    
    def __init__(self):
        from flask import Flask, request, jsonify
        self.flask_app = Flask(__name__)
        self.dispatcher = CallbackDispatcher()
        self.application = None
        self._setup_routes()
    
    def _setup_routes(self):
        """Настройка маршрутов Flask"""
        
        @self.flask_app.route(Config.WEBHOOK_PATH, methods=['POST'])
        async def webhook():
            """Обработка входящих обновлений"""
            if request.method == "POST":
                update_data = request.get_json()
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    await self.process_update(update_data)
                    return {"ok": True}
                except Exception as e:
                    logger.error("webhook_error", error=str(e), exc_info=True)
                    return {"ok": False, "error": str(e)}, 500
                finally:
                    loop.close()
            
            return {"ok": False}, 405
        
        @self.flask_app.route('/health', methods=['GET'])
        def health():
            """Health check для Render"""
            return {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "bot": Config.BOT_USERNAME
            }
        
        @self.flask_app.route('/', methods=['GET'])
        def index():
            """Корневой маршрут"""
            return {
                "name": "Intimate Profiles Bot",
                "version": "12.0",
                "status": "running",
                "webhook": Config.get_webhook_url()
            }
    
    async def process_update(self, update_data: dict):
        """Обработка одного обновления"""
        if not self.application:
            await self._setup_application()
        
        update = Update.de_json(update_data, self.application.bot)
        
        if update.callback_query:
            context = ContextTypes.DEFAULT_TYPE(self.application)
            context.user_data.clear()
            await self.dispatcher.dispatch(update, context)
        else:
            await self.application.process_update(update)
    
    async def _setup_application(self):
        """Настройка приложения"""
        builder = Application.builder()
        builder.token(Config.TELEGRAM_TOKEN)
        builder.job_queue(None)
        
        self.application = builder.build()
        
        # Добавляем ConversationHandler
        conv_handler = self._create_conversation_handler()
        self.application.add_handler(conv_handler)
    
    def _create_conversation_handler(self) -> ConversationHandler:
        """Создание ConversationHandler"""
        return ConversationHandler(
            entry_points=[
                CommandHandler('start', self.dispatcher.dispatch),
                CallbackQueryHandler(self.dispatcher.dispatch)
            ],
            states={
                state: [CallbackQueryHandler(self.dispatcher.dispatch)] 
                for state in [
                    States.RESULTS_SCREEN,
                    States.SEXUAL_PROFILE,
                    States.INVITE_CREATE,
                    States.HUB_PROFILES,
                    States.FRIEND_MENU,
                    States.FOUR_F_MENU,
                    States.FOUR_F_CONTENT,
                    States.FOUR_F_PURCHASE,
                ]
            },
            fallbacks=[
                CommandHandler('start', self.dispatcher.dispatch),
                CallbackQueryHandler(self.dispatcher.dispatch)
            ],
            name="intimate_bot_v12",
            persistent=False,
            per_chat=False,
            per_user=True,
            per_message=False
        )
    
    async def set_webhook(self):
        """Установка webhook"""
        webhook_url = Config.get_webhook_url()
        if not webhook_url:
            logger.error("WEBHOOK_URL not configured")
            return False
        
        async with Application.builder().token(Config.TELEGRAM_TOKEN).build() as app:
            try:
                await app.bot.set_webhook(
                    url=webhook_url,
                    allowed_updates=["message", "callback_query"],
                    drop_pending_updates=True
                )
                webhook_info = await app.bot.get_webhook_info()
                logger.info("webhook_set", url=webhook_info.url)
                return True
            except Exception as e:
                logger.error("webhook_set_failed", error=str(e))
                return False
    
    def start(self):
        """Запуск webhook-сервера"""
        print("\n" + "="*70)
        print("🔞 ИНТИМНЫЕ ПРОФИЛИ И 4F-КЛЮЧИ v12.0")
        print("="*70)
        print("🚀 РЕЖИМ: WEBHOOK (ПРОДАКШН)")
        print(f"📁 Корень проекта: {PROJECT_ROOT}")
        print(f"🌐 Webhook URL: {Config.get_webhook_url()}")
        print(f"🔌 Порт: {Config.PORT}")
        print("="*70)
        
        # Устанавливаем webhook
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            success = loop.run_until_complete(self.set_webhook())
            if not success:
                print("❌ НЕ УДАЛОСЬ УСТАНОВИТЬ WEBHOOK!")
                return
            print("✅ Webhook установлен успешно")
        finally:
            loop.close()
        
        # Запускаем Flask
        self.flask_app.run(
            host='0.0.0.0',
            port=Config.PORT,
            debug=False,
            threaded=True
        )

# ============================================================================
# ТЕСТОВЫЙ ЗАГРУЗЧИК - ИЗ sexual_module.py
# ============================================================================

async def test_profile_loader():
    """Тестирование загрузчика профилей"""
    print("\n" + "🚀"*50)
    print("🚀 ТЕСТИРОВАНИЕ ЗАГРУЗЧИКА ИНТИМНОГО ПРОФИЛЯ")
    print("🚀"*50 + "\n")
    
    profile = await ProfileLoader.load_intimate_profile(debug=True, force_reload=True)
    
    if profile and profile != ProfileLoader._get_emergency_profile():
        print("\n✅ ТЕСТ УСПЕШЕН! Профиль загружен.")
        print(f"📊 Тип: {profile.get('profile_type')}")
        print(f"🧠 Архетип: {profile.get('archetype')}")
        sections = profile.get('sections', {})
        print(f"📋 Секций: {len(sections)}")
        return True
    else:
        print("\n❌ ТЕСТ ПРОВАЛЕН! Профиль не загружен.")
        return False

# ============================================================================
# ЛОКАЛЬНЫЙ ЗАПУСК (POLLING)
# ============================================================================

async def polling_main():
    """Запуск в режиме polling для локальной разработки"""
    print("\n" + "="*70)
    print("🔞 ИНТИМНЫЕ ПРОФИЛИ И 4F-КЛЮЧИ v12.0")
    print("="*70)
    print("🚀 РЕЖИМ: POLLING (ЛОКАЛЬНАЯ РАЗРАБОТКА)")
    print("="*70)
    
    if not Config.TELEGRAM_TOKEN:
        print("\n❌ ОШИБКА: Укажите TELEGRAM_BOT_TOKEN!")
        return
    
    # Создаем приложение
    builder = Application.builder()
    builder.token(Config.TELEGRAM_TOKEN)
    builder.job_queue(None)
    
    app = builder.build()
    dispatcher = CallbackDispatcher()
    
    # Добавляем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', dispatcher.dispatch),
            CallbackQueryHandler(dispatcher.dispatch)
        ],
        states={
            state: [CallbackQueryHandler(dispatcher.dispatch)] 
            for state in [
                States.RESULTS_SCREEN,
                States.SEXUAL_PROFILE,
                States.INVITE_CREATE,
                States.HUB_PROFILES,
                States.FRIEND_MENU,
                States.FOUR_F_MENU,
                States.FOUR_F_CONTENT,
                States.FOUR_F_PURCHASE,
            ]
        },
        fallbacks=[
            CommandHandler('start', dispatcher.dispatch),
            CallbackQueryHandler(dispatcher.dispatch)
        ],
        name="intimate_bot_v12_polling",
        persistent=False
    )
    
    app.add_handler(conv_handler)
    
    # Запускаем с обработкой сигналов
    stop_event = asyncio.Event()
    
    def signal_handler():
        logger.info("⏳ Получен сигнал остановки...")
        stop_event.set()
    
    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)
    
    try:
        await app.initialize()
        await app.updater.start_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
            error_callback=lambda e: logger.error(f"Polling error: {e}")
        )
        await app.start()
        
        logger.info("🚀 Бот запущен в polling режиме")
        print("="*70)
        
        await stop_event.wait()
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
    finally:
        logger.info("⏳ Останавливаем бота...")
        await asyncio.sleep(0.5)
        
        if app.updater.running:
            await app.updater.stop()
        
        await app.stop()
        await app.shutdown()
        
        logger.info("✅ Бот остановлен корректно")

# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

def main():
    """Главная функция запуска"""
    
    if Config.is_render():
        # На Render - запускаем webhook
        bot = WebhookBot()
        bot.start()
    else:
        # Локально - запускаем polling
        try:
            asyncio.run(polling_main())
        except KeyboardInterrupt:
            print("\n👋 Бот остановлен пользователем")
        except Exception as e:
            print(f"\n❌ Фатальная ошибка: {e}")
            logger.error("fatal_error", exc_info=True)
            sys.exit(1)

# ============================================================================
# ЗАПУСК ТЕСТА ПРИ ПРЯМОМ ВЫПОЛНЕНИИ
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Только тест загрузчика
        asyncio.run(test_profile_loader())
    else:
        # Запуск бота
        main()
