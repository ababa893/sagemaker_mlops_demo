import os
from pathlib import Path, PosixPath
import platform
import json
import sys
import subprocess
import re
from datetime import datetime

from git import Repo

sd = Path(__file__).parent.resolve()
sys.path.append(str(sd))


class ConfigManager(object):
    def create_config(self, dst_path):
        """trainer用の設定を新規作成する．
        
        パス・URI等はここで設定する必要はない．
        trainer.pyで指定した引数に応じてあとで
        出力先の設定JSONファイルにすべて記録される
        
        Parameters
        ----------
        dst_path : str
            設定ファイルの出力先パス
        """
        # trainer用の設定に必要な情報の取得
        repo_root = 5
        repo = Repo(sd.parents[repo_root])
        pip_freezed = subprocess.run(['pip', 'freeze'], stdout=subprocess.PIPE)
        packages = pip_freezed.stdout.decode('utf-8').split()
        self.dst_path = self._dst_path_w_timestamp(dst_path)

        # 設定の新規作成
        config = {
            'config_path': Path(self.dst_path).resolve(),  # training時のみ使用
            'hyper_params': {
                'random_state': 0,
                'solver': 'lbfgs',
                'class_weight': 'balanced',
                'n_jobs': -1,
                'cv': 5,
                'return_train_score': True
            },
            'python': {
                'interpreter': sys.executable,
                'version': platform.python_version(),
                'packages': packages
            },
            'repository': {
                'active_branch': repo.active_branch.name,
                'commit_version': repo.active_branch.commit.hexsha
            },
            'train_datetime': self.train_dt
        }
        self.save_config(config, self.dst_path)

    def _dst_path_w_timestamp(self, dst_path):
        self.train_dt = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
        if isinstance(dst_path, PosixPath):
            dst_path = str(dst_path)
        dst_path = dst_path.replace('.json', '')
        dst_path += f'_{self.train_dt}.json'
        return dst_path

    def remove_info(self, config_path, target_keys):
        with open(config_path, encoding='utf-8') as f:
            config = json.load(f)

        for k in target_keys:
            if k in config:
                config.pop(k)

        self.save_config(config, config_path)

    def add_info(self, config_path, target_dict):
        with open(config_path, encoding='utf-8') as f:
            config = json.load(f)

        for k, v in target_dict.items():
            config[k] = v

        self.save_config(config, config_path)

    def save_config(self, config, config_path):
        config = self._posixpath2str(config)
        if isinstance(config_path, PosixPath):
            os.makedirs(config_path.parent, exist_ok=True)
        else:
            os.makedirs(Path(config_path).parent, exist_ok=True)
        with open(config_path, 'w', encoding='utf8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    def _posixpath2str(self, target_dict):
        if isinstance(target_dict, dict):
            for k, v in target_dict.items():
                if isinstance(v, dict):
                    target_dict[k] = self._posixpath2str(v)
                if isinstance(v, list):
                    target_dict[k] = \
                        [self._posixpath2str(v_val) for v_val in v]
                elif isinstance(v, PosixPath):
                    target_dict[k] = str(v)
        return target_dict

    def load_config(self, config_path, expected_keys):
        with open(config_path, encoding='utf-8') as f:
            config = json.load(f)

        # 想定する例外
        if not isinstance(config, dict):
            errmsg = f'設定ファイルが{type(config)}型となっている．' \
                + 'dictでなければならない．'
            raise TypeError(errmsg)

        from utils import Utils
        Utils.validate_dict(config, expected_keys)

        return config

    def get_newest_filepath(self, config_dir, searchmode=None):
        path_config_dir = Path(config_dir)
        if not path_config_dir.exists():
            raise IOError(f'{config_dir}が存在しません．')
        config_filepaths = path_config_dir.glob('*.json')
        config_filepaths = list(map(str, config_filepaths))

        if searchmode == 'filename':
            pattern = r'.*_'
            created_times = \
                [re.sub(pattern, '', cfp) for cfp in config_filepaths]
            created_latest = sorted(created_times, reverse=True)[0]
            newest_filepath = None
            for cfp in config_filepaths:
                if cfp.endswith(created_latest):
                    newest_filepath = cfp
        else:
            max_birthtime = 0
            newest_filepath = None
            for cf in config_filepaths:
                birthtime = self._creation_date(cf)
                if max_birthtime < birthtime:
                    max_birthtime = birthtime
                    newest_filepath = cf

        return Path(newest_filepath)

    def _creation_date(self, path_to_file):
        """
        Ref: https://bit.ly/36AcG6R
        """
        if platform.system() == 'Windows':
            return os.path.getctime(path_to_file)
        else:
            stat = os.stat(path_to_file)
            try:
                return stat.st_birthtime
            except AttributeError:
                # We're probably on Linux.
                # No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                return stat.st_mtime
