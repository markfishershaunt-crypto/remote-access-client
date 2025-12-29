import logging
from pywinauto import Desktop

logger = logging.getLogger(__name__)


class UIInteraction:
    def interact(self, element_path, action, params):
        """Взаимодействие с UI элементом"""
        try:
            desktop = Desktop(backend="uia")
            element = self._find_element_by_path(desktop, element_path)
            
            if not element:
                return {'success': False, 'error': 'Element not found'}
            
            # Выполнение действия
            if action == 'click':
                element.click_input()
            elif action == 'double_click':
                element.double_click_input()
            elif action == 'right_click':
                element.right_click_input()
            elif action == 'type':
                text = params.get('text', '')
                element.type_keys(text)
            elif action == 'set_text':
                text = params.get('text', '')
                element.set_edit_text(text)
            elif action == 'select':
                element.select()
            else:
                return {'success': False, 'error': f'Unknown action: {action}'}
            
            return {'success': True, 'action': action}
            
        except Exception as e:
            logger.error(f"UI interaction error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _find_element_by_path(self, root, path):
        """Поиск элемента по пути"""
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
