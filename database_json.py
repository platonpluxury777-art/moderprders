import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any

DATA_DIR = "data"

# Пути к файлам
FILES = {
    "users": os.path.join(DATA_DIR, "users.json"),
    "warn_history": os.path.join(DATA_DIR, "warn_history.json"),
    "roles": os.path.join(DATA_DIR, "roles.json"),
    "user_roles": os.path.join(DATA_DIR, "user_roles.json"),
    "filters": os.path.join(DATA_DIR, "filters.json"),
    "tickets": os.path.join(DATA_DIR, "tickets.json"),
    "chat_settings": os.path.join(DATA_DIR, "chat_settings.json"),
}

# Данные в памяти
_data: Dict[str, Any] = {
    "users": {},
    "warn_history": [],
    "roles": {},
    "user_roles": {},
    "filters": {},
    "tickets": [],
    "chat_settings": {},
}


def init_db():
    """Создаёт папку и файлы, загружает данные в память"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Создаём файлы если их нет
    for key, path in FILES.items():
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({} if key not in ["warn_history", "tickets"] else [], f, ensure_ascii=False, indent=2)
    
    # Загружаем всё в память
    load_all()
    
    # Дефолтные роли
    if "admin" not in _data["roles"]:
        _data["roles"]["admin"] = "all"
    if "moder" not in _data["roles"]:
        _data["roles"]["moder"] = "mute,unmute,ban,unban,kick,warn,unwarn,delete,cleanup,pin,unpin"
    if "helper" not in _data["roles"]:
        _data["roles"]["helper"] = "warn,delete,mute"
    save_file("roles")


def load_all():
    """Загружает все JSON-файлы в память"""
    for key, path in FILES.items():
        try:
            with open(path, "r", encoding="utf-8") as f:
                _data[key] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            _data[key] = {} if key not in ["warn_history", "tickets"] else []


def save_file(key: str):
    """Сохраняет конкретный файл"""
    with open(FILES[key], "w", encoding="utf-8") as f:
        json.dump(_data[key], f, ensure_ascii=False, indent=2)


# ==================== USERS ====================

def get_user(user_id: int) -> Optional[Dict]:
    """Получить пользователя по ID"""
    return _data["users"].get(str(user_id))


def create_user(user_id: int, username: str = "", first_name: str = "") -> Dict:
    """Создать или вернуть существующего пользователя"""
    uid = str(user_id)
    if uid not in _data["users"]:
        _data["users"][uid] = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "balance": 0,
            "warns": 0,
            "is_banned": False,
            "is_muted": False,
            "mute_until": 0,
            "last_daily": "",
            "last_bonus": "",
            "last_work": "",
        }
        save_file("users")
    return _data["users"][uid]


def update_user(user_id: int, **kwargs):
    """Обновить поля пользователя"""
    uid = str(user_id)
    if uid in _data["users"]:
        _data["users"][uid].update(kwargs)
        save_file("users")


def add_balance(user_id: int, amount: int):
    """Добавить к балансу"""
    uid = str(user_id)
    if uid in _data["users"]:
        _data["users"][uid]["balance"] += amount
        save_file("users")


def get_top_users(limit: int = 10) -> List[Dict]:
    """Топ пользователей по балансу"""
    users_list = list(_data["users"].values())
    users_list.sort(key=lambda x: x["balance"], reverse=True)
    return users_list[:limit]


# ==================== WARNS ====================

def add_warn(user_id: int, admin_id: int, reason: str = "", warn_type: str = "warn") -> int:
    """Добавить варн, возвращает общее количество варнов"""
    warn = {
        "id": len(_data["warn_history"]) + 1,
        "user_id": user_id,
        "admin_id": admin_id,
        "reason": reason,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "warn_type": warn_type,
    }
    _data["warn_history"].append(warn)
    
    uid = str(user_id)
    if uid in _data["users"]:
        _data["users"][uid]["warns"] += 1
    else:
        create_user(user_id)
        _data["users"][uid]["warns"] = 1
    
    save_file("warn_history")
    save_file("users")
    return _data["users"][uid]["warns"]


def remove_warn(user_id: int, warn_id: int = None) -> bool:
    """Снять варн. Если warn_id не указан, снимает последний"""
    global _data
    user_warns = [w for w in _data["warn_history"] if w["user_id"] == user_id]
    if not user_warns:
        return False
    
    if warn_id:
        target = next((w for w in user_warns if w["id"] == warn_id), None)
        if target:
            _data["warn_history"].remove(target)
    else:
        _data["warn_history"].remove(user_warns[-1])
    
    uid = str(user_id)
    if uid in _data["users"] and _data["users"][uid]["warns"] > 0:
        _data["users"][uid]["warns"] -= 1
    
    save_file("warn_history")
    save_file("users")
    return True


def get_warns(user_id: int) -> List[Dict]:
    """Получить все варны пользователя"""
    return [w for w in _data["warn_history"] if w["user_id"] == user_id]


def get_warn_by_id(warn_id: int) -> Optional[Dict]:
    """Получить варн по ID"""
    for w in _data["warn_history"]:
        if w["id"] == warn_id:
            return w
    return None


# ==================== ROLES ====================

def get_role_permissions(role_name: str) -> str:
    """Получить права роли"""
    return _data["roles"].get(role_name, "")


def add_user_role(user_id: int, role_name: str):
    """Выдать роль пользователю"""
    uid = str(user_id)
    if uid not in _data["user_roles"]:
        _data["user_roles"][uid] = []
    if role_name not in _data["user_roles"][uid]:
        _data["user_roles"][uid].append(role_name)
        save_file("user_roles")


def remove_user_role(user_id: int, role_name: str):
    """Снять роль с пользователя"""
    uid = str(user_id)
    if uid in _data["user_roles"] and role_name in _data["user_roles"][uid]:
        _data["user_roles"][uid].remove(role_name)
        save_file("user_roles")


def get_user_roles(user_id: int) -> List[str]:
    """Получить роли пользователя"""
    return _data["user_roles"].get(str(user_id), [])


def has_permission(user_id: int, permission: str) -> bool:
    """Проверить, есть ли у пользователя право"""
    if user_id in ADMIN_IDS:
        return True
    roles = get_user_roles(user_id)
    for role in roles:
        perms = get_role_permissions(role)
        if perms == "all" or permission in perms.split(","):
            return True
    return False


def get_staff_list() -> List[Dict]:
    """Список всех пользователей с ролями"""
    staff = []
    for uid, roles in _data["user_roles"].items():
        if roles:
            user = get_user(int(uid))
            staff.append({
                "user_id": int(uid),
                "username": user["username"] if user else "",
                "first_name": user["first_name"] if user else "",
                "roles": roles,
            })
    return staff


# ==================== FILTERS ====================

def add_filter_word(word: str):
    """Добавить слово в фильтр"""
    _data["filters"][word.lower()] = True
    save_file("filters")


def remove_filter_word(word: str) -> bool:
    """Удалить слово из фильтра"""
    word = word.lower()
    if word in _data["filters"]:
        del _data["filters"][word]
        save_file("filters")
        return True
    return False


def get_filter_words() -> List[str]:
    """Список всех запрещённых слов"""
    return list(_data["filters"].keys())


def check_message_for_filters(text: str) -> Optional[str]:
    """Проверить текст на запрещённые слова. Возвращает найденное слово или None"""
    text_lower = text.lower()
    for word in _data["filters"]:
        if word in text_lower:
            return word
    return None


# ==================== TICKETS ====================

def create_ticket(user_id: int, subject: str) -> int:
    """Создать тикет, возвращает его ID"""
    ticket = {
        "id": len(_data["tickets"]) + 1,
        "user_id": user_id,
        "subject": subject,
        "status": "open",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _data["tickets"].append(ticket)
    save_file("tickets")
    return ticket["id"]


def get_ticket(ticket_id: int) -> Optional[Dict]:
    """Получить тикет по ID"""
    for t in _data["tickets"]:
        if t["id"] == ticket_id:
            return t
    return None


def get_open_tickets() -> List[Dict]:
    """Список открытых тикетов"""
    return [t for t in _data["tickets"] if t["status"] == "open"]


def close_ticket(ticket_id: int) -> bool:
    """Закрыть тикет"""
    ticket = get_ticket(ticket_id)
    if ticket:
        ticket["status"] = "closed"
        save_file("tickets")
        return True
    return False


# ==================== CHAT SETTINGS ====================

def get_chat_setting(chat_id: int, key: str, default: str = "") -> str:
    """Получить настройку чата"""
    chat = _data["chat_settings"].get(str(chat_id), {})
    return chat.get(key, default)


def set_chat_setting(chat_id: int, key: str, value: str):
    """Установить настройку чата"""
    cid = str(chat_id)
    if cid not in _data["chat_settings"]:
        _data["chat_settings"][cid] = {}
    _data["chat_settings"][cid][key] = value
    save_file("chat_settings")


# Импорт конфига для has_permission
from config import ADMIN_IDS