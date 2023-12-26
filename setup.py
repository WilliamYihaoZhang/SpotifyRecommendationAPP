#a file to store all the requirements for the app and service

from setuptools import setup, find_packages

requires = [
    'flask',
    'spotipy',
    'html5lib',
    'requests',
    'requests_html',
    'beautifulsoup4',
    'pathlib',
    'pandas'
]

setup(
    name='SpotifyRecommendations',
    version='1.0',
    description='An application that retrieves Spotify users top songs, to give recommendations',
    author='WilliamZhang',
    author_email='williamyihaozhang@gmail.com',
    keywords='web flask',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires
)