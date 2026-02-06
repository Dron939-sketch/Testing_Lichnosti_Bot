"""
HTTP сервер для обработки webhook от ЮKassa
"""

from aiohttp import web
import os
import json
import logging
import asyncio
from webhook_handler import create_webhook_handler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальный обработчик
webhook_handler = None

async def handle_yookassa_webhook(request):
    """
    Обработчик POST запросов от ЮKassa
    """
    try:
        # Читаем тело запроса
        body = await request.text()
        
        if not body:
            logger.error("❌ Empty request body")
            return web.Response(text='Empty body', status=400)
        
        # Получаем заголовки
        headers = dict(request.headers)
        
        # Логируем входящий запрос (без sensitive данных)
        logger.info(f"🌐 Webhook received from {request.remote}")
        
        # Обрабатываем webhook
        result = await webhook_handler.handle_webhook_request(body, headers)
        
        if result.get('status') == 'success':
            logger.info(f"✅ Webhook processed successfully: {result.get('event')}")
            return web.Response(
                text=json.dumps(result),
                content_type='application/json',
                status=200
            )
        else:
            logger.error(f"❌ Webhook processing failed: {result.get('message')}")
            return web.Response(
                text=json.dumps(result),
                content_type='application/json',
                status=400
            )
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in webhook handler: {e}")
        return web.Response(
            text=json.dumps({"status": "error", "message": str(e)}),
            content_type='application/json',
            status=500
        )

async def handle_health_check(request):
    """Health check endpoint"""
    return web.Response(
        text=json.dumps({
            "status": "healthy",
            "service": "YooKassa Webhook Handler",
            "time": asyncio.get_event_loop().time()
        }),
        content_type='application/json'
    )

async def handle_test_webhook(request):
    """Тестовый endpoint для проверки"""
    return web.Response(
        text=json.dumps({
            "status": "ok",
            "message": "Webhook server is running",
            "endpoints": {
                "POST /yookassa-webhook": "Handle YooKassa notifications",
                "GET /health": "Health check",
                "GET /test": "Test endpoint"
            }
        }),
        content_type='application/json'
    )

async def start_background_tasks(app):
    """Запуск фоновых задач"""
    logger.info("🚀 Starting background tasks...")
    # Здесь можно запустить периодические задачи
    
async def cleanup_background_tasks(app):
    """Очистка фоновых задач"""
    logger.info("🧹 Cleaning up background tasks...")

def create_app(bot_instance=None):
    """
    Создание приложения
    
    Args:
        bot_instance: Экземпляр Telegram бота (для отправки уведомлений)
    """
    global webhook_handler
    
    # Создаем обработчик
    webhook_handler = create_webhook_handler(bot_instance)
    
    app = web.Application()
    
    # Добавляем middleware для логирования
    @web.middleware
    async def log_middleware(request, handler):
        logger.debug(f"📥 {request.method} {request.path} from {request.remote}")
        response = await handler(request)
        logger.debug(f"📤 {request.method} {request.path} -> {response.status}")
        return response
    
    app.middlewares.append(log_middleware)
    
    # Регистрируем маршруты
    app.router.add_post('/yookassa-webhook', handle_yookassa_webhook)
    app.router.add_get('/health', handle_health_check)
    app.router.add_get('/test', handle_test_webhook)
    app.router.add_get('/', handle_test_webhook)
    
    # Фоновые задачи
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    
    return app

def run_server(host='0.0.0.0', port=None, bot_instance=None):
    """
    Запуск сервера
    
    Args:
        host: Хост для запуска
        port: Порт (берется из переменной окружения PORT или 10000)
        bot_instance: Экземпляр Telegram бота
    """
    port = int(os.environ.get("PORT", port or 10000))
    
    app = create_app(bot_instance)
    
    logger.info(f"🚀 Starting webhook server on {host}:{port}")
    logger.info(f"🌐 Webhook URL: https://your-domain.onrender.com/yookassa-webhook")
    logger.info(f"🏥 Health check: https://your-domain.onrender.com/health")
    
    web.run_app(app, host=host, port=port)

if __name__ == "__main__":
    # Запуск сервера без бота (для тестирования)
    run_server()
