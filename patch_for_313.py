# patch_for_313.py
import sys

# Создаем простую реализацию imghdr
class SimpleImghdr:
    @staticmethod
    def what(file, h=None):
        """Минимальная реализация для определения типа изображения"""
        if h is None:
            if hasattr(file, 'read'):
                pos = file.tell()
                h = file.read(32)
                file.seek(pos)
            elif isinstance(file, bytes):
                h = file[:32]
            elif isinstance(file, str):
                with open(file, 'rb') as f:
                    h = f.read(32)
            else:
                return None
        
        if not h:
            return None
        
        # Простые проверки
        if h.startswith(b'\xff\xd8'):
            return 'jpeg'
        elif h.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
        elif h.startswith(b'GIF87a') or h.startswith(b'GIF89a'):
            return 'gif'
        elif h.startswith(b'BM'):
            return 'bmp'
        elif len(h) >= 12 and h.startswith(b'RIFF') and h[8:12] == b'WEBP':
            return 'webp'
        
        return None

# Заменяем модуль
sys.modules['imghdr'] = SimpleImghdr()
