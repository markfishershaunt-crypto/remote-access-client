import json
import zlib
import base64
import logging
from pywinauto import Desktop
from pywinauto.application import Application

logger = logging.getLogger(__name__)


class UITreeCapture:
    def __init__(self, max_depth=8):
        self.max_depth = max_depth
        self.last_tree = None
    
    def capture(self, full=True, element_path=None):
        """Захват UI-дерева"""
        try:
            desktop = Desktop(backend="uia")
            
            if element_path:
                # Захват конкретного элемента
                element = self._find_element_by_path(desktop, element_path)
                if element:
                    return self._element_to_dict(element, depth=0)
                else:
                    return {'error': 'Element not found'}
            else:
                # Захват всего рабочего стола
                tree = self._element_to_dict(desktop, depth=0)
                
                if full:
                    self.last_tree = tree
                
                return tree
                
        except Exception as e:
            logger.error(f"UI capture error: {e}")
            return {'error': str(e)}
    
    def _element_to_dict(self, element, depth=0):
        """Конвертация элемента в словарь"""
        if depth > self.max_depth:
            return None
        
        try:
            elem_dict = {
                'class_name': element.class_name() if hasattr(element, 'class_name') else '',
                'name': element.window_text() if hasattr(element, 'window_text') else '',
                'control_type': str(element.element_info.control_type) if hasattr(element, 'element_info') else '',
                'enabled': element.is_enabled() if hasattr(element, 'is_enabled') else False,
                'visible': element.is_visible() if hasattr(element, 'is_visible') else False,
                'children': []
            }
            
            # Координаты
            try:
                rect = element.rectangle()
                elem_dict['rect'] = {
                    'left': rect.left,
                    'top': rect.top,
                    'right': rect.right,
                    'bottom': rect.bottom
                }
            except:
                elem_dict['rect'] = None
            
            # Дочерние элементы (ограничиваем количество)
            try:
                children = element.children()
                for i, child in enumerate(children[:30]):  # Максимум 30 детей
                    child_dict = self._element_to_dict(child, depth + 1)
                    if child_dict:
                        child_dict['index'] = i
                        elem_dict['children'].append(child_dict)
            except:
                pass
            
            return elem_dict
            
        except Exception as e:
            logger.error(f"Element conversion error: {e}")
            return None
    
    def _find_element_by_path(self, root, path):
        """Поиск элемента по пути (например, '0.1.3')"""
        try:
            indices = [int(x) for x in path.split('.')]
            current = root
            
            for idx in indices:
                children = current.children()
                if idx < len(children):
                    current = children[idx]
                else:
                    return None
            
            return current
        except:
            return None
    
    def compress(self, ui_tree):
        """Сжатие UI-дерева"""
        try:
            json_str = json.dumps(ui_tree, ensure_ascii=False)
            json_bytes = json_str.encode('utf-8')
            compressed = zlib.compress(json_bytes, level=6)
            compressed_base64 = base64.b64encode(compressed).decode('ascii')
            
            logger.info(f"Compressed: {len(json_bytes)} -> {len(compressed)} bytes "
                       f"({(1 - len(compressed)/len(json_bytes))*100:.1f}% reduction)")
            
            return compressed_base64
        except Exception as e:
            logger.error(f"Compression error: {e}")
            return None
