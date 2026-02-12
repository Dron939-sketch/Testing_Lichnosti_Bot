#!/bin/bash

echo "🚀 СОЗДАНИЕ default.json ФАЙЛОВ ДЛЯ 4F И 18+"

# 1. 4F/default.json для каждой функции
mkdir -p профили/4F/{1F,2F,3F,4F}

# 1F
cat > профили/4F/1F/default.json << 'EOF'
{
  "profile_key": "default",
  "function": "1F",
  "function_name": "🔥 КЛЮЧ ВОЗБУЖДЕНИЯ",
  "category": "reptile",
  "price": 99,
  "is_stub": true,
  "is_demo": true,
  "short_description": "Каждый человек возбуждается по-своему. Узнайте, что включает именно вашего партнера.",
  "demo_limitation": {
    "title": "📌 В ПОЛНОЙ ВЕРСИИ:",
    "content": [
      "• 🔥 Точные триггер-фразы под профиль партнера",
      "• 🧠 Нейрохимический разбор",
      "• 💞 Сценарий идеальной близости"
    ],
    "price": 99
  }
}
EOF

# 2F
cat > профили/4F/2F/default.json << 'EOF'
{
  "profile_key": "default",
  "function": "2F",
  "function_name": "🍽 КЛЮЧ ГОЛОДА",
  "category": "reptile",
  "price": 99,
  "is_stub": true,
  "is_demo": true,
  "short_description": "Чего он/она хочет на самом деле? У каждого свой базовый голод.",
  "demo_limitation": {
    "title": "📌 В ПОЛНОЙ ВЕРСИИ:",
    "content": [
      "• 🍽 3 фразы-разрешения «хотеть»",
      "• 👁️ 5 признаков активации голода",
      "• 📋 Протокол насыщения"
    ],
    "price": 99
  }
}
EOF

# 3F
cat > профили/4F/3F/default.json << 'EOF'
{
  "profile_key": "default",
  "function": "3F",
  "function_name": "⚡ КЛЮЧ СТРАХА",
  "category": "reptile",
  "price": 99,
  "is_stub": true,
  "is_demo": true,
  "short_description": "Чего он/она боится больше смерти? Древний рептильный код.",
  "demo_limitation": {
    "title": "📌 В ПОЛНОЙ ВЕРСИИ:",
    "content": [
      "• ⚡ 3 точных триггера страха",
      "• 💊 3 противоядия",
      "• ❌ Что категорически нельзя делать"
    ],
    "price": 99
  }
}
EOF

# 4F
cat > профили/4F/4F/default.json << 'EOF'
{
  "profile_key": "default",
  "function": "4F",
  "function_name": "💡 КЛЮЧ ИДЕИ",
  "category": "reptile",
  "price": 99,
  "is_stub": true,
  "is_demo": true,
  "short_description": "Гениальные идеи не приходят по расписанию. Но есть состояние, в котором они случаются.",
  "demo_limitation": {
    "title": "📌 В ПОЛНОЙ ВЕРСИИ:",
    "content": [
      "• 💡 3 вопроса-ключа",
      "• 🕯️ Ритуалы входа в поток",
      "• 📋 Протокол «От ступора к инсайту»"
    ],
    "price": 99
  }
}
EOF

# 2. Сексуальный 18+ default.json
mkdir -p профили/сексуальный_18

cat > профили/сексуальный_18/default.json << 'EOF'
{
  "profile_key": "default",
  "header": "🔞 ИНТИМНЫЙ ПРОФИЛЬ",
  "title": "В РАЗРАБОТКЕ",
  "description": "Для этого общего профиля интимное описание еще создается. Каждый из 36 профилей имеет уникальную сексуальную нейрохимию.",
  "turn_ons": [],
  "blocks": [],
  "is_stub": true,
  "contact": "@meysternlp"
}
EOF

echo "✅ ГОТОВО! Создано:"
find профили -name "default.json" | wc -l
