from setuptools import setup, find_packages

setup(
    name="ocr_project",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'azure-core',
        'azure-ai-formrecognizer',
        'PyMuPDF',
        'Pillow',
        'python-dotenv',
        'pandas',
        'requests',
        'faker',
        'flask'
    ],
    package_data={
        'ocr_project': ['config/*', 'resources/*'],
    },
    entry_points={
        'console_scripts': [
            'run-ocr=ocr_project.services.main:main',
            'run-web=ocr_project.web.app:main', 
        ],
    }
)