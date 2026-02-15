#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import base64
import hashlib
import json
import os
import re
import tarfile
import tempfile
import time
import urllib.request
import urllib.error
import urllib.parse
import http.cookiejar

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community',
}

DOCUMENTATION = r'''
---
module: galaxy_service

short_description: Validate and test Ansible Galaxy service

version_added: "1.0.0"

description:
    - Validates Galaxy service health status
    - Tests authentication
    - Uploads test collections
    - Downloads and verifies collections
    - Can be used to verify Galaxy service functionality

options:
    galaxy_url:
        description:
            - The URL of the Galaxy server.
        required: true
        type: str
    username:
        description:
            - Username for Galaxy authentication.
        required: true
        type: str
    password:
        description:
            - Password for Galaxy authentication.
        required: true
        type: str
        no_log: true
    action:
        description:
            - Action to perform.
        required: true
        choices: [validate, upload, download, test]
        type: str
    collection_name:
        description:
            - Collection name in format namespace.name (e.g., community.zabbix).
            - Required for download action.
        type: str
    collection_version:
        description:
            - Collection version to download.
            - If not specified, downloads the latest version.
        type: str
    src:
        description:
            - Path to collection tarball or directory to upload.
            - If not specified, creates a test collection automatically.
        type: path
    dest:
        description:
            - Path to save downloaded collection tarball.
            - Required for download action.
        type: path
    validate_certs:
        description:
            - Whether to validate SSL certificates.
        default: True
        type: bool
    wait_timeout:
        description:
            - Time in seconds to wait for collection processing.
        default: 120
        type: int

author:
    - Galaxy Team
'''

EXAMPLES = r'''
- name: Validate Galaxy service health
  galaxy_service:
    galaxy_url: "https://galaxy-web.orb.local"
    username: "admin"
    password: "admin"
    action: validate

- name: Test complete Galaxy workflow
  galaxy_service:
    galaxy_url: "https://galaxy-web.orb.local"
    username: "admin"
    password: "admin"
    action: test
  register: result

- name: Upload a collection
  galaxy_service:
    galaxy_url: "https://galaxy-web.orb.local"
    username: "admin"
    password: "admin"
    action: upload
    src: "/path/to/my_collection.tar.gz"
'''

RETURN = r'''
msg:
    description: Message describing the result.
    type: str
    returned: always
changed:
    description: Whether any change was made.
    type: bool
    returned: always
api_status:
    description: API status code.
    type: int
    returned: when action is validate or test
database_connected:
    description: Database connection status.
    type: bool
    returned: when action is validate or test
redis_connected:
    description: Redis connection status.
    type: bool
    returned: when action is validate or test
components:
    description: List of Galaxy components and versions.
    type: dict
    returned: when action is validate or test
collections_count:
    description: Number of collections in the server.
    type: int
    returned: when action is validate or test
upload_result:
    description: Upload result information.
    type: dict
    returned: when action is upload or test
'''


class GalaxyService:
    def __init__(self, module):
        self.module = module
        self.galaxy_url = module.params['galaxy_url'].rstrip('/')
        self.username = module.params['username']
        self.password = module.params['password']
        self.action = module.params.get('action', 'validate')
        self.collection_name = module.params.get('collection_name')
        self.collection_version = module.params.get('collection_version')
        self.src = module.params.get('src')
        self.dest = module.params.get('dest')
        self.validate_certs = module.params.get('validate_certs', True)
        self.wait_timeout = module.params.get('wait_timeout', 120)
        self.token = None

        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))

    def make_request(self, url, method='GET', data=None, headers=None):
        """Make HTTP request to Galaxy server with Basic Auth."""
        if headers is None:
            headers = {}

        auth_string = base64.b64encode(('%s:%s' % (self.username, self.password)).encode()).decode()
        headers['Authorization'] = 'Basic %s' % auth_string

        try:
            if data and method == 'POST':
                data = json.dumps(data).encode('utf-8')
                headers['Content-Type'] = 'application/json'

            request = urllib.request.Request(url, data=data, headers=headers, method=method)
            response = self.opener.open(request)
            return response.getcode(), json.loads(response.read())
        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read())
                return e.code, error_body
            except:
                return e.code, {'error': str(e)}
        except urllib.error.URLError as e:
            return 0, {'error': str(e)}

    def authenticate(self):
        """Authenticate with Galaxy using Basic Auth for API access."""
        try:
            test_url = '%s/api/galaxy/v3/collections/' % self.galaxy_url
            auth_string = base64.b64encode(('%s:%s' % (self.username, self.password)).encode()).decode()
            headers = {'Authorization': 'Basic %s' % auth_string}
            
            request = urllib.request.Request(test_url, headers=headers)
            response = urllib.request.urlopen(request)
            
            if response.getcode() == 200:
                return True, "Authentication successful (Basic Auth)"
            else:
                return False, "Authentication failed: HTTP %s" % response.getcode()
        except urllib.error.HTTPError as e:
            return False, "Authentication failed: HTTP %s" % e.code
        except Exception as e:
            return False, "Authentication failed: %s" % str(e)

    def check_status(self):
        """Check Galaxy service status."""
        status_url = '%s/api/galaxy/pulp/api/v3/status/' % self.galaxy_url
        status_code, response = self.make_request(status_url)

        result = {
            'api_status': status_code,
            'database_connected': False,
            'redis_connected': False,
            'components': {},
            'collections_count': 0,
        }

        if status_code == 200:
            result['database_connected'] = response.get('database_connection', {}).get('connected', False)
            result['redis_connected'] = response.get('redis_connection', {}).get('connected', False)

            versions = response.get('versions', [])
            for v in versions:
                result['components'][v['component']] = v['version']

            collections_url = '%s/api/galaxy/v3/collections/' % self.galaxy_url
            collections_status, collections_response = self.make_request(collections_url)
            if collections_status == 200:
                result['collections_count'] = len(collections_response.get('results', []))

        return result

    def create_test_collection(self):
        """Create a test collection for upload."""
        temp_dir = tempfile.mkdtemp()
        collection_name = "validate_test_%d" % int(time.time())

        collection_dir = os.path.join(temp_dir, collection_name, 'tests')
        os.makedirs(collection_dir)

        galaxy_yml = """namespace: %s
name: %s
version: 1.0.0
readme: README.md
authors:
  - Test Author <test@example.com>
description: Test collection for Galaxy service validation
""" % (collection_name, collection_name)

        with open(os.path.join(temp_dir, collection_name, 'README.md'), 'w') as f:
            f.write("# Test Collection\n\nThis is a test collection for Galaxy validation.\n")

        with open(os.path.join(temp_dir, collection_name, 'galaxy.yml'), 'w') as f:
            f.write(galaxy_yml)

        roles_dir = os.path.join(temp_dir, collection_name, 'roles')
        os.makedirs(os.path.join(roles_dir, 'test_role', 'meta'))

        with open(os.path.join(roles_dir, 'test_role', 'meta', 'main.yml'), 'w') as f:
            f.write("""---
galaxy_info:
  role_name: test_role
  author: Test Author
  description: Test role
  license: MIT
  min_ansible_version: "2.9"
""")

        with open(os.path.join(collection_dir, 'test.yml'), 'w') as f:
            f.write("""---
- name: Test playbook
  hosts: localhost
  gather_facts: no
  tasks:
    - name: Debug message
      debug:
        msg: "Test task from Galaxy validation"
""")

        tar_path = os.path.join(temp_dir, '%s-1.0.0.tar.gz' % collection_name)

        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(os.path.join(temp_dir, collection_name),
                   arcname=collection_name)

        return tar_path, collection_name

    def upload_collection(self, tar_path=None):
        """Upload collection to Galaxy."""
        if not tar_path:
            tar_path, collection_name = self.create_test_collection()
            created_temp = True
        else:
            collection_name = os.path.basename(tar_path).replace('.tar.gz', '')
            created_temp = False

        upload_url = '%s/api/galaxy/v3/collections/' % self.galaxy_url

        with open(tar_path, 'rb') as f:
            file_content = f.read()

        boundary = '----GalaxyBoundary%d' % int(time.time())
        body_parts = []
        body_parts.append(b'--%s\r\n' % boundary.encode())
        body_parts.append(b'Content-Disposition: form-data; name="file"; filename="%s"\r\n' % os.path.basename(tar_path).encode())
        body_parts.append(b'Content-Type: application/gzip\r\n\r\n')
        body_parts.append(file_content)
        body_parts.append(b'\r\n--%s--\r\n' % boundary.encode())

        body = b''.join(body_parts)

        headers = {
            'Content-Type': 'multipart/form-data; boundary=%s' % boundary,
        }

        result = {
            'collection': collection_name,
            'uploaded': False,
            'import_status': 'unknown',
        }

        try:
            request = urllib.request.Request(upload_url, data=body, headers=headers, method='POST')
            response = urllib.request.urlopen(request)
            response_data = json.loads(response.read())

            if response.getcode() == 202:
                task_id = response_data.get('task')
                result['task_id'] = task_id

                if task_id:
                    result['import_status'] = self._wait_for_import(task_id)
            elif response.getcode() in [200, 201]:
                result['uploaded'] = True

            return result

        except urllib.error.HTTPError as e:
            try:
                error = json.loads(e.read())
                result['error'] = error.get('error', str(e))
            except:
                result['error'] = str(e)
            return result
        finally:
            if created_temp and os.path.exists(tar_path):
                os.remove(tar_path)

    def _wait_for_import(self, task_id):
        """Wait for collection import to complete."""
        task_url = '%s/api/galaxy/v3/imports/tasks/%s/' % (self.galaxy_url, task_id)

        start_time = time.time()
        while time.time() - start_time < self.wait_timeout:
            time.sleep(2)
            status, task_result = self.make_request(task_url)

            if status == 200:
                state = task_result.get('state')
                if state == 'success':
                    return 'success'
                elif state == 'failed':
                    return 'failed'

        return 'timeout'

    def download_collection(self, collection_name, version=None, dest=None):
        """Download collection from Galaxy."""
        if not dest:
            dest = '/tmp/%s.tar.gz' % collection_name.replace('.', '_')

        parts = collection_name.split('.')
        if len(parts) != 2:
            return {'error': 'Collection must be in format namespace.name'}

        namespace, name = parts

        versions_url = '%s/api/galaxy/v3/collections/%s/%s/versions/' % (self.galaxy_url, namespace, name)
        status, response = self.make_request(versions_url)

        if status != 200:
            return {'error': 'Failed to get collection versions'}

        versions = response.get('results', [])
        if not versions:
            return {'error': 'No versions found'}

        if version:
            version_to_download = version
        else:
            version_to_download = versions[0]['version']

        download_url = None
        for v in versions:
            if v['version'] == version_to_download:
                download_url = '%s%s' % (self.galaxy_url, v['download_url'])
                break

        if not download_url:
            return {'error': 'Version %s not found' % version_to_download}

        try:
            request = urllib.request.Request(download_url)
            response = urllib.request.urlopen(request)

            with open(dest, 'wb') as f:
                f.write(response.read())

            return {
                'downloaded': True,
                'path': dest,
                'collection': collection_name,
                'version': version_to_download,
            }

        except Exception as e:
            return {'error': 'Download failed: %s' % str(e)}


def run_module():
    module_args = dict(
        galaxy_url=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        action=dict(type='str', required=True, choices=['validate', 'upload', 'download', 'test']),
        collection_name=dict(type='str'),
        collection_version=dict(type='str'),
        src=dict(type='path'),
        dest=dict(type='path'),
        validate_certs=dict(type='bool', default=True),
        wait_timeout=dict(type='int', default=120),
    )

    result = dict(
        changed=False,
        msg='',
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False,
        required_if=[
            ('action', 'download', ['collection_name', 'dest']),
        ]
    )

    galaxy = GalaxyService(module)

    success, msg = galaxy.authenticate()
    if not success:
        module.fail_json(msg=msg)

    if module.params['action'] == 'validate':
        status_result = galaxy.check_status()
        result['api_status'] = status_result['api_status']
        result['database_connected'] = status_result['database_connected']
        result['redis_connected'] = status_result['redis_connected']
        result['components'] = status_result['components']
        result['collections_count'] = status_result['collections_count']

        if status_result['api_status'] == 200:
            result['msg'] = 'Galaxy service is healthy'
            if status_result['database_connected']:
                module.exit_json(**result)
            else:
                module.fail_json(msg='Galaxy service has issues - database not connected')
        else:
            module.fail_json(msg='Galaxy API returned status: %s' % status_result['api_status'])

    elif module.params['action'] == 'upload':
        upload_result = galaxy.upload_collection(module.params.get('src'))
        result['upload_result'] = upload_result
        result['changed'] = True

        if upload_result.get('error'):
            module.fail_json(msg="Upload failed: %s" % upload_result['error'])
        elif upload_result.get('import_status') == 'success':
            result['msg'] = 'Collection uploaded and imported successfully'
            module.exit_json(**result)
        else:
            result['msg'] = 'Collection uploaded (import status: %s)' % upload_result.get('import_status', 'unknown')
            module.exit_json(**result)

    elif module.params['action'] == 'download':
        download_result = galaxy.download_collection(
            module.params['collection_name'],
            module.params.get('collection_version'),
            module.params.get('dest')
        )
        result['download_result'] = download_result
        result['changed'] = True

        if download_result.get('error'):
            module.fail_json(msg="Download failed: %s" % download_result['error'])
        else:
            result['msg'] = 'Collection downloaded successfully'
            module.exit_json(**result)

    elif module.params['action'] == 'test':
        status_result = galaxy.check_status()
        result['api_status'] = status_result['api_status']
        result['database_connected'] = status_result['database_connected']
        result['redis_connected'] = status_result['redis_connected']
        result['components'] = status_result['components']

        if status_result['api_status'] != 200:
            module.fail_json(msg='API status check failed')

        upload_result = galaxy.upload_collection()
        result['upload_result'] = upload_result

        if upload_result.get('error'):
            module.fail_json(msg='Upload failed: %s' % upload_result['error'])

        result['msg'] = 'Galaxy service validation complete'
        if status_result['database_connected'] and upload_result.get('import_status') == 'success':
            module.exit_json(**result)
        else:
            module.fail_json(msg='Validation issues detected')


def main():
    run_module()


if __name__ == '__main__':
    main()
