#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('15.204.11.19', username='root', password='Jakes1328!@', timeout=10)

print('=' * 60)
print('🔧 FIXING dotfile_settings.gni')
print('=' * 60)
print('')

dotfile_path = '/opt/phazebrowser/src/build/dotfile_settings.gni'

# Create proper dotfile_settings.gni with correct scope
dotfile_content = """# dotfile_settings.gni
# Settings for PhazeBrowser build

build_dotfile_settings = {
  exec_script_allowlist = []
}
"""

# Write using printf to avoid heredoc issues
cmd = f"printf '%s' '{dotfile_content}' > {dotfile_path}"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.read()

# Verify
stdin, stdout, stderr = ssh.exec_command(f'cat {dotfile_path}')
content = stdout.read().decode()
print('Created file:')
print(content)
print('')

# Test gn gen
print('Testing gn gen (this may take a minute)...')
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/phazebrowser/src && '
    '/opt/phazebrowser/src/buildtools/linux64/gn gen out/Default --args="is_debug=false" 2>&1 | head -30'
)
gn_output = stdout.read().decode()
print(gn_output)

if 'Done' in gn_output or 'Generating' in gn_output:
    print('')
    print('✅ Build files generation started!')
else:
    print('')
    print('⚠️  May need to check errors above')

ssh.close()

