import os, sys
from pathlib import Path

def _patch_all():
    try:
        import zenml.artifact_stores.base_artifact_store as _bs
        def _fixed_validate(self, path):
            rp = str(Path(path).absolute().resolve()).replace('\\', '/')
            cp = str(Path(self.fixed_root_path).absolute().resolve()).replace('\\', '/')
            if not rp.startswith(cp):
                raise FileNotFoundError(
                    f"File `{rp}` is outside of artifact store bounds `{cp}`"
                )
        _bs.BaseArtifactStore._validate_path = _fixed_validate
    except Exception:
        pass
    try:
        import shutil as _shutil
        _orig = _shutil.copyfile
        def _fixed_copyfile(src, dst, **kw):
            src_s = str(Path(src).absolute().resolve()).replace('\\', '/')
            dst_s = str(Path(dst).absolute().resolve()).replace('\\', '/')
            return _orig(src_s, dst_s, **kw)
        _shutil.copyfile = _fixed_copyfile
    except Exception:
        pass

_patch_all()
