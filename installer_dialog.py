# -*- coding: utf-8 -*-
"""
PyArchInit Installer - Dialog UI
"""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QGroupBox, QTextEdit, QProgressBar,
    QFrame, QMessageBox
)
from qgis.PyQt.QtGui import QFont


class InstallerDialog(QDialog):
    """Dialog for PyArchInit Installer."""

    def __init__(self, installer, parent=None):
        """Constructor.

        :param installer: The PyArchInitInstaller instance
        :param parent: Parent widget
        """
        super().__init__(parent)
        self.installer = installer
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("PyArchInit Installer")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Title
        title_label = QLabel("PyArchInit Installer")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Subtitle
        subtitle = QLabel("Install or update PyArchInit plugin from GitHub")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: gray;")
        layout.addWidget(subtitle)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Current installation status
        status_group = QGroupBox("Current Installation")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("Checking...")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)

        self.version_label = QLabel("")
        self.version_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.version_label)

        self.path_label = QLabel("")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: gray; font-size: 10px;")
        status_layout.addWidget(self.path_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Branch selection
        branch_group = QGroupBox("Select Version to Install")
        branch_layout = QVBoxLayout()

        self.branch_button_group = QButtonGroup(self)

        self.master_radio = QRadioButton("Master (Stable)")
        self.master_radio.setToolTip("Download the stable master branch")
        self.master_radio.setChecked(True)
        self.branch_button_group.addButton(self.master_radio, 0)
        branch_layout.addWidget(self.master_radio)

        master_desc = QLabel("    Recommended for production use")
        master_desc.setStyleSheet("color: gray; font-size: 10px;")
        branch_layout.addWidget(master_desc)

        self.dev_radio = QRadioButton("Development (Qt6 Migration)")
        self.dev_radio.setToolTip("Download the qt6-migration development branch")
        self.branch_button_group.addButton(self.dev_radio, 1)
        branch_layout.addWidget(self.dev_radio)

        dev_desc = QLabel("    Latest features, may be unstable (branch: feature/qt6-migration)")
        dev_desc.setStyleSheet("color: gray; font-size: 10px;")
        branch_layout.addWidget(dev_desc)

        branch_group.setLayout(branch_layout)
        layout.addWidget(branch_group)

        # Progress section
        progress_group = QGroupBox("Installation Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.log_text.setPlaceholderText("Installation log will appear here...")
        progress_layout.addWidget(self.log_text)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.install_button = QPushButton("Install / Update")
        self.install_button.setMinimumHeight(40)
        self.install_button.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1b5e20;
            }
            QPushButton:disabled {
                background-color: #a5d6a7;
            }
        """)
        self.install_button.clicked.connect(self.on_install_clicked)
        button_layout.addWidget(self.install_button)

        self.close_button = QPushButton("Close")
        self.close_button.setMinimumHeight(40)
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

        # Warning label
        warning_label = QLabel(
            "Note: After installation, you need to restart QGIS to load the plugin."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #ff9800; font-size: 10px;")
        warning_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(warning_label)

        self.setLayout(layout)

    def update_current_status(self, info):
        """Update the current installation status display.

        :param info: Dict with exists, path, version, folder_name
        """
        if info['exists']:
            self.status_label.setText("PyArchInit is currently installed")
            self.status_label.setStyleSheet("color: #2e7d32;")
            self.version_label.setText(f"Version: {info['version'] or 'Unknown'}")
            self.path_label.setText(f"Location: {info['path']}")

            if info['folder_name'] != 'pyarchinit':
                self.log_message(f"Warning: Plugin folder is named '{info['folder_name']}' instead of 'pyarchinit'")
        else:
            self.status_label.setText("PyArchInit is not installed")
            self.status_label.setStyleSheet("color: #f44336;")
            self.version_label.setText("")
            self.path_label.setText(f"Plugins path: {self.installer.get_plugins_path()}")

    def log_message(self, message):
        """Add a message to the log.

        :param message: Message to add
        """
        self.log_text.append(message)
        # Scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_install_clicked(self):
        """Handle install button click."""
        branch = 'master' if self.master_radio.isChecked() else 'dev'

        # Confirm installation
        existing = self.installer.get_existing_pyarchinit_info()
        if existing['exists']:
            reply = QMessageBox.question(
                self,
                'Confirm Installation',
                f"This will replace the existing PyArchInit installation.\n\n"
                f"Current version: {existing['version'] or 'Unknown'}\n"
                f"Current folder: {existing['folder_name']}\n\n"
                f"Install {branch} branch?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # Disable UI during installation
        self.install_button.setEnabled(False)
        self.master_radio.setEnabled(False)
        self.dev_radio.setEnabled(False)
        self.progress_bar.setVisible(True)

        self.log_text.clear()
        self.log_message(f"Starting installation of {branch} branch...")

        # Start installation
        self.installer.install_plugin(
            branch,
            progress_callback=self.on_progress,
            finished_callback=self.on_finished
        )

    def on_progress(self, message):
        """Handle progress updates.

        :param message: Progress message
        """
        self.log_message(message)

    def on_finished(self, success, message):
        """Handle installation completion.

        :param success: Whether installation succeeded
        :param message: Result message
        """
        self.progress_bar.setVisible(False)
        self.install_button.setEnabled(True)
        self.master_radio.setEnabled(True)
        self.dev_radio.setEnabled(True)

        if success:
            self.log_message("Installation completed successfully!")
            QMessageBox.information(self, "Installation Complete", message)

            # Update status display
            existing = self.installer.get_existing_pyarchinit_info()
            self.update_current_status(existing)
        else:
            self.log_message(f"Installation failed: {message}")
            QMessageBox.critical(self, "Installation Failed", message)
