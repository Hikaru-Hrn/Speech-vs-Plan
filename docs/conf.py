# docs/source/conf.py
import os
import sys

# Устанавливаем переменную окружения для Sphinx
os.environ['SPHINX_BUILD'] = '1'

# Путь к вашему коду
sys.path.insert(0, os.path.abspath('../src'))

# Мокаем зависимости
autodoc_mock_imports = ['requests']

# Настройки проекта
project = 'Speech-vs-Plan'
copyright = '2026, Ilya Gorokhov, Sergey Pleskunov, Maxim Yakimov'
author = 'Ilya Gorokhov, Sergey Pleskunov, Maxim Yakimov'
release = '1.0.0'

# Расширения
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

# Настройки autodoc
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': True,
    'special-members': '__init__',
    'inherited-members': False,
    'show-inheritance': True,
}

# Настройки napoleon (для вашего стиля docstring)
napoleon_google_docstring = False  # Вы используете не Google стиль
napoleon_numpy_docstring = False   # Вы используете не NumPy стиль
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_ivar = True

templates_path = ['_templates']
exclude_patterns = []

language = 'ru'

html_theme = 'alabaster'
html_static_path = ['_static']
