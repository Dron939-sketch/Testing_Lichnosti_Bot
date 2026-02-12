#!/bin/bash

echo "🚀 СОЗДАНИЕ ПАПКИ sexual_functions/ И ФАЙЛОВ-ЗАГЛУШЕК 4F"

# 1. Создаем основную папку
mkdir -p sexual_functions

# 2. Создаем папки для каждого профиля
mkdir -p sexual_functions/sa_1_def
mkdir -p sexual_functions/sa_2_sit
mkdir -p sexual_functions/sa_4_cap
mkdir -p sexual_functions/sa_5_int
mkdir -p sexual_functions/sp_3_con
mkdir -p sexual_functions/default

echo "✅ Папки созданы"

# 3. Создаем index.json с маппингом
cat > sexual_functions/index.json << 'EOF'
{
  "mapping": {
    "SA_1_DEF": "sa_1_def",
    "SA_2_SIT": "sa_2_sit",
    "SA_4_EXP": "sa_4_cap",
    "SA_5_INT": "sa_5_int",
    "SP_3_CON": "sp_3_con"
  },
  "default": "default",
  "version": "1.0.0",
  "description": "Маппинг общих профилей на интимные для 4F-функций"
}
EOF

echo "✅ index.json создан"

# 4. СОЗДАЕМ ФАЙЛ-ЗАГЛУШКУ ДЛЯ 1F (ВСЕ ПРОФИЛИ)
for profile in sa_1_def sa_2_sit sa_4_cap sa_5_int sp_3_con default; do
  cat > sexual_functions/$profile/1F.json << 'EOF'
{
  "profile_key": "PROFILE_PLACEHOLDER",
  "function": "1F",
  "title": "🔥 1F: КЛЮЧ ВОЗБУЖДЕНИЯ",
  "short_description": "Как вызвать сексуальное желание, страсть, одержимость",
  "price": 99,
  "is_stub": true,
  "stub_note": "⚠️ РЕЖИМ ЗАГЛУШКИ: файл будет заменен на реальный контент",
  "content": {
    "description": "Это временный файл-заглушка. Полная версия 1F для данного профиля будет доступна после наполнения базы знаний.",
    "available_in": "следующее обновление",
    "contact": "@meysternlp"
  },
  "preview": {
    "teaser": "Знаете, что включает его/ее желание быстрее всего? Не тело, а...",
    "hint": "Полная версия содержит 3 точных триггер-фразы и анализ нейрохимии"
  }
}
EOF
  echo "✅ sexual_functions/$profile/1F.json создан"
done

# 5. СОЗДАЕМ ФАЙЛ-ЗАГЛУШКУ ДЛЯ 2F (ВСЕ ПРОФИЛИ)
for profile in sa_1_def sa_2_sit sa_4_cap sa_5_int sp_3_con default; do
  cat > sexual_functions/$profile/2F.json << 'EOF'
{
  "profile_key": "PROFILE_PLACEHOLDER",
  "function": "2F",
  "title": "🍽 2F: КЛЮЧ ГОЛОДА",
  "short_description": "Как пробудить аппетит, жажду обладания, присвоение",
  "price": 99,
  "is_stub": true,
  "stub_note": "⚠️ РЕЖИМ ЗАГЛУШКИ: файл будет заменен на реальный контент",
  "content": {
    "description": "Это временный файл-заглушка. Полная версия 2F для данного профиля будет доступна после наполнения базы знаний.",
    "available_in": "следующее обновление",
    "contact": "@meysternlp"
  },
  "preview": {
    "teaser": "Его/ее голод — это не голод по сексу. Это голод по...",
    "hint": "Полная версия раскрывает скрытые мотивы и дает 3 стратегии"
  }
}
EOF
  echo "✅ sexual_functions/$profile/2F.json создан"
done

# 6. СОЗДАЕМ ФАЙЛ-ЗАГЛУШКУ ДЛЯ 3F (ВСЕ ПРОФИЛИ)
for profile in sa_1_def sa_2_sit sa_4_cap sa_5_int sp_3_con default; do
  cat > sexual_functions/$profile/3F.json << 'EOF'
{
  "profile_key": "PROFILE_PLACEHOLDER",
  "function": "3F",
  "title": "⚡ 3F: КЛЮЧ СТРАХА",
  "short_description": "Что вызывает тревогу, как обходить защитные механизмы",
  "price": 99,
  "is_stub": true,
  "stub_note": "⚠️ РЕЖИМ ЗАГЛУШКИ: файл будет заменен на реальный контент",
  "content": {
    "description": "Это временный файл-заглушка. Полная версия 3F для данного профиля будет доступна после наполнения базы знаний.",
    "available_in": "следующее обновление",
    "contact": "@meysternlp"
  },
  "preview": {
    "teaser": "Чего он/она боится больше смерти? Не потери работы, не болезни...",
    "hint": "Полная версия содержит 3 обходных пути и анализ эволюционного страха"
  }
}
EOF
  echo "✅ sexual_functions/$profile/3F.json создан"
done

# 7. СОЗДАЕМ ФАЙЛ-ЗАГЛУШКУ ДЛЯ 4F (ВСЕ ПРОФИЛИ)
for profile in sa_1_def sa_2_sit sa_4_cap sa_5_int sp_3_con default; do
  cat > sexual_functions/$profile/4F.json << 'EOF'
{
  "profile_key": "PROFILE_PLACEHOLDER",
  "function": "4F",
  "title": "💡 4F: КЛЮЧ ИДЕИ",
  "short_description": "Как рождаются инсайты, в каком состоянии приходят озарения",
  "price": 99,
  "is_stub": true,
  "stub_note": "⚠️ РЕЖИМ ЗАГЛУШКИ: файл будет заменен на реальный контент",
  "content": {
    "description": "Это временный файл-заглушка. Полная версия 4F для данного профиля будет доступна после наполнения базы знаний.",
    "available_in": "следующее обновление",
    "contact": "@meysternlp"
  },
  "preview": {
    "teaser": "Его/ее гениальные идеи приходят не в офисе и не в душе. Они приходят...",
    "hint": "Полная версия содержит 4 вопроса-ключа и точное состояние входа"
  }
}
EOF
  echo "✅ sexual_functions/$profile/4F.json создан"
done

# 8. СОЗДАЕМ README ДЛЯ ПАПКИ
cat > sexual_functions/README.md << 'EOF'
# 🧬 sexual_functions/ — Хранилище 4F-ключей

## Структура папки
