import subprocess
import logging

logger = logging.getLogger(__name__)


class CommandExecutor:
    def execute(self, command, timeout=30):
        """Выполнение команды"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            return {
                'output': output,
                'error': None if success else f"Exit code: {result.returncode}",
                'success': success
            }
            
        except subprocess.TimeoutExpired:
            return {
                'output': '',
                'error': f'Command timeout ({timeout}s)',
                'success': False
            }
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {
                'output': '',
                'error': str(e),
                'success': False
            }
