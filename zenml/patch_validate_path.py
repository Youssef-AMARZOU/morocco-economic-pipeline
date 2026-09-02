fp = '/opt/venv/lib/python3.12/site-packages/zenml/artifact_stores/base_artifact_store.py'
c = open(fp).read()
old = "        from pathlib import Path as _P\n        resolved_root = str(_P(self.fixed_root_path).absolute().resolve())\n        if not path.startswith(resolved_root):\n            raise FileNotFoundError(\n                f\"File {path_n} is outside of \"\n                f\"artifact store bounds {root_n}\"\n            )"
new = "        from pathlib import Path as _P\n        resolved_root = str(_P(self.fixed_root_path).absolute().resolve()).replace(chr(92), '/')\n        path_normalized = str(_P(path).absolute().resolve()).replace(chr(92), '/')\n        if not path_normalized.startswith(resolved_root):\n            raise FileNotFoundError(\n                f\"File {path_normalized} is outside of \"\n                f\"artifact store bounds {resolved_root}\"\n            )"
print('old found:', old in c)
c = c.replace(old, new)
print('new found after replace:', 'path_normalized' in c)
open(fp,'w').write(c)
print('Patched!')
