import os.path as osp
from odoo import models


class Build(models.Model):
    _inherit = 'runbot.build'

    def _cmd(
            self, python_params=None, py_version=None,
            local_only=True, sub_command=None
    ):
        command = super()._cmd(
            python_params=python_params, py_version=py_version,
            local_only=local_only, sub_command=sub_command
        )
        pres = command.pres
        py_version = (py_version
                      if py_version is not None
                      else self._get_py_version()
                      )
        pip = 'pip%s' % py_version
        pres.append(['sudo', pip, 'install', 'setuptools-odoo'])
        server_commit = self._get_server_commit()
        sourcepath = self._docker_source_folder(server_commit)
        odoo_short_version = self.version_id.number.split('.')[0]
        pres.append(['cp', '-r', sourcepath, '/tmp'])
        pres.append([
            'sudo', pip, 'install', '-e', osp.join('/tmp', sourcepath)
        ])
        pres.append(['rm', '-f', 'test_requirements.txt'])
        pres.append(['touch', 'test_requirements.txt'])
        for commit in (
                self.env.context.get('defined_commit_ids') or
                self.params_id.commit_ids
        ):
            if not commit.repo_id.manifest_files:
                continue
            if commit == server_commit:
                continue
            repo_dir = self._docker_source_folder(commit)
            cp_repo_dir = osp.join('/tmp', repo_dir)
            pres.append(['cp', '-r', repo_dir, '/tmp'])
            pres.append([
                'setuptools-odoo-make-default',
                '--clean',
                '--addons-dir',
                cp_repo_dir
            ])
            setup_dir =  osp.join(cp_repo_dir, 'setup')
            pres.append([
                'for addon in $(ls %s -I README -I _metapackage) ; do '
                'echo "-e file://%s/setup/${addon}#egg=odoo%s-addon-${addon}" >> test_requirements.txt ; '
                'done'
                %
                (setup_dir, cp_repo_dir, odoo_short_version)])
        pres.append([
            'sudo', pip, 'install', '--pre', '-r', 'test_requirements.txt',
            # I get a crash installing pyyaml when using this, removing for now
            # '--extra-index-url', 'https://wheelhouse.odoo-community.org/oca-simple/'
        ])
        return command

    def _get_addons_path(self):
        # we copy in /tmp to get a RW directory that can be installed in
        # develop mode
        for path in super()._get_addons_path():
            yield osp.join('/tmp', path)
