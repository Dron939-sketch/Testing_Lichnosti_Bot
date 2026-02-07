# В файле database.py найдите функцию create_payment и замените её:

def create_payment(self, payment_data):
    """Создает новую запись о платеже в БД"""
    try:
        required_fields = ['payment_id', 'user_id', 'amount']
        for field in required_fields:
            if field not in payment_data:
                logger.error(f"Missing required field: {field}")
                return False
        
        with self.db_cursor() as cursor:
            # SQL для вставки платежа
            if self.is_postgres:
                sql = """
                INSERT INTO payments (
                    payment_id, user_id, amount, email, description, 
                    status, yookassa_id, metadata, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """
                values = (
                    payment_data.get('payment_id'),
                    payment_data.get('user_id'),
                    float(payment_data.get('amount', 0)),
                    payment_data.get('email', ''),
                    payment_data.get('description', ''),
                    payment_data.get('status', 'pending'),
                    payment_data.get('yookassa_id'),
                    payment_data.get('metadata', '{}')
                )
            else:
                sql = """
                INSERT INTO payments (
                    payment_id, user_id, amount, email, description, 
                    status, yookassa_id, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """
                values = (
                    payment_data.get('payment_id'),
                    payment_data.get('user_id'),
                    float(payment_data.get('amount', 0)),
                    payment_data.get('email', ''),
                    payment_data.get('description', ''),
                    payment_data.get('status', 'pending'),
                    payment_data.get('yookassa_id'),
                    payment_data.get('metadata', '{}')
                )
            
            cursor.execute(sql, values)
            return True
            
    except Exception as e:
        logger.error(f"❌ Error creating payment: {e}")
        return False
