from distutils.spawn import find_executable
from setuptools import setup, Extension, __version__ as setuptools_version
from setuptools.command.build_ext import build_ext
import subprocess
import sys
import os
import shutil

VERSION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VERSION')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
README = open(os.path.join(SCRIPT_DIR, "README.md")).read()

if not os.path.exists(os.path.join(os.path.dirname(__file__), '.git')):
    use_scm_version = False
    shutil.copy('VERSION', 'retro/VERSION.txt')
else:
    def version_scheme(version):
        with open(VERSION_PATH) as v:
            version_file = v.read().strip()
        if version.distance:
            version_file += '.dev%d' % version.distance
        return version_file

    def local_scheme(version):
        v = ''
        if version.distance:
            v = '+' + version.node
        return v
    use_scm_version = {'write_to': 'retro/VERSION.txt',
                       'version_scheme': version_scheme,
                       'local_scheme': local_scheme}


class CMakeBuild(build_ext):
    def run(self):
        suffix = super(CMakeBuild, self).get_ext_filename('')
        pyext_suffix = '-DPYEXT_SUFFIX:STRING=%s' % suffix
        pylib_dir = ''
        if not self.inplace:
            pylib_dir = '-DPYLIB_DIRECTORY:PATH=%s' % self.build_lib
        if self.debug:
            build_type = '-DCMAKE_BUILD_TYPE=Debug'
        else:
            build_type = ''
        python_executable = '-DPYTHON_EXECUTABLE:STRING=%s' % sys.executable
        cmake_exe = find_executable('cmake')
        if not cmake_exe:
            try:
                import cmake
            except ImportError:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'cmake'])
                import cmake
            cmake_exe = os.path.join(cmake.CMAKE_BIN_DIR, 'cmake')
        subprocess.check_call([cmake_exe, '.', '-G', 'Unix Makefiles', build_type, pyext_suffix, pylib_dir, python_executable])
        if self.parallel:
            jobs = '-j%d' % self.parallel
        else:
            import multiprocessing
            jobs = '-j%d' % multiprocessing.cpu_count()
        make_exe = find_executable('make')
        if not make_exe:
            raise RuntimeError('Could not find Make executable. Is it installed?')
        subprocess.check_call([make_exe, jobs, 'retro'])
        cwd = os.getcwd()
        os.chdir(f'{os.path.dirname(__file__)}/Dispel')
        subprocess.check_call([make_exe])
        os.chdir(cwd)



platform_globs = ['*-%s/*' % plat for plat in ['Nes', 'Snes', 'Genesis', 'Atari2600', 'GameBoy', 'Sms', 'GameGear', 'PCEngine', 'GbColor', 'GbAdvance']]

kwargs = {}
if tuple(int(v) for v in setuptools_version.split('.')[:3]) >= (24, 2, 0):
    kwargs['python_requires'] = '>=3.6.0'


setup(
    name='gym-retro',
    long_description=README,
    long_description_content_type="text/markdown",
    author='OpenAI',
    author_email='csh@openai.com',
    url='https://github.com/openai/retro',
    version=open(VERSION_PATH, 'r').read().strip(),
    license='MIT',
    install_requires=['gym', 'pyglet>=1.3.2,==1.*,<=1.5.0', 'sysv_ipc==1.1.0'],
    ext_modules=[Extension('retro._retro', ['CMakeLists.txt', 'src/*.cpp'])],
    cmdclass={'build_ext': CMakeBuild},
    packages=['retro', 'retro.data', 'retro.data.stable', 'retro.data.experimental', 'retro.data.contrib', 'retro.scripts', 'retro.import', 'retro.examples'],
    package_data={
        'retro': ['cores/*.json', 'cores/*_libretro*', 'VERSION.txt', 'README.md', 'LICENSES.md'],
        'retro.data.stable': platform_globs,
        'retro.data.experimental': platform_globs,
        'retro.data.contrib': platform_globs,
    },
    extras_require={'docs': ['sphinx', 'sphinx_rtd_theme', 'sphinx-autobuild', 'm2r']},
    setup_requires=['setuptools_scm'],
    use_scm_version=use_scm_version,
    **kwargs
)
