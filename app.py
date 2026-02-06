# ============================================
# ГЛАВНАЯ ФУНКЦИЯ (асинхронная версия)
# ============================================

async def main_async():
    """Асинхронная версия основной функции"""
    print("\n" + "="*50)
    print("🚀 ЗАПУСК TELEGRAM БОТА ВАРИАТИКА ver 2.0")
    print("="*50)
    print("РЕЖИМ: БОЕВОЙ С ЮKASSA")
    print("="*50 + "\n")
    
    # Проверка конфигурации:
    try:
        config.validate()
        print("✅ Конфигурация проверена")
        
        print(f"🤖 Bot Token: {'✅' if config.TELEGRAM_BOT_TOKEN else '❌'}")
        print(f"💰 YooKassa: {'✅' if config.YOOKASSA_SHOP_ID and config.YOOKASSA_SECRET_KEY else '❌'}")
        print(f"🔗 Webhook: {config.WEBHOOK_URL}")
        print(f"💵 Сумма: {config.PAYMENT_AMOUNT} {config.PAYMENT_CURRENCY}")
        
        if not config.is_payment_enabled:
            print("\n⚠️  ПРЕДУПРЕЖДЕНИЕ: Платежи ЮKassa НЕ настроены!")
            print("   Бот будет работать, но платежи НЕ БУДУТ доступны!")
            
    except ValueError as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("="*50)
        print("ПРОВЕРЬТЕ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
        print("1. TELEGRAM_BOT_TOKEN - токен бота")
        print("2. YOOKASSA_SHOP_ID - Shop ID из ЮKassa")
        print("3. YOOKASSA_SECRET_KEY - Secret Key из ЮKassa")
        print("4. WEBHOOK_URL - ваш Render URL")
        return
    
    # Проверка загрузки профилей
    print("\n🔍 ПРОВЕРКА ЗАГРУЗКИ ПРОФИЛЕЙ")
    print("="*30)
    
    all_profiles = loader.get_all_profiles()
    print(f"📊 Всего профилей загружено: {len(all_profiles)}")
    
    # Проверяем профили по типам
    for profile_type in ['sa', 'sp', 'ia', 'ip']:
        type_profiles = [p for p in all_profiles if p.lower().startswith(f"{profile_type}_")]
        print(f"🔍 {profile_type.upper()} профилей: {len(type_profiles)}")
    
    # Проверяем наличие sp_4_val (проблемный профиль)
    sp_4_profiles = [p for p in all_profiles if 'sp_4' in p.lower()]
    print(f"\n🔍 SP_4 профили: {sp_4_profiles}")
    
    # Если нет sp_4_val, используем fallback
    if 'sp_4_val' not in [p.lower() for p in all_profiles]:
        print("⚠️  ВНИМАНИЕ: профиль sp_4_val не найден!")
        print("   Будет использован fallback профиль")
    
    print("="*30)
    print("🤖 Запускаю Telegram бота...")
    
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # Создаем ConversationHandler с per_message=True
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_test, pattern="^start_test$")
        ],
        states={
            STAGE_1: [
                CallbackQueryHandler(show_stage_1_details, pattern="^stage1_details$"),
                CallbackQueryHandler(back_to_stage1_intro, pattern="^back_to_stage1_intro$"),
                CallbackQueryHandler(start_stage_1, pattern="^start_stage_1$"),
                CallbackQueryHandler(handle_stage_1_answer, pattern="^stage1_")
            ],
            STAGE_2: [
                CallbackQueryHandler(show_stage_2_intro, pattern="^show_stage_2_intro$"),
                CallbackQueryHandler(show_stage_2_details, pattern="^stage2_details$"),
                CallbackQueryHandler(back_to_stage2_intro, pattern="^back_to_stage2_intro$"),
                CallbackQueryHandler(start_stage_2, pattern="^start_stage_2$"),
                CallbackQueryHandler(handle_stage_2_answer, pattern="^stage2_")
            ],
            STAGE_3: [
                CallbackQueryHandler(show_stage_3_intro, pattern="^show_stage_3_intro$"),
                CallbackQueryHandler(show_stage_3_details, pattern="^stage3_details$"),
                CallbackQueryHandler(back_to_stage3_intro, pattern="^back_to_stage3_intro$"),
                CallbackQueryHandler(start_stage_3, pattern="^start_stage_3$"),
                CallbackQueryHandler(handle_stage_3_answer, pattern="^stage3_")
            ],
            STAGE_4: [
                CallbackQueryHandler(show_stage_4_intro, pattern="^show_stage_4_intro$"),
                CallbackQueryHandler(show_stage_4_details, pattern="^stage4_details$"),
                CallbackQueryHandler(back_to_stage4_intro, pattern="^back_to_stage4_intro$"),
                CallbackQueryHandler(start_stage_4, pattern="^start_stage_4$"),
                CallbackQueryHandler(handle_stage_4_answer, pattern="^stage4_")
            ],
            CLARIFICATION: [
                CallbackQueryHandler(handle_clarification_answer, pattern="^clarify_")
            ],
            DILTS_CLARIFICATION: [
                CallbackQueryHandler(handle_dilts_clarification, pattern="^dilts_clarify_")
            ],
            RESULTS: [
                CallbackQueryHandler(get_gift_screen, pattern="^get_gift$"),
                CallbackQueryHandler(open_gift_screen, pattern="^open_gift$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(show_results_screen, pattern="^show_results$")
            ],
            GIFT_SCREEN: [
                CallbackQueryHandler(confirm_share, pattern="^confirm_share$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(get_gift_screen, pattern="^get_gift$")
            ],
            PACKAGE_SCREEN: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(show_package_screen, pattern="^show_package$"),
                CallbackQueryHandler(handle_payment_start, pattern="^start_payment$")
            ],
            PAYMENT_SCREEN: [
                CallbackQueryHandler(check_payment_status, pattern="^check_payment_"),
                CallbackQueryHandler(cancel_payment, pattern="^cancel_payment$"),
                CallbackQueryHandler(retry_payment, pattern="^retry_payment$"),
                CallbackQueryHandler(ask_for_email, pattern="^ask_email$"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$")
            ],
            PAYMENT_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email_input),
                CallbackQueryHandler(skip_email, pattern="^skip_email$"),
                CallbackQueryHandler(back_to_payment, pattern="^back_to_payment$")
            ],
            PAYMENT_CHECK: [
                CallbackQueryHandler(check_payment_status, pattern="^check_payment_"),
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$")
            ],
            PAYMENT_SUCCESS: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(restart_test, pattern="^restart_test$")
            ],
            OPEN_GIFT_SCREEN: [
                CallbackQueryHandler(back_to_results, pattern="^back_to_results$"),
                CallbackQueryHandler(open_gift_screen, pattern="^open_gift$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
        per_message=True  # ← ОБЯЗАТЕЛЬНО!
    )
    
    # Добавляем обработчики команд
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("payment_help", payment_help_command))
    application.add_handler(CommandHandler("payment_status", payment_status_command))
    application.add_handler(CommandHandler("payment_test", payment_test_command))
    
    logger.info("🚀 Telegram бот запущен: ВАРИАТИКА ver 2.0 + ЮKassa")
    logger.info(f"💰 Payment enabled: {config.is_payment_enabled}")
    logger.info(f"🔗 Webhook URL: {config.WEBHOOK_URL}")
    logger.info(f"💵 Amount: {config.PAYMENT_AMOUNT} {config.PAYMENT_CURRENCY}")
    
    if config.is_payment_enabled:
        logger.info("✅ Платежная система готова к работе")
    else:
        logger.warning("⚠️  Платежная система НЕ настроена")
    
    # Запуск бота
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Синхронная обертка для запуска бота"""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
