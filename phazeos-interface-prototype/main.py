#!/usr/bin/env python3
"""
PhazeOS Interface Prototype
Revolutionary intent-based computing interface
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import re

class PhazeInterface:
    """The Phaze - Universal Command Surface"""
    
    def __init__(self):
        self.commands = self._load_command_map()
        self.context = {
            'current_app': None,
            'recent_files': [],
            'user_intent': None
        }
    
    def _load_command_map(self) -> Dict[str, Dict]:
        """Map natural language to system commands"""
        return {
            # Software installation
            'install': {
                'pattern': r'install|get|add|download',
                'action': self._install_software,
                'examples': ['install firefox', 'get blender', 'add steam']
            },
            # File operations
            'open': {
                'pattern': r'open|show|launch|start',
                'action': self._open_file_or_app,
                'examples': ['open firefox', 'show my photos', 'launch terminal']
            },
            # System settings
            'settings': {
                'pattern': r'(bright|dark|volume|wifi|network|screen)',
                'action': self._system_settings,
                'examples': ['make screen brighter', 'connect to wifi', 'turn volume up']
            },
            # File search
            'find': {
                'pattern': r'find|search|where|my|that',
                'action': self._find_files,
                'examples': ['find my resume', 'where is that pdf', 'show my documents']
            },
            # System info
            'info': {
                'pattern': r'(cpu|memory|disk|what|how|status)',
                'action': self._system_info,
                'examples': ['what is using cpu', 'show memory usage', 'system status']
            }
        }
    
    def process_intent(self, user_input: str) -> Dict[str, Any]:
        """Process natural language input and return action"""
        user_input = user_input.lower().strip()
        
        # Find matching command category
        for category, config in self.commands.items():
            if re.search(config['pattern'], user_input):
                result = config['action'](user_input)
                return {
                    'success': True,
                    'action': category,
                    'result': result,
                    'user_input': user_input
                }
        
        # No match found
        return {
            'success': False,
            'message': f"I'm not sure how to '{user_input}'. Try: install, open, find, or settings.",
            'suggestions': self._get_suggestions(user_input)
        }
    
    def _install_software(self, intent: str) -> Dict[str, Any]:
        """Handle software installation intent"""
        # Extract package name
        words = intent.split()
        package = None
        
        # Find package name (usually after install/get/add)
        for i, word in enumerate(words):
            if word in ['install', 'get', 'add', 'download']:
                if i + 1 < len(words):
                    package = words[i + 1]
                    break
        
        if not package:
            return {'error': 'What would you like to install?'}
        
        # Map common names to package names
        package_map = {
            'firefox': 'firefox',
            'chrome': 'google-chrome',
            'blender': 'blender',
            'steam': 'steam',
            'gimp': 'gimp',
            'vscode': 'code',
            'code': 'code'
        }
        
        package_name = package_map.get(package, package)
        
        return {
            'action': 'install',
            'package': package_name,
            'command': f'sudo pacman -S {package_name}',
            'message': f'Installing {package_name}...'
        }
    
    def _open_file_or_app(self, intent: str) -> Dict[str, Any]:
        """Handle opening files or applications"""
        words = intent.split()
        
        # Remove "open", "show", "launch", "start"
        intent_clean = ' '.join([w for w in words if w not in ['open', 'show', 'launch', 'start']])
        
        # Check if it's an app
        apps = ['firefox', 'terminal', 'files', 'settings', 'calculator', 'blender', 'gimp']
        for app in apps:
            if app in intent_clean:
                return {
                    'action': 'launch_app',
                    'app': app,
                    'command': self._get_app_command(app)
                }
        
        # Otherwise, search for file
        return {
            'action': 'search_file',
            'query': intent_clean,
            'message': f'Searching for "{intent_clean}"...'
        }
    
    def _get_app_command(self, app: str) -> str:
        """Get command to launch app"""
        app_commands = {
            'firefox': 'firefox',
            'terminal': 'konsole',
            'files': 'dolphin',
            'settings': 'systemsettings5',
            'calculator': 'kcalc',
            'blender': 'blender',
            'gimp': 'gimp'
        }
        return app_commands.get(app, app)
    
    def _system_settings(self, intent: str) -> Dict[str, Any]:
        """Handle system settings changes"""
        if 'bright' in intent:
            return {
                'action': 'brightness',
                'direction': 'up' if 'up' in intent or 'bright' in intent else 'down',
                'message': 'Adjusting screen brightness...'
            }
        elif 'volume' in intent:
            return {
                'action': 'volume',
                'direction': 'up' if 'up' in intent else 'down',
                'message': 'Adjusting volume...'
            }
        elif 'wifi' in intent or 'network' in intent:
            return {
                'action': 'network',
                'message': 'Opening network settings...'
            }
        
        return {'error': 'What setting would you like to change?'}
    
    def _find_files(self, intent: str) -> Dict[str, Any]:
        """Handle file search"""
        # Extract search query
        query = intent.replace('find', '').replace('search', '').replace('where', '').replace('my', '').strip()
        
        return {
            'action': 'search',
            'query': query,
            'message': f'Searching for "{query}"...'
        }
    
    def _system_info(self, intent: str) -> Dict[str, Any]:
        """Handle system information requests"""
        if 'cpu' in intent:
            return {
                'action': 'show_cpu',
                'message': 'Showing CPU usage...'
            }
        elif 'memory' in intent or 'ram' in intent:
            return {
                'action': 'show_memory',
                'message': 'Showing memory usage...'
            }
        elif 'disk' in intent or 'space' in intent:
            return {
                'action': 'show_disk',
                'message': 'Showing disk usage...'
            }
        
        return {
            'action': 'system_status',
            'message': 'Showing system status...'
        }
    
    def _get_suggestions(self, intent: str) -> List[str]:
        """Get suggestions based on partial input"""
        # Simple suggestion engine
        suggestions = []
        words = intent.split()
        
        if len(words) == 1:
            suggestions = [
                f'{words[0]} firefox',
                f'{words[0]} blender',
                f'{words[0]} my files'
            ]
        
        return suggestions


def main():
    """Interactive PhazeOS interface"""
    print("=" * 60)
    print("    PHAZEOS INTERFACE PROTOTYPE")
    print("    'No Terminal. No Desktop. Just Intentions.'")
    print("=" * 60)
    print()
    print("Press Super key (or type 'quit' to exit)")
    print("Examples:")
    print("  - install firefox")
    print("  - open my photos")
    print("  - make screen brighter")
    print("  - find my resume")
    print()
    
    phaze = PhazeInterface()
    
    while True:
        try:
            user_input = input("Phaze> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            
            if not user_input:
                continue
            
            result = phaze.process_intent(user_input)
            
            if result['success']:
                print(f"✅ {result['result'].get('message', 'Done!')}")
                if 'command' in result['result']:
                    print(f"   Command: {result['result']['command']}")
            else:
                print(f"❌ {result['message']}")
                if result.get('suggestions'):
                    print("   Suggestions:")
                    for sug in result['suggestions']:
                        print(f"     - {sug}")
            
            print()
        
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == '__main__':
    main()
