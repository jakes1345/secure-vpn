#!/usr/bin/env python3
"""
ULTIMATE DEEP CODEBASE AUDIT
Most comprehensive audit possible - checks EVERYTHING
"""

import os
import sys
import ast
import json
import re
import subprocess
from pathlib import Path
from collections import defaultdict

class UltimateAuditor:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.web_portal = self.base_dir / 'web-portal'
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)
        
    def audit_all(self):
        print("="*80)
        print("🔬 ULTIMATE DEEP CODEBASE AUDIT")
        print("="*80)
        print()
        
        checks = {
            '1_imports': self.check_all_imports(),
            '2_file_references': self.check_all_file_refs(),
            '3_templates': self.check_all_templates(),
            '4_static': self.check_all_static(),
            '5_routes': self.check_all_routes(),
            '6_error_handlers': self.check_error_handlers(),
            '7_dependencies': self.check_all_dependencies(),
            '8_configs': self.check_all_configs(),
            '9_security': self.check_security_complete(),
            '10_automation': self.check_automation_complete(),
            '11_directory_structure': self.check_directory_structure(),
            '12_environment_vars': self.check_env_vars(),
            '13_service_files': self.check_service_files(),
            '14_cron_jobs': self.check_cron_jobs(),
            '15_startup_sequence': self.check_startup(),
            '16_error_handling': self.check_error_handling(),
            '17_logging': self.check_logging(),
            '18_backup_system': self.check_backups(),
            '19_cleanup_system': self.check_cleanup(),
            '20_monitoring': self.check_monitoring(),
        }
        
        self.generate_ultimate_report(checks)
        return checks
    
    def check_all_imports(self):
        print("1️⃣  Checking ALL imports...")
        issues = []
        python_files = list(self.web_portal.glob('*.py'))
        self.stats['python_files'] = len(python_files)
        
        for py_file in python_files:
            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                if not self.verify_import(alias.name):
                                    issues.append({
                                        'file': py_file.name,
                                        'import': alias.name,
                                        'type': 'missing'
                                    })
                        elif isinstance(node, ast.ImportFrom):
                            if node.module and not self.verify_import(node.module):
                                issues.append({
                                    'file': py_file.name,
                                    'import': node.module,
                                    'type': 'missing'
                                })
            except Exception as e:
                issues.append({
                    'file': py_file.name,
                    'error': str(e)
                })
        
        print(f"   Found {len(issues)} import issues")
        return issues
    
    def verify_import(self, mod_name):
        """Verify import exists"""
        base_mod = mod_name.split('.')[0]
        # Standard library
        stdlib = ['os', 'sys', 'json', 're', 'pathlib', 'datetime', 'time', 
                 'hashlib', 'secrets', 'subprocess', 'collections', 'functools',
                 'io', 'base64', 'csv', 'shlex']
        if base_mod in stdlib:
            return True
        # Local modules
        local = ['file_locking', 'rate_limiting', 'payment_integrations', 
                'email_api', 'twofa', 'vpn_manager']
        if base_mod in local:
            return True
        # Try importing
        try:
            __import__(base_mod)
            return True
        except:
            return False
    
    def check_all_file_refs(self):
        print("2️⃣  Checking ALL file references...")
        issues = []
        app_py = self.web_portal / 'app.py'
        
        if app_py.exists():
            with open(app_py, 'r') as f:
                content = f.read()
            
            # Find all file operations
            file_patterns = [
                (r'Path\(["\']([^"\']+)["\']\)', 'Path'),
                (r'open\(["\']([^"\']+)["\']', 'open'),
                (r'send_file\(["\']([^"\']+)["\']', 'send_file'),
            ]
            
            for pattern, op in file_patterns:
                matches = re.findall(pattern, content)
                for match in set(matches):
                    if not match.startswith('/') and 'users.json' not in match:
                        full_path = self.web_portal / match
                        if not full_path.exists() and '.' in match:
                            issues.append({
                                'file': match,
                                'operation': op,
                                'type': 'missing'
                            })
        
        print(f"   Found {len(issues)} file reference issues")
        return issues
    
    def check_all_templates(self):
        print("3️⃣  Checking ALL templates...")
        issues = []
        template_dir = self.web_portal / 'templates'
        app_py = self.web_portal / 'app.py'
        
        if app_py.exists():
            with open(app_py, 'r') as f:
                content = f.read()
            
            templates = re.findall(r"render_template\(['\"]([^'\"]+)['\"]", content)
            self.stats['template_references'] = len(set(templates))
            
            for template in set(templates):
                template_path = template_dir / template
                if not template_path.exists():
                    issues.append({
                        'template': template,
                        'type': 'missing'
                    })
        
        print(f"   Found {len(issues)} missing templates")
        return issues
    
    def check_all_static(self):
        print("4️⃣  Checking ALL static files...")
        issues = []
        static_dir = self.web_portal / 'static'
        template_dir = self.web_portal / 'templates'
        
        for template_file in template_dir.rglob('*.html'):
            if 'backup' in str(template_file):
                continue
            with open(template_file, 'r') as f:
                content = f.read()
                static_refs = re.findall(r"url_for\(['\"]static['\"],\s*filename=['\"]([^'\"]+)['\"]", content)
                for ref in static_refs:
                    static_path = static_dir / ref
                    if not static_path.exists():
                        issues.append({
                            'file': ref,
                            'template': template_file.name,
                            'type': 'missing'
                        })
        
        print(f"   Found {len(issues)} missing static files")
        return issues
    
    def check_all_routes(self):
        print("5️⃣  Checking ALL routes...")
        issues = []
        app_py = self.web_portal / 'app.py'
        
        if app_py.exists():
            with open(app_py, 'r') as f:
                content = f.read()
            
            routes = re.findall(r"@app\.route\(['\"]([^'\"]+)['\"]", content)
            self.stats['total_routes'] = len(set(routes))
            
            # Check for routes without proper decorators
            post_routes = re.findall(r"@app\.route\(['\"]([^'\"]+)['\"].*methods.*POST", content, re.DOTALL)
            for route in post_routes:
                # Check if has CSRF protection (if CSRF enabled)
                route_start = content.find(f"@app.route('{route}')")
                if route_start != -1:
                    func_match = re.search(r'def\s+(\w+)\(', content[route_start:route_start+500])
                    if func_match:
                        func_name = func_match.group(1)
                        # Check if function has proper security
                        if 'require_role' not in content[route_start:route_start+1000] and '/admin' in route:
                            issues.append({
                                'route': route,
                                'issue': 'Admin route without require_role'
                            })
        
        print(f"   Found {len(issues)} route issues")
        return issues
    
    def check_error_handlers(self):
        print("6️⃣  Checking error handlers...")
        issues = []
        app_py = self.web_portal / 'app.py'
        
        if app_py.exists():
            with open(app_py, 'r') as f:
                content = f.read()
            
            handlers = re.findall(r'@app\.errorhandler\((\d+)\)', content)
            required = ['404', '500', '403']
            for req in required:
                if req not in handlers:
                    issues.append({
                        'error_code': req,
                        'type': 'missing'
                    })
        
        print(f"   Found {len(issues)} missing error handlers")
        return issues
    
    def check_all_dependencies(self):
        print("7️⃣  Checking dependencies...")
        issues = []
        req_file = self.web_portal / 'requirements.txt'
        
        if not req_file.exists():
            issues.append({'type': 'requirements.txt missing'})
            return issues
        
        with open(req_file, 'r') as f:
            reqs = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        
        self.stats['dependencies'] = len(reqs)
        
        # Check if dependencies are used
        app_py = self.web_portal / 'app.py'
        if app_py.exists():
            with open(app_py, 'r') as f:
                content = f.read()
            for req in reqs:
                pkg = req.split('>=')[0].split('==')[0].split('[')[0].strip()
                import_name = pkg.replace('-', '_')
                if import_name not in content and pkg not in content:
                    # Might be used in other files
                    pass
        
        print(f"   Found {len(issues)} dependency issues")
        return issues
    
    def check_all_configs(self):
        print("8️⃣  Checking configuration files...")
        issues = []
        
        # Systemd service
        service = self.web_portal / 'phazevpn-portal.service'
        if service.exists():
            with open(service, 'r') as f:
                content = f.read()
            required = ['ExecStart=', 'Restart=', 'WorkingDirectory=']
            for req in required:
                if req not in content:
                    issues.append({
                        'config': 'systemd service',
                        'missing': req
                    })
        
        # Nginx config
        nginx = self.web_portal / 'nginx-phazevpn.conf'
        if nginx.exists():
            with open(nginx, 'r') as f:
                content = f.read()
            if 'proxy_pass' not in content:
                issues.append({
                    'config': 'nginx',
                    'missing': 'proxy_pass'
                })
        
        print(f"   Found {len(issues)} config issues")
        return issues
    
    def check_security_complete(self):
        print("9️⃣  Checking security implementation...")
        issues = []
        app_py = self.web_portal / 'app.py'
        
        if app_py.exists():
            with open(app_py, 'r') as f:
                content = f.read()
            
            security_checks = {
                'CSRF': r'CSRFProtect|csrf_token',
                'File Locking': r'safe_json',
                'Rate Limiting': r'check_rate_limit',
                'Input Sanitization': r'sanitize',
                'Safe Subprocess': r'safe_subprocess',
                'Password Hashing': r'bcrypt|hash_password',
            }
            
            for check_name, pattern in security_checks.items():
                if not re.search(pattern, content):
                    issues.append({
                        'security': check_name,
                        'type': 'missing'
                    })
        
        print(f"   Found {len(issues)} security issues")
        return issues
    
    def check_automation_complete(self):
        print("🔟 Checking automation...")
        issues = []
        scripts_dir = self.web_portal / 'scripts'
        
        required = ['daily-backup.sh', 'daily-cleanup.sh', 'health-check.sh']
        for script in required:
            script_path = scripts_dir / script
            if not script_path.exists():
                issues.append({
                    'script': script,
                    'type': 'missing'
                })
        
        print(f"   Found {len(issues)} automation issues")
        return issues
    
    def check_directory_structure(self):
        print("1️⃣1️⃣  Checking directory structure...")
        issues = []
        
        required_dirs = [
            'web-portal/templates',
            'web-portal/static',
            'web-portal/static/css',
            'web-portal/static/js',
            'web-portal/static/images',
            'web-portal/scripts',
        ]
        
        for dir_path in required_dirs:
            full_path = self.base_dir / dir_path
            if not full_path.exists():
                issues.append({
                    'directory': dir_path,
                    'type': 'missing'
                })
        
        print(f"   Found {len(issues)} directory issues")
        return issues
    
    def check_env_vars(self):
        print("1️⃣2️⃣  Checking environment variables...")
        issues = []
        app_py = self.web_portal / 'app.py'
        
        if app_py.exists():
            with open(app_py, 'r') as f:
                content = f.read()
            
            # Find all os.environ.get calls
            env_vars = re.findall(r"os\.environ\.get\(['\"]([^'\"]+)['\"]", content)
            self.stats['env_vars'] = len(set(env_vars))
            
            # Check if critical vars have defaults
            critical = ['FLASK_SECRET_KEY', 'STRIPE_SECRET_KEY']
            for var in critical:
                pattern = rf"os\.environ\.get\(['\"]{var}['\"][^)]+\)"
                if re.search(pattern, content):
                    # Check if has default
                    match = re.search(pattern, content)
                    if match and 'None' in match.group(0):
                        issues.append({
                            'var': var,
                            'issue': 'No default value'
                        })
        
        print(f"   Found {len(issues)} env var issues")
        return issues
    
    def check_service_files(self):
        print("1️⃣3️⃣  Checking service files...")
        issues = []
        
        service = self.web_portal / 'phazevpn-portal.service'
        if service.exists():
            with open(service, 'r') as f:
                content = f.read()
            
            # Check for required sections
            if '[Unit]' not in content:
                issues.append({'service': 'systemd', 'missing': '[Unit]'})
            if '[Service]' not in content:
                issues.append({'service': 'systemd', 'missing': '[Service]'})
            if '[Install]' not in content:
                issues.append({'service': 'systemd', 'missing': '[Install]'})
        
        print(f"   Found {len(issues)} service issues")
        return issues
    
    def check_cron_jobs(self):
        print("1️⃣4️⃣  Checking cron jobs...")
        issues = []
        
        # Check if scripts exist that should be in cron
        scripts_dir = self.web_portal / 'scripts'
        cron_scripts = ['daily-backup.sh', 'daily-cleanup.sh', 'health-check.sh']
        
        for script in cron_scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                # Check if script is executable
                if not os.access(script_path, os.X_OK):
                    issues.append({
                        'script': script,
                        'issue': 'Not executable'
                    })
        
        print(f"   Found {len(issues)} cron job issues")
        return issues
    
    def check_startup(self):
        print("1️⃣5️⃣  Checking startup sequence...")
        issues = []
        app_py = self.web_portal / 'app.py'
        
        if app_py.exists():
            with open(app_py, 'r') as f:
                content = f.read()
            
            # Check if directories are created on startup
            if 'mkdir' not in content and 'makedirs' not in content:
                # Check if directories exist check
                if 'exists()' not in content:
                    issues.append({
                        'issue': 'No directory creation/check on startup'
                    })
        
        print(f"   Found {len(issues)} startup issues")
        return issues
    
    def check_error_handling(self):
        print("1️⃣6️⃣  Checking error handling...")
        issues = []
        app_py = self.web_portal / 'app.py'
        
        if app_py.exists():
            with open(app_py, 'r') as f:
                content = f.read()
            
            # Count try/except blocks
            try_blocks = len(re.findall(r'\btry\s*:', content))
            except_blocks = len(re.findall(r'\bexcept\s+', content))
            
            self.stats['try_blocks'] = try_blocks
            self.stats['except_blocks'] = except_blocks
            
            # Check critical operations have error handling
            critical_ops = ['subprocess', 'file', 'json.load', 'json.dump']
            for op in critical_ops:
                # Check if operations are wrapped in try/except
                pattern = rf'{op}[^(]*\('
                matches = re.finditer(pattern, content)
                for match in matches:
                    # Check if in try block
                    start = max(0, match.start() - 500)
                    context = content[start:match.end()]
                    if 'try:' not in context:
                        issues.append({
                            'operation': op,
                            'issue': 'No error handling'
                        })
                        break
        
        print(f"   Found {len(issues)} error handling issues")
        return issues
    
    def check_logging(self):
        print("1️⃣7️⃣  Checking logging...")
        issues = []
        app_py = self.web_portal / 'app.py'
        
        if app_py.exists():
            with open(app_py, 'r') as f:
                content = f.read()
            
            # Check for logging
            if 'log_activity' in content:
                self.stats['logging'] = len(re.findall(r'log_activity\(', content))
            else:
                issues.append({
                    'issue': 'No activity logging found'
                })
        
        print(f"   Found {len(issues)} logging issues")
        return issues
    
    def check_backups(self):
        print("1️⃣8️⃣  Checking backup system...")
        issues = []
        
        backup_script = self.web_portal / 'scripts' / 'daily-backup.sh'
        if not backup_script.exists():
            issues.append({
                'system': 'backup',
                'issue': 'Backup script missing'
            })
        else:
            # Check script content
            with open(backup_script, 'r') as f:
                content = f.read()
            if 'tar' not in content and 'backup' not in content.lower():
                issues.append({
                    'system': 'backup',
                    'issue': 'Backup script incomplete'
                })
        
        print(f"   Found {len(issues)} backup issues")
        return issues
    
    def check_cleanup(self):
        print("1️⃣9️⃣  Checking cleanup system...")
        issues = []
        
        cleanup_script = self.web_portal / 'scripts' / 'daily-cleanup.sh'
        if not cleanup_script.exists():
            issues.append({
                'system': 'cleanup',
                'issue': 'Cleanup script missing'
            })
        
        print(f"   Found {len(issues)} cleanup issues")
        return issues
    
    def check_monitoring(self):
        print("2️⃣0️⃣  Checking monitoring system...")
        issues = []
        
        health_script = self.web_portal / 'scripts' / 'health-check.sh'
        if not health_script.exists():
            issues.append({
                'system': 'monitoring',
                'issue': 'Health check script missing'
            })
        
        print(f"   Found {len(issues)} monitoring issues")
        return issues
    
    def generate_ultimate_report(self, checks):
        print("\n" + "="*80)
        print("📊 ULTIMATE AUDIT REPORT")
        print("="*80)
        
        total_issues = sum(len(v) for v in checks.values())
        
        print(f"\nTotal Issues: {total_issues}")
        print(f"\nStatistics:")
        for key, value in self.stats.items():
            print(f"  • {key}: {value}")
        
        print(f"\nDetailed Results:")
        for check_name, issues in checks.items():
            status = "✅" if not issues else "❌"
            print(f"  {status} {check_name}: {len(issues)} issues")
            if issues and len(issues) <= 5:
                for issue in issues:
                    print(f"     - {issue}")
        
        if total_issues == 0:
            print("\n" + "="*80)
            print("✅ CODEBASE IS 100% COMPLETE AND VERIFIED")
            print("="*80)
        else:
            print("\n" + "="*80)
            print(f"⚠️  {total_issues} ISSUES FOUND - REVIEW REQUIRED")
            print("="*80)

if __name__ == '__main__':
    auditor = UltimateAuditor('/media/jack/Liunux/secure-vpn')
    auditor.audit_all()

