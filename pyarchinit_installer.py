# -*- coding: utf-8 -*-
"""
PyArchInit Installer - Main Plugin Class
"""

import os
import shutil
import tempfile
import zipfile
import configparser
from pathlib import Path

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from qgis.core import QgsApplication

from .installer_dialog import InstallerDialog


class PyArchInitInstaller:
    """QGIS Plugin Implementation."""

    # GitHub repository info
    REPO_OWNER = "pyarchinit"
    REPO_NAME = "pyarchinit"
    MASTER_BRANCH = "master"
    DEV_BRANCH = "feature/qt6-migration"

    GITHUB_ZIP_URL = "https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        # Initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'pyarchinit_installer_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr('&PyArchInit Installer')

        # Network manager for downloads
        self.network_manager = QNetworkAccessManager()
        self.current_reply = None
        self.dialog = None

    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('PyArchInitInstaller', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar."""

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = os.path.join(self.plugin_dir, 'icon.png')

        self.add_action(
            icon_path,
            text=self.tr('Install/Update PyArchInit'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr('&PyArchInit Installer'), action)
            self.iface.removeToolBarIcon(action)

    def get_plugins_path(self):
        """Get the QGIS plugins directory path."""
        return os.path.join(
            QgsApplication.qgisSettingsDirPath(),
            'python', 'plugins'
        )

    def get_existing_pyarchinit_info(self):
        """Check for existing pyarchinit installation and get its info.

        Returns a dict with:
        - exists: bool
        - path: str (path to the plugin folder)
        - version: str (version from metadata.txt if available)
        - folder_name: str (actual folder name)
        """
        plugins_path = self.get_plugins_path()
        result = {
            'exists': False,
            'path': None,
            'version': None,
            'folder_name': None
        }

        # Folders to exclude (this installer plugin)
        exclude_folders = [
            'pyarchinit_installer',
            'pyarchinit-installer'
        ]

        # Check for various possible folder names
        possible_names = [
            'pyarchinit',
            'pyarchinit-master',
            'pyarchinit-main',
            'pyarchinit-feature-qt6-migration',
            'pyarchinit-dev'
        ]

        # Also check for any folder starting with 'pyarchinit' but exclude installer
        if os.path.exists(plugins_path):
            for item in os.listdir(plugins_path):
                item_path = os.path.join(plugins_path, item)
                # Skip if it's the installer plugin
                if item.lower() in [x.lower() for x in exclude_folders]:
                    continue
                if os.path.isdir(item_path) and item.lower().startswith('pyarchinit'):
                    if item not in possible_names:
                        possible_names.append(item)

        for name in possible_names:
            # Skip installer folders
            if name.lower() in [x.lower() for x in exclude_folders]:
                continue

            plugin_path = os.path.join(plugins_path, name)
            if os.path.exists(plugin_path) and os.path.isdir(plugin_path):
                # Verify it's actually pyarchinit by checking metadata.txt name
                metadata_path = os.path.join(plugin_path, 'metadata.txt')
                if os.path.exists(metadata_path):
                    try:
                        config = configparser.ConfigParser()
                        config.read(metadata_path)
                        plugin_name = config.get('general', 'name', fallback='').lower()
                        # Skip if this is the installer
                        if 'installer' in plugin_name:
                            continue
                        result['exists'] = True
                        result['path'] = plugin_path
                        result['folder_name'] = name
                        result['version'] = config.get('general', 'version', fallback='Unknown')
                    except Exception:
                        # If we can't read metadata, assume it's pyarchinit
                        result['exists'] = True
                        result['path'] = plugin_path
                        result['folder_name'] = name
                        result['version'] = 'Unknown'
                else:
                    # No metadata.txt, might be pyarchinit without metadata
                    result['exists'] = True
                    result['path'] = plugin_path
                    result['folder_name'] = name
                    result['version'] = 'Unknown'

                if result['exists']:
                    break  # Found one, stop searching

        return result

    def download_branch(self, branch, callback):
        """Download a branch from GitHub as a zip file.

        :param branch: Branch name to download
        :param callback: Function to call when download completes
        """
        url = self.GITHUB_ZIP_URL.format(
            owner=self.REPO_OWNER,
            repo=self.REPO_NAME,
            branch=branch
        )

        request = QNetworkRequest(QUrl(url))
        request.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)

        self.current_reply = self.network_manager.get(request)
        self.current_reply.finished.connect(lambda: callback(self.current_reply))

        return self.current_reply

    def install_plugin(self, branch, progress_callback=None, finished_callback=None):
        """Download and install the plugin from the specified branch.

        :param branch: Branch to install ('master' or 'dev')
        :param progress_callback: Function to call with progress updates
        :param finished_callback: Function to call when finished (success, message)
        """
        actual_branch = self.MASTER_BRANCH if branch == 'master' else self.DEV_BRANCH

        if progress_callback:
            progress_callback(f"Downloading {branch} branch...")

        def on_download_complete(reply):
            if reply.error() != QNetworkReply.NoError:
                if finished_callback:
                    finished_callback(False, f"Download error: {reply.errorString()}")
                return

            try:
                if progress_callback:
                    progress_callback("Download complete. Installing...")

                # Save to temp file
                temp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(temp_dir, 'pyarchinit.zip')

                with open(zip_path, 'wb') as f:
                    f.write(reply.readAll().data())

                if progress_callback:
                    progress_callback("Extracting files...")

                # Extract zip
                extract_dir = os.path.join(temp_dir, 'extracted')
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                # Find the extracted folder (it will have a branch-specific name)
                extracted_folders = os.listdir(extract_dir)
                if not extracted_folders:
                    if finished_callback:
                        finished_callback(False, "No files found in downloaded archive")
                    return

                source_folder = os.path.join(extract_dir, extracted_folders[0])

                if progress_callback:
                    progress_callback("Checking existing installation...")

                # Get plugins path and target path
                plugins_path = self.get_plugins_path()
                target_path = os.path.join(plugins_path, 'pyarchinit')

                # Remove any existing pyarchinit installations
                existing = self.get_existing_pyarchinit_info()
                if existing['exists']:
                    if progress_callback:
                        progress_callback(f"Removing existing installation: {existing['folder_name']}...")
                    try:
                        shutil.rmtree(existing['path'])
                    except Exception as e:
                        if finished_callback:
                            finished_callback(False, f"Failed to remove existing installation: {str(e)}")
                        return

                # Also check if target exists (in case folder name was different)
                if os.path.exists(target_path):
                    if progress_callback:
                        progress_callback("Removing old pyarchinit folder...")
                    shutil.rmtree(target_path)

                if progress_callback:
                    progress_callback("Copying new plugin files...")

                # Copy new plugin to plugins directory
                shutil.copytree(source_folder, target_path)

                # Clean up temp directory
                if progress_callback:
                    progress_callback("Cleaning up...")
                shutil.rmtree(temp_dir)

                # Get installed version
                new_info = self.get_existing_pyarchinit_info()
                version = new_info.get('version', 'Unknown')

                if finished_callback:
                    finished_callback(True, f"PyArchInit {branch} (v{version}) installed successfully!\n\nPlease restart QGIS to load the plugin.")

            except Exception as e:
                if finished_callback:
                    finished_callback(False, f"Installation error: {str(e)}")

        self.download_branch(actual_branch, on_download_complete)

    def run(self):
        """Run method that performs all the real work."""
        # Create and show the dialog
        self.dialog = InstallerDialog(self)

        # Get current installation info
        existing = self.get_existing_pyarchinit_info()
        self.dialog.update_current_status(existing)

        self.dialog.show()
