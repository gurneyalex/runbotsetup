import ast
import logging
import os.path as osp
from odoo import fields, models

_logger = logging.getLogger(__name__)


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
            setup_dir = osp.join(cp_repo_dir, 'setup')
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

    def _get_available_modules_in_trigger_repos(self):
        available_modules = {}
        dependency_repos = self.trigger_id.dependency_ids
        for commit in (self.env.context.get('defined_commit_ids') or
                       self.params_id.commit_ids):
            for (addons_path,
                 module,
                 manifest_path) in commit._get_available_modules():
                if commit.repo_id in dependency_repos:
                    # we don't want modules from the dependency repositories
                    continue
                _logger.info('checking: %r/%r/%r', addons_path, module, manifest_path)
                try:
                    dirname = commit._source_path()
                    filename = osp.join(dirname, addons_path, module, manifest_path)
                    manifest = ast.literal_eval(open(filename).read())
                    if manifest.get('installable', True):
                        depends = manifest.get('depends', ['base'])
                        available_modules[module] = depends
                except OSError as exc:
                    _logger.warn('%s', exc)
        return available_modules


class BuildConfigStep(models.Model):
    _inherit = 'runbot.build.config.step'

    install_dependencies = fields.Boolean(
        'Install Dependencies',
        default=False, tracking=True,
        help='only install the dependencies of the trigger modules')

    def _dependency_modules_to_install(self, build):
        mods_to_install = self._modules_to_install(build)
        mods_in_trigger_repos = build._get_available_modules_in_trigger_repos()
        trigger_modules = set(mods_in_trigger_repos)
        dependencies = set()
        for mod, deps in mods_in_trigger_repos.items():
            # we consider only the dependencies of modules which should be
            # installed (to take the filters into accound)
            if mod in mods_to_install:
                dependencies |= set(deps)
        dependencies -= trigger_modules
        return dependencies

    def _run_install_odoo(self, build, log_path):
        cmd = super()._run_install_odoo(build, log_path)
        command = cmd['cmd']
        if self.install_dependencies:
            # XXX maybe we want to rebuild a command with just the addons path
            # and the modules to install
            pres = command.pres
            preinstall = command.cmd.copy()
            (server_commit, server_file) = build._get_server_info()
            server_dir = build._docker_source_folder(server_commit)
            idx = preinstall.index(osp.join(server_dir, server_file))
            if self.sub_command:
                # remove subcommand
                del preinstall[idx+1]
            # remove coverage / flamegraph
            preinstall[:idx] = [preinstall[0]]
            # disable tests
            try:
                preinstall.remove('--test-enable')
            except ValueError:
                pass
            idx = preinstall.index('-i')
            dependencies = self._dependency_modules_to_install(build)
            build._log(
                'install_odoo',
                'Will pre-install the following dependencies: %s' %
                ", ".join(dependencies)
            )
            preinstall[idx+1] = ",".join(dependencies)
            if '--log-level=test' in preinstall:
                preinstall.remove('--log-level=test')
            preinstall.append('--log-level=warn')
            pres.append(['echo', '"Preinstallation of dependencies: %s"' %
                         ", ".join(dependencies)])
            pres.append(['echo', '"This may take a while"'])
            pres.append(preinstall)
            pres.append(['echo', '"Done preinstalling dependencies"'])
        _logger.info('command.pres: %s', command.pres)
        _logger.info('command.cmd: %s', command.cmd)
        return cmd
